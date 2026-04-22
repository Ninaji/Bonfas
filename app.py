"""
Backend Flask — expõe dados de raças/linhagens/essências/traços e persiste
o equipamento do personagem em SQLite.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS

BASE = Path(__file__).parent
DB_PATH = BASE / "bonfas.db"

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
    allowed = ["Nome", "Nivel", "DonoUsuario", "PVAtual", "PVMaximo"]
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
    esc_fields = ["Id_Raca", "Id_Linhagem", "Id_Essencia", "Id_Classe",
                  "Id_Subclasse", "NivelMultiClasse"]
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
       - intersecao de tags do personagem com tags do talento != vazio
       - NivelMinimo <= personagem.Nivel
       - ainda nao escolhido"""
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
        talento_tags = set(json.loads(t["TagsJSON"] or "[]"))
        # talento exige que TODAS as tags dele estejam no personagem
        # (talento c/ {humano,erthari} só fica disponível se o personagem for humano E erthari)
        if not talento_tags.issubset(tags):
            continue
        t["TagsJSON"] = list(talento_tags)    # devolve como array
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
    conn.execute(
        """INSERT INTO TB_PersonagemTalento
               (Id_Personagem, Categoria, Nivel, Nome, Detalhes, Id_TalentoRacial)
               VALUES (?, ?, ?, ?, ?, ?)""",
        (pid, cat, t["NivelMinimo"], t["Nome"][:150], (t["PreReqTexto"] or "")[:200], id_tal),
    )
    conn.commit()
    return jsonify({"ok": True, "talento": t["Nome"], "categoria": cat})


