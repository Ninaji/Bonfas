"""Popula Místico: 8 subs (Patronos) + classe Nv 1-20 + sub Nv 3 features."""
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_MISTICO = 11
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

FEATS = json.loads(Path("mistico_features.json").read_text(encoding="utf-8"))
SUBS_PARSED = json.loads(Path("mistico_subs.json").read_text(encoding="utf-8"))
desc_by = {(f["nivel"], f["nome"]): f["descricao"] for f in FEATS}

SUBS = [
    {"nome": "O Afogado",       "slug": "o-afogado",       "tagline": "Pacto com entidade abissal das profundezas — tentáculos, oceano e marés."},
    {"nome": "A Arquifada",     "slug": "a-arquifada",     "tagline": "Pacto com soberana feérica — encantos, presença e tramas das fronteiras silvestres."},
    {"nome": "O Ceifador",      "slug": "o-ceifador",      "tagline": "Pacto com entidade da morte — marca da finitude, mortalha e fim escrito."},
    {"nome": "O Celestial",     "slug": "o-celestial",     "tagline": "Pacto com ente angelical — chama luminosa, cura e proteção contra trevas."},
    {"nome": "O Gênio",         "slug": "o-genio",         "tagline": "Pacto com gênio elemental — receptáculo, presentes elementais e desejos limitados."},
    {"nome": "O Grande Antigo", "slug": "o-grande-antigo", "tagline": "Pacto com entidade aberracional — sussurros, mente alheia e delírio cósmico."},
    {"nome": "O Imortal",       "slug": "o-imortal",       "tagline": "Pacto com ser perpétuo — proteção da morte, ressurreição e poder eterno."},
    {"nome": "O Ínfero",        "slug": "o-infero",        "tagline": "Pacto com diabo dos infernos — moedas, contratos, fortalecimento e cláusulas."},
]

# Habs CLASSE Místico (Id_Subclasse=NULL). 4 Manifestações Nv 1 entram como classe-only
# (cada Místico escolhe 1 — gating por tag fica como pendência).
CLASSE_FEATS = [
    (1,  "Feitiçaria Mística",                   0, "classe"),
    (1,  "Manifestação Mística",                 1, "classe"),
    (1,  "Manifestação — Arma Mística",          0, "classe"),
    (1,  "Manifestação — Contrato Místico",      0, "classe"),
    (1,  "Manifestação — Livro Místico",         0, "classe"),
    (1,  "Manifestação — Marca Mística",         0, "classe"),
    (2,  "Segredos Místicos",                    0, "classe"),
    (3,  "Manifestação Mística Aprimorada",      0, "classe"),
    (3,  "Arma Mística — Armas Múltiplas",       0, "classe"),
    (3,  "Arma Mística — Destruição Mística",    0, "classe"),
    (3,  "Contrato Místico — Ligação Amplificada", 0, "classe"),
    (3,  "Livro Místico — Preparação de Magia",  0, "classe"),
    (3,  "Marca Mística — Marca Protetora",      0, "classe"),
    (3,  "Patrono Transcendental",               1, "subclasse"),  # header
    (4,  "Incremento no Valor de Habilidade",    1, "classe"),
    (6,  "Patrono Transcendental",               1, "subclasse"),
    (9,  "Contatar o Patrono",                   0, "classe"),
    (10, "Patrono Transcendental",               1, "subclasse"),
    (11, "Arcana Mística",                       0, "classe"),
    (13, "Arcana Mística — Addendum de 7º ciclo",0, "classe"),
    (14, "Patrono Transcendental",               1, "subclasse"),
    (15, "Arcana Mística — Addendum de 8º ciclo",0, "classe"),
    (17, "Arcana Mística — Addendum de 9º ciclo",0, "classe"),
    (18, "Manifestação Mística Avançada",        0, "classe"),
    (18, "Arma Mística — Destruição Mística Aprimorada", 0, "classe"),
    (18, "Contrato Místico — Cláusula de Poder", 0, "classe"),
    (18, "Livro Místico — Favor Místico Aprimorado", 0, "classe"),
    (18, "Marca Mística — Segunda Marca",        0, "classe"),
    (20, "Mestre Místico",                       0, "classe"),
    # ASIs adicionais (Nv 8/12/16/19) — não detectados pelo parser; entram como classe
    (8,  "Incremento no Valor de Habilidade",    1, "classe"),
    (12, "Incremento no Valor de Habilidade",    1, "classe"),
    (16, "Incremento no Valor de Habilidade",    1, "classe"),
    (19, "Incremento no Valor de Habilidade",    1, "classe"),
]

# Mapeamento Nv 6/10/14 por sub (mapeamento por palavra-chave)
SUB_FEAT_BY_SLUG: dict[tuple[int,str], str] = {}
for s in SUBS_PARSED:
    slug_canon = next((sub["slug"] for sub in SUBS if sub["slug"] == s["slug"]), s["slug"])
    for feat in s["features_sub"]:
        SUB_FEAT_BY_SLUG[(feat["nivel"], feat["nome"])] = slug_canon

