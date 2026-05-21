"""Migra Elementos das sub-linhagens de essência para TagsJSON.

Hoje TB_EssenciaLinhagem.Elemento é fonte separada que o backend injeta direto
em state.resistencias. Pra a regra de tags universais valer, popular TagsJSON
com `resist:<Elemento_canonico>` em cada sub-linhagem.

Normalização contra ELEMENTOS_CANONICOS (5.5e BR):
  Trovão     → Trovejante
  Elétrico   → Raio (interpretação 5.5e)
  resto já é canônico (Fogo, Ácido, Frio).

A coluna Elemento também é atualizada pra ficar consistente com a tag — assim
o agregador deduplica corretamente em (tipo, elem.lower()) e auto_efeitos
mostra o nome canônico.

Idempotente. Backup automático.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'

ELEMENTOS_CANONICOS = frozenset({
    "Ácido", "Concussão", "Cortante", "Energia", "Fogo", "Frio",
    "Necrótico", "Perfurante", "Psíquico", "Radiante", "Raio",
    "Trovejante", "Veneno",
})

NORM = {
    "Trovão":   "Trovejante",
    "Elétrico": "Raio",
}

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

rows = cur.execute(
    "SELECT Id_EssLinhagem, Nome, Elemento, TagsJSON FROM TB_EssenciaLinhagem"
).fetchall()
for r in rows:
    elem_raw = (r['Elemento'] or '').strip()
    if not elem_raw:
        print(f"  id={r['Id_EssLinhagem']} {r['Nome']}: sem Elemento — skip")
        continue
    elem = NORM.get(elem_raw, elem_raw)
    if elem not in ELEMENTOS_CANONICOS:
        print(f"  id={r['Id_EssLinhagem']} {r['Nome']}: Elemento {elem_raw!r} não é canônico — skip")
        continue
    # Tags existentes: preserva, mas substitui qualquer resist:* por resist:<elem>.
    try:
        existing = json.loads(r['TagsJSON'] or '[]') or []
    except (json.JSONDecodeError, TypeError):
        existing = []
    new_tags = [t for t in existing
                if not (isinstance(t, str) and t.startswith('resist:'))]
    new_tags.append(f'resist:{elem}')
    new_json = json.dumps(new_tags, ensure_ascii=False)

    # UPDATE Elemento (canonical) + TagsJSON
    cur.execute(
        "UPDATE TB_EssenciaLinhagem SET Elemento=?, TagsJSON=? WHERE Id_EssLinhagem=?",
        (elem, new_json, r['Id_EssLinhagem']),
    )
    label = f"{elem_raw} -> {elem}" if elem_raw != elem else elem
    # print sem chars exoticos (Windows cp1252 estoura com seta unicode)
    print(f"  id={r['Id_EssLinhagem']:2} {r['Nome']:15} elem={label:25} TagsJSON={new_json}".encode('ascii', 'replace').decode('ascii'))

conn.commit()
conn.close()
print('OK')
