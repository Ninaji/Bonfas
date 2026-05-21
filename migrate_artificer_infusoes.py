"""Campo "Infusões de Artificer" (Artífice, Id_Classe=1). Migração FOCADA
(sem wipe da classe). Faz três coisas:

1. Insere o catálogo de 42 Infusões em TB_OpcaoJogo (Tipo='infusao-artificer').
   NivelMinimo = nível de restrição (1 = sem restrição). PreReqTexto guarda o
   texto original ("—" ou "Artífice de Xº nível").

2. Marca a feature Nv 2 "Infusões" com a tag progressiva
   pick:infusao-artificer  n_por_nivel {2:4, 6:5, 10:6, 14:7, 18:8}
   (= coluna "Infusões Conhecidas" da tabela do Artífice).

3. Cria o talento "Infusão de Artificer" (Tipo='talento-geral') com tag
   pick:infusao-artificer:1 — cada cópia soma +1 slot (o renderer soma todos
   os tags pick:infusao-artificer, igual metamagia/estilo-danca).

O picker de cada slot oferece (a) infusões do catálogo filtradas por
NivelMinimo<=nível Artífice, ou (b) Replicar Item Mágico (item da página de
equipamentos, tratado como infusão). Backup automático.
"""
from __future__ import annotations
import json, re, shutil, sqlite3, sys, time, unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_ARTIFICE = 1

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

INFUSOES = json.loads(Path("infusoes_artificer.json").read_text(encoding="utf-8"))

# Progressão "Infusões Conhecidas" (Recursos Artificer.txt)
N_POR_NIVEL = {"2": 4, "6": 5, "10": 6, "14": 7, "18": 8}


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. Catálogo de Infusões em TB_OpcaoJogo ===
print("=== Catálogo de Infusões (TB_OpcaoJogo Tipo='infusao-artificer') ===")
ndel = cur.execute("DELETE FROM TB_OpcaoJogo WHERE Tipo='infusao-artificer'").rowcount
print(f"  limpas: {ndel}")
ins = 0
for inf in INFUSOES:
    slug = slugify(inf["nome"])
    desc = inf["desc"]
    # remove o prefixo "Pré-requisito: ..." do início da descrição
    desc = re.sub(r"^Pré-requisito:\s*[^.]*?\s*(?=[A-ZÀ-Ú])", "", desc, count=1).strip()
    cur.execute(
        """INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, PreReqTexto, NivelMinimo)
           VALUES (?,?,?,?,?,?)""",
        (inf["nome"], slug, "infusao-artificer", desc,
         inf["prereq_txt"], inf["nivel_minimo"]),
    )
    ins += 1
print(f"  inseridas: {ins}")
from collections import Counter
porn = Counter(i["nivel_minimo"] for i in INFUSOES)
print(f"  por nível de restrição: {dict(sorted(porn.items()))}")

# === 2. Tag progressiva na feature Nv 2 "Infusões" ===
print("\n=== Tag pick:infusao-artificer na feature 'Infusões' (Nv 2) ===")
tag = json.dumps([{"tag": "pick:infusao-artificer", "n_por_nivel": N_POR_NIVEL}],
                 ensure_ascii=False)
n = cur.execute(
    "UPDATE TB_ClasseHabilidade SET TagsJSON=? "
    "WHERE Id_Classe=? AND Nome='Infusões' AND Id_Subclasse IS NULL",
    (tag, ID_ARTIFICE),
).rowcount
print(f"  features atualizadas: {n}")
print(f"  tag: {tag}")

# === 3. Talento "Infusão de Artificer" (+1 slot) ===
print("\n=== Talento 'Infusão de Artificer' (talento-geral, +1) ===")
cur.execute("DELETE FROM TB_OpcaoJogo WHERE Tipo='talento-geral' AND Slug='infusao-de-artificer'")
cur.execute(
    """INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, TagsJSON, NivelMinimo)
       VALUES (?,?,?,?,?,?)""",
    ("Infusão de Artificer", "infusao-de-artificer", "talento-geral",
     "Você aprende os segredos da infusão arcana. Ganha +1 Infusão Conhecida "
     "(soma à progressão do Artífice). Pode ser tomado mais de uma vez; cada "
     "cópia concede +1 Infusão Conhecida.",
     json.dumps(["pick:infusao-artificer:1"], ensure_ascii=False), 1),
)
print("  talento criado: Infusão de Artificer -> pick:infusao-artificer:1")

conn.commit()

# === Validação ===
print("\n=== Validação ===")
tot = cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='infusao-artificer'").fetchone()[0]
print(f"  infusões no catálogo: {tot}")
chk = cur.execute(
    "SELECT TagsJSON FROM TB_ClasseHabilidade WHERE Id_Classe=1 AND Nome='Infusões' AND Id_Subclasse IS NULL"
).fetchone()
print(f"  Infusões TagsJSON: {chk[0] if chk else None}")
tal = cur.execute("SELECT Nome, TagsJSON FROM TB_OpcaoJogo WHERE Slug='infusao-de-artificer'").fetchone()
print(f"  talento: {tal}")

conn.close()
print("\nDONE.")
