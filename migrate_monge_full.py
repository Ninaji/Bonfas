"""Migration Monge: 10 subs + Nv 3 features + classe Nv 1-20 +
   features Nv 6/11/17 da Palma Aberta (sub do Sam pid=6 a vir).

Idempotente: skipKinds em todas as inserções."""
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_MONGE = 12

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

FEATS = json.loads(Path("monge_features.json").read_text(encoding="utf-8"))
SUBS_PARSED = json.loads(Path("monge_subs.json").read_text(encoding="utf-8"))

# Lookup
desc_by = {(f["nivel"], f["nome"]): f["descricao"] for f in FEATS}

# H4 que não foram pegos pelo parser (só capturou H3) — entram com desc placeholder.
desc_by[(3,  "Tradição Monástica")] = (
    "Você adota uma Tradição Monástica que molda sua filosofia, técnicas e poderes. "
    "Cada Tradição concede características nos níveis 3, 6, 11 e 17."
)
desc_by[(6,  "Tradição Monástica")] = "Você ganha uma característica de Tradição Monástica do 6º nível."
desc_by[(11, "Tradição Monástica")] = "Você ganha uma característica de Tradição Monástica do 11º nível."
desc_by[(17, "Tradição Monástica")] = "Você ganha uma característica de Tradição Monástica do 17º nível."

# Taglines curtas (escritas à mão — parser pegou texto cru gigante)
SUBS = [
    {"nome": "Tradição da Alma Ardente",   "slug": "alma-ardente",   "tagline": "Monges que canalizam fogo interior através dos Ardores da Alma."},
    {"nome": "Tradição da Alma Astral",    "slug": "alma-astral",    "tagline": "Monges que projetam membros etéreos da própria essência astral."},
    {"nome": "Tradição Elemental",         "slug": "elemental",      "tagline": "Monges que canalizam os elementos primordiais em forma e técnica."},
    {"nome": "Tradição Imortal",           "slug": "imortal",        "tagline": "Monges que dominam a fronteira entre vida e morte."},
    {"nome": "Tradição Kensei",            "slug": "kensei",         "tagline": "Monges que tratam a arma branca como extensão do próprio corpo."},
    {"nome": "Tradição da Misericórdia",   "slug": "misericordia",   "tagline": "Monges curadores e algozes que decidem quem vive e quem cai."},
    {"nome": "Tradição da Palma Aberta",   "slug": "palma-aberta",   "tagline": "Monges que dominam o uso do Ki em técnicas de combate desarmado."},
    {"nome": "Tradição do Punho Bêbado",   "slug": "punho-bebado",   "tagline": "Monges cujo cambaleio confunde e ferve em violência etílica."},
    {"nome": "Tradição do Punho do Dragão","slug": "punho-do-dragao","tagline": "Monges discípulos de dragões — sopro, aura e fúria primordial."},
    {"nome": "Tradição das Sombras",       "slug": "sombras",        "tagline": "Monges silenciosos que se movem pela penumbra como furtivos."},
]

# Features CLASSE Monge (Id_Subclasse=NULL). Tem_escolha=1 só pra ASIs e "Tradição Monástica".
CLASSE_FEATS = [
    # (nivel, nome, tem_escolha, origem)
    (1,  "Artes Marciais",                      0, "classe"),
    (1,  "Guerreiro sem Armadura",              0, "classe"),
    (2,  "Ki",                                  0, "classe"),
    (2,  "Passo Veloz",                         0, "classe"),
    (2,  "Desviar Ataques",                     0, "classe"),
    (3,  "Tradição Monástica",                  1, "subclasse"),  # pick:subclasse
    (4,  "Aprimoramento no Valor de Habilidade",1, "classe"),
    (4,  "Queda Lenta",                         0, "classe"),
    (4,  "Cura Acelerada",                      0, "classe"),
    (5,  "Ataque Extra",                        0, "classe"),
    (5,  "Golpe Atordoante",                    0, "classe"),
    (6,  "Golpes de Ki",                        0, "classe"),
    (6,  "Momento de Ajuste",                   0, "classe"),
    (6,  "Tradição Monástica",                  1, "subclasse"),  # header
    (7,  "Evasão",                              0, "classe"),
    (8,  "Aprimoramento no Valor de Habilidade",1, "classe"),
    (9,  "Movimento Acrobático",                0, "classe"),
    (10, "Restauração Interior",                0, "classe"),
    (11, "Tradição Monástica",                  1, "subclasse"),  # header
    (12, "Aprimoramento no Valor de Habilidade",1, "classe"),
    (13, "Desviar Energia",                     0, "classe"),
    (14, "Sobrevivente Disciplinado",           0, "classe"),
    (15, "Corpo Atemporal",                     0, "classe"),
    (16, "Aprimoramento no Valor de Habilidade",1, "classe"),
    (17, "Tradição Monástica",                  1, "subclasse"),  # header
    (18, "Defesa Superior",                     0, "classe"),
    (19, "Aprimoramento no Valor de Habilidade",1, "classe"),
    (20, "Corpo & Mente",                       0, "classe"),
]

