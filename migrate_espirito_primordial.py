"""Schema + 3 variantes do Espírito Primordial + tag pick na hab id=125
(Companheiro Primordial — sub Aliança Selvagem do Caçador, Nv 3)."""
import json, shutil, sqlite3, time

DB = "bonfas.db"
ID_HAB_COMPANHEIRO = 125
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

# Stats compartilhadas: CA 13, PV 20 + 10×(nv-3), atributos 16/16/16/10/14/12.
# Velocidades inferidas (raw HTML deixa "Velocidade:" vazio — Terra/Céu/Mar especificadas aqui).
VARIANTES = [
    {
        "slug": "terra", "nome": "Terra",
        "andar": 40, "voar": 0, "nadar": 0, "escalar": 0,
        "flavor": "Companheiro robusto adaptado a terra firme — quadrúpede ágil em florestas, montanhas e planícies.",
    },
    {
        "slug": "ceu", "nome": "Céu",
        "andar": 30, "voar": 60, "nadar": 0, "escalar": 0,
        "flavor": "Companheiro alado — mensageiro do alto, vigia das ravinas e visão a kilômetros.",
    },
    {
        "slug": "mar", "nome": "Mar",
        "andar": 20, "voar": 0, "nadar": 60, "escalar": 0,
        "flavor": "Companheiro aquático — caça em rios, mangues e profundidades onde poucos seguem.",
    },
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_EspiritoPrimordialVariante (
    Id_Variante INTEGER PRIMARY KEY AUTOINCREMENT,
    Slug VARCHAR(20) UNIQUE NOT NULL,
    Nome VARCHAR(40) NOT NULL,
    CA INTEGER NOT NULL DEFAULT 13,
    PV_Base INTEGER NOT NULL DEFAULT 20,        -- PV no Nv 3
    PV_PorNivel INTEGER NOT NULL DEFAULT 10,    -- por nível de Caçador após o 3º
    Forca INTEGER NOT NULL DEFAULT 16,
    Destreza INTEGER NOT NULL DEFAULT 16,
    Constituicao INTEGER NOT NULL DEFAULT 16,
    Inteligencia INTEGER NOT NULL DEFAULT 10,
    Sabedoria INTEGER NOT NULL DEFAULT 14,
    Carisma INTEGER NOT NULL DEFAULT 12,
    Vel_Andar INTEGER NOT NULL DEFAULT 30,
    Vel_Voar INTEGER NOT NULL DEFAULT 0,
    Vel_Nadar INTEGER NOT NULL DEFAULT 0,
    Vel_Escalar INTEGER NOT NULL DEFAULT 0,
    Flavor TEXT
);
""")

# Catálogo TB_EspiritoPrimordialVariante
ins = 0
for v in VARIANTES:
    if not cur.execute("SELECT 1 FROM TB_EspiritoPrimordialVariante WHERE Slug=?", (v["slug"],)).fetchone():
        cur.execute(
            """INSERT INTO TB_EspiritoPrimordialVariante
               (Slug, Nome, Vel_Andar, Vel_Voar, Vel_Nadar, Vel_Escalar, Flavor)
               VALUES (?,?,?,?,?,?,?)""",
            (v["slug"], v["nome"], v["andar"], v["voar"], v["nadar"], v["escalar"], v["flavor"]),
        )
        ins += 1
print(f"TB_EspiritoPrimordialVariante: {ins} inseridos / {len(VARIANTES) - ins} existiam")

# Catálogo TB_OpcaoJogo (universal picker) — cada opção tem TagsJSON ativando a tag da variante.
TIPO = "alianca-selvagem-companheiro"
opcoes_ja = {r[0] for r in cur.execute("SELECT Slug FROM TB_OpcaoJogo WHERE Tipo=?", (TIPO,))}
for v in VARIANTES:
    tag_var = f"alianca-selvagem-companheiro-{v['slug']}"
    payload_tags = json.dumps([tag_var], ensure_ascii=False)
    if v["slug"] in opcoes_ja:
        cur.execute(
            "UPDATE TB_OpcaoJogo SET Nome=?, Descricao=?, TagsJSON=? WHERE Tipo=? AND Slug=?",
            (v["nome"], v["flavor"], payload_tags, TIPO, v["slug"]),
        )
    else:
        cur.execute(
            """INSERT INTO TB_OpcaoJogo (Tipo, Nome, Slug, Descricao, TagsJSON)
               VALUES (?,?,?,?,?)""",
            (TIPO, v["nome"], v["slug"], v["flavor"], payload_tags),
        )
print(f"TB_OpcaoJogo: 3 entries Tipo='{TIPO}' (com TagsJSON ativando alianca-selvagem-companheiro-<slug>)")

# Tag pick na hab Companheiro Primordial
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
            (f'["pick:{TIPO}:1"]', ID_HAB_COMPANHEIRO))
print(f"Hab id={ID_HAB_COMPANHEIRO} (Companheiro Primordial): TagsJSON=['pick:{TIPO}:1']")

conn.commit()
conn.close()
print("\nDONE.")
