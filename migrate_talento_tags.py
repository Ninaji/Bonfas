"""Tags em TB_TalentoRacial (talentos de raça/essência).

Tags suportadas para movimento:
  - andar:<Xft>  — override base de caminhada (ex.: anão andar:25ft)
  - voar:<Xft|eq>   — Asas da Condenação: voar:eq
  - nadar:<Xft|eq>
  - cavar:<Xft|eq>

Idempotente.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def merge_tags(raw_existing: str | None, novas: list[str]) -> str:
    existing: list[str] = []
    if raw_existing:
        try:
            loaded = json.loads(raw_existing)
            if isinstance(loaded, list):
                existing = [t for t in loaded if isinstance(t, str)]
        except (json.JSONDecodeError, TypeError):
            pass
    seen, out = set(), []
    for t in existing + novas:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return json.dumps(out, ensure_ascii=False)


TAGS_BY_NOME = {
    'Asas da Condenação':  ['voar:eq'],
    # outros candidatos quando o catálogo crescer:
    #   'Talento de Voo':     ['voar:30ft']
    #   'Camuflagem Anfíbia': ['nadar:eq']
    #   'Cavadora':           ['cavar:20ft']
}

aplicados = 0
for nome, tags in TAGS_BY_NOME.items():
    rows_q = cur.execute(
        'SELECT Id_TalentoRacial, TagsJSON FROM TB_TalentoRacial WHERE Nome=?', (nome,)
    ).fetchall()
    for r in rows_q:
        merged = merge_tags(r['TagsJSON'], tags)
        cur.execute(
            'UPDATE TB_TalentoRacial SET TagsJSON=? WHERE Id_TalentoRacial=?',
            (merged, r['Id_TalentoRacial']),
        )
        aplicados += 1
        print(f'  [{nome}] id={r["Id_TalentoRacial"]} -> {merged}')

conn.commit()
print(f'Total: {aplicados} talento(s)')
conn.close()
print('OK')