# Mapeamento de sub-feature por (nivel, nome) -> slug da sub.
# Foco: TODAS as Nv 3 (já agrupadas no parser por offset). E Nv 6/11/17 da Palma Aberta.
# Demais subs Nv 6/11/17 ficam pra futura iteração (mapeamento por leitura textual).
SUB_FEAT_BY_SLUG: dict[tuple[int,str], str] = {}

# Nv 3: pega o que o parser já agrupou em SUBS_PARSED[i]["features_sub"]
for s in SUBS_PARSED:
    slug_map = next((sub["slug"] for sub in SUBS if sub["slug"] == s["slug"]), s["slug"])
    for feat in s["features_sub"]:
        SUB_FEAT_BY_SLUG[(feat["nivel"], feat["nome"])] = slug_map

# Nv 6/11/17 da Palma Aberta (sub do Sam):
SUB_FEAT_BY_SLUG[(6,  "Ataque Desestabilizador")] = "palma-aberta"
SUB_FEAT_BY_SLUG[(11, "Sentido de Ki")]            = "palma-aberta"
SUB_FEAT_BY_SLUG[(17, "Palma Vibrante")]           = "palma-aberta"


def upsert_sub(cur, sub: dict) -> int:
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_MONGE, sub["slug"]),
    ).fetchone()
    if row:
        sid = row[0]
        cur.execute(
            "UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
            (sub["nome"], sub["tagline"], sid),
        )
        return sid
    cur.execute(
        "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
        (ID_MONGE, sub["nome"], sub["slug"], sub["tagline"]),
    )
    return cur.lastrowid


def upsert_hab(cur, id_sub, nome, nivel, tem_escolha, origem):
    desc = desc_by.get((nivel, nome))
    if desc is None:
        return f"NO-DESC ({nivel},{nome})"
    if id_sub is None:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND NivelAdquirido=?",
            (ID_MONGE, nome, nivel),
        ).fetchone()
    else:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND NivelAdquirido=?",
            (ID_MONGE, id_sub, nome, nivel),
        ).fetchone()
    if row:
        return "skip"
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?,?,?,?,?,?,?,NULL)""",
        (ID_MONGE, id_sub, nome, desc, nivel, tem_escolha, origem),
    )
    return "ins"


conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Subclasses
print("=== SUBCLASSES ===")
slug_to_sid = {}
for sub in SUBS:
    sid = upsert_sub(cur, sub)
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3}  {sub['slug']:<22} {sub['nome']}")

# 2) Classe Nv 1-20 (não-sub)
print("\n=== CLASSE (Id_Subclasse=NULL) ===")
for nivel, nome, tem_esc, origem in CLASSE_FEATS:
    res = upsert_hab(cur, None, nome, nivel, tem_esc, origem)
    print(f"  Nv{nivel:>2} esc={tem_esc} {nome:<48} [{res}]")

# 3) Sub Nv 3 features (do parser) + Palma Aberta Nv 6/11/17
print("\n=== SUBCLASSES — features mapeadas ===")
by_sub_count = {}
for (nivel, nome), slug in SUB_FEAT_BY_SLUG.items():
    sid = slug_to_sid.get(slug)
    if sid is None:
        print(f"  WARNING: sub slug {slug!r} não existe — pula ({nivel},{nome})")
        continue
    res = upsert_hab(cur, sid, nome, nivel, 0, "subclasse")
    by_sub_count[slug] = by_sub_count.get(slug, 0) + (1 if res == "ins" else 0)
    print(f"  sub {sid:>3} ({slug:<18}) Nv{nivel:>2} {nome:<40} [{res}]")

conn.commit()

print("\n=== STATS ===")
total_classe = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL", (ID_MONGE,)
).fetchone()[0]
print(f"  Habs CLASSE Monge: {total_classe}")
for slug, sid in slug_to_sid.items():
    n = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse=?",
        (ID_MONGE, sid),
    ).fetchone()[0]
    print(f"  sub {sid:>3} {slug:<22} {n} habs")

conn.close()
print("\nDONE.")
