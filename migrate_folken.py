"""Popular raça Folken + 5 linhagens + 18 traços + 27 talentos no DB.

Lê de folken_parsed.json (gerado por parse_folken.py).
Idempotente via Slug UNIQUE em TB_Raca/Linhagem/Talento.
"""
import json
import re
import shutil
import sqlite3
import time
from pathlib import Path

DB = 'bonfas.db'
DATA_PATH = Path('folken_parsed.json')

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

data = json.loads(DATA_PATH.read_text(encoding='utf-8'))

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[áàâãä]", "a", s); s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s); s = re.sub(r"[óòôõö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s); s = re.sub(r"[ç]", "c", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# 1. Inserir raça
existing = cur.execute("SELECT Id_Raca FROM TB_Raca WHERE Slug=?", ("folken",)).fetchone()
if existing:
    id_raca = existing['Id_Raca']
    print(f"Raça Folken já existe (id={id_raca})")
else:
    cur.execute(
        "INSERT INTO TB_Raca (Nome, Slug, Tagline, PermiteEssencia) VALUES (?,?,?,1)",
        ("Folken", "folken", "Pequenos, sortudos, geniais."),
    )
    id_raca = cur.lastrowid
    print(f"Raça Folken inserida (id={id_raca})")

# 2. Linhagens
linhagens_ids = {}
for lin in data['linhagens']:
    slug = lin['slug']
    existing = cur.execute(
        "SELECT Id_Linhagem FROM TB_Linhagem WHERE Id_Raca=? AND Slug=?",
        (id_raca, slug),
    ).fetchone()
    if existing:
        linhagens_ids[lin['nome']] = existing['Id_Linhagem']
        continue
    cur.execute(
        "INSERT INTO TB_Linhagem (Id_Raca, Nome, Slug, Descricao) VALUES (?,?,?,?)",
        (id_raca, lin['nome'], slug, lin.get('tagline', '')),
    )
    linhagens_ids[lin['nome']] = cur.lastrowid
    print(f"  + linhagem {lin['nome']} id={cur.lastrowid}")

# 3. Traços base (Id_Linhagem=NULL, Id_Essencia=NULL) e por linhagem
def insert_traco(nome, descricao, id_lin=None, nivel=1):
    existing = cur.execute(
        "SELECT Id_Traco FROM TB_TracoRacial WHERE Id_Raca=? AND Nome=? AND "
        "(Id_Linhagem IS ? OR Id_Linhagem=?)",
        (id_raca, nome, id_lin, id_lin),
    ).fetchone()
    if existing:
        return existing['Id_Traco']
    cur.execute(
        """INSERT INTO TB_TracoRacial (Id_Raca, Id_Linhagem, Nome, Descricao, NivelRequisito)
           VALUES (?,?,?,?,?)""",
        (id_raca, id_lin, nome, descricao or '', nivel),
    )
    return cur.lastrowid

for t in data['tracos_base']:
    insert_traco(t['nome'], t['descricao'])
    print(f"  traco base + {t['nome']}")

for lin_nome, tracos in data['tracos_linhagem'].items():
    id_lin = linhagens_ids.get(lin_nome)
    if not id_lin: continue
    for t in tracos:
        insert_traco(t['nome'], t['descricao'], id_lin=id_lin)
    print(f"  linhagem {lin_nome}: {len(tracos)} tracos")

# 4. Talentos racial (Evolução Racial — Folken). NivelMinimo=1 default (refinar depois).
for tal in data['talentos']:
    nome = tal['nome']
    slug = slugify(nome)
    existing = cur.execute(
        "SELECT Id_TalentoRacial FROM TB_TalentoRacial WHERE Slug=?",
        (slug,),
    ).fetchone()
    if existing:
        continue
    cur.execute(
        """INSERT INTO TB_TalentoRacial (Nome, Slug, TagsJSON, NivelMinimo, Descricao, Fonte)
           VALUES (?,?,?,?,?,?)""",
        (nome, slug, json.dumps(["folken"]), 1, tal.get('descricao', ''), 'folken'),
    )
print(f"Talentos racial Folken: {len(data['talentos'])} processados")

conn.commit()
conn.close()
print('OK')
