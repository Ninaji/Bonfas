"""
Backend Flask — expõe dados de raças/linhagens/essências/traços e persiste
o equipamento do personagem em SQLite.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, redirect, request, send_from_directory
from flask_cors import CORS

BASE = Path(__file__).parent
DB_PATH = BASE / "bonfas.db"

# ---------------------------------------------------------------------------
# Vocabulário canônico D&D 5.5e BR (Bonfire Tales). Tags fora destas listas
# são silenciosamente ignoradas (com log) — evita typos virarem dado real.
# ---------------------------------------------------------------------------
ELEMENTOS_CANONICOS: frozenset[str] = frozenset({
    "Ácido", "Concussão", "Cortante", "Energia", "Fogo", "Frio",
    "Necrótico", "Perfurante", "Psíquico", "Radiante", "Raio",
    "Trovejante", "Veneno",
})

# ---------------------------------------------------------------------------
# Tags FLAG (binárias) — só presença/ausência, sem valor após dois-pontos.
#
#   "magico" — fonte do dano/efeito é mágica (presença=sim, ausência=não).
#              Aplica-se quando o texto da hab/item diz "mágico" (ex.: ataques
#              de Patrono Mágico, Wraps of Unarmed Power, +X Weapon, etc).
#              NÃO confundir com 'ataque-magico' (eixo de ROLAGEM — abaixo).
#              É binário: se tem 'mágico' no texto → tag presente; senão, não.
#              Reservada para uso futuro (resistência por fonte, bypass de
#              resistências de monstros, etc).
#
# ATAQUES — taxonomia imutável (regra do sistema; não modificar). 4 tags
# combinadas em 2 eixos ortogonais:
#
#   Eixo 1 (distância):
#     "ataque-corpo-a-corpo" — alvo até 1,5m (5ft) ou alcance da arma corpo.
#     "ataque-distancia"     — alvo a partir do alcance da arma/magia.
#
#   Eixo 2 (rolagem de acerto):
#     "ataque-fisico"  — usa Mod-FOR/DES + BP. Inclui armas, desarmado,
#                        armas naturais. Tem 3 SUBTIPOS (filhos):
#         "ataque-desarmado"     — punho, cotovelo, joelho (Monge etc).
#         "ataque-com-arma"      — espada, arco, etc.
#         "ataque-arma-natural"  — garras, chifres, presas, mordida.
#       Talentos/efeitos podem interagir só com 1 dos subtipos (ex: Wraps
#       of Unarmed Power afeta apenas 'ataque-desarmado').
#     "ataque-magico"  — usa Mod-CONJURAÇÃO + BP (cantrip de ataque, magia
#                        com jogada de ataque). Distinto de 'magico' (fonte).
#
#   Combinações típicas: corpo+físico (espada), distância+físico (arco),
#   corpo+mágico (toque-mágico), distância+mágico (Raio Eldritch).
#   Habs/talentos declaram QUAIS combinações afetam — interaçãode efeitos
#   (ex: bônus de dano em ataques corpo-a-corpo físicos com arma natural).
#
# Outras flags já em uso: 'conjurador', 'segredos', 'inimigo-favorito',
# 'evolucao-totemica', 'estilos-ki', 'alianca-selvagem-companheiro-{terra,ceu,mar}'.
# ---------------------------------------------------------------------------

CONDICOES_CANONICAS: frozenset[str] = frozenset({
    "Agarrado", "Amedrontado", "Atordoado", "Caído", "Cego",
    "Doente",  # imune a doenças (Saúde Divina do Paladino Nv 3)
    "Enfeitiçado", "Envenenado", "Exaustão", "Incapacitado",
    "Inconsciente", "Invisível", "Paralisado", "Petrificado",
    "Restringido", "Surdo",
})

# 18 perícias D&D 5.5e — toda ficha precisa ter as mesmas. Inseridas
# automaticamente em personagem_full quando ausentes (idempotente via UNIQUE).
PERICIAS_PADRAO: tuple[tuple[str, str], ...] = (
    ("Acrobacia",         "DES"),
    ("Adestrar Animais",  "SAB"),
    ("Arcanismo",         "INT"),
    ("Atletismo",         "FOR"),
    ("Atuação",           "CAR"),
    ("Enganação",         "CAR"),
    ("Furtividade",       "DES"),
    ("História",          "INT"),
    ("Intimidação",       "CAR"),
    ("Intuição",          "SAB"),
    ("Investigação",      "INT"),
    ("Medicina",          "SAB"),
    ("Natureza",          "INT"),
    ("Percepção",         "SAB"),
    ("Persuasão",         "CAR"),
    ("Prestidigitação",   "DES"),
    ("Religião",          "INT"),
    ("Sobrevivência",     "SAB"),
)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        # tabela auxiliar para persistir fichas de equipamento
        conn.execute(
            """CREATE TABLE IF NOT EXISTS TB_EquipamentoPersonagem (
                   Id          INTEGER PRIMARY KEY AUTOINCREMENT,
                   CharacterId TEXT    NOT NULL UNIQUE,
                   Payload     TEXT    NOT NULL,
                   UpdatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP
               )"""
        )
        conn.commit()
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def rows(q: str, *a) -> list[dict]:
    return [dict(r) for r in db().execute(q, a).fetchall()]


def one(q: str, *a) -> dict | None:
    r = db().execute(q, a).fetchone()
    return dict(r) if r else None


# ---------------------------------------------------------------------------
# Página + estáticos
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/demo")
def demo():
    return send_from_directory("templates", "index.html")


# ---------------------------------------------------------------------------
# API: raças
# ---------------------------------------------------------------------------
@app.get("/api/racas")
def list_racas():
    return jsonify(rows("SELECT * FROM TB_Raca ORDER BY Nome"))


@app.get("/api/racas/<slug>")
def get_raca(slug: str):
    raca = one("SELECT * FROM TB_Raca WHERE Slug = ?", slug)
    if not raca:
        return jsonify({"error": "not found"}), 404
    raca["linhagens"] = rows(
        "SELECT * FROM TB_Linhagem WHERE Id_Raca = ? ORDER BY Nome", raca["Id_Raca"]
    )
    raca["tracos"] = rows(
        "SELECT * FROM TB_TracoRacial WHERE Id_Raca = ? ORDER BY NivelRequisito, Nome",
        raca["Id_Raca"],
    )
    return jsonify(raca)


@app.get("/api/linhagens")
def list_linhagens():
    return jsonify(rows(
        """SELECT l.*, r.Nome AS RacaNome, r.Slug AS RacaSlug
             FROM TB_Linhagem l JOIN TB_Raca r ON r.Id_Raca = l.Id_Raca
             ORDER BY r.Nome, l.Nome"""
    ))


@app.get("/api/essencias")
def list_essencias():
    return jsonify(rows("SELECT * FROM TB_Essencia ORDER BY Nome"))


@app.get("/api/essencias/<slug>/linhagens")
def essencia_linhagens(slug: str):
    e = one("SELECT Id_Essencia FROM TB_Essencia WHERE Slug = ?", slug)
    if not e:
        return jsonify([])
    return jsonify(rows(
        "SELECT * FROM TB_EssenciaLinhagem WHERE Id_Essencia = ? ORDER BY Nome",
        e["Id_Essencia"],
    ))


@app.get("/api/racas/<slug>/linhagens")
def raca_linhagens(slug: str):
    r = one("SELECT Id_Raca, PermiteEssencia FROM TB_Raca WHERE Slug = ?", slug)
    if not r:
        return jsonify([])
    linhagens = rows(
        "SELECT * FROM TB_Linhagem WHERE Id_Raca = ? ORDER BY Nome", r["Id_Raca"]
    )
    # adiciona opção "Essenciata" se raça permite essência
    if r["PermiteEssencia"]:
        linhagens.append({
            "Id_Linhagem": None,
            "Nome": "Essenciata",
            "Slug": "__essenciata",
            "Descricao": "A linhagem vem de uma Essência (Infernal, Celestial...).",
            "__marker": "essencia",
        })
    return jsonify(linhagens)


@app.get("/api/classes/<slug>/subclasses")
def classe_subclasses(slug: str):
    c = one("SELECT Id_Classe FROM TB_Classe WHERE Slug = ?", slug)
    if not c:
        return jsonify([])
    return jsonify(rows(
        "SELECT * FROM TB_Subclasse WHERE Id_Classe = ? ORDER BY Nome", c["Id_Classe"]
    ))


@app.get("/api/tracos")
def list_tracos():
    raca = request.args.get("raca")
    if raca:
        return jsonify(rows(
            """SELECT t.* FROM TB_TracoRacial t
                 JOIN TB_Raca r ON r.Id_Raca = t.Id_Raca
                WHERE r.Slug = ? ORDER BY t.NivelRequisito, t.Nome""",
            raca,
        ))
    return jsonify(rows("SELECT * FROM TB_TracoRacial ORDER BY Id_Raca, NivelRequisito"))


# ---------------------------------------------------------------------------
# API: itens (catálogo — TB_Item / TB_ItemSlot)
# ---------------------------------------------------------------------------
# uma seção da mochila pode aceitar MÚLTIPLOS tipos de slot
# (ex.: "Armas e Escudos" aceita arma, escudo e item empunhado)
# mapeamento seção-da-mochila -> códigos de slot aceitos
#   gloves  = luvas (Wearing_in_Hands)       -> slot corporal "Mãos"
#   held    = empunhado (Holding_in_Hands)   -> vai para Armas ou Varinhas
BAG_TO_SLOT_CODES = {
    "armas":       ["weapon", "shield", "held"],
    "varinhas":    ["wand", "rod", "held"],
    "empunhados":  ["held"],          # seção exclusiva para itens empunhados
    "armaduras":   ["armor"],
    "torso_bag":   ["torso"],
    "costas_bag":  ["back"],
    "cintura_bag": ["waist"],
    "cabeca_bag":  ["head"],
    "rosto_bag":   ["face"],
    "pescoco_bag": ["neck"],
    "bracos_bag":  ["arms"],
    "maos_bag":    ["gloves"],    # apenas luvas
    "pes_bag":     ["feet"],
    "aneis_bag":   ["ring"],
    "flutuando":   ["hovering"],
    "municao":     ["ammunition"],
    "edificacao":  ["building"],
    "pocoes":      ["potion"],
    "pergaminhos": ["scroll"],
    "tatuagens":   ["tattoo"],
    "veiculos":    ["vehicle"],
    "acessorios":  ["accessory"],
}


@app.get("/api/item-slots")
def list_item_slots():
    return jsonify(rows("SELECT * FROM TB_ItemSlot ORDER BY Nome"))


@app.get("/api/items")
def list_items():
    """Busca itens.
       ?q=texto         match em Nome/NomeTraduzido (case-insensitive, substring)
       ?slot=codigo     filtra por s.Codigo OU s.SlotFicha (ex.: weapon, maos)
       ?bag=codigo      filtra por seção da mochila — expande para um OR
                        de códigos de slot compatíveis
       ?limit=50        default 50, max 200
    """
    q     = (request.args.get("q")    or "").strip()
    slot  = (request.args.get("slot") or "").strip().lower()
    bag   = (request.args.get("bag")  or "").strip().lower()
    limit = min(int(request.args.get("limit", 50)), 200)

    where, args = [], []
    if slot:
        # slot pode ser um Codigo (weapon, gloves...) OU um SlotFicha (maos, aneis...)
        where.append("(s.Codigo = ? OR s.SlotFicha = ?)")
        args += [slot, slot]
        # caso especial: slot do corpo "maos" = apenas luvas (não itens empunhados)
    if bag:
        codes = BAG_TO_SLOT_CODES.get(bag, [bag])
        placeholders = ",".join("?" * len(codes))
        where.append(f"s.Codigo IN ({placeholders})")
        args += codes
    if q:
        where.append("(LOWER(i.Nome) LIKE ? OR LOWER(COALESCE(i.NomeTraduzido,'')) LIKE ?)")
        like = f"%{q.lower()}%"
        args += [like, like]

    wsql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""SELECT i.Id_Item, i.Nome, i.NomeTraduzido, i.Slug, i.Source,
                     i.Tipo, i.Attunement, i.Damage, i.Weight, i.Value,
                     s.Codigo AS SlotCodigo, s.Nome AS SlotNome,
                     s.SlotFicha, s.BagSecao
                FROM TB_Item i
           LEFT JOIN TB_ItemSlot s ON s.Id_Slot = i.Id_Slot
                {wsql}
            ORDER BY i.Nome
               LIMIT ?"""
    args.append(limit)
    return jsonify(rows(sql, *args))


# ---------------------------------------------------------------------------
# API: classes / subclasses / recursos / habilidades
# ---------------------------------------------------------------------------
# endpoint temporário para receber dumps do scraper via fetch no navegador
@app.put("/api/dump/<name>")
def put_dump(name: str):
    if not re.fullmatch(r"[a-zA-Z0-9_\-]+", name):
        return jsonify({"error": "nome inválido"}), 400
    p = BASE / f"dump_{name}.json"
    raw = request.get_data(as_text=True)
    p.write_text(raw, encoding="utf-8")
    return jsonify({"ok": True, "bytes": len(raw), "path": str(p)})


@app.get("/api/classes")
def list_classes():
    return jsonify(rows("SELECT * FROM TB_Classe ORDER BY Nome"))


@app.get("/api/classes/<slug>")
def get_classe(slug: str):
    c = one("SELECT * FROM TB_Classe WHERE Slug = ?", slug)
    if not c:
        return jsonify({"error": "not found"}), 404
    c["subclasses"] = rows(
        "SELECT * FROM TB_Subclasse WHERE Id_Classe = ? ORDER BY Nome",
        c["Id_Classe"],
    )
    c["recursos"] = rows(
        "SELECT * FROM TB_RecursoClasse WHERE Id_Classe = ? ORDER BY Nivel, Nome",
        c["Id_Classe"],
    )
    c["habilidades"] = rows(
        "SELECT * FROM TB_ClasseHabilidade WHERE Id_Classe = ? ORDER BY NivelAdquirido, Nome",
        c["Id_Classe"],
    )
    c["opcoes"] = rows(
        """SELECT o.* FROM TB_OpcaoJogo o
             JOIN TB_AcessoOpcao a ON a.Id_Opcao = o.Id_Opcao
            WHERE a.Id_Classe = ? ORDER BY o.Tipo, o.Nome""",
        c["Id_Classe"],
    )
    return jsonify(c)


@app.get("/api/subclasses/<int:id_sub>")
def get_subclasse(id_sub: int):
    s = one("SELECT * FROM TB_Subclasse WHERE Id_Subclasse = ?", id_sub)
    if not s:
        return jsonify({"error": "not found"}), 404
    s["recursos"] = rows(
        "SELECT * FROM TB_RecursoClasse WHERE Id_Subclasse = ? ORDER BY Nivel, Nome",
        id_sub,
    )
    s["habilidades"] = rows(
        "SELECT * FROM TB_ClasseHabilidade WHERE Id_Subclasse = ? ORDER BY NivelAdquirido, Nome",
        id_sub,
    )
    return jsonify(s)


@app.get("/api/opcoes")
def list_opcoes():
    tipo = request.args.get("tipo")
    if tipo:
        return jsonify(rows("SELECT * FROM TB_OpcaoJogo WHERE Tipo=? ORDER BY Nome", tipo))
    return jsonify(rows("SELECT * FROM TB_OpcaoJogo ORDER BY Tipo, Nome"))


@app.get("/api/items/<int:item_id>")
def get_item(item_id: int):
    r = one(
        """SELECT i.*, s.Codigo AS SlotCodigo, s.Nome AS SlotNome,
                  s.SlotFicha, s.BagSecao
             FROM TB_Item i LEFT JOIN TB_ItemSlot s ON s.Id_Slot = i.Id_Slot
            WHERE i.Id_Item = ?""",
        item_id,
    )
    if not r:
        return jsonify({"error": "not found"}), 404
    return jsonify(r)


# ---------------------------------------------------------------------------
# API: personagens + ficha compilada
# ---------------------------------------------------------------------------
@app.post("/api/personagens")
def create_personagem():
    d = request.get_json(force=True) or {}
    nome = (d.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "nome obrigatório"}), 400
    conn = db()
    cur = conn.execute(
        "INSERT INTO TB_Personagem (Nome, DonoUsuario, Nivel) VALUES (?, ?, ?)",
        (nome[:150], (d.get("dono") or "")[:100] or None, int(d.get("nivel") or 1)),
    )
    pid = cur.lastrowid
    conn.execute(
        """INSERT INTO TB_PersonagemEscolha
               (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
               VALUES (?, NULL, NULL, NULL, NULL, NULL)""",
        (pid,),
    )
    conn.execute("INSERT INTO TB_PersonagemAtributo (Id_Personagem) VALUES (?)", (pid,))
    conn.commit()
    return jsonify({"id": pid, "nome": nome, "nivel": d.get("nivel") or 1})


def _personagem_raw(pid: int) -> dict | None:
    p = one("SELECT * FROM TB_Personagem WHERE Id_Personagem = ?", pid)
    if not p:
        return None
    p["escolha"] = one(
        "SELECT * FROM TB_PersonagemEscolha WHERE Id_Personagem = ?", pid,
    )
    p["atributos"] = one(
        "SELECT * FROM TB_PersonagemAtributo WHERE Id_Personagem = ?", pid,
    )
    return p


@app.get("/api/personagens/<int:pid>")
def get_personagem(pid: int):
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    return jsonify(p)