# Nv 6/10/14 (mapeamento explícito)
SUB_FEAT_BY_SLUG.update({
    # Nv 6
    (6,  "Alma Oceânica"):       "o-afogado",
    (6,  "Guardião Afogado"):    "o-afogado",     # Afogado tem 2 escolhas Nv 6
    (6,  "Escapada Elusiva"):    "a-arquifada",
    (6,  "Movimento Fantasma"):  "o-ceifador",
    (6,  "Alma Radiante"):       "o-celestial",
    (6,  "Presente Elemental"):  "o-genio",
    (6,  "Proteção Entrópica"):  "o-grande-antigo",
    (6,  "Tocado Pelo Túmulo"):  "o-imortal",
    (6,  "Cláusula Complementar"): "o-infero",
    # Nv 10
    (10, "Um com as Profundezas"):    "o-afogado",
    (10, "Presença Contagiante"):     "a-arquifada",
    (10, "Mortalha do Ceifador"):     "o-ceifador",
    (10, "Fortalecimento Angelical"): "o-celestial",
    (10, "Santuário Pessoal"):        "o-genio",
    (10, "Escudo do Pensamento"):     "o-grande-antigo",
    (10, "Proteção da Morte"):        "o-imortal",
    (10, "Fortalecimento Ínfero"):    "o-infero",
    # Nv 14
    (14, "Mergulho do Afogado"):    "o-afogado",
    (14, "Delírio Enegrecido"):     "o-grande-antigo",
    (14, "Ímpeto do Ceifador"):     "o-ceifador",
    (14, "Vingança Abrasadora"):    "o-celestial",
    (14, "Desejo Limitado"):        "o-genio",
    (14, "Criar Lacaio"):           "a-arquifada",  # criar lacaio feérico
    (14, "Levante-se"):             "o-imortal",
    (14, "Passeio Infernal"):       "o-infero",
})


def upsert_sub(cur, sub):
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_MISTICO, sub["slug"]),
    ).fetchone()
    if row:
        cur.execute("UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
                    (sub["nome"], sub["tagline"], row[0]))
        return row[0]
    cur.execute("INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
                (ID_MISTICO, sub["nome"], sub["slug"], sub["tagline"]))
    return cur.lastrowid


def upsert_hab(cur, id_sub, nome, nivel, tem_esc, origem):
    desc = desc_by.get((nivel, nome))
    if desc is None:
        return f"NO-DESC ({nivel},{nome})"
    if id_sub is None:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND NivelAdquirido=?",
            (ID_MISTICO, nome, nivel)).fetchone()
    else:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND NivelAdquirido=?",
            (ID_MISTICO, id_sub, nome, nivel)).fetchone()
    if row: return "skip"
    cur.execute(
        "INSERT INTO TB_ClasseHabilidade "
        "(Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON) "
        "VALUES (?,?,?,?,?,?,?,NULL)",
        (ID_MISTICO, id_sub, nome, desc, nivel, tem_esc, origem),
    )
    return "ins"


# Adiciona desc placeholder pras habs sem desc no parser
desc_by[(8,  "Incremento no Valor de Habilidade")] = "ASI: +2 em 1 atributo OU +1 em 2 atributos OU pegue um talento."
desc_by[(12, "Incremento no Valor de Habilidade")] = desc_by[(8, "Incremento no Valor de Habilidade")]
desc_by[(16, "Incremento no Valor de Habilidade")] = desc_by[(8, "Incremento no Valor de Habilidade")]
desc_by[(19, "Incremento no Valor de Habilidade")] = desc_by[(8, "Incremento no Valor de Habilidade")]
desc_by[(3,  "Patrono Transcendental")] = "Você ganha características da subclasse (Patrono) escolhida no Nv 3."
desc_by[(6,  "Patrono Transcendental")] = "Característica adicional da sub Nv 6."
desc_by[(10, "Patrono Transcendental")] = "Característica adicional da sub Nv 10."
desc_by[(14, "Patrono Transcendental")] = "Característica adicional da sub Nv 14."

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=== SUBS ===")
slug_to_sid = {}
for sub in SUBS:
    sid = upsert_sub(cur, sub)
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3}  {sub['slug']:<22} {sub['nome']}")

print("\n=== CLASSE ===")
for nv, nome, esc, orig in CLASSE_FEATS:
    res = upsert_hab(cur, None, nome, nv, esc, orig)
    print(f"  Nv{nv:>2} esc={esc} {nome:<46} [{res}]")

print("\n=== SUBS — features ===")
for (nv, nome), slug in SUB_FEAT_BY_SLUG.items():
    sid = slug_to_sid.get(slug)
    if sid is None:
        print(f"  WARN {slug!r} não existe — pula ({nv},{nome})")
        continue
    res = upsert_hab(cur, sid, nome, nv, 0, "subclasse")
    print(f"  sub {sid:>3} ({slug:<18}) Nv{nv:>2} {nome:<40} [{res}]")

conn.commit()

print("\n=== STATS ===")
total_classe = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL", (ID_MISTICO,)
).fetchone()[0]
print(f"  Habs CLASSE Místico: {total_classe}")
for slug, sid in slug_to_sid.items():
    n = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse=?",
        (ID_MISTICO, sid),
    ).fetchone()[0]
    print(f"  sub {sid:>3} {slug:<22} {n} habs")

conn.close()
print("\nDONE.")
