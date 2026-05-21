"""Schema + catálogo + tag para Inimigo Favorito (Caçador Nv 2).

Espelha o pattern de Segredos:
  - TB_InimigoFavorito (catálogo, 12 entries)
  - TB_PersonagemInimigoFavorito (escolhas)
  - Tag flat ["inimigo-favorito"] na hab id=123 (gate da section no front)

Limite/progressão já vem de TB_RecursoClasse "Inimigo Favorito" (1 Nv 2-5, 2 Nv 6-13, 3 Nv 14-20).
"""
import shutil
import sqlite3
import time

DB = "bonfas.db"
ID_HAB_INIM = 123  # Caçador Nv 2 Inimigo Favorito

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

INIMIGOS = [
    ("Aberrações",      "aberracoes"),
    ("Bestas",          "bestas"),
    ("Celestiais",      "celestiais"),
    ("Constructos",     "constructos"),
    ("Corruptores",     "corruptores"),
    ("Dragões",         "dragoes"),
    ("Elementais",      "elementais"),
    ("Fadas",           "fadas"),
    ("Gigantes",        "gigantes"),
    ("Humanoides",      "humanoides"),
    ("Monstruosidades", "monstruosidades"),
    ("Mortos-vivos",    "mortos-vivos"),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_InimigoFavorito (
    Id_InimigoFavorito INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome   VARCHAR(60) NOT NULL,
    Slug   VARCHAR(60) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS TB_PersonagemInimigoFavorito (
    Id            INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem INTEGER NOT NULL,
    Id_InimigoFavorito INTEGER NOT NULL,
    Id_Habilidade INTEGER,
    UNIQUE (Id_Personagem, Id_InimigoFavorito),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem),
    FOREIGN KEY (Id_InimigoFavorito) REFERENCES TB_InimigoFavorito(Id_InimigoFavorito)
);
""")
print("Schema OK")

ins = 0
for nome, slug in INIMIGOS:
    if not cur.execute("SELECT 1 FROM TB_InimigoFavorito WHERE Slug=?", (slug,)).fetchone():
        cur.execute("INSERT INTO TB_InimigoFavorito (Nome, Slug) VALUES (?,?)", (nome, slug))
        ins += 1
print(f"Catálogo: {ins} inseridos / {len(INIMIGOS) - ins} já existiam (total {len(INIMIGOS)})")

cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
            ('["inimigo-favorito"]', ID_HAB_INIM))
r = cur.execute("SELECT Nome, TagsJSON FROM TB_ClasseHabilidade WHERE Id_Habilidade=?", (ID_HAB_INIM,)).fetchone()
print(f"\nHab id={ID_HAB_INIM}: {r[0]} | tags={r[1]}")

conn.commit()
conn.close()
print("\nDONE.")