@app.post("/api/personagens/<int:pid>/talento-manual")
def talento_manual(pid: int):
    d = request.get_json(force=True) or {}
    cat = (d.get("categoria") or "classe").strip()
    if cat not in ("classe", "geral", "extra", "raca", "essencia"):
        cat = "classe"
    nivel = int(d.get("nivel") or 1)
    nome = (d.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "nome obrigatório"}), 400
    conn = db()
    # 1 slot por (categoria, nivel): remove anterior
    conn.execute(
        "DELETE FROM TB_PersonagemTalento WHERE Id_Personagem=? AND Categoria=? AND Nivel=?",
        (pid, cat, nivel),
    )
    conn.execute(
        "INSERT INTO TB_PersonagemTalento (Id_Personagem, Categoria, Nivel, Nome) VALUES (?,?,?,?)",
        (pid, cat, nivel, nome[:150]),
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


@app.put("/api/personagens/<int:pid>/habilidade-opcao/<int:hid>")
def put_hab_opcao(pid: int, hid: int):
    d = request.get_json(force=True) or {}
    texto = (d.get("texto") or "").strip()
    conn = db()
    conn.execute(
        "DELETE FROM TB_PersonagemHabilidadeOpcao WHERE Id_Personagem=? AND Id_Habilidade=?",
        (pid, hid),
    )
    if texto:
        conn.execute(
            "INSERT INTO TB_PersonagemHabilidadeOpcao (Id_Personagem, Id_Habilidade, Texto) VALUES (?,?,?)",
            (pid, hid, texto[:300]),
        )
    conn.commit()
    return jsonify({"ok": True})


@app.get("/api/personagens/<int:pid>/full")
def personagem_full(pid: int):
    """Retorna TUDO do personagem (cru + tabelas auxiliares) para a página /ficha."""
    p = _personagem_raw(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    esc = p["escolha"] or {}
    def _getopt(tbl, k, val):
        return one(f"SELECT * FROM {tbl} WHERE {k} = ?", val) if val else None
    raca     = _getopt("TB_Raca",       "Id_Raca",      esc.get("Id_Raca"))
    linhagem = _getopt("TB_Linhagem",   "Id_Linhagem",  esc.get("Id_Linhagem"))
    essencia = _getopt("TB_Essencia",   "Id_Essencia",  esc.get("Id_Essencia"))
    ess_lin  = _getopt("TB_EssenciaLinhagem", "Id_EssLinhagem", esc.get("Id_EssLinhagem"))
    classe   = _getopt("TB_Classe",     "Id_Classe",    esc.get("Id_Classe"))
    sub      = _getopt("TB_Subclasse",  "Id_Subclasse", esc.get("Id_Subclasse"))

    niv = p["Nivel"] or 1
    tracos = rows("SELECT * FROM TB_TracoRacial WHERE Id_Raca = ? AND NivelRequisito <= ? ORDER BY NivelRequisito",
                  esc.get("Id_Raca") or -1, niv) if raca else []
    rec_prog = rows("SELECT * FROM TB_RecursoClasse WHERE Id_Classe = ? AND Nivel <= ? ORDER BY Nivel, Nome",
                    esc.get("Id_Classe") or -1, niv) if classe else []
    habs_cls = rows(
        """SELECT h.*, o.Texto AS OpcaoEscolhida
             FROM TB_ClasseHabilidade h
        LEFT JOIN TB_PersonagemHabilidadeOpcao o
               ON o.Id_Habilidade = h.Id_Habilidade AND o.Id_Personagem = ?
            WHERE h.Id_Classe = ? AND h.Id_Subclasse IS NULL
              AND h.NivelAdquirido <= ?
            ORDER BY h.NivelAdquirido, h.Nome""",
        pid, esc.get("Id_Classe") or -1, niv,
    ) if classe else []
    habs_sub = rows(
        """SELECT h.*, o.Texto AS OpcaoEscolhida
             FROM TB_ClasseHabilidade h
        LEFT JOIN TB_PersonagemHabilidadeOpcao o
               ON o.Id_Habilidade = h.Id_Habilidade AND o.Id_Personagem = ?
            WHERE h.Id_Subclasse = ?
              AND h.NivelAdquirido <= ?
            ORDER BY h.NivelAdquirido, h.Nome""",
        pid, esc.get("Id_Subclasse") or -1, niv,
    ) if sub else []

    # auto-efeitos da linhagem da essência: resistência elemental + truque + magia nv3
    auto_efeitos = {}
    if ess_lin:
        niv = p["Nivel"] or 1
        auto_efeitos = {
            "origem": f"Linhagem {ess_lin['Nome']} ({essencia['Nome'] if essencia else ''})",
            "resistencia": ess_lin.get("Elemento"),
            "truque":      ess_lin.get("TruqueNome"),
            "magia_n3":    ess_lin.get("MagiaN3Nome") if niv >= 3 else None,
        }

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

    return jsonify({
        "personagem":  p,
        "raca":        raca,
        "linhagem":    linhagem,
        "essencia":    essencia,
        "ess_linhagem": ess_lin,
        "auto_efeitos": auto_efeitos,
        "classe":      classe,
        "subclasse":   sub,
        "limites":     limites,
        "tracos":      tracos,
        "recursos_classe": rec_prog,
        "habilidades_classe": habs_cls,
        "habilidades_subclasse": habs_sub,
        "pericias":    rows("SELECT * FROM TB_PersonagemPericia WHERE Id_Personagem = ? ORDER BY Nome", pid),
        "talentos":    rows("SELECT * FROM TB_PersonagemTalento WHERE Id_Personagem = ? ORDER BY Categoria, Nivel", pid),
        "idiomas":     rows("SELECT * FROM TB_PersonagemIdioma WHERE Id_Personagem = ? ORDER BY Tipo, Nome", pid),
        "resistencias":rows("SELECT * FROM TB_PersonagemResistencia WHERE Id_Personagem = ?", pid),
        "personalidade": rows("SELECT * FROM TB_PersonagemPersonalidade WHERE Id_Personagem = ?", pid),
        "inventario":  rows("SELECT * FROM TB_PersonagemInventarioItem WHERE Id_Personagem = ? ORDER BY Id", pid),
        "magias":      rows("SELECT * FROM TB_PersonagemMagia WHERE Id_Personagem = ? ORDER BY Nivel, Nome", pid),
        "tecnicas":    rows("SELECT * FROM TB_PersonagemTecnica WHERE Id_Personagem = ? ORDER BY Nome", pid),
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


if __name__ == "__main__":
    if not DB_PATH.exists():
        print("⚠  bonfas.db não existe — rode `python init_db.py` primeiro.")
    app.run(debug=True, port=5000)
