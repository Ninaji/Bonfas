"""Adiciona `cond-immune:Amedrontado` na hab Aura da Coragem (Id 1242, Paladino Nv 10).

PHB 2024 Aura of Courage: Paladino e aliados na aura são imunes a Amedrontado.
Modelagem mínima: tag de imunidade no Paladino dono da hab. Aliados ficam fora
do escopo (sistema não modela auras-de-grupo ainda).

Idempotente: preserva tags existentes, evita duplicar `cond-immune:Amedrontado`.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
HID = 1242
NOVA_TAG = "cond-immune:Amedrontado"

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

r = cur.execute(
    "SELECT Id_Habilidade, Nome, TagsJSON FROM TB_ClasseHabilidade WHERE Id_Habilidade=?",
    (HID,),
).fetchone()
if not r:
    raise SystemExit(f'Hab {HID} nao encontrada')
print(f"Antes: hab {r['Id_Habilidade']} '{r['Nome']}' TagsJSON={r['TagsJSON']!r}")

try:
    tags = json.loads(r['TagsJSON'] or "[]") or []
except (json.JSONDecodeError, TypeError):
    tags = []
ja_tem = any(
    (t == NOVA_TAG) or (isinstance(t, dict) and t.get("tag") == NOVA_TAG)
    for t in tags
)
if ja_tem:
    print(f"Ja tem '{NOVA_TAG}' — skip")
else:
    tags.append(NOVA_TAG)
    cur.execute(
        "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
        (json.dumps(tags, ensure_ascii=False), HID),
    )
    print(f"Depois: TagsJSON={json.dumps(tags, ensure_ascii=False)}")

conn.commit()
conn.close()
print('OK')
