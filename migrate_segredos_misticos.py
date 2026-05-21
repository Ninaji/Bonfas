"""Schema + catálogo + tag para Segredos Místicos (Místico Nv 2+).
Padrão idêntico aos Segredos do Caçador / Estilos de Ki / Inimigo Favorito."""
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_MISTICO = 11
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

SEGREDOS = json.loads(Path("mistico_segredos.json").read_text(encoding="utf-8"))

# Mapa seção → (nivel_min, gate_tag opcional)
# Seção determina pré-requisito: só pode aprender se char atender.
SECAO_META = {
    "Invocações Místicas de 1º Nível":               (1,  None),
    "Segredos Místicos de 5º Nível":                  (5,  None),
    "Segredos Místicos de 7º Nível":                  (7,  None),
    "Segredos Místicos de 9º Nível":                  (9,  None),
    "Segredos Místicos de 15º Nível":                 (15, None),
    "Segredos Místicos de Rajada Mística (Eldritch Blast)": (1, None),  # exige cantrip Rajada Mística
    "Segredos Místicos de Maldições":                 (1,  None),  # gate por magia Maldição? (livre por hora)
    "Segredos Místicos Arma Mística":                 (1,  "manifestacao-arma-mistica"),
    "Segredos Místicos Contrato Místico":             (1,  "manifestacao-contrato-mistico"),
    "Segredos Místicos Livro Místico":                (1,  "manifestacao-livro-mistico"),
    "Segredos Místicos Joia Mística":                 (1,  "manifestacao-marca-mistica"),  # 'Joia' = Marca no catálogo Bonfire
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_SegredoMistico (
    Id_Segredo  INTEGER PRIMARY KEY AUTOINCREMENT,
    Slug        VARCHAR(80) UNIQUE NOT NULL,
    Nome        VARCHAR(120) NOT NULL,
    Secao       VARCHAR(80) NOT NULL,
    NivelMin    INTEGER NOT NULL DEFAULT 1,
    GateTag     VARCHAR(80),
    Descricao   TEXT
);
CREATE TABLE IF NOT EXISTS TB_PersonagemSegredoMistico (
    Id            INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem INTEGER NOT NULL,
    Id_Segredo    INTEGER NOT NULL,
    SlotIndex     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (Id_Personagem, SlotIndex),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem),
    FOREIGN KEY (Id_Segredo) REFERENCES TB_SegredoMistico(Id_Segredo)
);
""")
print("Schema OK")

# 2) Catálogo
ins = 0
for s in SEGREDOS:
    nv_min, gate = SECAO_META.get(s["secao"], (1, None))
    if cur.execute("SELECT 1 FROM TB_SegredoMistico WHERE Slug=?", (s["slug"],)).fetchone():
        continue
    cur.execute(
        """INSERT INTO TB_SegredoMistico (Slug, Nome, Secao, NivelMin, GateTag, Descricao)
           VALUES (?,?,?,?,?,?)""",
        (s["slug"], s["nome"], s["secao"], nv_min, gate, s["descricao"]),
    )
    ins += 1
print(f"Catálogo: {ins} inseridos / {len(SEGREDOS) - ins} existiam (total {len(SEGREDOS)})")

# 3) Tag flat 'segredos-misticos' na hab id=1533
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=1533",
            ('["segredos-misticos"]',))
print("Hab id=1533 'Segredos Místicos': TagsJSON=['segredos-misticos']")

conn.commit()
print("\n=== STATS por seção ===")
for r in cur.execute("SELECT Secao, COUNT(*) FROM TB_SegredoMistico GROUP BY Secao ORDER BY MIN(Id_Segredo)"):
    print(f"  {r[0]:<55} ({r[1]})")
conn.close()
print("\nDONE.")