@app.patch("/api/personagens/<int:pid>")
def update_personagem(pid: int):
    p = one("SELECT Id_Personagem FROM TB_Personagem WHERE Id_Personagem = ?", pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    d = request.get_json(force=True) or {}
    conn = db()
    # campos principais
    allowed = ["Nome", "Nivel", "DonoUsuario", "PVAtual", "PVMaximo", "Patente"]
    sets, args = [], []
    for k in allowed:
        if k in d:
            sets.append(f"{k} = ?")
            args.append(d[k])
    if sets:
        args.append(pid)
        conn.execute(
            f"UPDATE TB_Personagem SET {', '.join(sets)}, AtualizadoEm = CURRENT_TIMESTAMP "
            f"WHERE Id_Personagem = ?",
            args,
        )
    # escolhas (raça/classe/etc)
    esc_fields = ["Id_Raca", "Id_Linhagem", "Id_Essencia", "Id_EssLinhagem",
                  "Id_Classe", "Id_Subclasse", "NivelMultiClasse",
                  "Id_TalentoOrigem", "Id_TalentoOrigemExtra",
                  "Id_TalentoOrigemRacial"]
    e_sets, e_args = [], []
    for k in esc_fields:
        if k in d:
            e_sets.append(f"{k} = ?")
            e_args.append(d[k])
    if e_sets:
        e_args.append(pid)
        conn.execute(
            f"UPDATE TB_PersonagemEscolha SET {', '.join(e_sets)} WHERE Id_Personagem = ?",
            e_args,
        )
    # atributos
    atr_fields = ["Forca", "Destreza", "Constituicao", "Inteligencia", "Sabedoria", "Carisma"]
    a_sets, a_args = [], []
    for k in atr_fields:
        if k in d:
            a_sets.append(f"{k} = ?")
            a_args.append(int(d[k]))
    if a_sets:
        a_args.append(pid)
        conn.execute(
            f"UPDATE TB_PersonagemAtributo SET {', '.join(a_sets)} WHERE Id_Personagem = ?",
            a_args,
        )
    conn.commit()
    return jsonify(_personagem_raw(pid))


@app.put("/api/personagens/<int:pid>/background")
def put_background(pid: int):
    """Grava background do personagem com validação D&D 5.5:
       - bonus: dict {atributo: valor}, soma = 3, máx individual = 2
       - items: lista de {tipo: 'idioma'|'ferramenta', nome: str}, exatamente 2 (opcional)"""
    d = request.get_json(force=True) or {}
    nome = (d.get("nome") or "").strip()[:150]
    bonus = d.get("bonus") or {}
    items = d.get("items") or []

    # validação de bônus
    ATR_VALID = {"Forca","Destreza","Constituicao","Inteligencia","Sabedoria","Carisma"}
    if not isinstance(bonus, dict):
        return jsonify({"error": "bonus precisa ser dict"}), 400
    bonus_clean = {}
    for k, v in bonus.items():
        if k not in ATR_VALID:
            return jsonify({"error": f"atributo inválido: {k}"}), 400
        iv = int(v)
        if iv < 0 or iv > 2:
            return jsonify({"error": f"bônus em {k} fora da faixa (0-2)"}), 400
        if iv > 0:
            bonus_clean[k] = iv
    if sum(bonus_clean.values()) != 3:
        return jsonify({"error": "soma dos bônus deve ser 3 (ex: 1+1+1 ou 2+1)"}), 400

    # validação de items
    if len(items) > 2:
        return jsonify({"error": "no máx 2 items (ferramentas ou idiomas)"}), 400
    for it in items:
        if it.get("tipo") not in ("idioma", "ferramenta"):
            return jsonify({"error": "tipo deve ser 'idioma' ou 'ferramenta'"}), 400

    conn = db()
    conn.execute(
        "UPDATE TB_Personagem SET BackgroundNome=?, BackgroundBonusJSON=? WHERE Id_Personagem=?",
        (nome, json.dumps(bonus_clean), pid),
    )
    # remove items antigos do background e insere novos
    conn.execute("DELETE FROM TB_PersonagemIdioma WHERE Id_Personagem=? AND Origem='background'", (pid,))
    for it in items:
        n = (it.get("nome") or "").strip()
        if not n:
            continue
        conn.execute(
            """INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem)
                   VALUES (?, ?, ?, 'background')""",
            (pid, it["tipo"], n[:100]),
        )
    conn.commit()
    return jsonify({"ok": True, "nome": nome, "bonus": bonus_clean})


@app.get("/api/personagens/<int:pid>/talentos-raciais-disponiveis")
def talentos_disponiveis(pid: int):
    """Retorna talentos raciais que o personagem PODE escolher:
       - tags-de-filtro do talento ⊆ tags do personagem
       - NivelMinimo <= personagem.Nivel
       - ainda nao escolhido

    TagsJSON do talento mistura tags de FILTRO (humano/infernal/orgulho — slugs
    de raça/linhagem/essência) com tags de EFEITO (voar:eq, +manobras:2, etc.).
    Filtro só considera tags que pertencem ao vocabulário dinâmico de slugs.
    Tags de efeito (com `:`, com `+`, dicts) são ignoradas pra fins de visibilidade.
    """
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    esc = p["escolha"] or {}
    nivel = p["Nivel"] or 1

    # coleta tags do personagem
    tags = set()
    if esc.get("Id_Raca"):
        r = one("SELECT Slug FROM TB_Raca WHERE Id_Raca = ?", esc["Id_Raca"])
        if r: tags.add(r["Slug"])
    if esc.get("Id_Linhagem"):
        l = one("SELECT Slug FROM TB_Linhagem WHERE Id_Linhagem = ?", esc["Id_Linhagem"])
        if l:
            # Linhagens humanas vem como "erthari-humanos-da-terra" → normaliza primeira palavra
            slug = (l["Slug"] or "").split("-")[0]
            if slug: tags.add(slug)
    if esc.get("Id_Essencia"):
        e = one("SELECT Slug FROM TB_Essencia WHERE Id_Essencia = ?", esc["Id_Essencia"])
        if e:
            # "essencia-infernal" → "infernal"
            s = (e["Slug"] or "").replace("essencia-", "").replace("ess-", "")
            if s: tags.add(s)
    if esc.get("Id_EssLinhagem"):
        el = one("SELECT Slug FROM TB_EssenciaLinhagem WHERE Id_EssLinhagem = ?", esc["Id_EssLinhagem"])
        if el: tags.add(el["Slug"])

    # Vocabulário canônico de tags-de-filtro: união de slugs de raça/linhagem/
    # essência/sub-linhagem. Tags do talento que NÃO estão neste vocabulário
    # são tratadas como tags-de-efeito e ignoradas no filtro.
    vocab: set[str] = set()
    for r in rows("SELECT Slug FROM TB_Raca WHERE Slug IS NOT NULL"):
        vocab.add(r["Slug"])
    for r in rows("SELECT Slug FROM TB_Linhagem WHERE Slug IS NOT NULL"):
        s = (r["Slug"] or "").split("-")[0]
        if s: vocab.add(s)
    for r in rows("SELECT Slug FROM TB_Essencia WHERE Slug IS NOT NULL"):
        s = (r["Slug"] or "").replace("essencia-", "").replace("ess-", "")
        if s: vocab.add(s)
    for r in rows("SELECT Slug FROM TB_EssenciaLinhagem WHERE Slug IS NOT NULL"):
        vocab.add(r["Slug"])

    # já escolhidos
    ja = {r["Id_TalentoRacial"] for r in rows(
        "SELECT Id_TalentoRacial FROM TB_PersonagemTalento WHERE Id_Personagem = ? AND Id_TalentoRacial IS NOT NULL",
        pid,
    )}

    # retorna TODOS os talentos — o filtro por nível fica no UI (slots)
    # isso permite planejamento (escolher um talento de tier acima do nível atual)
    todos = rows(
        "SELECT * FROM TB_TalentoRacial ORDER BY Fonte, NivelMinimo, Nome",
    )
    out = []
    for t in todos:
        if t["Id_TalentoRacial"] in ja:
            continue
        try:
            raw_tags = json.loads(t["TagsJSON"] or "[]") or []
        except (json.JSONDecodeError, TypeError):
            raw_tags = []
        # Tags-de-filtro = strings que estão no vocabulário canônico.
        # Tags-de-efeito (dicts, prefixos como "voar:eq", "+manobras", etc.) são ignoradas.
        filter_tags = {x for x in raw_tags if isinstance(x, str) and x in vocab}
        if not filter_tags.issubset(tags):
            continue
        # devolve a TagsJSON crua (preserva forma string ou objeto pra UI)
        t["TagsJSON"] = raw_tags
        out.append(t)

    return jsonify({"tags_personagem": sorted(tags), "talentos": out, "nivel": nivel})


@app.post("/api/personagens/<int:pid>/talentos-raciais")
def adicionar_talento_racial(pid: int):
    d = request.get_json(force=True) or {}
    id_tal = d.get("id_talento")
    cat    = (d.get("categoria") or "raca").strip()
    if cat not in ("raca", "essencia", "geral", "extra"):
        cat = "raca"
    if not id_tal:
        return jsonify({"error": "id_talento obrigatório"}), 400
    t = one("SELECT * FROM TB_TalentoRacial WHERE Id_TalentoRacial = ?", id_tal)
    if not t:
        return jsonify({"error": "talento não encontrado"}), 404
    conn = db()
    # remove talento anterior no mesmo (categoria, nivel) — 1 slot por tier
    conn.execute(
        """DELETE FROM TB_PersonagemTalento
           WHERE Id_Personagem=? AND Categoria=? AND Nivel=?""",
        (pid, cat, t["NivelMinimo"]),
    )
    # Detalhes: descrição completa do talento (se ausente, fallback pro PreReqTexto)
    detalhes = (t.get("Descricao") or t.get("PreReqTexto") or "")[:3000]
    conn.execute(
        """INSERT INTO TB_PersonagemTalento
               (Id_Personagem, Categoria, Nivel, Nome, Detalhes, Id_TalentoRacial)
               VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, cat, t["NivelMinimo"], t["Nome"][:150], detalhes, id_tal),
    )
    conn.commit()
    return jsonify({"ok": True, "talento": t["Nome"], "categoria": cat})


_RE_AUMENTO_ATRIBUTO = re.compile(
    r"Aumento\s+de\s+Atributo:\s*\+?(\d+)\s+(?:de|do|da)\s+([^.]+?)\.",
    re.I,
)
_ATR_NAMES_LOWER_TO_SHORT = {
    "forca": "for", "força": "for",
    "destreza": "dex",
    "constituicao": "con", "constituição": "con",
    "inteligencia": "int", "inteligência": "int",
    "sabedoria": "sab",
    "carisma": "car",
}
_ATR_FULL_BY_SHORT = {
    "for": "Forca", "dex": "Destreza", "con": "Constituicao",
    "int": "Inteligencia", "sab": "Sabedoria", "car": "Carisma",
}


def _atributos_efetivos(p: dict, talentos: list[dict]) -> dict:
    """Soma base + background bonuses + ASI de talentos de classe (so unlocked)."""
    base = p.get("atributos") or {}
    nivel_pers = p.get("Nivel") or 1
    full = {
        "Forca": int(base.get("Forca") or 10),
        "Destreza": int(base.get("Destreza") or 10),
        "Constituicao": int(base.get("Constituicao") or 10),
        "Inteligencia": int(base.get("Inteligencia") or 10),
        "Sabedoria": int(base.get("Sabedoria") or 10),
        "Carisma": int(base.get("Carisma") or 10),
    }
    bg_json = p.get("BackgroundBonusJSON")
    if bg_json:
        try:
            bg = json.loads(bg_json)
            for k, v in bg.items():
                if k in full and isinstance(v, (int, float)):
                    full[k] += int(v)
        except (json.JSONDecodeError, TypeError):
            pass
    # ASI de talentos de classe + extras (origin feats, etc.) — só os com nivel <= nivel personagem
    # AumentoAtributo agora pode ser CSV ('for' ou 'for,dex' p/ +1+1).
    for t in talentos:
        if t.get("Categoria") not in ("classe", "extra"):
            continue
        if (t.get("Nivel") or 1) > nivel_pers:
            continue
        atr_raw = (t.get("AumentoAtributo") or "").lower().strip()
        if not atr_raw:
            continue
        spec = t.get("AumentoSpec") or {}
        bonus = int(spec.get("bonus") or 1)
        for atr_short in [a.strip() for a in atr_raw.split(",") if a.strip()]:
            atr_full = _ATR_FULL_BY_SHORT.get(atr_short)
            if atr_full:
                full[atr_full] += bonus
    # CAP em 20 — talentos normais não passam de 20. Items futuros que quebrem
    # o cap entrarão por mecanismo separado (ex.: bonus_items >0 adicionado depois).
    # Sinalizamos quais atributos atingiram o cap pra UI renderizar 🔒.
    locked_at_20: dict[str, bool] = {}
    for k in list(full.keys()):
        if full[k] > 20:
            locked_at_20[k] = True
            full[k] = 20
    # mod (D&D)
    mods = {k: (v - 10) // 2 for k, v in full.items()}
    return {"valores": full, "modificadores": mods, "locked_at_20": locked_at_20}


def _build_talentos(pid: int) -> list[dict]:
    """Retorna talentos do personagem com Detalhes_Final + spec de aumento de atributo."""
    # IMPORTANTE: SELECT pt.* já inclui pt.TagsJSON; aliasing COALESCE como "TagsJSON" é
    # ambíguo e o SQLite resolve pra pt.TagsJSON (vence a primeira ocorrência).
    # Listamos todas colunas relevantes de pt explicitamente exceto TagsJSON, que vem do COALESCE.
    talentos = rows(
        "SELECT pt.Id_Talento, pt.Id_Personagem, pt.Categoria, pt.Nivel, pt.Nome, pt.Detalhes, "
        "       pt.Id_TalentoRacial, pt.AumentoAtributo, pt.Id_Classe, "
        "       COALESCE(tr.Descricao, pt.Detalhes) AS Detalhes_Final, "
        "       tr.Descricao AS DescricaoCatalogo, "
        "       tr.PreReqTexto AS PreReqTexto, "
        "       COALESCE(pt.TagsJSON, tr.TagsJSON) AS TagsJSON "
        "  FROM TB_PersonagemTalento pt "
        "  LEFT JOIN TB_TalentoRacial tr ON tr.Id_TalentoRacial = pt.Id_TalentoRacial "
        " WHERE pt.Id_Personagem = ? ORDER BY pt.Categoria, pt.Nivel",
        pid,
    )
    for t in talentos:
        spec = _aumento_atributo_parse(t.get("Detalhes_Final") or "")
        t["AumentoSpec"] = spec
    return talentos


def _aumento_atributo_parse(descricao: str) -> dict | None:
    """Parseia 'Aumento de Atributo' line. Returns spec or None.
    Padrões reconhecidos:
      '+1 de Forca'                              → {bonus:1, picks:1, permitidos:['for']}
      '+1 de Forca ou Destreza'                  → {bonus:1, picks:1, permitidos:['for','dex']}
      '+1 de (atributo à sua escolha)'           → {bonus:1, picks:1, qualquer:True}
      '+2 de (atributo à sua escolha)'           → {bonus:2, picks:1, qualquer:True}
      '+1 em dois atributos diferentes ...'      → {bonus:1, picks:2, qualquer:True, diferentes:True}
    """
    if not descricao:
        return None

    # Detecta caso "+1 em dois atributos" (com ou sem "diferentes")
    m_2 = re.search(r"\+\s*1\s+em\s+dois\s+atributos(\s+diferentes)?", descricao, re.I)
    if m_2:
        return {
            "bonus": 1, "picks": 2, "diferentes": bool(m_2.group(1)),
            "permitidos": list(_ATR_FULL_BY_SHORT.keys()), "qualquer": True,
        }

    m = _RE_AUMENTO_ATRIBUTO.search(descricao)
    if not m:
        return None
    try:
        bonus = int(m.group(1))
    except (TypeError, ValueError):
        bonus = 1
    rest = m.group(2).strip().lower()
    if "à sua escolha" in rest or "a sua escolha" in rest or "qualquer" in rest:
        return {"bonus": bonus, "picks": 1,
                "permitidos": list(_ATR_FULL_BY_SHORT.keys()), "qualquer": True}
    # caso especial: "do atributo de conjuração [...]" — INT/SAB/CAR canonicamente
    if "atributo de conjura" in rest or "atributo da conjura" in rest:
        return {"bonus": bonus, "picks": 1,
                "permitidos": ["int", "sab", "car"], "qualquer": False,
                "conjuracao_attr": True}
    out: list[str] = []
    for parte in re.split(r"\s+ou\s+|\s*,\s*", rest):
        parte = parte.strip()
        short = _ATR_NAMES_LOWER_TO_SHORT.get(parte)
        if short and short not in out:
            out.append(short)
    return {"bonus": bonus, "picks": 1, "permitidos": out, "qualquer": False}


@app.put("/api/personagens/<int:pid>/talentos/<int:tid>/aumento-atributo")
def set_talento_aumento_atributo(pid: int, tid: int):
    """Define qual(is) atributo(s) recebe(m) o aumento.
    Body: {'atributo': 'for' | 'for,dex' | null}.

    Para talentos com picks=2, espera CSV de 2 atributos diferentes.
    """
    d = request.get_json(force=True) or {}
    atr_raw = d.get("atributo")
    if atr_raw is None or atr_raw == "":
        atr_csv = None
    else:
        partes = [p.strip().lower() for p in str(atr_raw).split(",") if p.strip()]
        for p in partes:
            if p not in _ATR_FULL_BY_SHORT:
                return jsonify({"error": f"atributo invalido: {p}"}), 400
        if len(partes) > 2:
            return jsonify({"error": "max 2 atributos por talento"}), 400
        # Atributos repetidos são PERMITIDOS — escolher 'for,for' resulta em +2 Forca.
        atr_csv = ",".join(partes)
    conn = db()
    conn.execute(
        "UPDATE TB_PersonagemTalento SET AumentoAtributo=? WHERE Id_Personagem=? AND Id_Talento=?",
        (atr_csv, pid, tid),
    )
    conn.commit()
    return jsonify({"ok": True, "atributo": atr_csv})


@app.post("/api/personagens/<int:pid>/talento-manual")
def talento_manual(pid: int):
    d = request.get_json(force=True) or {}
    cat = (d.get("categoria") or "classe").strip()
    if cat not in ("classe", "geral", "extra", "raca", "essencia"):
        cat = "classe"
    nivel = int(d.get("nivel") or 1)
    id_classe = d.get("id_classe")  # multiclasse: slot pertence a UMA classe
    nome = (d.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "nome obrigatório"}), 400
    detalhes = (d.get("detalhes") or "").strip()
    conn = db()
    # 1 slot por (categoria, nivel, id_classe): remove anterior matching mesmo slot
    if id_classe is not None and cat == "classe":
        conn.execute(
            "DELETE FROM TB_PersonagemTalento WHERE Id_Personagem=? AND Categoria=? AND Nivel=? AND Id_Classe=?",
            (pid, cat, nivel, int(id_classe)),
        )
    else:
        conn.execute(
            "DELETE FROM TB_PersonagemTalento WHERE Id_Personagem=? AND Categoria=? AND Nivel=?",
            (pid, cat, nivel),
        )
    # Propaga TagsJSON do catálogo TB_OpcaoJogo (talento-geral/talento-origem)
    # pra pt.TagsJSON — necessário pra tags como pick:talento-origem:1 (Raízes
    # Profundas), pick:talento-geral:1 (Multi-talentoso futuramente como geral),
    # save-prof:$atributo (Resiliente) funcionarem após inserção via talento-manual.
    cat_tags = conn.execute(
        "SELECT TagsJSON FROM TB_OpcaoJogo WHERE Nome=? COLLATE NOCASE",
        (nome,),
    ).fetchone()
    catalog_tags_json = cat_tags[0] if cat_tags and cat_tags[0] else None
    conn.execute(
        "INSERT INTO TB_PersonagemTalento (Id_Personagem, Categoria, Nivel, Id_Classe, Nome, Detalhes, TagsJSON) "
        "VALUES (?,?,?,?,?,?,?)",
        (pid, cat, nivel, int(id_classe) if id_classe else None,
         nome[:150], detalhes[:3000] or None, catalog_tags_json),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/talentos/<int:tid>")
def remover_talento(pid: int, tid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemTalento WHERE Id_Personagem = ? AND Id_Talento = ?", (pid, tid))
    conn.commit()
    return jsonify({"ok": True})


@app.put("/api/personagens/<int:pid>/personalidade")
def put_personalidade(pid: int):
    d = request.get_json(force=True) or {}
    tipo = (d.get("tipo") or "").strip()
    texto = (d.get("texto") or "").strip()
    if tipo not in ("traco", "ideal", "vinculo", "defeito"):
        return jsonify({"error": "tipo inválido"}), 400
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemPersonalidade WHERE Id_Personagem = ? AND Tipo = ?",
        (pid, tipo),
    )
    if texto:
        conn.execute(
            "INSERT INTO TB_PersonagemPersonalidade (Id_Personagem, Tipo, Texto) VALUES (?, ?, ?)",
            (pid, tipo, texto),
        )
    conn.commit()
    return jsonify({"ok": True})


@app.get("/api/personagens/<int:pid>/manobras-disponiveis")
def manobras_disponiveis(pid: int):
    """Retorna manobras que o personagem pode adquirir.
    Filtro: classe(Fonte) = classe.Slug do personagem + Grau ≤ grau máximo pelo nível."""
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    esc = p["escolha"] or {}
    nivel = p["Nivel"] or 1

    classe = one("SELECT Slug FROM TB_Classe WHERE Id_Classe=?", esc.get("Id_Classe")) if esc.get("Id_Classe") else None
    if not classe:
        return jsonify({"classe": None, "grau_max": 0, "ja_escolhidas": [], "manobras": []})

    # grau máximo pelo nível do personagem (D&D 5.5: 1=liv.1, 2=liv.5, 3=liv.11, 4=liv.15)
    if   nivel >= 15: grau_max = 4
    elif nivel >= 11: grau_max = 3
    elif nivel >=  5: grau_max = 2
    else:             grau_max = 1

    ja = {r["Id_Manobra"] for r in rows(
        "SELECT Id_Manobra FROM TB_PersonagemTecnica WHERE Id_Personagem=? AND Id_Manobra IS NOT NULL", pid,
    )}

    manobras = rows(
        """SELECT * FROM TB_Manobra
            WHERE Fonte=? AND Grau <= ?
            ORDER BY Grau, Nome""",
        classe["Slug"], grau_max,
    )
    for m in manobras:
        m["ja_escolhida"] = m["Id_Manobra"] in ja
        m["TagsJSON"] = json.loads(m["TagsJSON"] or "[]")

    return jsonify({
        "classe": classe["Slug"],
        "grau_max": grau_max,
        "nivel": nivel,
        "manobras": manobras,
    })


@app.post("/api/personagens/<int:pid>/tecnicas")
def add_tecnica(pid: int):
    """Adiciona manobra. Prioridade:
       - id_manobra → puxa do catálogo TB_Manobra (nome, descricao)
       - nome livre → fallback p/ texto arbitrário"""
    d = request.get_json(force=True) or {}
    id_manobra = d.get("id_manobra")
    nome = (d.get("nome") or "").strip()
    descricao = (d.get("descricao") or "").strip()

    if id_manobra:
        mn = one("SELECT * FROM TB_Manobra WHERE Id_Manobra=?", id_manobra)
        if not mn:
            return jsonify({"error": "manobra não encontrada"}), 404
        # não duplica
        ja = one(
            "SELECT Id FROM TB_PersonagemTecnica WHERE Id_Personagem=? AND Id_Manobra=?",
            pid, id_manobra,
        )
        if ja:
            return jsonify({"ok": True, "msg": "já adquirida"})
        nome = mn["Nome"]
        descricao = mn["Descricao"]

    if not nome:
        return jsonify({"error": "nome ou id_manobra obrigatório"}), 400

    conn = db()
    conn.execute(
        """INSERT INTO TB_PersonagemTecnica
               (Id_Personagem, Nome, Descricao, Id_Habilidade, Id_Manobra)
               VALUES (?, ?, ?, ?, ?)""",
        (pid, nome[:150], descricao[:3000] or None,
         int(d["id_habilidade"]) if d.get("id_habilidade") else None,
         int(id_manobra) if id_manobra else None),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/tecnicas/<int:tid>")
def del_tecnica(pid: int, tid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemTecnica WHERE Id_Personagem=? AND Id=?", (pid, tid))
    conn.commit()
    return jsonify({"ok": True})


# =========================================================================
# Segredos de Caçador (paralelo a Técnicas/Manobras do Guerreiro)
# =========================================================================
@app.get("/api/personagens/<int:pid>/segredos-disponiveis")
def segredos_disponiveis(pid: int):
    """Retorna catálogo TB_Segredo + flag ja_escolhida. Sem filtro de grau —
    Caçador tem todos os 19 desde Nv 2; o limite de QUANTOS conhecer vem
    de TB_RecursoClasse 'Segredos' (state.limites.segredos)."""
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    ja = {r["Id_Segredo"] for r in rows(
        "SELECT Id_Segredo FROM TB_PersonagemSegredo WHERE Id_Personagem=?", pid,
    )}
    segredos = rows("SELECT * FROM TB_Segredo ORDER BY Linha, Nome")
    for s in segredos:
        s["ja_escolhido"] = s["Id_Segredo"] in ja
    return jsonify({"segredos": segredos, "total": len(segredos)})


@app.post("/api/personagens/<int:pid>/segredos")
def add_segredo(pid: int):
    d = request.get_json(force=True) or {}
    id_segredo = d.get("id_segredo")
    if not id_segredo:
        return jsonify({"error": "id_segredo obrigatório"}), 400
    s = one("SELECT * FROM TB_Segredo WHERE Id_Segredo=?", id_segredo)
    if not s:
        return jsonify({"error": "segredo não encontrado"}), 404
    ja = one(
        "SELECT Id FROM TB_PersonagemSegredo WHERE Id_Personagem=? AND Id_Segredo=?",
        pid, id_segredo,
    )
    if ja:
        return jsonify({"ok": True, "msg": "já adquirido"})
    conn = db()
    conn.execute(
        """INSERT INTO TB_PersonagemSegredo (Id_Personagem, Id_Segredo, Id_Habilidade)
           VALUES (?,?,?)""",
        (pid, id_segredo, int(d["id_habilidade"]) if d.get("id_habilidade") else None),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/segredos/<int:sid>")
def del_segredo(pid: int, sid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemSegredo WHERE Id_Personagem=? AND Id=?", (pid, sid))
    conn.commit()
    return jsonify({"ok": True})


# =========================================================================
# Inimigo Favorito (Caçador) — paralelo a Segredos
# =========================================================================
@app.get("/api/personagens/<int:pid>/inimigos-favoritos-disponiveis")
def inimigos_favoritos_disponiveis(pid: int):
    if not _personagem_raw(pid):
        return jsonify({"error": "not found"}), 404
    ja = {r["Id_InimigoFavorito"] for r in rows(
        "SELECT Id_InimigoFavorito FROM TB_PersonagemInimigoFavorito WHERE Id_Personagem=?", pid,
    )}
    inimigos = rows("SELECT * FROM TB_InimigoFavorito ORDER BY Nome")
    for i in inimigos:
        i["ja_escolhido"] = i["Id_InimigoFavorito"] in ja
    return jsonify({"inimigos": inimigos, "total": len(inimigos)})


@app.post("/api/personagens/<int:pid>/inimigos-favoritos")
def add_inimigo_favorito(pid: int):
    d = request.get_json(force=True) or {}
    id_inim = d.get("id_inimigo_favorito")
    if not id_inim:
        return jsonify({"error": "id_inimigo_favorito obrigatório"}), 400
    if not one("SELECT 1 FROM TB_InimigoFavorito WHERE Id_InimigoFavorito=?", id_inim):
        return jsonify({"error": "inimigo não encontrado"}), 404
    if one("SELECT Id FROM TB_PersonagemInimigoFavorito WHERE Id_Personagem=? AND Id_InimigoFavorito=?", pid, id_inim):
        return jsonify({"ok": True, "msg": "já adquirido"})
    conn = db()
    conn.execute(
        """INSERT INTO TB_PersonagemInimigoFavorito (Id_Personagem, Id_InimigoFavorito, Id_Habilidade)
           VALUES (?,?,?)""",
        (pid, id_inim, int(d["id_habilidade"]) if d.get("id_habilidade") else None),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/inimigos-favoritos/<int:iid>")
def del_inimigo_favorito(pid: int, iid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemInimigoFavorito WHERE Id_Personagem=? AND Id=?", (pid, iid))
    conn.commit()
    return jsonify({"ok": True})


# =========================================================================
# Evolução Totêmica (sub Aliança Selvagem) — paralelo a Inimigo Favorito
# =========================================================================
@app.get("/api/personagens/<int:pid>/evolucoes-totemicas-disponiveis")
def evolucoes_totemicas_disponiveis(pid: int):
    if not _personagem_raw(pid):
        return jsonify({"error": "not found"}), 404
    ja = {r["Id_Evolucao"] for r in rows(
        "SELECT Id_Evolucao FROM TB_PersonagemEvolucaoTotemica WHERE Id_Personagem=?", pid,
    )}
    catalog = rows("SELECT * FROM TB_EvolucaoTotemica ORDER BY Tier DESC, Nome")
    for c in catalog:
        # Resistência Elemental pode repetir (variante diferente). Outras não.
        c["repetivel"] = (c["Slug"] == "resistencia-elemental")
        c["ja_escolhida"] = (c["Id_Evolucao"] in ja) and not c["repetivel"]
    return jsonify({"evolucoes": catalog, "total": len(catalog)})


@app.post("/api/personagens/<int:pid>/evolucoes-totemicas")
def add_evolucao_totemica(pid: int):
    d = request.get_json(force=True) or {}
    id_ev = d.get("id_evolucao")
    if not id_ev:
        return jsonify({"error": "id_evolucao obrigatório"}), 400
    ev = one("SELECT * FROM TB_EvolucaoTotemica WHERE Id_Evolucao=?", id_ev)
    if not ev:
        return jsonify({"error": "evolução não encontrada"}), 404
    repetivel = ev["Slug"] == "resistencia-elemental"
    if not repetivel:
        if one("SELECT Id FROM TB_PersonagemEvolucaoTotemica WHERE Id_Personagem=? AND Id_Evolucao=?", pid, id_ev):
            return jsonify({"ok": True, "msg": "já adquirida"})
    # próxima slot livre
    used = {r["SlotIndex"] for r in rows(
        "SELECT SlotIndex FROM TB_PersonagemEvolucaoTotemica WHERE Id_Personagem=?", pid,
    )}
    slot_idx = 0
    while slot_idx in used:
        slot_idx += 1
    conn = db()
    conn.execute(
        """INSERT INTO TB_PersonagemEvolucaoTotemica
           (Id_Personagem, Id_Evolucao, Id_Habilidade, Variante, SlotIndex)
           VALUES (?,?,?,?,?)""",
        (pid, id_ev,
         int(d["id_habilidade"]) if d.get("id_habilidade") else None,
         (d.get("variante") or None),
         slot_idx),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/evolucoes-totemicas/<int:eid>")
def del_evolucao_totemica(pid: int, eid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemEvolucaoTotemica WHERE Id_Personagem=? AND Id=?", (pid, eid))
    conn.commit()
    return jsonify({"ok": True})


# =========================================================================
# Estilos de Ki (Monge) — paralelo a Inimigo Favorito
# =========================================================================
@app.get("/api/personagens/<int:pid>/estilos-ki-disponiveis")
def estilos_ki_disponiveis(pid: int):
    """Catálogo de estilos disponíveis. Sub Kensei (com tag 'kensei-estilos')
    vê apenas estilos do catálogo 'kensei'; demais Monges veem 'ki'."""
    if not _personagem_raw(pid):
        return jsonify({"error": "not found"}), 404
    # Detecta catálogo via tag em hab/talento ativos do char.
    # Reusa o mesmo path simplificado do agregador: olha TagsJSON nas habs ativas.
    is_kensei = bool(rows(
        "SELECT 1 FROM TB_ClasseHabilidade h "
        "  JOIN TB_PersonagemClasse pc ON pc.Id_Subclasse = h.Id_Subclasse "
        " WHERE pc.Id_Personagem=? AND h.NivelAdquirido <= pc.Nivel "
        "   AND h.TagsJSON LIKE '%kensei-estilos%'",
        pid,
    ))
    catalogo = "kensei" if is_kensei else "ki"
    ja = {r["Id_Estilo"] for r in rows(
        "SELECT Id_Estilo FROM TB_PersonagemEstiloKi WHERE Id_Personagem=?", pid,
    )}
    estilos = rows("SELECT * FROM TB_EstiloKi WHERE Catalogo=? ORDER BY CustoKi, Nome", catalogo)
    for e in estilos:
        e["ja_escolhido"] = e["Id_Estilo"] in ja
    return jsonify({"estilos": estilos, "total": len(estilos), "catalogo": catalogo})


@app.post("/api/personagens/<int:pid>/estilos-ki")
def add_estilo_ki(pid: int):
    d = request.get_json(force=True) or {}
    id_est = d.get("id_estilo")
    if not id_est:
        return jsonify({"error": "id_estilo obrigatório"}), 400
    if not one("SELECT 1 FROM TB_EstiloKi WHERE Id_Estilo=?", id_est):
        return jsonify({"error": "estilo não encontrado"}), 404
    if one("SELECT Id FROM TB_PersonagemEstiloKi WHERE Id_Personagem=? AND Id_Estilo=?", pid, id_est):
        return jsonify({"ok": True, "msg": "já adquirido"})
    used = {r["SlotIndex"] for r in rows(
        "SELECT SlotIndex FROM TB_PersonagemEstiloKi WHERE Id_Personagem=?", pid,
    )}
    slot = 0
    while slot in used: slot += 1
    db().execute(
        "INSERT INTO TB_PersonagemEstiloKi (Id_Personagem, Id_Estilo, Id_Habilidade, SlotIndex) VALUES (?,?,?,?)",
        (pid, id_est, int(d["id_habilidade"]) if d.get("id_habilidade") else None, slot),
    )
    db().commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/estilos-ki/<int:eid>")
def del_estilo_ki(pid: int, eid: int):
    db().execute("DELETE FROM TB_PersonagemEstiloKi WHERE Id_Personagem=? AND Id=?", (pid, eid))
    db().commit()
    return jsonify({"ok": True})


# =========================================================================
# Segredos Místicos (Místico) — paralelo a Segredos do Caçador
# =========================================================================
@app.get("/api/personagens/<int:pid>/segredos-misticos-disponiveis")
def segredos_misticos_disponiveis(pid: int):
    """Lista catálogo TB_SegredoMistico filtrado por NivelMin (≤ Nv Místico)
    e GateTag (se exigida, deve estar em aggregated_tags).
    O filtro real acontece no agregador via tag-em-opção; aqui retornamos
    catálogo completo + flags ja_escolhido/ok-pra-pegar."""
    p = _personagem_raw(pid)
    if not p: return jsonify({"error": "not found"}), 404
    ja = {r["Id_Segredo"] for r in rows(
        "SELECT Id_Segredo FROM TB_PersonagemSegredoMistico WHERE Id_Personagem=?", pid,
    )}
    # Tags ativas — pra checar gates
    # (uso simplificado: query TB_ClasseHabilidade com TagsJSON, sem rodar agregador completo)
    tags_ativas: set[str] = set()
    for c_pc in rows("SELECT Id_Subclasse, Nivel FROM TB_PersonagemClasse WHERE Id_Personagem=?", pid):
        for h in rows(
            "SELECT TagsJSON FROM TB_ClasseHabilidade "
            " WHERE Id_Subclasse=? AND NivelAdquirido<=?",
            c_pc["Id_Subclasse"], c_pc["Nivel"] or 0,
        ):
            try:
                for t in json.loads(h["TagsJSON"] or "[]") or []:
                    if isinstance(t, str): tags_ativas.add(t)
            except (json.JSONDecodeError, TypeError):
                pass
    # Tag em opção escolhida — TB_PersonagemEscolhaTag
    for et in rows("SELECT Tipo, Valor FROM TB_PersonagemEscolhaTag WHERE Id_Personagem=?", pid):
        opt = one("SELECT TagsJSON FROM TB_OpcaoJogo WHERE Tipo=? AND Nome=?", et["Tipo"], et["Valor"])
        if opt:
            try:
                for t in json.loads(opt["TagsJSON"] or "[]") or []:
                    if isinstance(t, str): tags_ativas.add(t)
            except (json.JSONDecodeError, TypeError): pass

    # Nivel da classe Místico do char (multiclass-aware)
    cls_mistico_nv = 0
    for c_pc in rows(
        "SELECT pc.Nivel, c.Slug FROM TB_PersonagemClasse pc "
        "  JOIN TB_Classe c ON c.Id_Classe=pc.Id_Classe "
        " WHERE pc.Id_Personagem=? AND LOWER(c.Slug)='mistico'",
        pid,
    ):
        cls_mistico_nv = max(cls_mistico_nv, c_pc["Nivel"] or 0)

    segs = rows("SELECT * FROM TB_SegredoMistico ORDER BY NivelMin, Secao, Nome")
    for s in segs:
        s["ja_escolhido"] = s["Id_Segredo"] in ja
        s["nivel_ok"]     = cls_mistico_nv >= (s["NivelMin"] or 1)
        s["gate_ok"]      = (not s["GateTag"]) or (s["GateTag"] in tags_ativas)
        s["repetivel"]    = bool(s.get("Repetivel"))
        # Repetível: pode pegar de novo mesmo já tendo. Bloquear só por nível/gate.
        bloqueado = (s["ja_escolhido"] and not s["repetivel"])
        s["disponivel"]   = (s["nivel_ok"] and s["gate_ok"] and not bloqueado)
    return jsonify({"segredos": segs, "total": len(segs), "mistico_nivel": cls_mistico_nv})


@app.post("/api/personagens/<int:pid>/segredos-misticos")
def add_segredo_mistico(pid: int):
    d = request.get_json(force=True) or {}
    sid = d.get("id_segredo")
    if not sid: return jsonify({"error": "id_segredo obrigatório"}), 400
    seg = one("SELECT Id_Segredo, Repetivel FROM TB_SegredoMistico WHERE Id_Segredo=?", sid)
    if not seg:
        return jsonify({"error": "segredo não encontrado"}), 404
    if not seg["Repetivel"] and one(
        "SELECT Id FROM TB_PersonagemSegredoMistico WHERE Id_Personagem=? AND Id_Segredo=?", pid, sid
    ):
        return jsonify({"ok": True, "msg": "já adquirido"})
    used = {r["SlotIndex"] for r in rows(
        "SELECT SlotIndex FROM TB_PersonagemSegredoMistico WHERE Id_Personagem=?", pid,
    )}
    slot = 0
    while slot in used: slot += 1
    db().execute(
        "INSERT INTO TB_PersonagemSegredoMistico (Id_Personagem, Id_Segredo, SlotIndex) VALUES (?,?,?)",
        (pid, sid, slot),
    )
    db().commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/segredos-misticos/<int:sid>")
def del_segredo_mistico(pid: int, sid: int):
    db().execute(
        "DELETE FROM TB_PersonagemSegredoMisticoTalento "
        "WHERE Id_PersonagemSegredoMistico=?", (sid,),
    )
    db().execute("DELETE FROM TB_PersonagemSegredoMistico WHERE Id_Personagem=? AND Id=?", (pid, sid))
    db().commit()
    return jsonify({"ok": True})


# Set/unset Talento de Origem associado a uma instância de segredo místico.
# Usado pelo "Aprendizado dos Antigos" (Repetivel + TagsJSON pick:talento-origem:1).
@app.post("/api/personagens/<int:pid>/segredos-misticos/<int:sid>/talento-origem")
def set_segredo_talento(pid: int, sid: int):
    d = request.get_json(force=True) or {}
    tid = d.get("id_talento_origem")
    # Confirma que o segredo pertence ao char (e existe)
    if not one(
        "SELECT 1 FROM TB_PersonagemSegredoMistico WHERE Id=? AND Id_Personagem=?", sid, pid
    ):
        return jsonify({"error": "segredo místico não pertence a esse personagem"}), 404
    if tid is None:
        db().execute(
            "DELETE FROM TB_PersonagemSegredoMisticoTalento WHERE Id_PersonagemSegredoMistico=?",
            (sid,),
        )
    else:
        if not one("SELECT 1 FROM TB_OpcaoJogo WHERE Id_Opcao=? AND Tipo='talento-origem'", tid):
            return jsonify({"error": "talento de origem inválido"}), 400
        # upsert manual (tabela tem UNIQUE em Id_PersonagemSegredoMistico)
        existe = one(
            "SELECT Id FROM TB_PersonagemSegredoMisticoTalento WHERE Id_PersonagemSegredoMistico=?",
            sid,
        )
        if existe:
            db().execute(
                "UPDATE TB_PersonagemSegredoMisticoTalento SET Id_TalentoOrigem=? "
                "WHERE Id_PersonagemSegredoMistico=?", (tid, sid),
            )
        else:
            db().execute(
                "INSERT INTO TB_PersonagemSegredoMisticoTalento "
                "(Id_PersonagemSegredoMistico, Id_TalentoOrigem) VALUES (?,?)", (sid, tid),
            )
    db().commit()
    return jsonify({"ok": True})


# =========================================================================
# Idiomas/Ferramentas aprendidos depois (por dinheiro/treino, sem origem fixa)
# =========================================================================
@app.post("/api/personagens/<int:pid>/aprendidos")
def add_aprendido(pid: int):
    """Body: {tipo: 'idioma'|'ferramenta', nome: str}.
    Origem='aprendido' — sem traço/background/classe."""
    d = request.get_json(force=True) or {}
    tipo = (d.get("tipo") or "").strip()
    nome = (d.get("nome") or "").strip()
    if tipo not in ("idioma", "ferramenta") or not nome:
        return jsonify({"error": "tipo (idioma|ferramenta) e nome obrigatórios"}), 400
    # Não duplicar mesmo (tipo, nome) sob origem 'aprendido'
    if one(
        "SELECT Id FROM TB_PersonagemIdioma WHERE Id_Personagem=? AND Tipo=? AND LOWER(Nome)=? AND Origem='aprendido'",
        pid, tipo, nome.lower(),
    ):
        return jsonify({"ok": True, "msg": "já aprendido"})
    db().execute(
        "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,'aprendido')",
        (pid, tipo, nome[:100]),
    )
    db().commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/idiomas/<int:iid>")
def del_idioma_ferramenta(pid: int, iid: int):
    """Remove uma entrada de TB_PersonagemIdioma pelo Id (qualquer origem)."""
    db().execute("DELETE FROM TB_PersonagemIdioma WHERE Id_Personagem=? AND Id=?", (pid, iid))
    db().commit()
    return jsonify({"ok": True})


# =========================================================================
# Maestrias de Armas
# =========================================================================
@app.get("/api/armas")
def list_armas():
    """Lista catalogo de armas com MaestriasJSON parseado."""
    cat = request.args.get("categoria")
    if cat:
        out = rows("SELECT * FROM TB_Arma WHERE Categoria=? ORDER BY Nome", cat)
    else:
        out = rows("SELECT * FROM TB_Arma ORDER BY Categoria, Nome")
    for r in out:
        try:
            r["Maestrias"] = json.loads(r.get("MaestriasJSON") or "[]")
        except (json.JSONDecodeError, TypeError):
            r["Maestrias"] = []
    return jsonify(out)


@app.get("/api/maestrias")
def list_maestrias():
    """Lista catalogo de maestrias (tipos)."""
    return jsonify(rows("SELECT * FROM TB_Maestria ORDER BY Nome"))


@app.post("/api/personagens/<int:pid>/maestrias-armas")
def add_maestria_arma(pid: int):
    """Salva escolha {id_arma, id_maestria, slot_index}.

    Backend resolve nome/efeito por JOIN. Substitui slot existente.
    """
    d = request.get_json(force=True) or {}
    id_arma = d.get("id_arma")
    id_maestria = d.get("id_maestria")
    slot_index = d.get("slot_index")
    if not id_arma:
        return jsonify({"error": "id_arma obrigatorio"}), 400
    arma = one("SELECT Id_Arma, Nome, MaestriasJSON FROM TB_Arma WHERE Id_Arma=?", id_arma)
    if not arma:
        return jsonify({"error": "arma nao encontrada"}), 404
    if id_maestria is not None:
        mae = one("SELECT Id_Maestria FROM TB_Maestria WHERE Id_Maestria=?", id_maestria)
        if not mae:
            return jsonify({"error": "maestria nao encontrada"}), 404
    if slot_index is None:
        slot_index = 0
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemMaestriaArma "
        "WHERE Id_Personagem=? AND SlotIndex=?",
        (pid, slot_index),
    )
    conn.execute(
        "INSERT INTO TB_PersonagemMaestriaArma "
        "(Id_Personagem, Id_Arma, Id_Maestria, SlotIndex) VALUES (?,?,?,?)",
        (pid, id_arma, id_maestria, slot_index),
    )
    conn.commit()
    return jsonify({"ok": True, "slot_index": slot_index, "id_arma": id_arma, "id_maestria": id_maestria})


@app.post("/api/personagens/<int:pid>/magias")
def add_magia(pid: int):
    """Adiciona uma magia escrita à mão. Body: {nivel: 0-9, nome: str, preparada?: 0|1}."""
    d = request.get_json(force=True) or {}
    nivel = int(d.get("nivel") or 0)
    nome = (d.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "nome obrigatório"}), 400
    if nivel < 0 or nivel > 9:
        return jsonify({"error": "nivel deve ser 0..9"}), 400
    preparada = 1 if d.get("preparada") else 0
    conn = db()
    conn.execute(
        "INSERT INTO TB_PersonagemMagia (Id_Personagem, Nivel, Nome, Preparada, Concentracao, Ritual) "
        "VALUES (?,?,?,?,0,0)",
        (pid, nivel, nome[:200], preparada),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.put("/api/personagens/<int:pid>/magias/<int:mid>")
def update_magia(pid: int, mid: int):
    """Atualiza Preparada (toggle). Body: {preparada: 0|1}."""
    d = request.get_json(force=True) or {}
    if "preparada" not in d:
        return jsonify({"error": "campo 'preparada' obrigatório"}), 400
    conn = db()
    conn.execute(
        "UPDATE TB_PersonagemMagia SET Preparada=? WHERE Id_Personagem=? AND Id=?",
        (1 if d["preparada"] else 0, pid, mid),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/magias/<int:mid>")
def delete_magia(pid: int, mid: int):
    conn = db()
    conn.execute("DELETE FROM TB_PersonagemMagia WHERE Id_Personagem=? AND Id=?", (pid, mid))
    conn.commit()
    return jsonify({"ok": True})


# PHB 2024 — tabela de spell slots multiclasse (caster level 1..20).
# Cada tupla = (nv1, nv2, nv3, nv4, nv5, nv6, nv7, nv8, nv9) slots.
MULTICLASS_SPELL_SLOTS: tuple[tuple[int, ...], ...] = (
    (2, 0, 0, 0, 0, 0, 0, 0, 0),  # caster lv 1
    (3, 0, 0, 0, 0, 0, 0, 0, 0),  # 2
    (4, 2, 0, 0, 0, 0, 0, 0, 0),  # 3
    (4, 3, 0, 0, 0, 0, 0, 0, 0),  # 4
    (4, 3, 2, 0, 0, 0, 0, 0, 0),  # 5
    (4, 3, 3, 0, 0, 0, 0, 0, 0),  # 6
    (4, 3, 3, 1, 0, 0, 0, 0, 0),  # 7
    (4, 3, 3, 2, 0, 0, 0, 0, 0),  # 8
    (4, 3, 3, 3, 1, 0, 0, 0, 0),  # 9
    (4, 3, 3, 3, 2, 0, 0, 0, 0),  # 10
    (4, 3, 3, 3, 2, 1, 0, 0, 0),  # 11
    (4, 3, 3, 3, 2, 1, 0, 0, 0),  # 12
    (4, 3, 3, 3, 2, 1, 1, 0, 0),  # 13
    (4, 3, 3, 3, 2, 1, 1, 0, 0),  # 14
    (4, 3, 3, 3, 2, 1, 1, 1, 0),  # 15
    (4, 3, 3, 3, 2, 1, 1, 1, 0),  # 16
    (4, 3, 3, 3, 2, 1, 1, 1, 1),  # 17
    (4, 3, 3, 3, 3, 1, 1, 1, 1),  # 18
    (4, 3, 3, 3, 3, 2, 1, 1, 1),  # 19
    (4, 3, 3, 3, 3, 2, 2, 1, 1),  # 20
)


# Subclasses 1/3 caster (3rd-cast via subclasse — não via classe)
THIRD_CASTER_SUBCLASS_SLUGS: frozenset[str] = frozenset({
    "cavaleiro-arcano",                # Eldritch Knight (Guerreiro)
    "trapaceiro-arcano",               # variante slug legacy (compat)
    "trilha-do-trapaceiro-arcano",     # Bonfire Ladino — slug atual com prefix Trilha
})


def _calc_ca_efetiva(p: dict, classes_pc: list[dict],
                    profs_armadura_extras: list[dict], talentos_full: list[dict],
                    tag_origem: list = None) -> dict:
    """Calcula CA placeholder a partir de proficiências de armadura.

    Regra (D&D 5.5e padrão, sem catálogo de armaduras ainda):
      - Sem proficiência de armadura: 10 + DES
      - Leve: 11 + DES (placeholder = Couro Acolchoado)
      - Média: 14 + min(DES, 2) (placeholder = Cota Brunida)
      - Pesada: 18 (placeholder = Placas; ignora DES)
      - + 2 se proficiência em Escudo

    Override por tag 'unarmored-defense:<Atributo>' (Monge SAB, Bárbaro CON):
      - Substitui base se "sem prof" — CA = 10 + DES + mod(<Atributo>)

    Pega a MELHOR categoria que o personagem tem proficiência. Fontes:
      - TB_Classe.ArmorProfJSON da classe primária (Ordem=0) e demais classes
      - tags `prof-armadura:<categoria>` (raça, talentos, traços)

    Retorna dict com 'valor' (int), 'detalhe' (string explicativa),
    'override' (valor manual de TB_Personagem.CA, se diferente do calculado).
    """
    # 1) Coleta categorias de proficiência (case-insensitive)
    cats: set[str] = set()
    for c_pc in classes_pc:
        raw = c_pc.get("ArmorProfJSON")
        if raw:
            try:
                for it in json.loads(raw) or []:
                    if isinstance(it, str) and it.strip():
                        cats.add(it.strip().lower())
            except (json.JSONDecodeError, TypeError):
                pass
    # Tags prof-armadura
    for x in profs_armadura_extras or []:
        v = (x.get("valor") or "").strip().lower()
        if v:
            cats.add(v)

    # 2) Mod DES final (com bg + ASIs). _atributos_efetivos retorna
    # {modificadores: {Destreza: N}, valores: {Destreza: M}}.
    atribs_full = _atributos_efetivos(p, talentos_full) or {}
    des_mod = int(atribs_full.get("modificadores", {}).get("Destreza", 0))

    # 3) Detecta melhor categoria. Aliases pt/en — singular, plural, com prefixo "armadura".
    def _has(cats: set[str], words: set[str]) -> bool:
        # match exato OU substring (cobre "armadura X" / "armaduras X" / "X armor")
        for c in cats:
            if c in words: return True
            for w in words:
                if w in c: return True
        return False
    has_pesada = _has(cats, {"pesada", "heavy"})
    has_media  = _has(cats, {"média", "media", "medium"})
    has_leve   = _has(cats, {"leve", "light"})
    has_escudo = _has(cats, {"escudo", "shield"})

    # 4) unarmored-defense (Monge "Guerreiro sem Armadura": +SAB; Bárbaro: +CON).
    # Só aplica se o char NÃO está usando armadura — placeholder = sem prof equivale
    # a "sem armadura" pra esse cálculo.
    unarm_atr = None
    if tag_origem:
        for t, _o in tag_origem:
            if t.startswith("unarmored-defense:"):
                unarm_atr = t.split(":", 1)[1].strip()
                break
    unarm_mod = 0
    if unarm_atr:
        unarm_mod = int(atribs_full.get("modificadores", {}).get(unarm_atr, 0))

    if has_pesada:
        valor = 18
        detalhe = "Placas (placeholder Pesada): 18"
    elif has_media:
        valor = 14 + min(des_mod, 2)
        detalhe = f"Cota Brunida (placeholder Média): 14 + DES(max +2) = 14 + {min(des_mod,2)}"
    elif has_leve:
        valor = 11 + des_mod
        detalhe = f"Couro Acolchoado (placeholder Leve): 11 + DES = 11 + {des_mod}"
    elif unarm_atr:
        valor = 10 + des_mod + unarm_mod
        detalhe = f"Defesa sem Armadura: 10 + DES + {unarm_atr[:3].upper()} = 10 + {des_mod} + {unarm_mod}"
    else:
        valor = 10 + des_mod
        detalhe = f"Sem armadura: 10 + DES = 10 + {des_mod}"

    if has_escudo:
        valor += 2
        detalhe += " · Escudo +2"

    p_ca_override = p.get("CA")
    return {
        "valor": valor,
        "detalhe": detalhe,
        "categorias_prof": sorted(cats),
        "override": p_ca_override if (p_ca_override is not None and p_ca_override != valor) else None,
        "des_mod": des_mod,
    }


def _calc_surto_selvagem(classes_pc: list[dict], flat_tags: set[str]) -> dict | None:
    """Calcula CR máximo de besta para Surto Selvagem (Forma Selvagem).

    Retorna None se char não tem nível em Druida. Caso contrário:
      - eh_lua=True: ND máximo = ⌈nivel/3⌉  (Círculo da Lua)
      - eh_lua=False: tabela canônica Druida — Nv2=1/4, Nv4=1/2, Nv8=1
      - formas_conhecidas: 4 (Nv2-3), 6 (Nv4-7), 8 (Nv8+)
      - voo: liberado a partir Nv8

    Frontend exibe seção quando tag 'surto-selvagem' está em aggregated_tags.
    Tag 'druida-lua' (presente em features do Círculo da Lua) muda o cálculo.
    """
    nivel = next(
        (c.get("Nivel", 0) for c in classes_pc
         if (c.get("SlugClasse") or "").lower() == "druida"),
        0,
    )
    if nivel <= 0:
        return None
    eh_lua = "druida-lua" in flat_tags
    if eh_lua:
        # ⌈nivel / 3⌉ — Nv3=1, Nv6=2, Nv9=3, Nv12=4, Nv15=5, Nv18=6, Nv20=7
        cr_int = (nivel + 2) // 3
        cr_label = str(cr_int)
        cr_value = float(cr_int)
    else:
        if nivel >= 8:
            cr_label, cr_value = "1", 1.0
        elif nivel >= 4:
            cr_label, cr_value = "1/2", 0.5
        elif nivel >= 2:
            cr_label, cr_value = "1/4", 0.25
        else:
            cr_label, cr_value = "—", 0.0
    if nivel >= 8:
        formas = 8
    elif nivel >= 4:
        formas = 6
    elif nivel >= 2:
        formas = 4
    else:
        formas = 0
    return {
        "nivel_druida": nivel,
        "cr_max": cr_label,
        "cr_max_num": cr_value,
        "eh_lua": eh_lua,
        "formas_conhecidas": formas,
        "voo": nivel >= 8,
    }


def _calc_caster_level(classes_pc: list[dict]) -> int:
    """Soma os níveis de classe ponderados pelo tipo de conjuração:
    full = 1x, half = 1/2 (round down), third = 1/3 (ROUND UP).
    Half-caster Nv 1 NÃO contribui. Third-caster só conta a partir do Nv 3.
    Third também pode vir via subclasse (Cavaleiro Arcano, Trapaceiro Arcano).

    Third-caster usa ceil em vez de floor pra bater com a tabela canônica
    da subclasse 5.5e (EK F19-20 → 4°slot=1). Em multiclass real (1/3 +
    outra caster), a regra estrita do PHB diz floor — refinar quando
    surgir caso (Frosty é Guerreiro puro, então single-class manda).

    EXCLUI Místico — Pact Magic é isolada (Warlock-style); slots calculados
    separadamente em _calc_mistico_level.
    """
    total = 0
    for c in classes_pc:
        # Pula Místico — slots vão pro pact_slots, não pro spell_slots multiclasse.
        slug_cls = (c.get("SlugClasse") or "").lower()
        nome_cls = (c.get("NomeClasse") or "").lower()
        if slug_cls == "mistico" or nome_cls.startswith("místic") or nome_cls.startswith("mistic"):
            continue
        conj = (c.get("Conjuracao") or "").lower() if isinstance(c, dict) else ""
        if not conj:
            cls = one("SELECT Conjuracao FROM TB_Classe WHERE Id_Classe=?", c["Id_Classe"])
            conj = (cls.get("Conjuracao") or "").lower() if cls else ""
        nivel = c.get("Nivel") or 0
        # Override: se classe é 'none' mas tem subclasse 1/3 caster, vira 'third'
        if conj in ("none", ""):
            sub = one("SELECT Slug FROM TB_Subclasse WHERE Id_Subclasse=?", c.get("Id_Subclasse"))
            if sub and (sub.get("Slug") or "").lower() in THIRD_CASTER_SUBCLASS_SLUGS:
                conj = "third"
        if conj == "full":
            total += nivel
        elif conj == "half":
            if nivel >= 2:
                total += nivel // 2
        elif conj == "third":
            if nivel >= 3:
                total += (nivel + 2) // 3  # ceil(nivel/3) — tabela EK single-class
    return total


def _calc_mistico_level(classes_pc: list[dict]) -> int:
    """Retorna o nível da CLASSE Místico no personagem (0 se não tem)."""
    for c in classes_pc:
        slug_cls = (c.get("SlugClasse") or "").lower()
        nome_cls = (c.get("NomeClasse") or "").lower()
        if slug_cls == "mistico" or nome_cls.startswith("místic") or nome_cls.startswith("mistic"):
            return c.get("Nivel") or 0
    return 0


def _calc_feiticaria_mistica(classes_pc: list[dict]) -> dict | None:
    """Retorna recursos de Feitiçaria Mística (sistema de Pontos de Misticismo
    do Bonfire — NÃO slots fixos como outras casters). Lê TB_RecursoClasse
    do Místico no nivel atual:
      - pontos_max: 5..24 (Pontos de Misticismo)
      - ciclo_max: 1..5 (ciclo máximo de feitiço criável via pontos)
      - magias_lim: 2..14 (Magias Conhecidas — total de feitiços que conhece)
      - truques_lim: 2..4 (Truques Conhecidos)
    Tabela de conversão pontos → slot (fixa pelas regras):
      1°=2pt · 2°=3pt · 3°=4pt · 4°=5pt · 5°=6pt
    """
    nv = _calc_mistico_level(classes_pc)
    if nv <= 0:
        return None
    cls_id = next((c["Id_Classe"] for c in classes_pc
                   if (c.get("SlugClasse") or "").lower() == "mistico"), None)
    if cls_id is None:
        return None

    def _val(nome: str, padrao: int = 0) -> int:
        r = one(
            "SELECT Valor FROM TB_RecursoClasse "
            " WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND Nivel<=? "
            " ORDER BY Nivel DESC LIMIT 1",
            cls_id, nome, nv,
        )
        try:
            return int(r["Valor"]) if r and r["Valor"] else padrao
        except (TypeError, ValueError):
            return padrao

    return {
        "nivel_mistico":   nv,
        "pontos_max":      _val("Pontos de Misticismo", 0),
        "ciclo_max":       _val("Ciclo de Feitiços", 1),
        "magias_lim":      _val("Magias Conhecidas", 0),
        "truques_lim":     _val("Truques Conhecidos", 0),
        "conversao_pontos_slot": {"1": 2, "2": 3, "3": 4, "4": 5, "5": 6},
    }


def _spell_slots_dict(caster_level: int) -> dict[str, int]:
    """Retorna {1: n, 2: n, ...} apenas com níveis que têm slots > 0."""
    if caster_level <= 0:
        return {}
    idx = min(caster_level, 20) - 1
    row = MULTICLASS_SPELL_SLOTS[idx]
    return {str(i+1): n for i, n in enumerate(row) if n > 0}


def _atribs_do_personagem(pid: int) -> dict[str, int]:
    """Retorna atributos EFETIVOS do personagem: base + Background + ASIs de talentos.
    Usado para checagem de prereq de multiclasse — o jogador deve poder pegar a multiclasse
    com o atributo final que ele já enxerga na ficha (ex.: Pal req STR 13, base 12 +1 bg = 13 OK).
    """
    r = one("SELECT * FROM TB_PersonagemAtributo WHERE Id_Personagem=?", pid)
    if not r:
        return {}
    p_row = one(
        "SELECT Nivel, BackgroundBonusJSON FROM TB_Personagem WHERE Id_Personagem=?",
        pid,
    ) or {}
    p_dict = {
        "Nivel": p_row.get("Nivel") or 1,
        "BackgroundBonusJSON": p_row.get("BackgroundBonusJSON"),
        "atributos": {
            "Forca": r.get("Forca") or 10,
            "Destreza": r.get("Destreza") or 10,
            "Constituicao": r.get("Constituicao") or 10,
            "Inteligencia": r.get("Inteligencia") or 10,
            "Sabedoria": r.get("Sabedoria") or 10,
            "Carisma": r.get("Carisma") or 10,
        },
    }
    talentos = _build_talentos(pid)
    return _atributos_efetivos(p_dict, talentos)["valores"]


def _check_prereq_classe(req_json: str | None, atribs: dict[str, int]) -> tuple[bool, str]:
    """Confere se atributos do personagem batem o req da classe.
    Retorna (ok, motivo_se_falha).
    """
    if not req_json:
        return True, ""
    try:
        req = json.loads(req_json)
    except (json.JSONDecodeError, TypeError):
        return True, ""
    minimo = int(req.get("min") or 13)
    nomes = req.get("atribs") or []
    logica = (req.get("logica") or "all").lower()
    if not nomes:
        return True, ""
    valores = [atribs.get(n, 0) for n in nomes]
    if logica == "any":
        ok = any(v >= minimo for v in valores)
    else:
        ok = all(v >= minimo for v in valores)
    if ok:
        return True, ""
    pares = [f"{n} {v}/{minimo}" for n, v in zip(nomes, valores)]
    conector = " OU " if logica == "any" else " E "
    return False, f"Requer {conector.join(pares)}"


def _multiclass_prereq_check(pid: int, id_classe_alvo: int,
                              ignorar_classes: list[int] | None = None) -> tuple[bool, list[str]]:
    """Multiclass: precisa atender prereq da classe ALVO e de TODAS as classes
    atuais do personagem (exceto as listadas em ignorar_classes — útil para edit).
    Retorna (ok, lista_de_motivos_de_falha).
    """
    atribs = _atribs_do_personagem(pid)
    motivos: list[str] = []

    # Classe alvo
    cls_alvo = one("SELECT Nome, MulticlassReqJSON FROM TB_Classe WHERE Id_Classe=?", id_classe_alvo)
    if cls_alvo:
        ok, motivo = _check_prereq_classe(cls_alvo.get("MulticlassReqJSON"), atribs)
        if not ok:
            motivos.append(f"{cls_alvo['Nome']}: {motivo}")

    # Classes atuais (incluindo a primária — todas precisam atender)
    ignorar = set(ignorar_classes or [])
    atuais = rows(
        "SELECT pc.Id_Classe, c.Nome, c.MulticlassReqJSON "
        "FROM TB_PersonagemClasse pc "
        "JOIN TB_Classe c ON c.Id_Classe = pc.Id_Classe "
        "WHERE pc.Id_Personagem=?", pid,
    )
    for c in atuais:
        if c["Id_Classe"] in ignorar or c["Id_Classe"] == id_classe_alvo:
            continue
        ok, motivo = _check_prereq_classe(c["MulticlassReqJSON"], atribs)
        if not ok:
            motivos.append(f"{c['Nome']}: {motivo}")
    return (len(motivos) == 0), motivos


def _sync_nivel_total(pid: int) -> None:
    """Atualiza TB_Personagem.Nivel = SUM(TB_PersonagemClasse.Nivel)."""
    conn = db()
    total_row = conn.execute(
        "SELECT COALESCE(SUM(Nivel), 1) AS t FROM TB_PersonagemClasse WHERE Id_Personagem=?",
        (pid,),
    ).fetchone()
    total = total_row["t"] if total_row else 1
    conn.execute(
        "UPDATE TB_Personagem SET Nivel=?, AtualizadoEm=CURRENT_TIMESTAMP WHERE Id_Personagem=?",
        (total, pid),
    )
    conn.commit()


@app.post("/api/personagens/<int:pid>/classes")
def add_classe(pid: int):
    """Adiciona uma classe ao personagem (multiclasse).
    Body: {Id_Classe, Id_Subclasse?, Nivel, Force?}.
    Valida prereqs PHB 2024. Body.Force=true ignora validação (debug).
    """
    d = request.get_json(force=True) or {}
    id_classe = d.get("Id_Classe")
    if not id_classe:
        return jsonify({"error": "Id_Classe obrigatório"}), 400
    id_sub = d.get("Id_Subclasse")
    nivel = max(1, min(20, int(d.get("Nivel") or 1)))
    forcar = bool(d.get("Force"))

    # Multiclass prereq: só checa se já há outra classe (= é multi)
    has_existing = (one(
        "SELECT COUNT(*) AS n FROM TB_PersonagemClasse WHERE Id_Personagem=?", pid,
    ) or {}).get("n", 0) > 0
    if has_existing and not forcar:
        ok, motivos = _multiclass_prereq_check(pid, int(id_classe))
        if not ok:
            return jsonify({"error": "prereq multiclasse não atendido",
                            "motivos": motivos}), 400

    conn = db()
    row = conn.execute(
        "SELECT COALESCE(MAX(Ordem), -1) + 1 AS n FROM TB_PersonagemClasse WHERE Id_Personagem=?",
        (pid,),
    ).fetchone()
    next_ordem = row["n"]
    try:
        conn.execute(
            "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) "
            "VALUES (?, ?, ?, ?, ?)",
            (pid, id_classe, id_sub, nivel, next_ordem),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        return jsonify({"error": f"classe já existe: {e}"}), 400
    _sync_nivel_total(pid)
    return jsonify({"ok": True})


@app.get("/api/personagens/<int:pid>/classes-elegiveis")
def list_classes_elegiveis(pid: int):
    """Lista todas as classes com flag de elegibilidade pra multiclasse.
    Útil pro picker filtrar/anotar visualmente.
    Retorna [{Id_Classe, Nome, Slug, MulticlassReqJSON, MulticlassProfJSON,
              elegivel: bool, motivo: str|null}, ...]
    """
    todas = rows("SELECT Id_Classe, Nome, Slug, DadoVida, "
                  "       MulticlassReqJSON, MulticlassProfJSON "
                  "FROM TB_Classe ORDER BY Nome")
    has_existing = (one(
        "SELECT COUNT(*) AS n FROM TB_PersonagemClasse WHERE Id_Personagem=?", pid,
    ) or {}).get("n", 0) > 0
    ja_tem = {r["Id_Classe"] for r in rows(
        "SELECT Id_Classe FROM TB_PersonagemClasse WHERE Id_Personagem=?", pid,
    )}
    out = []
    for c in todas:
        item = dict(c)
        item["ja_tem"] = c["Id_Classe"] in ja_tem
        if not has_existing:
            # Personagem novo (sem classes) — qualquer classe inicial é elegível
            item["elegivel"] = True
            item["motivo"] = None
        else:
            ok, motivos = _multiclass_prereq_check(pid, c["Id_Classe"])
            item["elegivel"] = ok
            item["motivo"] = "; ".join(motivos) if motivos else None
        out.append(item)
    return jsonify(out)


@app.put("/api/personagens/<int:pid>/classes/<int:id_pc>")
def update_classe(pid: int, id_pc: int):
    """Atualiza Nivel e/ou Id_Subclasse de uma entrada multiclasse.
    Body: {Nivel?, Id_Subclasse?}.
    """
    d = request.get_json(force=True) or {}
    sets, args = [], []
    if "Nivel" in d:
        sets.append("Nivel = ?")
        args.append(max(1, min(20, int(d["Nivel"]))))
    if "Id_Subclasse" in d:
        sets.append("Id_Subclasse = ?")
        args.append(d["Id_Subclasse"])
    if not sets:
        return jsonify({"error": "nada para atualizar"}), 400
    args += [pid, id_pc]
    conn = db()
    conn.execute(
        f"UPDATE TB_PersonagemClasse SET {', '.join(sets)} "
        f"WHERE Id_Personagem=? AND Id_PersonagemClasse=?",
        args,
    )
    conn.commit()
    _sync_nivel_total(pid)
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/classes/<int:id_pc>")
def delete_classe(pid: int, id_pc: int):
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemClasse WHERE Id_Personagem=? AND Id_PersonagemClasse=?",
        (pid, id_pc),
    )
    conn.commit()
    _sync_nivel_total(pid)
    return jsonify({"ok": True})


@app.put("/api/personagens/<int:pid>/pericias/<int:peric_id>")
def update_pericia(pid: int, peric_id: int):
    """Toggle Proficiente / Expertise BASE (classe + background) de uma perícia.
    Body: {proficiente?: 0|1, expertise?: 0|1}.
    Não usar para picks de traços/habs — usar /escolhas-pericia.
    """
    d = request.get_json(force=True) or {}
    sets = []
    args: list = []
    if "proficiente" in d:
        sets.append("Proficiente = ?")
        args.append(1 if d["proficiente"] else 0)
    if "expertise" in d:
        sets.append("Expertise = ?")
        args.append(1 if d["expertise"] else 0)
    if not sets:
        return jsonify({"error": "nada para atualizar"}), 400
    args += [pid, peric_id]
    conn = db()
    conn.execute(
        f"UPDATE TB_PersonagemPericia SET {', '.join(sets)} "
        f"WHERE Id_Personagem=? AND Id_Pericia=?",
        args,
    )
    conn.commit()
    return jsonify({"ok": True})


@app.post("/api/personagens/<int:pid>/escolhas-pericia")
def post_escolha_pericia(pid: int):
    """Adiciona/atualiza um pick de perícia (via traço com pick:pericia:N).
    Body: {origem: str, slot: int, id_pericia: int, tipo?: 'proficiencia'|'expertise'}.
    """
    d = request.get_json(force=True) or {}
    origem = (d.get("origem") or "").strip()
    slot = d.get("slot")
    id_pericia = d.get("id_pericia")
    tipo = d.get("tipo") or "proficiencia"
    if not origem or slot is None or id_pericia is None:
        return jsonify({"error": "origem, slot e id_pericia obrigatórios"}), 400
    if tipo not in ("proficiencia", "expertise"):
        return jsonify({"error": "tipo deve ser proficiencia ou expertise"}), 400
    conn = db()
    # upsert: REPLACE pra mesmo (pid, origem, slot)
    conn.execute(
        "INSERT OR REPLACE INTO TB_PersonagemEscolhaPericia "
        "(Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo) VALUES (?,?,?,?,?)",
        (pid, origem, int(slot), int(id_pericia), tipo),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/escolhas-pericia/<origem>/<int:slot>")
def del_escolha_pericia(pid: int, origem: str, slot: int):
    """Remove pick de perícia (esvaziar slot)."""
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemEscolhaPericia "
        "WHERE Id_Personagem=? AND Origem=? AND SlotIndex=?",
        (pid, origem, slot),
    )
    conn.commit()
    return jsonify({"ok": True})


@app.post("/api/personagens/<int:pid>/escolhas-idioma")
def post_escolha_idioma(pid: int):
    """Adiciona/atualiza pick de idioma ou ferramenta (via traço com pick:idioma:N ou pick:ferramenta:N).
    Body: {origem: str, slot: int, tipo: 'idioma'|'ferramenta', nome: str}.
    Armazena em TB_PersonagemIdioma com Origem='pick:<Traço>:<slot>'.
    """
    d = request.get_json(force=True) or {}
    origem = (d.get("origem") or "").strip()
    slot = d.get("slot")
    tipo = (d.get("tipo") or "").strip()
    nome = (d.get("nome") or "").strip()
    if not origem or slot is None or not tipo or not nome:
        return jsonify({"error": "origem, slot, tipo e nome obrigatórios"}), 400
    if tipo not in ("idioma", "ferramenta"):
        return jsonify({"error": "tipo deve ser idioma ou ferramenta"}), 400
    origem_str = f"pick:{origem}:{int(slot)}"
    conn = db()
    # remove pick anterior daquele slot
    conn.execute(
        "DELETE FROM TB_PersonagemIdioma WHERE Id_Personagem=? AND Origem=?",
        (pid, origem_str),
    )
    # se já existe row com o mesmo Tipo+Nome (de outra origem), reaproveita movendo pra esta origem
    cur = conn.cursor()
    cur.execute(
        "UPDATE TB_PersonagemIdioma SET Origem=? "
        "WHERE Id_Personagem=? AND Tipo=? AND LOWER(Nome)=LOWER(?)",
        (origem_str, pid, tipo, nome[:100]),
    )
    if cur.rowcount == 0:
        conn.execute(
            "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
            (pid, tipo, nome[:100], origem_str),
        )
    conn.commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/escolhas-idioma/<origem>/<int:slot>")
def del_escolha_idioma(pid: int, origem: str, slot: int):
    """Remove pick de idioma/ferramenta (esvaziar slot)."""
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemIdioma WHERE Id_Personagem=? AND Origem=?",
        (pid, f"pick:{origem}:{slot}"),
    )
    conn.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Escolhas de tag genéricas (TB_PersonagemEscolhaTag) — pra qualquer pick:<tipo>
# que não seja perícia/idioma/ferramenta. Tipos suportados na prática:
# estilo-de-luta, maestria-arma, talento-geral, talento-origem, manobra,
# pericia-cortesao, etc. — qualquer Tipo de TB_OpcaoJogo OU outras tabelas
# (ex: TB_Maestria pra maestria-arma).
# ---------------------------------------------------------------------------
@app.post("/api/personagens/<int:pid>/escolhas-tag")
def post_escolha_tag(pid: int):
    """Adiciona/atualiza pick de tag genérica.
    Body: {origem: str, tipo: str, slot_index: int, valor: str}.
    Armazena em TB_PersonagemEscolhaTag com PK (pid, origem, tipo, slot_index)."""
    d = request.get_json(force=True) or {}
    origem = (d.get("origem") or "").strip()
    tipo = (d.get("tipo") or "").strip()
    slot = d.get("slot_index")
    valor = (d.get("valor") or "").strip()
    if not origem or not tipo or slot is None or not valor:
        return jsonify({"error": "origem, tipo, slot_index e valor obrigatórios"}), 400
    db().execute(
        "INSERT INTO TB_PersonagemEscolhaTag (Id_Personagem, Origem, Tipo, SlotIndex, Valor) "
        "VALUES (?,?,?,?,?) "
        "ON CONFLICT(Id_Personagem, Origem, Tipo, SlotIndex) "
        "DO UPDATE SET Valor=excluded.Valor",
        (pid, origem, tipo, int(slot), valor[:150]),
    )
    db().commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/escolhas-tag/<origem>/<tipo>/<int:slot>")
def del_escolha_tag(pid: int, origem: str, tipo: str, slot: int):
    """Remove pick de tag genérica (esvazia slot)."""
    db().execute(
        "DELETE FROM TB_PersonagemEscolhaTag "
        "WHERE Id_Personagem=? AND Origem=? AND Tipo=? AND SlotIndex=?",
        (pid, origem, tipo, slot),
    )
    db().commit()
    return jsonify({"ok": True})


@app.delete("/api/personagens/<int:pid>/maestrias-armas/<int:slot>")
def del_maestria_arma(pid: int, slot: int):
    """Remove escolha do slot."""
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemMaestriaArma "
        "WHERE Id_Personagem=? AND SlotIndex=?",
        (pid, slot),
    )
    conn.commit()
    return jsonify({"ok": True})


def _ensure_pericias_padrao(pid: int) -> None:
    """Garante que o personagem tenha as 18 perícias padrão. Idempotente
    via UNIQUE(Id_Personagem, Nome) — INSERT OR IGNORE preserva flags
    existentes (Proficiente/Expertise) se a row já existe.
    """
    conn = db()
    conn.executemany(
        "INSERT OR IGNORE INTO TB_PersonagemPericia "
        "(Id_Personagem, Nome, Atributo, Proficiente, Expertise) VALUES (?, ?, ?, 0, 0)",
        [(pid, nome, atrib) for nome, atrib in PERICIAS_PADRAO],
    )
    conn.commit()


@app.get("/api/personagens/<int:pid>/full")
def personagem_full(pid: int):
    """Retorna TUDO do personagem (cru + tabelas auxiliares) para a página /ficha."""
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    _ensure_pericias_padrao(pid)
    esc = p["escolha"] or {}
    def _getopt(tbl, k, val):
        return one(f"SELECT * FROM {tbl} WHERE {k} = ?", val) if val else None
    raca     = _getopt("TB_Raca",       "Id_Raca",      esc.get("Id_Raca"))
    linhagem = _getopt("TB_Linhagem",   "Id_Linhagem",  esc.get("Id_Linhagem"))
    essencia = _getopt("TB_Essencia",   "Id_Essencia",  esc.get("Id_Essencia"))
    ess_lin  = _getopt("TB_EssenciaLinhagem", "Id_EssLinhagem", esc.get("Id_EssLinhagem"))
    classe   = _getopt("TB_Classe",     "Id_Classe",    esc.get("Id_Classe"))
    sub      = _getopt("TB_Subclasse",  "Id_Subclasse", esc.get("Id_Subclasse"))

    # Multiclasse: lista de classes com seus respectivos níveis e subclasses.
    # Se a tabela TB_PersonagemClasse estiver vazia, fallback pra classe primária
    # (Id_Classe/Id_Subclasse de TB_PersonagemEscolha) usando p.Nivel inteiro.
    classes_pc = rows(
        """SELECT pc.Id_PersonagemClasse, pc.Id_Classe, pc.Id_Subclasse, pc.Nivel, pc.Ordem,
                  c.Nome AS NomeClasse, c.Slug AS SlugClasse,
                  c.SavesJSON AS SavesJSON, c.DadoVida AS DadoVida,
                  c.Conjuracao AS Conjuracao,
                  c.MulticlassReqJSON AS MulticlassReqJSON,
                  c.MulticlassProfJSON AS MulticlassProfJSON,
                  c.SkillsJSON AS SkillsJSON,
                  c.ArmorProfJSON AS ArmorProfJSON,
                  c.WeaponProfJSON AS WeaponProfJSON,
                  c.ToolProfJSON AS ToolProfJSON,
                  c.EquipamentoInicialJSON AS EquipamentoInicialJSON,
                  c.TagsJSON AS ClasseTagsJSON,
                  s.Nome AS NomeSubclasse,
                  s.Tagline AS SubclasseTagline,
                  s.TagsJSON AS SubclasseTagsJSON
           FROM TB_PersonagemClasse pc
           JOIN TB_Classe c ON c.Id_Classe = pc.Id_Classe
           LEFT JOIN TB_Subclasse s ON s.Id_Subclasse = pc.Id_Subclasse
           WHERE pc.Id_Personagem = ?
           ORDER BY pc.Ordem, pc.Id_PersonagemClasse""",
        pid,
    )
    if not classes_pc and esc.get("Id_Classe"):
        # Compat: personagem antigo sem entry em TB_PersonagemClasse — sintetiza a partir da escolha.
        classes_pc = [{
            "Id_PersonagemClasse": None,
            "Id_Classe":     esc.get("Id_Classe"),
            "Id_Subclasse":  esc.get("Id_Subclasse"),
            "Nivel":         p["Nivel"] or 1,
            "Ordem":         0,
            "NomeClasse":    classe.get("Nome") if classe else None,
            "SlugClasse":    classe.get("Slug") if classe else None,
            "SavesJSON":     classe.get("SavesJSON") if classe else None,
            "DadoVida":      classe.get("DadoVida") if classe else None,
            "NomeSubclasse": sub.get("Nome") if sub else None,
        }]
    # SOURCE OF TRUTH: state.classe (singular, primária) vem de classes_pc[0],
    # NÃO de TB_PersonagemEscolha (que pode estar stale após delete/swap).
    # Re-popula classe/sub pra alinhar com a primeira entry de TB_PersonagemClasse.
    if classes_pc:
        primeira = classes_pc[0]
        classe = _getopt("TB_Classe", "Id_Classe", primeira.get("Id_Classe"))
        sub    = _getopt("TB_Subclasse", "Id_Subclasse", primeira.get("Id_Subclasse"))
    else:
        classe = None
        sub = None
    # Total = sum dos níveis de classe (se houver), senão p.Nivel.
    nivel_total = sum(c["Nivel"] for c in classes_pc) if classes_pc else (p["Nivel"] or 1)

    # Talento de Origem: principal (BG) + extra (Raízes Profundas) + racial (traço com pick:talento-origem:1)
    talento_origem = None
    talento_origem_extra = None
    talento_origem_racial = None
    magia_expandida: list[dict] = []

    def _carrega_origem(id_opcao):
        if not id_opcao:
            return None, []
        op = one(
            "SELECT * FROM TB_OpcaoJogo WHERE Id_Opcao=? AND Tipo='talento-origem'",
            id_opcao,
        )
        magias: list[dict] = []
        if op and op.get("MagiaExpandidaJSON"):
            try:
                magias = json.loads(op["MagiaExpandidaJSON"]) or []
            except (json.JSONDecodeError, TypeError):
                magias = []
        return op, magias

    talento_origem, m_principal = _carrega_origem(esc.get("Id_TalentoOrigem"))
    talento_origem_extra, m_extra = _carrega_origem(esc.get("Id_TalentoOrigemExtra"))
    talento_origem_racial, m_racial = _carrega_origem(esc.get("Id_TalentoOrigemRacial"))

    nivel_pers = p["Nivel"] or 1
    # pv_bonus_origem é computado mais abaixo a partir do tag_origem agregado
    # (regra de tags universais — ver docs/regra-tags-universais.md §7).
    # marca cada magia com o talento de origem dela (pra UI distinguir)
    for m in m_principal:
        m["__via_origem"] = talento_origem["Nome"] if talento_origem else None
    for m in m_extra:
        m["__via_origem"] = talento_origem_extra["Nome"] if talento_origem_extra else None
    for m in m_racial:
        m["__via_origem"] = talento_origem_racial["Nome"] if talento_origem_racial else None
    # magia_expandida: APENAS magias vindas de talento de origem (Marcas, etc.)
    magia_expandida = m_principal + m_extra + m_racial
    # magias_subclasse: vindas de classe/subclasse (Magias de Domínio, Juramento etc.)
    # — auto-prep da feature, slot vem da multiclasse.
    magias_subclasse: list[dict] = []
    sub_magias_rows = rows(
        "SELECT s.Nome AS NomeSub, s.MagiaExpandidaJSON AS Mags "
        "FROM TB_PersonagemClasse pc "
        "JOIN TB_Subclasse s ON s.Id_Subclasse = pc.Id_Subclasse "
        "WHERE pc.Id_Personagem=? AND s.MagiaExpandidaJSON IS NOT NULL", pid,
    )
    for r in sub_magias_rows:
        try:
            mags = json.loads(r.get("Mags") or "[]") or []
        except (json.JSONDecodeError, TypeError):
            mags = []
        for m in mags:
            m["__via_origem"] = r.get("NomeSub") or "?"
            magias_subclasse.append(m)

    niv = p["Nivel"] or 1
    # Tracos: combina raça base + linhagem (se tiver) + essência base + sub-linhagem (se tiver).
    # Usa filtros condicionais para nao retornar tudo.
    id_raca = esc.get("Id_Raca")
    id_linhagem = esc.get("Id_Linhagem")
    id_essencia = esc.get("Id_Essencia")
    id_esslin = esc.get("Id_EssLinhagem")
    cond_parts = []
    args: list = []
    if id_raca:
        # raça base (sem linhagem nem essência amarrada)
        cond_parts.append(
            "(Id_Raca = ? AND Id_Linhagem IS NULL AND Id_Essencia IS NULL AND Id_EssLinhagem IS NULL)"
        )
        args.append(id_raca)
        if id_linhagem:
            cond_parts.append("(Id_Raca = ? AND Id_Linhagem = ?)")
            args += [id_raca, id_linhagem]
    if id_essencia:
        cond_parts.append(
            "(Id_Essencia = ? AND Id_EssLinhagem IS NULL AND Id_Raca IS NULL)"
        )
        args.append(id_essencia)
        if id_esslin:
            cond_parts.append("(Id_EssLinhagem = ?)")
            args.append(id_esslin)
    if cond_parts:
        sql = (
            "SELECT * FROM TB_TracoRacial "
            " WHERE NivelRequisito <= ? AND ("
            + " OR ".join(cond_parts)
            + ") ORDER BY (Id_Raca IS NULL), (Id_Linhagem IS NOT NULL OR Id_EssLinhagem IS NOT NULL), NivelRequisito"
        )
        tracos = rows(sql, niv, *args)
    else:
        tracos = []

    # Primeira classe (ordem=0) é quem concede a escolha de perícias do PHB 2024.
    # Multiclasse NÃO concede skills (apenas armor/weapons específicos por classe).
    # Renderizado como traço sintético com pick:pericia:N + filtro pela lista da classe.
    if classes_pc:
        primeira_pc = classes_pc[0]   # já ordenado por Ordem
        primeira_classe_row = one(
            "SELECT Nome, SkillsJSON FROM TB_Classe WHERE Id_Classe=?",
            primeira_pc["Id_Classe"],
        )
        if primeira_classe_row and primeira_classe_row.get("SkillsJSON"):
            try:
                skills_spec = json.loads(primeira_classe_row["SkillsJSON"]) or {}
            except (json.JSONDecodeError, TypeError):
                skills_spec = {}
            choose = int(skills_spec.get("choose") or 0)
            from_list = skills_spec.get("from") or []
            if choose > 0:
                tracos.append({
                    "Id_Traco": None,
                    "Nome": primeira_classe_row["Nome"],   # Origem em TB_PersonagemEscolhaPericia
                    "Descricao": (
                        f"**Perícias de Classe ({primeira_classe_row['Nome']}, primeira classe):** "
                        f"escolha {choose} dentre {', '.join(from_list)}."
                    ),
                    "TagsJSON": json.dumps([f"pick:pericia:{choose}"], ensure_ascii=False),
                    "PickFromList": from_list,            # frontend filtra picker por essa lista
                    "Id_Raca": None, "Id_Linhagem": None, "Id_Essencia": None, "Id_EssLinhagem": None,
                    "NivelRequisito": 1,
                    "_synth_classe": True,
                })
    # Multiclasse: agrega habs por classe usando o NÍVEL DAQUELA CLASSE
    # (não o nivel total). RecursoClasse também filtrado por classe individual.
    rec_prog = []
    habs_cls = []
    habs_sub = []
    for c_pc in classes_pc:
        cls_id = c_pc["Id_Classe"]
        sub_id = c_pc["Id_Subclasse"]
        nivel_classe = c_pc["Nivel"] or 1
        rec_prog.extend(rows(
            "SELECT * FROM TB_RecursoClasse WHERE Id_Classe=? AND Nivel<=? ORDER BY Nivel, Nome",
            cls_id, nivel_classe,
        ))
        # NivelClasse = nível DAQUELA classe (não nivel total). Usado por
        # tags com n_por_nivel pra resolver progressão por classe (ex.
        # Maestria de Armas Guerreiro: 3→4→5→6 conforme Nv 1/4/10/16).
        habs_cls.extend(rows(
            "SELECT h.*, ? AS NivelClasse FROM TB_ClasseHabilidade h "
            "WHERE h.Id_Classe=? AND h.Id_Subclasse IS NULL AND h.NivelAdquirido<=? "
            "ORDER BY h.NivelAdquirido, h.Nome",
            nivel_classe, cls_id, nivel_classe,
        ))
        if sub_id:
            habs_sub.extend(rows(
                "SELECT h.*, ? AS NivelClasse FROM TB_ClasseHabilidade h "
                "WHERE h.Id_Subclasse=? AND h.NivelAdquirido<=? "
                "ORDER BY h.NivelAdquirido, h.Nome",
                nivel_classe, sub_id, nivel_classe,
            ))

    # ---- Agrega tags das habilidades ativas (TagsJSON) ----
    # Tags suportadas:
    #   "expertise:<NomePericia>"  → pericia.Expertise = 1
    #   "prof:<NomePericia>"       → pericia.Proficiente = 1
    #   "save-prof:<Atributo>"     → atributo entra em saves_proficientes
    #   "resist:<Elemento>" / "immune:<Elemento>" / "vuln:<Elemento>"  → entra em resistencias
    # Tracker pra gerar lista de origem por tag.
    hab_tags: set[str] = set()
    tag_origem: list[tuple[str, str]] = []  # [(tag, origem)]
    tag_locked: list[tuple[str, str, int]] = []  # [(tag, origem, min_nivel)] — gated, não vale no efeito
    # Talentos do personagem com TagsJSON (raça/essência/classe). Carrega 1× e reusa.
    talentos_full = _build_talentos(pid)
    nivel_pers = p["Nivel"] or 1

    def _resolve_n_por_nivel(progressao: dict, nivel_efetivo: int) -> int | None:
        """Pega o maior nível de chave <= nivel_efetivo e retorna o valor.
        progressao: {"1": 3, "4": 4, "10": 5, "16": 6} → Nv 16 → 6."""
        aplicaveis: list[tuple[int, int]] = []
        for k, v in progressao.items():
            try:
                aplicaveis.append((int(k), int(v)))
            except (ValueError, TypeError):
                continue
        aplicaveis = [(lv, val) for lv, val in aplicaveis if lv <= nivel_efetivo]
        if not aplicaveis:
            return None
        return max(aplicaveis, key=lambda kv: kv[0])[1]

    def _agg_tags_from(items: list[dict], nome_field: str = "Nome", level_field: str | None = None):
        for it in items:
            # respeita gate de nível quando fornecido
            if level_field is not None:
                lvl = it.get(level_field) or 1
                if lvl > nivel_pers:
                    continue
            raw = it.get("TagsJSON")
            if not raw:
                continue
            # nivel efetivo pra resolver n_por_nivel: usa NivelClasse quando o
            # item carrega (hab/classe/sub), senão nivel_pers (total).
            nivel_efetivo = it.get("NivelClasse") or nivel_pers
            try:
                for t in json.loads(raw) or []:
                    # Forma string: "pick:pericia:2" | "expertise:Arcanismo" | ...
                    if isinstance(t, str):
                        # Tags 'gate:X' são meta-flags de display (frontend usa pra
                        # condicionar exibição). NÃO devem entrar no pool ativo —
                        # senão a própria gate-tag se ativa e a hab nunca esconde.
                        if t.startswith("gate:"):
                            continue
                        # Placeholder $atributo — expande usando AumentoAtributo do
                        # item (talentos como "Resiliente" cujo +1 e save-prof
                        # dependem do atributo escolhido pelo jogador).
                        if "$atributo" in t:
                            aum = (it.get("AumentoAtributo") or "").lower().strip()
                            for short in [s.strip() for s in aum.split(",") if s.strip()]:
                                full_attr = _ATR_FULL_BY_SHORT.get(short)
                                if full_attr:
                                    expanded = t.replace("$atributo", full_attr)
                                    hab_tags.add(expanded)
                                    tag_origem.append((expanded, it.get(nome_field) or "?"))
                            continue
                        hab_tags.add(t)
                        tag_origem.append((t, it.get(nome_field) or "?"))
                    # Forma objeto: {"tag": "pick:pericia:1", "filter": [...]}
                    # ou {"tag": "pick:maestria-arma", "n_por_nivel": {"1":3,"4":4,"10":5,"16":6}}
                    elif isinstance(t, dict) and isinstance(t.get("tag"), str):
                        base = t["tag"]
                        # Resolve progressão se houver
                        prog = t.get("n_por_nivel")
                        if isinstance(prog, dict) and prog:
                            n = _resolve_n_por_nivel(prog, nivel_efetivo)
                            if n is None:
                                continue  # nivel_efetivo abaixo do mínimo da progressão
                            tag_str = f"{base}:{n}"
                        else:
                            tag_str = base
                        # Filter (whitelist) — sufixo =A|B|C
                        flt = t.get("filter")
                        if isinstance(flt, list) and flt:
                            tag_str = f"{tag_str}={'|'.join(str(x) for x in flt)}"
                        # Gate min_nivel: tag locked não entra em hab_tags nem em
                        # tag_origem (não vale no efeito), mas vai pro payload com
                        # flag locked pra UI renderizar slot bloqueado.
                        min_nv = t.get("min_nivel")
                        if isinstance(min_nv, int) and nivel_efetivo < min_nv:
                            tag_locked.append((tag_str, it.get(nome_field) or "?", min_nv))
                            continue
                        hab_tags.add(tag_str)
                        tag_origem.append((tag_str, it.get(nome_field) or "?"))
            except (json.JSONDecodeError, TypeError):
                pass

    _agg_tags_from(habs_cls + habs_sub)            # já filtrados por nivel
    _agg_tags_from(tracos)                          # já filtrados por raça/lin/ess
    _agg_tags_from(talentos_full, level_field="Nivel")  # filtra ASIs futuros
    # Talentos de origem (principal/extra/racial) também entram no pool universal
    # (regra de tags universais) — assim pv-por-nivel:N e qualquer tag futura funcionam
    # idêntico vindo de qualquer fonte.
    _agg_tags_from([t for t in (talento_origem, talento_origem_extra, talento_origem_racial) if t])
    # Linha-mãe: classe(s)/subclasse(s) ativas do personagem (multiclasse) +
    # raça/linhagem/essência/sub-linhagem. TagsJSON nestas tabelas foi adicionado
    # via migrate_tags_universal.py — começa NULL em tudo; preencher via página debug.
    _classes_subs_mae: list[dict] = []
    for c_pc in classes_pc:
        nivel_da_classe = c_pc.get("Nivel") or 1
        c_row = one(
            "SELECT Nome, TagsJSON FROM TB_Classe WHERE Id_Classe=?",
            c_pc["Id_Classe"],
        )
        if c_row:
            c_row["NivelClasse"] = nivel_da_classe
            _classes_subs_mae.append(c_row)
        if c_pc.get("Id_Subclasse"):
            s_row = one(
                "SELECT Nome, TagsJSON FROM TB_Subclasse WHERE Id_Subclasse=?",
                c_pc["Id_Subclasse"],
            )
            if s_row:
                s_row["NivelClasse"] = nivel_da_classe
                _classes_subs_mae.append(s_row)
    _agg_tags_from(_classes_subs_mae)
    _agg_tags_from([r for r in (raca, linhagem, essencia, ess_lin) if r])

    # Tags vindas das ESCOLHAS do personagem (TB_PersonagemEscolhaTag → TB_OpcaoJogo).
    # Cada opção escolhida pode ter sua própria TagsJSON, que ativa quando a opção
    # é selecionada. Ex: "Armas Treinadas" da Doutrina Marcial tem +maestrias-arma:3.
    _opcoes_escolhidas = rows(
        "SELECT pet.Origem, pet.Tipo, pet.Valor, o.TagsJSON, o.Nome "
        "FROM TB_PersonagemEscolhaTag pet "
        "JOIN TB_OpcaoJogo o ON o.Tipo = pet.Tipo AND o.Nome = pet.Valor "
        "WHERE pet.Id_Personagem = ?",
        pid,
    )
    # origem = "<HabOrigem> · <NomeOpcao>" pra rastrear cadeia.
    for opc in _opcoes_escolhidas:
        opc["_NomeAgregador"] = f"{opc['Origem']} · {opc['Nome']}"
    _agg_tags_from(_opcoes_escolhidas, nome_field="_NomeAgregador")

    # `tags_de_opcoes_por_origem` — mapa {origem_str: [tags...]} com as tags
    # vindas das opções escolhidas pelo PERSONAGEM. NÃO modifica TB_ClasseHabilidade
    # nem atributos do registro da hab — é apenas um "overlay" runtime. Frontend
    # combina TagsJSON da hab + esse overlay no momento do render.
    tags_de_opcoes_por_origem: dict[str, list] = {}
    for opc in _opcoes_escolhidas:
        origem = opc.get("Origem")
        if not origem:
            continue
        try:
            opc_tags = json.loads(opc.get("TagsJSON") or "[]") or []
        except (json.JSONDecodeError, TypeError):
            opc_tags = []
        if not opc_tags:
            continue
        tags_de_opcoes_por_origem.setdefault(origem, []).extend(opc_tags)

    # =====================================================================
    # TAGS ACUMULADORAS — prefixo `+`. Princípio universal: cada ocorrência
    # da mesma tag soma o N. Múltiplas fontes acumulam.
    #
    # Sintaxe:
    #   "+manobras:6"            (forma string flat: soma 6 ao acumulador "manobras")
    #   {"tag":"+manobras", "n_por_nivel": {"1":3, "4":4}}
    #                            (forma objeto: N resolvido pelo nível efetivo
    #                             — já foi convertido em "+manobras:N" no agregador)
    #
    # Resultado: state.bonus_acumulados = {"manobras": 6, "ca": 2, ...}
    # state.bonus_fontes_por_chave[chave] = [{"nome":..., "valor":N}, ...] pro tooltip.
    # =====================================================================
    bonus_acumulados: dict[str, int] = {}
    bonus_fontes: dict[str, list[dict]] = {}
    for tag, origem_nome in tag_origem:
        if not tag.startswith("+"):
            continue
        # "+chave:N" — N pode ter sufixo "=A|B" do filter; ignora.
        body = tag[1:]
        chave, _, resto = body.partition(":")
        if not chave or not resto:
            continue
        n_str = resto.split("=", 1)[0]
        try:
            n_val = int(n_str)
        except ValueError:
            continue
        bonus_acumulados[chave] = bonus_acumulados.get(chave, 0) + n_val
        bonus_fontes.setdefault(chave, []).append({"nome": origem_nome, "valor": n_val})

    # pv-por-nivel:N — soma N × nivel_pers de qualquer tag agregada.
    # Caso especial PRESERVADO por compatibilidade (sem prefixo +). Tag legado
    # equivalente a "+pv:N×nivel" mas com semântica fixa "× nivel_pers".
    pv_bonus_origem_total = 0
    pv_bonus_origem_fontes: list[dict] = []
    for tag, origem_nome in tag_origem:
        if not tag.startswith("pv-por-nivel:"):
            continue
        try:
            por_nivel = int(tag.split(":", 1)[1])
        except (ValueError, IndexError):
            continue
        valor = por_nivel * nivel_pers
        pv_bonus_origem_total += valor
        pv_bonus_origem_fontes.append({"nome": origem_nome, "valor": valor})

    # Proficiências de armadura/arma vindas de tags `prof-armadura:X` e `prof-arma:X`.
    # Espelha o padrão de `prof:<Pericia>` mas pra armaduras/armas (categorias livres
    # como "Leve"/"Pesada"/"Marcial"/"Escudos"). Frontend mescla com as listas vindas
    # de TB_Classe.ArmorProfJSON / WeaponProfJSON na hora do render.
    profs_armadura_extras: list[dict] = []
    profs_arma_extras: list[dict] = []
    profs_ferramenta_extras: list[dict] = []
    profs_idioma_extras: list[dict] = []
    for tag, origem_nome in tag_origem:
        if tag.startswith("prof-armadura:"):
            valor = tag.split(":", 1)[1].strip()
            if valor:
                profs_armadura_extras.append({"valor": valor, "origem": origem_nome})
        elif tag.startswith("prof-arma:"):
            valor = tag.split(":", 1)[1].strip()
            if valor:
                profs_arma_extras.append({"valor": valor, "origem": origem_nome})
        elif tag.startswith("prof-ferramenta:"):
            valor = tag.split(":", 1)[1].strip()
            if valor:
                profs_ferramenta_extras.append({"valor": valor, "origem": origem_nome})
        elif tag.startswith("prof-idioma:"):
            valor = tag.split(":", 1)[1].strip()
            if valor:
                profs_idioma_extras.append({"valor": valor, "origem": origem_nome})

    expertise_pericias = {
        t.split(":", 1)[1].strip().lower()
        for t in hab_tags if t.startswith("expertise:")
    }
    prof_pericias = {
        t.split(":", 1)[1].strip().lower()
        for t in hab_tags if t.startswith("prof:")
    }
    saves_extra = {
        t.split(":", 1)[1].strip()
        for t in hab_tags if t.startswith("save-prof:")
    }

    # save-prof-vontade:<default>|<alt1>,<alt2>  (ex.: Vontade Firme do Ronin Nv 7)
    # Comportamento: se char já tem o save default de outra fonte → vira picker (alts).
    #                se NÃO tem → auto-aplica o default.
    # Saves vindos de classe = classe_saves; "outra fonte" inclui também save-prof:* já agregadas.
    classe_saves_set = set()
    if classe and classe.get("SavesJSON"):
        try:
            classe_saves_set = set(json.loads(classe["SavesJSON"]) or [])
        except (json.JSONDecodeError, TypeError):
            classe_saves_set = set()
    # 'saves_ja_tem' = saves vindos da classe + outros save-prof:* já agregados
    # (excluindo a cascata save-prof-vontade pra evitar self-reference).
    saves_ja_tem = classe_saves_set | saves_extra

    # Mapeamento short-attr → nome canônico (usado pra resolver pick em talentos
    # que armazenam escolha em AumentoAtributo: "int" → "Inteligencia").
    _ATR_FULL = {
        "for": "Forca", "dex": "Destreza", "des": "Destreza",
        "con": "Constituicao", "int": "Inteligencia",
        "sab": "Sabedoria", "car": "Carisma",
    }

    vontade_picks_por_hab: dict[int, str] = {}
    vontade_picks_por_talento: dict[int, str] = {}

    def _processa_vontade_tags(raw_tags: str | None, kind: str, item_id: int, item_nome: str = ""):
        """Processa tags save-prof-vontade num item (hab/talento/traço).
        Storage:
          - 'hab' / 'traco' / sintético: lê pick de TB_PersonagemEscolhaTag
            (Origem=item_nome, Tipo='save-prof-vontade', SlotIndex=0). Universal.
          - 'talento': lê de TB_PersonagemTalento.AumentoAtributo (legado, mantido).
        """
        try:
            v_tags = json.loads(raw_tags or "[]") or []
        except (json.JSONDecodeError, TypeError):
            return
        for vt in v_tags:
            if not isinstance(vt, str) or not vt.startswith("save-prof-vontade:"):
                continue
            valor = vt.split(":", 1)[1]
            if "|" not in valor:
                continue
            default_save, alts_str = valor.split("|", 1)
            default_save = default_save.strip()
            alts = [a.strip() for a in alts_str.split(",") if a.strip()]
            if default_save in saves_ja_tem:
                # precisa de pick — leitura por kind.
                chosen = ""
                if kind == "talento":
                    # talento: AumentoAtributo guarda short-attr ("int","car","sab")
                    pt = one(
                        "SELECT AumentoAtributo FROM TB_PersonagemTalento "
                        "WHERE Id_Personagem=? AND Id_Talento=?",
                        pid, item_id,
                    )
                    short = ((pt or {}).get("AumentoAtributo") or "").strip().lower() if pt else ""
                    chosen = _ATR_FULL.get(short, "")
                elif item_nome:
                    # hab / traco / sintético — TB_PersonagemEscolhaTag genérica
                    pick = one(
                        "SELECT Valor FROM TB_PersonagemEscolhaTag "
                        "WHERE Id_Personagem=? AND Origem=? AND Tipo='save-prof-vontade' AND SlotIndex=0",
                        pid, item_nome,
                    )
                    chosen = (pick or {}).get("Valor", "").strip() if pick else ""
                if chosen in alts:
                    saves_extra.add(chosen)
                    if kind == "hab":
                        vontade_picks_por_hab[item_id] = chosen
                    elif kind == "talento":
                        vontade_picks_por_talento[item_id] = chosen
                # senão: slot vazio — UI mostra picker
            else:
                # auto-aplica o default — funciona em qualquer fonte (hab/talento/traço).
                saves_extra.add(default_save)
                if kind == "hab":
                    vontade_picks_por_hab[item_id] = default_save
                elif kind == "talento":
                    vontade_picks_por_talento[item_id] = default_save

    for hab_v in habs_cls + habs_sub:
        _processa_vontade_tags(
            hab_v.get("TagsJSON"), "hab",
            hab_v["Id_Habilidade"], hab_v.get("Nome") or "",
        )
    for tal_v in talentos_full:
        if (tal_v.get("Nivel") or 1) > nivel_pers:
            continue
        _processa_vontade_tags(
            tal_v.get("TagsJSON"), "talento",
            tal_v["Id_Talento"], tal_v.get("Nome") or "",
        )
    # Traços (raça/linhagem/essência/sintético de classe) — também participam.
    for trc_v in tracos:
        _processa_vontade_tags(
            trc_v.get("TagsJSON"), "traco",
            trc_v.get("Id_Traco") or 0, trc_v.get("Nome") or "",
        )

    # Resistências/Imunidades/Vulnerabilidades de elemento (dano) e Condições (efeitos).
    # IMPORTANTE: elemento ≠ condição. "Veneno" é tipo de dano, "Envenenado" é condição.
    # Tags suportadas (somente valores canônicos D&D 5.5e BR / Bonfire Tales):
    #   resist:<Elemento> | immune:<Elemento> | vuln:<Elemento>
    #   cond-immune:<Condição> | adv-cond:<Condição>
    # Tags com valor fora das listas canônicas são IGNORADAS (logado em stderr).
    TAG_TIPO_ELEM = {"resist": "resistencia", "immune": "imunidade", "vuln": "vulnerabilidade"}
    TAG_TIPO_COND = {"cond-immune": "condicao-imune", "adv-cond": "condicao-vantagem"}
    # match case-insensitive; mapeamento volta pro canonical capitalizado
    elem_canon = {x.lower(): x for x in ELEMENTOS_CANONICOS}
    cond_canon = {x.lower(): x for x in CONDICOES_CANONICAS}
    resist_seen: dict[tuple[str, str], dict] = {}
    cond_seen: dict[tuple[str, str], dict] = {}
    for t, origem in tag_origem:
        prefix = t.split(":", 1)[0] if ":" in t else ""
        valor = t.split(":", 1)[1].strip() if ":" in t else ""
        if not valor:
            continue
        if prefix in TAG_TIPO_ELEM:
            canonical = elem_canon.get(valor.lower())
            if not canonical:
                print(f"[tag] elemento não-canônico ignorado: {t!r} (origem: {origem})")
                continue
            tipo = TAG_TIPO_ELEM[prefix]
            key = (tipo, canonical.lower())
            if key not in resist_seen:
                resist_seen[key] = {"Tipo": tipo, "DanoTipo": canonical, "Origem": origem}
        elif prefix in TAG_TIPO_COND:
            canonical = cond_canon.get(valor.lower())
            if not canonical:
                print(f"[tag] condição não-canônica ignorada: {t!r} (origem: {origem})")
                continue
            tipo = TAG_TIPO_COND[prefix]
            key = (tipo, canonical.lower())
            if key not in cond_seen:
                cond_seen[key] = {"Tipo": tipo, "Condicao": canonical, "Origem": origem}

    # Carrega pericias e aplica expertise das tags ativas
    pericias_rows = rows(
        "SELECT * FROM TB_PersonagemPericia WHERE Id_Personagem = ? ORDER BY Nome", pid,
    )
    for pe in pericias_rows:
        nome_lower = (pe.get("Nome") or "").strip().lower()
        if nome_lower in prof_pericias:
            pe["Proficiente"] = 1
        if nome_lower in expertise_pericias:
            # expertise implica proficiência (PHB 2024)
            pe["Proficiente"] = 1
            pe["Expertise"] = 1

    # Aplica escolhas de perícia (picks via traços/habs com tag pick:pericia:N)
    escolhas_pericia = rows(
        "SELECT Origem, SlotIndex, Id_Pericia, Tipo FROM TB_PersonagemEscolhaPericia "
        "WHERE Id_Personagem = ? ORDER BY Origem, SlotIndex", pid,
    )
    pericia_by_id = {pe["Id_Pericia"]: pe for pe in pericias_rows}
    for esc_p in escolhas_pericia:
        pe = pericia_by_id.get(esc_p["Id_Pericia"])
        if not pe:
            continue
        # injeta nome pra UI mostrar nos slots filled
        esc_p["NomePericia"] = pe.get("Nome")
        # marca proficiente/expertise efetivo
        if (esc_p.get("Tipo") or "proficiencia") == "expertise":
            pe["Proficiente"] = 1
            pe["Expertise"] = 1
        else:
            pe["Proficiente"] = 1

    # Escolhas de idioma/ferramenta — usa TB_PersonagemIdioma com Origem='pick:<Traço>:<slot>'
    pick_rows = rows(
        "SELECT Id, Tipo, Nome, Origem FROM TB_PersonagemIdioma "
        "WHERE Id_Personagem = ? AND Origem LIKE 'pick:%' "
        "ORDER BY Origem", pid,
    )
    escolhas_idioma: list[dict] = []
    for pr in pick_rows:
        # parse 'pick:<Traço>:<slot>'
        partes = (pr.get("Origem") or "").split(":", 2)
        if len(partes) != 3:
            continue
        try:
            slot_idx = int(partes[2])
        except ValueError:
            continue
        escolhas_idioma.append({
            "Id": pr["Id"],
            "Origem": partes[1],         # ex.: 'Poliglota'
            "SlotIndex": slot_idx,
            "Tipo": pr["Tipo"],          # 'idioma' | 'ferramenta'
            "Nome": pr["Nome"],
        })

    # Saves proficientes = classe.SavesJSON ∪ save-prof:* das habs
    classe_saves = []
    if classe and classe.get("SavesJSON"):
        try:
            classe_saves = json.loads(classe["SavesJSON"]) or []
        except (json.JSONDecodeError, TypeError):
            classe_saves = []
    saves_proficientes = sorted(set(classe_saves) | saves_extra)

    # auto-efeitos da linhagem da essência — resistência/truque/magia derivados
    # da TagsJSON da sub-linhagem (post-R4: as colunas Elemento/TruqueNome/MagiaN3Nome
    # foram dropadas; tags resist:<X>, truque-inato:<Nome>, magia-1uso:<Nome> são
    # a fonte canônica. Resistência já entra em resist_seen via _agg_tags_from acima.)
    auto_efeitos = {}
    if ess_lin:
        niv = p["Nivel"] or 1
        try:
            ess_tags = json.loads(ess_lin.get("TagsJSON") or "[]") or []
        except (json.JSONDecodeError, TypeError):
            ess_tags = []
        elemento = None
        truque = None
        magia = None
        for t in ess_tags:
            if not isinstance(t, str):
                continue
            if t.startswith("resist:"):
                elemento = t.split(":", 1)[1]
            elif t.startswith("truque-inato:"):
                truque = t.split(":", 1)[1]
            elif t.startswith("magia-1uso:"):
                magia = t.split(":", 1)[1]
        auto_efeitos = {
            "origem": f"Linhagem {ess_lin['Nome']} ({essencia['Nome'] if essencia else ''})",
            "resistencia": elemento,
            "truque":      truque,
            "magia_n3":    magia if niv >= 3 else None,
        }

    # Mescla manuais (TB_PersonagemResistencia) — usa Origem='manual' se vazio
    for r in rows("SELECT * FROM TB_PersonagemResistencia WHERE Id_Personagem = ?", pid):
        tipo = (r.get("Tipo") or "resistencia").lower()
        elem = (r.get("DanoTipo") or "").strip()
        if not elem:
            continue
        key = (tipo, elem.lower())
        if key not in resist_seen:
            resist_seen[key] = {"Tipo": tipo, "DanoTipo": elem, "Origem": "manual"}

    # Lista final ordenada (resistencia → imunidade → vulnerabilidade)
    TIPO_ORD = {"resistencia": 0, "imunidade": 1, "vulnerabilidade": 2}
    resistencias_efetivas = sorted(
        resist_seen.values(),
        key=lambda x: (TIPO_ORD.get(x["Tipo"], 9), x["DanoTipo"].lower()),
    )
    # Condições: imunes primeiro, depois vantagem em save
    COND_ORD = {"condicao-imune": 0, "condicao-vantagem": 1}
    condicoes_efetivas = sorted(
        cond_seen.values(),
        key=lambda x: (COND_ORD.get(x["Tipo"], 9), x["Condicao"].lower()),
    )

    # Movimentos (andar/voar/nadar/cavar/escalar) derivados de tags + Velocidade base.
    # Tags: andar:Xft, voar:Xft|eq, nadar:Xft|eq, cavar:Xft|eq, escalar:Xft|eq.
    # Convenção D&D 5.5: 5ft = 1.5m. Internamente trabalha em pés; m derivado.
    def _parse_velocidade_base_ft(s: str) -> int:
        """Extrai pés de um campo livre tipo '9 m / 30 ft' ou '30 ft' ou '9m'."""
        if not s:
            return 30  # default 5e
        m_ft = re.search(r"(\d+)\s*ft", s, re.I)
        if m_ft:
            return int(m_ft.group(1))
        m_m = re.search(r"(\d+(?:[.,]\d+)?)\s*m", s, re.I)
        if m_m:
            mt = float(m_m.group(1).replace(",", "."))
            return int(round(mt / 0.3))  # 1ft = 0.3m
        return 30

    def _ft_to_m(ft: int) -> float:
        return round(ft * 0.3, 1)

    andar_ft = _parse_velocidade_base_ft(p.get("Velocidade") or "")
    movimentos: dict[str, dict] = {}

    # Aplica override de andar via tag (raro)
    for t, origem in tag_origem:
        if t.startswith("andar:"):
            valor = t.split(":", 1)[1].strip()
            m_ft = re.match(r"(\d+)\s*ft$", valor, re.I)
            if m_ft:
                andar_ft = int(m_ft.group(1))
                movimentos["andar"] = {"ft": andar_ft, "m": _ft_to_m(andar_ft), "origem": origem}
                break  # primeiro override ganha

    if "andar" not in movimentos:
        movimentos["andar"] = {"ft": andar_ft, "m": _ft_to_m(andar_ft), "origem": "base"}

    # Voar/Nadar/Cavar/Escalar via tags
    for kind in ("voar", "nadar", "cavar", "escalar"):
        for t, origem in tag_origem:
            if not t.startswith(f"{kind}:"):
                continue
            valor = t.split(":", 1)[1].strip().lower()
            ft: int | None = None
            if valor == "eq":
                ft = andar_ft
            else:
                m_ft = re.match(r"(\d+)\s*ft$", valor)
                if m_ft:
                    ft = int(m_ft.group(1))
            if ft is None:
                continue
            # primeira tag desse kind ganha (descarta override silenciosa)
            if kind not in movimentos:
                movimentos[kind] = {"ft": ft, "m": _ft_to_m(ft), "origem": origem}

    # limites calculados pela tabela de progressão da classe (TB_RecursoClasse)
    # p/ X de Y exibido na ficha (ex.: Manobras Conhecidas 7/7)
    limites = {}
    if classe:
        for col_nome, chave in [
            ("Manobras Conhecidas", "manobras"),
            ("Dados de Combate", "dados_combate"),
            ("Quantidade de Dados", "qtd_dados"),
            ("Magias Preparadas", "magias_preparadas"),
            ("Truques", "truques"),
        ]:
            r = one(
                "SELECT Valor FROM TB_RecursoClasse WHERE Id_Classe=? AND Nome=? AND Nivel<=? ORDER BY Nivel DESC LIMIT 1",
                classe["Id_Classe"], col_nome, niv,
            )
            if r and r["Valor"] and r["Valor"] not in ("-", "—"):
                limites[chave] = r["Valor"]

    # ---- maestrias_armas_slots: progressão de Maestria de Armas (MULTICLASSE)
    # Soma slots de todas as classes ativas + slots vindos de habs (ex.: Doutrina
    # Marcial "Armas Treinadas" do Paladino dá +3).
    # Variantes de nome: "Maestrias de Armas", "Maestria com Armas", "Maestria em Armas".
    maestrias_armas_slots: list[dict] = []
    total_slots = 0
    slot_origens: list[tuple[int, str]] = []  # [(slot_idx, origem_label)]
    for c_pc in classes_pc:
        cls_id = c_pc["Id_Classe"]
        cls_nivel = c_pc["Nivel"] or 0
        cls_nome = c_pc["NomeClasse"] or "?"
        prog_ma = rows(
            "SELECT Nivel, Valor FROM TB_RecursoClasse "
            "WHERE Id_Classe=? AND Nome LIKE '%aestria%Arma%' AND Nivel<=? "
            "ORDER BY Nivel",
            cls_id, cls_nivel,
        )
        # Pega o MAIOR valor entre os níveis ≤ cls_nivel
        max_da_classe = 0
        for row in prog_ma:
            try:
                v = int(row["Valor"])
                if v > max_da_classe:
                    max_da_classe = v
            except (TypeError, ValueError):
                continue
        for _ in range(max_da_classe):
            total_slots += 1
            slot_origens.append((total_slots, cls_nome))
    # Tag acumuladora `+maestrias-arma:N` — qualquer fonte adiciona N slots.
    # Hoje vem da opção "Armas Treinadas" da Doutrina Marcial via tag-em-opção.
    # Universal: outra raça/talento que conceder maestrias adicionais soma aqui.
    bonus_maestrias = bonus_acumulados.get("maestrias-arma", 0)
    if bonus_maestrias > 0:
        # Origem: usa a primeira fonte se houver, senão "bonus".
        fontes_ma = bonus_fontes.get("maestrias-arma", [])
        origem_label = fontes_ma[0]["nome"] if fontes_ma else "bonus"
        for _ in range(bonus_maestrias):
            total_slots += 1
            slot_origens.append((total_slots, origem_label))
    for slot_idx, origem in slot_origens:
        maestrias_armas_slots.append({
            "slot": slot_idx,
            "min_level": 1,  # já validado pelo nivel da classe na coleta
            "origem": origem,
        })

    # ---- maestrias_armas: escolhas atuais do personagem (com JOIN)
    maestrias_armas = rows(
        "SELECT pma.Id, pma.SlotIndex, pma.Id_Arma, pma.Id_Maestria, "
        "       a.Nome AS ArmaNome, a.Categoria AS ArmaCategoria, a.Dano AS ArmaDano, "
        "       a.Propriedades AS ArmaPropriedades, a.MaestriasJSON AS ArmaMaestriasJSON, "
        "       m.Nome AS MaestriaNome, m.NomeIngles AS MaestriaIngles, m.Efeito AS MaestriaEfeito "
        "  FROM TB_PersonagemMaestriaArma pma "
        "  LEFT JOIN TB_Arma a ON a.Id_Arma = pma.Id_Arma "
        "  LEFT JOIN TB_Maestria m ON m.Id_Maestria = pma.Id_Maestria "
        " WHERE pma.Id_Personagem = ? "
        " ORDER BY pma.SlotIndex, pma.Id",
        pid,
    )
    # Anexa origem do slot (da progressão) e flag is_arma_kensei.
    # SlotIndex no DB é 0-based; slot_origens é 1-based.
    origem_by_slot1 = {sl["slot"]: sl["origem"] for sl in maestrias_armas_slots}
    for ma in maestrias_armas:
        slot1 = (ma.get("SlotIndex") or 0) + 1
        ma["Origem"] = origem_by_slot1.get(slot1)
        ma["is_arma_kensei"] = (ma["Origem"] == "Bushidō")

    # ---- manobras_slots: lista de slots com min_level computado da progressao
    # Permite ao frontend renderizar slots locked/unlocked por nivel + planejamento.
    manobras_slots: list[dict] = []
    if classe:
        prog = rows(
            "SELECT Nivel, Valor FROM TB_RecursoClasse "
            " WHERE Id_Classe=? AND Nome=? ORDER BY Nivel",
            classe["Id_Classe"], "Manobras Conhecidas",
        )
        max_limit = 0
        # para cada level da progressao, fixar min_level dos slots ate Valor
        slot_min_level: dict[int, int] = {}
        for row in prog:
            try:
                v = int(row["Valor"])
            except (TypeError, ValueError):
                continue
            for slot_idx in range(1, v + 1):
                if slot_idx not in slot_min_level:
                    slot_min_level[slot_idx] = row["Nivel"]
            if v > max_limit:
                max_limit = v
        for slot_idx in range(1, max_limit + 1):
            ml = slot_min_level.get(slot_idx)
            # grau_max naquele min_level (mesma logica de /manobras-disponiveis)
            if ml is None:
                grau_at = 0
            elif ml >= 15:
                grau_at = 4
            elif ml >= 11:
                grau_at = 3
            elif ml >= 5:
                grau_at = 2
            else:
                grau_at = 1
            manobras_slots.append({
                "slot": slot_idx,
                "min_level": ml,
                "grau_max_at": grau_at,
            })

    # Aplica tag acumuladora "+manobras:N" — slots adicionais ao final, todos
    # disponíveis no nivel atual (min_level=1) e com grau_max do char.
    bonus_manobras = bonus_acumulados.get("manobras", 0)
    if bonus_manobras > 0:
        # grau_at do último slot existente, fallback pelo nivel do personagem.
        if manobras_slots:
            grau_atual = manobras_slots[-1]["grau_max_at"]
        else:
            n = nivel_pers
            grau_atual = 4 if n >= 15 else 3 if n >= 11 else 2 if n >= 5 else 1
        for i in range(bonus_manobras):
            manobras_slots.append({
                "slot": len(manobras_slots) + 1,
                "min_level": 1,
                "grau_max_at": grau_atual,
                "from_bonus": True,
            })

    # ---- Caçador: shared lookup pra segredos + inimigo favorito.
    cacador_pc = None
    for c_pc in classes_pc:
        if (c_pc.get("SlugClasse") or "").lower() == "cacador" or \
           (c_pc.get("NomeClasse") or "").lower().startswith("caça"):
            cacador_pc = c_pc
            break
    cls_cac_id = cacador_pc["Id_Classe"] if cacador_pc else None
    cls_cac_nivel = (cacador_pc["Nivel"] or 0) if cacador_pc else 0

    # ---- segredos: paralelo ao manobras_slots, gated pela tag flat "segredos".
    has_segredos_tag = any(t == "segredos" for (t, _) in tag_origem)
    segredos_slots: list[dict] = []
    pontos_segredo_max = 0
    dado_cacador = None
    segredos_escolhas: list[dict] = []
    if has_segredos_tag:
        if cls_cac_id and cls_cac_nivel:
            # Slots por nível da classe Caçador (mesma lógica de manobras).
            prog_seg = rows(
                "SELECT Nivel, Valor FROM TB_RecursoClasse "
                " WHERE Id_Classe=? AND Nome=? ORDER BY Nivel",
                cls_cac_id, "Segredos",
            )
            slot_min: dict[int, int] = {}
            max_seg = 0
            for row in prog_seg:
                try:
                    v = int(row["Valor"])
                except (TypeError, ValueError):
                    continue
                if row["Nivel"] > cls_cac_nivel:
                    break
                for s_idx in range(1, v + 1):
                    if s_idx not in slot_min:
                        slot_min[s_idx] = row["Nivel"]
                if v > max_seg:
                    max_seg = v
            for s_idx in range(1, max_seg + 1):
                segredos_slots.append({
                    "slot": s_idx,
                    "min_level": slot_min.get(s_idx),
                })
            # +segredos:N tag acumuladora — extras de outras fontes.
            bonus_seg = bonus_acumulados.get("segredos", 0)
            for _ in range(bonus_seg):
                segredos_slots.append({
                    "slot": len(segredos_slots) + 1,
                    "min_level": 1,
                    "from_bonus": True,
                })
            # Pontos de Segredo + Dado: extrai de "Dados de Caçador" (formato "N (1dM)").
            r_dc = one(
                "SELECT Valor FROM TB_RecursoClasse "
                " WHERE Id_Classe=? AND Nome=? AND Nivel<=? ORDER BY Nivel DESC LIMIT 1",
                cls_cac_id, "Dados de Caçador", cls_cac_nivel,
            )
            if r_dc and r_dc["Valor"]:
                m_dc = re.match(r"\s*(\d+)\s*\((1d\d+)\)", r_dc["Valor"])
                if m_dc:
                    pontos_segredo_max = int(m_dc.group(1))
                    dado_cacador = m_dc.group(2)
            # Escolhas atuais com JOIN TB_Segredo
            segredos_escolhas = rows(
                "SELECT ps.Id, ps.Id_Segredo, ps.Id_Habilidade, "
                "       s.Nome, s.Slug, s.Linha, s.Custo, s.Acao, s.Flavor, s.Descricao "
                "  FROM TB_PersonagemSegredo ps "
                "  JOIN TB_Segredo s ON s.Id_Segredo = ps.Id_Segredo "
                " WHERE ps.Id_Personagem=? ORDER BY s.Linha, s.Nome",
                pid,
            )
            # limites.segredos = total de slots (base TB_Recurso + bonus)
            limites["segredos"] = str(len(segredos_slots))

    # ---- inimigos favoritos: idêntico padrão de segredos. Limite vem de
    # TB_RecursoClasse "Inimigo Favorito" (1/2/3 escala 2/6/14).
    has_inim_tag = any(t == "inimigo-favorito" for (t, _) in tag_origem)
    inimigos_favoritos_slots: list[dict] = []
    inimigos_favoritos_escolhas: list[dict] = []
    if has_inim_tag and cls_cac_id and cls_cac_nivel:
        prog_inim = rows(
            "SELECT Nivel, Valor FROM TB_RecursoClasse "
            " WHERE Id_Classe=? AND Nome=? ORDER BY Nivel",
            cls_cac_id, "Inimigo Favorito",
        )
        slot_min: dict[int, int] = {}
        max_inim = 0
        for row in prog_inim:
            try:
                v = int(row["Valor"])
            except (TypeError, ValueError):
                continue
            if row["Nivel"] > cls_cac_nivel:
                break
            for s_idx in range(1, v + 1):
                if s_idx not in slot_min:
                    slot_min[s_idx] = row["Nivel"]
            if v > max_inim:
                max_inim = v
        for s_idx in range(1, max_inim + 1):
            inimigos_favoritos_slots.append({
                "slot": s_idx,
                "min_level": slot_min.get(s_idx),
            })
        # Escolhas atuais com JOIN
        inimigos_favoritos_escolhas = rows(
            "SELECT pif.Id, pif.Id_InimigoFavorito, pif.Id_Habilidade, "
            "       i.Nome, i.Slug "
            "  FROM TB_PersonagemInimigoFavorito pif "
            "  JOIN TB_InimigoFavorito i ON i.Id_InimigoFavorito = pif.Id_InimigoFavorito "
            " WHERE pif.Id_Personagem=? ORDER BY i.Nome",
            pid,
        )
        limites["inimigos_favoritos"] = str(len(inimigos_favoritos_slots))

    # ---- evolução totêmica: gated pela tag flat "evolucao-totemica" (sub Aliança Selvagem).
    # Limite vem de TB_RecursoClasse Id_Subclasse=21 (Aliança) Nome="Evolução Totêmica".
    # Slots Nv 3+: Menor; Nv 6+: Menor OU Maior.
    has_evol_tag = any(t == "evolucao-totemica" for (t, _) in tag_origem)
    evolucoes_totemicas_slots: list[dict] = []
    evolucoes_totemicas_escolhas: list[dict] = []
    if has_evol_tag and cls_cac_id and cls_cac_nivel:
        prog_evol = rows(
            "SELECT Nivel, Valor FROM TB_RecursoClasse "
            " WHERE Id_Classe=? AND Nome=? ORDER BY Nivel",
            cls_cac_id, "Evolução Totêmica",
        )
        slot_min: dict[int, int] = {}
        max_evol = 0
        for row in prog_evol:
            try:
                v = int(row["Valor"])
            except (TypeError, ValueError):
                continue
            if row["Nivel"] > cls_cac_nivel:
                break
            for s_idx in range(1, v + 1):
                if s_idx not in slot_min:
                    slot_min[s_idx] = row["Nivel"]
            if v > max_evol:
                max_evol = v
        for s_idx in range(1, max_evol + 1):
            ml = slot_min.get(s_idx)
            # Slot 1 (Nv 3): só Menor. Slots 2+ (Nv 6+): Menor ou Maior.
            tier_max = "menor" if (ml is None or ml < 6) else "maior"
            evolucoes_totemicas_slots.append({
                "slot": s_idx,
                "min_level": ml,
                "tier_max": tier_max,
            })
        evolucoes_totemicas_escolhas = rows(
            "SELECT pe.Id, pe.Id_Evolucao, pe.SlotIndex, pe.Variante, pe.Id_Habilidade, "
            "       e.Nome, e.Slug, e.Tier, e.Descricao "
            "  FROM TB_PersonagemEvolucaoTotemica pe "
            "  JOIN TB_EvolucaoTotemica e ON e.Id_Evolucao = pe.Id_Evolucao "
            " WHERE pe.Id_Personagem=? ORDER BY pe.SlotIndex",
            pid,
        )
        limites["evolucoes_totemicas"] = str(len(evolucoes_totemicas_slots))

    # ---- estilos de ki (Monge): gated pela tag flat "estilos-ki".
    # Limite vem de TB_RecursoClasse "Estilos de Ki" pela classe Monge (Id_Subclasse NULL).
    has_ki_tag = any(t == "estilos-ki" for (t, _) in tag_origem)
    estilos_ki_slots: list[dict] = []
    estilos_ki_escolhas: list[dict] = []
    if has_ki_tag:
        # Pega nível da classe Monge (multiclasse-aware)
        monge_pc = None
        for c_pc in classes_pc:
            if (c_pc.get("SlugClasse") or "").lower() == "monge" or \
               (c_pc.get("NomeClasse") or "").lower() == "monge":
                monge_pc = c_pc
                break
        if monge_pc and (monge_pc["Nivel"] or 0):
            cls_id = monge_pc["Id_Classe"]; cls_nv = monge_pc["Nivel"]
            prog = rows(
                "SELECT Nivel, Valor FROM TB_RecursoClasse "
                " WHERE Id_Classe=? AND (Id_Subclasse IS NULL) AND Nome=? ORDER BY Nivel",
                cls_id, "Estilos de Ki",
            )
            slot_min: dict[int, int] = {}
            max_n = 0
            for row in prog:
                try: v = int(row["Valor"])
                except (TypeError, ValueError): continue
                if row["Nivel"] > cls_nv: break
                for s_idx in range(1, v + 1):
                    if s_idx not in slot_min: slot_min[s_idx] = row["Nivel"]
                if v > max_n: max_n = v
            for s_idx in range(1, max_n + 1):
                estilos_ki_slots.append({"slot": s_idx, "min_level": slot_min.get(s_idx)})
            estilos_ki_escolhas = rows(
                "SELECT pe.Id, pe.Id_Estilo, pe.SlotIndex, pe.Id_Habilidade, "
                "       e.Nome, e.Slug, e.CustoKi, e.Descricao "
                "  FROM TB_PersonagemEstiloKi pe "
                "  JOIN TB_EstiloKi e ON e.Id_Estilo = pe.Id_Estilo "
                " WHERE pe.Id_Personagem=? ORDER BY pe.SlotIndex",
                pid,
            )
            limites["estilos_ki"] = str(len(estilos_ki_slots))

    # ---- segredos místicos (Místico): gated pela tag flat 'segredos-misticos'.
    # Limite de slots vem de TB_RecursoClasse 'Segredos Conhecidos' do Místico.
    has_segm_tag = any(t == "segredos-misticos" for (t, _) in tag_origem)
    segredos_misticos_slots: list[dict] = []
    segredos_misticos_escolhas: list[dict] = []
    if has_segm_tag:
        # Nivel do Místico
        cls_m_id = None; cls_m_nv = 0
        for c_pc in classes_pc:
            if (c_pc.get("SlugClasse") or "").lower() == "mistico":
                cls_m_id = c_pc["Id_Classe"]; cls_m_nv = c_pc["Nivel"] or 0
                break
        if cls_m_id and cls_m_nv:
            prog = rows(
                "SELECT Nivel, Valor FROM TB_RecursoClasse "
                " WHERE Id_Classe=? AND Nome LIKE '%egredo%' AND Nivel<=? ORDER BY Nivel",
                cls_m_id, cls_m_nv,
            )
            slot_min: dict[int, int] = {}
            max_n = 0
            for row in prog:
                try: v = int(row["Valor"])
                except (TypeError, ValueError): continue
                for s_idx in range(1, v + 1):
                    if s_idx not in slot_min: slot_min[s_idx] = row["Nivel"]
                if v > max_n: max_n = v
            for s_idx in range(1, max_n + 1):
                segredos_misticos_slots.append({"slot": s_idx, "min_level": slot_min.get(s_idx)})
            segredos_misticos_escolhas = rows(
                "SELECT psm.Id, psm.Id_Segredo, psm.SlotIndex, "
                "       sm.Nome, sm.Slug, sm.Secao, sm.NivelMin, sm.GateTag, "
                "       sm.Repetivel, sm.TagsJSON, sm.Descricao "
                "  FROM TB_PersonagemSegredoMistico psm "
                "  JOIN TB_SegredoMistico sm ON sm.Id_Segredo = psm.Id_Segredo "
                " WHERE psm.Id_Personagem=? ORDER BY psm.SlotIndex",
                pid,
            )
            # Hidrata cada instância com o Talento de Origem associado (se houver).
            # Permite N talentos extras quando o segredo é Repetível.
            for seg in segredos_misticos_escolhas:
                t = one(
                    "SELECT op.Id_Opcao, op.Nome, op.Slug, op.Descricao, op.TagsJSON "
                    "  FROM TB_PersonagemSegredoMisticoTalento smt "
                    "  JOIN TB_OpcaoJogo op ON op.Id_Opcao = smt.Id_TalentoOrigem "
                    " WHERE smt.Id_PersonagemSegredoMistico=?",
                    seg["Id"],
                )
                seg["talento_origem"] = dict(t) if t else None
            limites["segredos_misticos"] = str(len(segredos_misticos_slots))
            # Agrega TagsJSON dos segredos místicos + dos talentos escolhidos via segredo
            # no pool universal (pick:talento-origem:1 do segredo + tags do talento em si).
            _agg_tags_from(segredos_misticos_escolhas)
            _agg_tags_from(
                [seg["talento_origem"] for seg in segredos_misticos_escolhas if seg.get("talento_origem")]
            )

    # Espírito Primordial — variante ativa (Terra/Céu/Mar) via tag de opção escolhida.
    # Tag esperada: alianca-selvagem-companheiro-<slug>. PV escala com nível de Caçador
    # (PV_Base no Nv 3 + PV_PorNivel × níveis adicionais).
    espirito_primordial = None
    if has_evol_tag and cls_cac_id and cls_cac_nivel:
        var_slug = None
        for t, _o in tag_origem:
            if t.startswith("alianca-selvagem-companheiro-"):
                var_slug = t.split("alianca-selvagem-companheiro-", 1)[1]
                break
        if var_slug:
            v = one("SELECT * FROM TB_EspiritoPrimordialVariante WHERE Slug=?", var_slug)
            if v:
                niveis_extras = max(0, cls_cac_nivel - 3)
                pv_max = v["PV_Base"] + v["PV_PorNivel"] * niveis_extras
                espirito_primordial = {
                    **v,
                    "PV_Max": pv_max,
                    "Nivel_Cacador": cls_cac_nivel,
                }

    return jsonify({
        "personagem":  p,
        "raca":        raca,
        "linhagem":    linhagem,
        "essencia":    essencia,
        "ess_linhagem": ess_lin,
        "aggregated_tags": (
            [{"tag": t, "origem": o} for (t, o) in tag_origem] +
            [{"tag": t, "origem": o, "locked": True, "min_nivel": mn}
             for (t, o, mn) in tag_locked]
        ),
        "bonus_acumulados": bonus_acumulados,
        "bonus_fontes": bonus_fontes,
        "tags_de_opcoes_por_origem": tags_de_opcoes_por_origem,
        "profs_armadura_extras": profs_armadura_extras,
        "profs_arma_extras": profs_arma_extras,
        "profs_ferramenta_extras": profs_ferramenta_extras,
        "profs_idioma_extras": profs_idioma_extras,
        "auto_efeitos": auto_efeitos,
        "classe":      classe,
        "classes":     classes_pc,
        "nivel_total": nivel_total,
        "caster_level": _calc_caster_level(classes_pc),
        "spell_slots": _spell_slots_dict(_calc_caster_level(classes_pc)),
        # Místico isolado — Feitiçaria Mística usa Pontos de Misticismo (Bonfire),
        # NÃO slots fixos. Multiclasse: não soma com outras casters; outras não somam aqui.
        "mistico_level": _calc_mistico_level(classes_pc),
        "feiticaria_mistica": _calc_feiticaria_mistica(classes_pc),
        "subclasse":   sub,
        "limites":     limites,
        "manobras_slots": manobras_slots,
        # Catalogo pool aberto de Técnicas de Furtividade (Ladino). Frontend mostra
        # essa lista quando aggregated_tags contém a tag flat 'tecnica-furtividade'.
        # NivelMinimo = custo em d6 (1, 2, 3, 4, 6) pra ordenação/agrupamento.
        "tecnicas_furtividade_catalogo": rows(
            "SELECT Id_Opcao, Nome, Slug, Descricao, NivelMinimo, PreReqTexto "
            "FROM TB_OpcaoJogo WHERE Tipo='tecnica-furtividade' "
            "ORDER BY NivelMinimo, Nome"
        ),
        # Catálogo de Metamagias (Feiticeiro). Frontend mostra picker quando há
        # tag pick:metamagia:N. NivelMinimo = custo em PF (1 ou 2).
        "metamagias_catalogo": rows(
            "SELECT Id_Opcao, Nome, Slug, Descricao, NivelMinimo, PreReqTexto "
            "FROM TB_OpcaoJogo WHERE Tipo='metamagia' "
            "ORDER BY NivelMinimo, Nome"
        ),
        # Catálogo de Estilos de Dança (Bardo da Dança). Frontend mostra picker
        # quando há tag pick:estilo-danca:N. Reusa TB_EstiloKi.Catalogo='ki'
        # (mesmo pool de 18 estilos do Monge); a regra de custo CK
        # "1 ponto de Ki" passa a ler como "1 uso de Inspiração Bárdica"
        # quando picked via Bardo da Dança.
        "estilos_danca_catalogo": rows(
            "SELECT Id_Estilo AS Id_Opcao, Nome, Slug, Descricao, "
            "       CustoKi AS NivelMinimo "
            "FROM TB_EstiloKi WHERE Catalogo='ki' ORDER BY CustoKi, Nome"
        ),
        # Catálogo de Infusões de Artificer. Frontend mostra picker quando há
        # tag pick:infusao-artificer:N. NivelMinimo = nível de restrição
        # (1 = sem restrição; o picker filtra NivelMinimo <= nível do Artífice).
        # Cada slot pode receber uma infusão OU um item replicado (Replicar Item
        # Mágico — escolhido da página de equipamentos, tratado como infusão).
        "infusoes_artificer_catalogo": rows(
            "SELECT Id_Opcao, Nome, Slug, Descricao, NivelMinimo, PreReqTexto "
            "FROM TB_OpcaoJogo WHERE Tipo='infusao-artificer' "
            "ORDER BY NivelMinimo, Nome"
        ),
        # Itens Infundidos — máximo de itens ativos (display). Progressão própria
        # do Artífice: Nv 2=2, 6=3, 10=4, 14=5, 18=6.
        "itens_infundidos_max": (lambda nv: (
            6 if nv >= 18 else 5 if nv >= 14 else 4 if nv >= 10
            else 3 if nv >= 6 else 2 if nv >= 2 else 0
        ))(next((c["Nivel"] for c in classes_pc
                 if (c.get("SlugClasse") or "").lower() == "artifice"), 0)),
        # Pontos de Feitiçaria — máximo = nível da classe Feiticeiro (canônico Bonfire).
        # Tag 'pontos-feiticaria' ativa a seção. PF_max = nível do Feiticeiro do char.
        "pontos_feiticaria_max": next(
            (c["Nivel"] for c in classes_pc
             if (c.get("SlugClasse") or "").lower() == "feiticeiro"),
            0,
        ),
        # Surto Selvagem ND Máximo (Druida). Tag 'surto-selvagem' ativa a seção.
        # Druida padrão: Nv2=1/4, Nv4=1/2, Nv8=1 (até Nv20).
        # Druida da Lua (tag 'druida-lua'): ND máximo = ⌈nivel_druida / 3⌉.
        # Frontend lê: surto_selvagem.{nivel, cr_max, eh_lua, formas_conhecidas, voo}.
        "surto_selvagem": _calc_surto_selvagem(
            classes_pc,
            {t for (t, _o) in tag_origem} | {t for (t, _o, _mn) in tag_locked},
        ),
        "atributos_efetivos": _atributos_efetivos(p, _build_talentos(pid)),
        "maestrias_armas_slots": maestrias_armas_slots,
        "maestrias_armas": maestrias_armas,
        "talento_origem": talento_origem,
        "talento_origem_extra": talento_origem_extra,
        "talento_origem_racial": talento_origem_racial,
        "pv_bonus_origem": {"total": pv_bonus_origem_total, "fontes": pv_bonus_origem_fontes},
        "magia_expandida": magia_expandida,
        "magias_subclasse": magias_subclasse,
        "tracos":      tracos,
        "recursos_classe": rec_prog,
        "habilidades_classe": habs_cls,
        "habilidades_subclasse": habs_sub,
        "pericias":    pericias_rows,
        "escolhas_pericia": escolhas_pericia,
        "escolhas_idioma":  escolhas_idioma,
        "escolhas_tag":     rows(
            "SELECT Origem, Tipo, SlotIndex, Valor FROM TB_PersonagemEscolhaTag "
            "WHERE Id_Personagem=? ORDER BY Origem, Tipo, SlotIndex", pid,
        ),
        "saves_proficientes": saves_proficientes,
        "classe_saves": sorted(classe_saves_set),
        "talentos":    _build_talentos(pid),
        "idiomas":     rows("SELECT * FROM TB_PersonagemIdioma WHERE Id_Personagem = ? ORDER BY Tipo, Nome", pid),
        "resistencias": resistencias_efetivas,
        "condicoes":    condicoes_efetivas,
        "movimentos":   movimentos,
        "personalidade": rows("SELECT * FROM TB_PersonagemPersonalidade WHERE Id_Personagem = ?", pid),
        "inventario":  rows("SELECT * FROM TB_PersonagemInventarioItem WHERE Id_Personagem = ? ORDER BY Id", pid),
        "magias":      rows("SELECT * FROM TB_PersonagemMagia WHERE Id_Personagem = ? ORDER BY Nivel, Nome", pid),
        "tecnicas":    rows(
            "SELECT t.*, m.Grau AS Grau, m.TagsJSON AS TagsJSON "
            "  FROM TB_PersonagemTecnica t "
            "  LEFT JOIN TB_Manobra m ON m.Id_Manobra = t.Id_Manobra "
            " WHERE t.Id_Personagem = ? ORDER BY t.Nome",
            pid,
        ),
        "segredos":           segredos_escolhas,
        "segredos_slots":     segredos_slots,
        "pontos_segredo_max": pontos_segredo_max,
        "dado_cacador":       dado_cacador,
        "inimigos_favoritos":       inimigos_favoritos_escolhas,
        "inimigos_favoritos_slots": inimigos_favoritos_slots,
        "evolucoes_totemicas":       evolucoes_totemicas_escolhas,
        "evolucoes_totemicas_slots": evolucoes_totemicas_slots,
        "espirito_primordial":       espirito_primordial,
        "estilos_ki":                estilos_ki_escolhas,
        "estilos_ki_slots":          estilos_ki_slots,
        "segredos_misticos":         segredos_misticos_escolhas,
        "segredos_misticos_slots":   segredos_misticos_slots,
        "ca_efetiva":                _calc_ca_efetiva(p, classes_pc, profs_armadura_extras, talentos_full, tag_origem),
    })


@app.get("/ficha/<int:pid>")
def ficha_page(pid: int):
    return send_from_directory("templates", "ficha.html")


@app.get("/api/personagens/<int:pid>/ficha")
def ficha_compilada(pid: int):
    """Retorna a FICHA COMPILADA do personagem: todas as regras já resolvidas
       com base nas escolhas + nível. Útil pro frontend de criação automática."""
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    esc = p["escolha"] or {}
    nivel = p["Nivel"] or 1

    raca = one("SELECT * FROM TB_Raca WHERE Id_Raca = ?", esc.get("Id_Raca")) if esc.get("Id_Raca") else None
    linhagem = one("SELECT * FROM TB_Linhagem WHERE Id_Linhagem = ?", esc.get("Id_Linhagem")) if esc.get("Id_Linhagem") else None
    essencia = one("SELECT * FROM TB_Essencia WHERE Id_Essencia = ?", esc.get("Id_Essencia")) if esc.get("Id_Essencia") else None
    classe   = one("SELECT * FROM TB_Classe   WHERE Id_Classe   = ?", esc.get("Id_Classe"))   if esc.get("Id_Classe")   else None
    sub      = one("SELECT * FROM TB_Subclasse WHERE Id_Subclasse = ?", esc.get("Id_Subclasse")) if esc.get("Id_Subclasse") else None

    # traços raciais da raça escolhida (filtra por nível)
    tracos = []
    if raca:
        tracos = rows(
            """SELECT * FROM TB_TracoRacial
                WHERE Id_Raca = ? AND NivelRequisito <= ?
                ORDER BY NivelRequisito, Nome""",
            raca["Id_Raca"], nivel,
        )

    # recursos de classe adquiridos até o nível atual
    recursos_classe = []
    if classe:
        recursos_classe = rows(
            """SELECT * FROM TB_RecursoClasse
                WHERE Id_Classe = ? AND Nivel <= ?
                  AND (Id_Subclasse IS NULL OR Id_Subclasse = ?)
                ORDER BY Nivel, Nome""",
            classe["Id_Classe"], nivel, esc.get("Id_Subclasse") or -1,
        )

    # habilidades de classe adquiridas até o nível atual (principais)
    habilidades_principais = []
    if classe:
        habilidades_principais = rows(
            """SELECT * FROM TB_ClasseHabilidade
                WHERE Id_Classe = ? AND Id_Subclasse IS NULL AND NivelAdquirido <= ?
                ORDER BY NivelAdquirido, Nome""",
            classe["Id_Classe"], nivel,
        )

    # habilidades da subclasse adquiridas até o nível atual
    habilidades_subclasse = []
    if sub:
        habilidades_subclasse = rows(
            """SELECT * FROM TB_ClasseHabilidade
                WHERE Id_Subclasse = ? AND NivelAdquirido <= ?
                ORDER BY NivelAdquirido, Nome""",
            sub["Id_Subclasse"], nivel,
        )

    return jsonify({
        "personagem": {
            "id": p["Id_Personagem"],
            "nome": p["Nome"],
            "nivel": nivel,
            "pv_atual": p.get("PVAtual"),
            "pv_maximo": p.get("PVMaximo"),
        },
        "atributos": p["atributos"],
        "escolhas": {
            "raca": raca,
            "linhagem": linhagem,
            "essencia": essencia,
            "classe": classe,
            "subclasse": sub,
        },
        "tracos_raciais": tracos,
        "recursos_classe_ate_nivel": recursos_classe,
        "habilidades_classe_principais": habilidades_principais,
        "habilidades_subclasse": habilidades_subclasse,
    })


@app.get("/api/personagens")
def list_personagens():
    return jsonify(rows(
        """SELECT p.Id_Personagem, p.Nome, p.Nivel,
                  c.Nome AS ClasseNome, s.Nome AS SubclasseNome,
                  r.Nome AS RacaNome
             FROM TB_Personagem p
        LEFT JOIN TB_PersonagemEscolha e ON e.Id_Personagem = p.Id_Personagem
        LEFT JOIN TB_Classe    c ON c.Id_Classe    = e.Id_Classe
        LEFT JOIN TB_Subclasse s ON s.Id_Subclasse = e.Id_Subclasse
        LEFT JOIN TB_Raca      r ON r.Id_Raca      = e.Id_Raca
            ORDER BY p.Nome"""
    ))


# ---------------------------------------------------------------------------
# API: equipamento do personagem (persistência opcional)
# ---------------------------------------------------------------------------
@app.get("/api/equipamento/<character_id>")
def get_equip(character_id: str):
    r = one("SELECT Payload FROM TB_EquipamentoPersonagem WHERE CharacterId = ?", character_id)
    if not r:
        return jsonify({"characterId": character_id, "data": None})
    return jsonify({"characterId": character_id, "data": json.loads(r["Payload"])})


@app.put("/api/equipamento/<character_id>")
def put_equip(character_id: str):
    payload = json.dumps(request.get_json(force=True), ensure_ascii=False)
    conn = db()
    conn.execute(
        """INSERT INTO TB_EquipamentoPersonagem (CharacterId, Payload)
               VALUES (?, ?)
             ON CONFLICT(CharacterId) DO UPDATE SET
                   Payload = excluded.Payload,
                   UpdatedAt = CURRENT_TIMESTAMP""",
        (character_id, payload),
    )
    conn.commit()
    return jsonify({"ok": True, "characterId": character_id})


# ===========================================================================
# DEBUG TAGS — páginas para edição manual de TagsJSON em todas as fontes
# (regra-tags-universais.md). Só ativas com app.debug=True.
# ===========================================================================
DEBUG_ENTIDADES = ("classes", "talentos", "racas", "essencias", "items")

# Whitelist de tabelas que aceitam PUT em TagsJSON (evita SQL-injection via path).
DEBUG_TAGS_TABELAS: dict[str, str] = {
    "TB_Raca":             "Id_Raca",
    "TB_Linhagem":         "Id_Linhagem",
    "TB_Classe":           "Id_Classe",
    "TB_Subclasse":        "Id_Subclasse",
    "TB_ClasseHabilidade": "Id_Habilidade",
    "TB_Essencia":         "Id_Essencia",
    "TB_EssenciaLinhagem": "Id_EssLinhagem",
    "TB_TracoRacial":      "Id_Traco",
    "TB_TalentoRacial":    "Id_TalentoRacial",
    "TB_OpcaoJogo":        "Id_Opcao",
    "TB_Item":             "Id_Item",
}


def _debug_guard():
    if not app.debug:
        return jsonify({"error": "debug routes only in debug mode"}), 403
    return None


def _validar_tags_canonicas(tags_json: str) -> list[str]:
    """Retorna lista de warnings (não bloqueia o save). Validação canônica
    contra ELEMENTOS_CANONICOS e CONDICOES_CANONICAS."""
    warns: list[str] = []
    try:
        tags = json.loads(tags_json) or []
    except (json.JSONDecodeError, TypeError):
        return ["JSON inválido"]
    for t in tags:
        s = t["tag"] if isinstance(t, dict) else t if isinstance(t, str) else None
        if not s:
            continue
        body = s.split("=", 1)[0]
        if body.startswith(("resist:", "immune:", "vuln:")):
            valor = body.split(":", 1)[1] if ":" in body else ""
            if valor not in ELEMENTOS_CANONICOS:
                warns.append(f"'{valor}' não é elemento canônico")
        elif body.startswith(("cond-immune:", "adv-cond:")):
            valor = body.split(":", 1)[1] if ":" in body else ""
            if valor not in CONDICOES_CANONICAS:
                warns.append(f"'{valor}' não é condição canônica")
    return warns


@app.get("/debug")
def debug_hub():
    err = _debug_guard()
    if err: return err
    return redirect("/debug/classes")


@app.get("/debug/<entidade>")
def debug_page(entidade: str):
    err = _debug_guard()
    if err: return err
    if entidade not in DEBUG_ENTIDADES:
        return jsonify({"error": f"entidade desconhecida: {entidade}"}), 404
    return send_from_directory("templates", "debug.html")


@app.put("/api/debug/tags/<tabela>/<int:id_>")
def debug_set_tags(tabela: str, id_: int):
    err = _debug_guard()
    if err: return err
    if tabela not in DEBUG_TAGS_TABELAS:
        return jsonify({"error": f"tabela {tabela} não permitida"}), 400
    pk = DEBUG_TAGS_TABELAS[tabela]
    payload = request.get_json(silent=True) or {}
    tags_raw = payload.get("tags")
    if tags_raw is None or tags_raw == "":
        new_value: str | None = None
    elif isinstance(tags_raw, str):
        try:
            parsed = json.loads(tags_raw)
        except json.JSONDecodeError as e:
            return jsonify({"error": f"JSON inválido: {e}"}), 400
        if not isinstance(parsed, list):
            return jsonify({"error": "TagsJSON deve ser array"}), 400
        new_value = json.dumps(parsed, ensure_ascii=False)
    elif isinstance(tags_raw, list):
        new_value = json.dumps(tags_raw, ensure_ascii=False)
    else:
        return jsonify({"error": "tags deve ser string JSON ou array"}), 400
    warnings = _validar_tags_canonicas(new_value or "[]")
    db().execute(f"UPDATE {tabela} SET TagsJSON = ? WHERE {pk} = ?", (new_value, id_))
    db().commit()
    return jsonify({"ok": True, "warnings": warnings, "saved": new_value})


@app.get("/api/debug/<entidade>")
def debug_listar(entidade: str):
    err = _debug_guard()
    if err: return err
    if entidade == "classes":
        classes = rows("SELECT Id_Classe, Nome, TagsJSON FROM TB_Classe ORDER BY Nome")
        for c in classes:
            c["habs_base"] = rows(
                "SELECT Id_Habilidade, NivelAdquirido, Nome, TagsJSON "
                "FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL "
                "ORDER BY NivelAdquirido, Nome", c["Id_Classe"],
            )
            subs = rows(
                "SELECT Id_Subclasse, Nome, TagsJSON FROM TB_Subclasse "
                "WHERE Id_Classe=? ORDER BY Nome", c["Id_Classe"],
            )
            for s in subs:
                s["habs"] = rows(
                    "SELECT Id_Habilidade, NivelAdquirido, Nome, TagsJSON "
                    "FROM TB_ClasseHabilidade WHERE Id_Subclasse=? "
                    "ORDER BY NivelAdquirido, Nome", s["Id_Subclasse"],
                )
            c["subclasses"] = subs
        return jsonify({"entidade": "classes", "groups": classes})

    if entidade == "talentos":
        # Talentos raciais cujo Fonte casa com Slug de raça/essência são exibidos
        # dentro das páginas /debug/racas e /debug/essencias respectivamente.
        # Aqui aparecem só os "órfãos" (Fonte sem casamento) + talentos de origem/gerais.
        # Convenção: TB_Essencia.Slug pode ter prefixo 'essencia-' enquanto
        # TB_TalentoRacial.Fonte usa o slug "puro" (ver regra-tags-universais.md §1.1
        # de docs/talentos-raca-essencia.md). Aceitamos as duas formas.
        slugs_racas = {r["Slug"] for r in rows("SELECT Slug FROM TB_Raca")}
        slugs_essencias_raw = [e["Slug"] for e in rows("SELECT Slug FROM TB_Essencia")]
        slugs_essencias: set[str] = set()
        for s in slugs_essencias_raw:
            slugs_essencias.add(s)
            if s.startswith("essencia-"):
                slugs_essencias.add(s[len("essencia-"):])
        slugs_classificados = slugs_racas | slugs_essencias
        all_racial = rows(
            "SELECT Id_TalentoRacial, Nome, TagsJSON, NivelMinimo, Fonte "
            "FROM TB_TalentoRacial ORDER BY Fonte, NivelMinimo, Nome"
        )
        racial_orphan = [t for t in all_racial if (t.get("Fonte") or "") not in slugs_classificados]
        origem = rows(
            "SELECT Id_Opcao, Nome, TagsJSON, Tipo FROM TB_OpcaoJogo "
            "WHERE Tipo IN ('talento-origem','talento-geral') ORDER BY Tipo, Nome"
        )
        return jsonify({"entidade": "talentos", "racial": racial_orphan, "origem_e_geral": origem})

    if entidade == "racas":
        racas = rows("SELECT Id_Raca, Slug, Nome, TagsJSON FROM TB_Raca ORDER BY Nome")
        for r in racas:
            r["tracos_base"] = rows(
                "SELECT Id_Traco, Nome, TagsJSON, NivelRequisito FROM TB_TracoRacial "
                "WHERE Id_Raca=? AND Id_Linhagem IS NULL AND Id_Essencia IS NULL "
                "ORDER BY NivelRequisito, Nome", r["Id_Raca"],
            )
            r["talentos_raciais"] = rows(
                "SELECT Id_TalentoRacial, Nome, TagsJSON, NivelMinimo, Fonte "
                "FROM TB_TalentoRacial WHERE Fonte=? "
                "ORDER BY NivelMinimo, Nome", r["Slug"],
            )
            r["linhagens"] = rows(
                "SELECT Id_Linhagem, Nome, TagsJSON FROM TB_Linhagem "
                "WHERE Id_Raca=? ORDER BY Nome", r["Id_Raca"],
            )
            for li in r["linhagens"]:
                li["tracos"] = rows(
                    "SELECT Id_Traco, Nome, TagsJSON, NivelRequisito FROM TB_TracoRacial "
                    "WHERE Id_Linhagem=? ORDER BY NivelRequisito, Nome", li["Id_Linhagem"],
                )
        return jsonify({"entidade": "racas", "groups": racas})

    if entidade == "essencias":
        essencias = rows("SELECT Id_Essencia, Slug, Nome, TagsJSON FROM TB_Essencia ORDER BY Nome")
        for e in essencias:
            e["tracos_base"] = rows(
                "SELECT Id_Traco, Nome, TagsJSON, NivelRequisito FROM TB_TracoRacial "
                "WHERE Id_Essencia=? AND Id_EssLinhagem IS NULL AND Id_Raca IS NULL "
                "ORDER BY NivelRequisito, Nome", e["Id_Essencia"],
            )
            # TB_TalentoRacial.Fonte usa slug "puro" (ex: 'infernal') enquanto
            # TB_Essencia.Slug pode ter prefixo (ex: 'essencia-infernal').
            slug_puro = e["Slug"][len("essencia-"):] if e["Slug"].startswith("essencia-") else e["Slug"]
            e["talentos_raciais"] = rows(
                "SELECT Id_TalentoRacial, Nome, TagsJSON, NivelMinimo, Fonte "
                "FROM TB_TalentoRacial WHERE Fonte=? OR Fonte=? "
                "ORDER BY NivelMinimo, Nome", e["Slug"], slug_puro,
            )
            e["sublinhagens"] = rows(
                "SELECT Id_EssLinhagem, Nome, TagsJSON "
                "FROM TB_EssenciaLinhagem WHERE Id_Essencia=? ORDER BY Nome", e["Id_Essencia"],
            )
            for sl in e["sublinhagens"]:
                sl["tracos"] = rows(
                    "SELECT Id_Traco, Nome, TagsJSON, NivelRequisito FROM TB_TracoRacial "
                    "WHERE Id_EssLinhagem=? ORDER BY NivelRequisito, Nome", sl["Id_EssLinhagem"],
                )
        return jsonify({"entidade": "essencias", "groups": essencias})

    if entidade == "items":
        items = rows(
            "SELECT i.Id_Item, i.Nome, i.NomeTraduzido, i.TagsJSON, "
            "       COALESCE(s.Nome,'(sem slot)') AS SlotNome "
            "FROM TB_Item i LEFT JOIN TB_ItemSlot s ON s.Id_Slot = i.Id_Slot "
            "ORDER BY SlotNome, i.Nome"
        )
        return jsonify({"entidade": "items", "items": items})

    return jsonify({"error": f"entidade desconhecida: {entidade}"}), 404


if __name__ == "__main__":
    if not DB_PATH.exists():
        print("⚠  bonfas.db não existe — rode `python init_db.py` primeiro.")
    app.run(debug=True, port=5000)
