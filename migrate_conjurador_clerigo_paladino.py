"""Adiciona tag categórica `conjurador` nas habs de Conjuração do Clérigo e Paladino.

  - hab 1307 Clérigo Nv 1 'Conjuração'
  - hab 1228 Paladino Nv 1 'Conjuração'

Skipa hab 310 (Mago · Conjurador 'Mestre da Conjuração' Nv 14) — não concede
conjuração base, é upgrade. Mago Nv 1 já tem `conjurador`.

Idempotente: preserva tags existentes, evita duplicar.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
HABS = [1307, 1228]
NOVA_TAG = "conjurador"

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for hid in HABS:
    r = cur.execute(
        "SELECT Id_Habilidade, Nome, TagsJSON FROM TB_ClasseHabilidade WHERE Id_Habilidade=?",
        (hid,),
    ).fetchone()
    if not r:
        print(f"  hab {hid}: nao encontrada — skip")
        continue
    try:
        tags = json.loads(r['TagsJSON'] or "[]") or []
    except (json.JSONDecodeError, TypeError):
        tags = []
    ja_tem = NOVA_TAG in [t for t in tags if isinstance(t, str)]
    if ja_tem:
        print(f"  hab {hid} '{r['Nome']}': ja tem '{NOVA_TAG}' — skip")
        continue
    tags.append(NOVA_TAG)
    cur.execute(
        "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
        (json.dumps(tags, ensure_ascii=False), hid),
    )
    print(f"  hab {hid} '{r['Nome']}': TagsJSON={json.dumps(tags, ensure_ascii=False)}")

conn.commit()
conn.close()
print('OK')
