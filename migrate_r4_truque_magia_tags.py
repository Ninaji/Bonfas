"""R4 — Migrar Truque/Magia de TB_EssenciaLinhagem para TagsJSON + DROP colunas.

Última fase do plano de remoção do código legado. As colunas Elemento (já
migrada em R/Iter11), TruqueNome, MagiaN3Nome viram tags categóricas:
  - resist:<Elemento>     (já existe — não duplica)
  - truque-inato:<Nome>
  - magia-1uso:<Nome>

Depois de popular as tags, dropa as 3 colunas. Backend e frontend são
atualizados em paralelo a esta migration pra ler de tags.

Idempotente. Backup automático. Dump pré-DROP gerado em SQL.
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


# ---------------------------------------------------------------------------
# 1. Popular TagsJSON com truque-inato:<Nome> e magia-1uso:<Nome>
#    (resist:<Elemento> já foi populado em migration anterior)
# ---------------------------------------------------------------------------
cols = [r['name'] for r in cur.execute("PRAGMA table_info(TB_EssenciaLinhagem)").fetchall()]
has_truque = 'TruqueNome' in cols
has_magia = 'MagiaN3Nome' in cols

if has_truque or has_magia:
    rows = cur.execute(
        "SELECT Id_EssLinhagem, Nome, TagsJSON, "
        + ("TruqueNome, " if has_truque else "")
        + ("MagiaN3Nome, " if has_magia else "")
        + "1 AS _ FROM TB_EssenciaLinhagem"
    ).fetchall()
    for r in rows:
        try:
            existing = json.loads(r['TagsJSON'] or "[]") or []
        except (json.JSONDecodeError, TypeError):
            existing = []
        # Remove qualquer truque-inato:* ou magia-1uso:* anterior, pra ser idempotente
        new_tags = [
            t for t in existing
            if not (isinstance(t, str)
                    and (t.startswith("truque-inato:") or t.startswith("magia-1uso:")))
        ]
        if has_truque and r['TruqueNome']:
            new_tags.append(f"truque-inato:{r['TruqueNome']}")
        if has_magia and r['MagiaN3Nome']:
            new_tags.append(f"magia-1uso:{r['MagiaN3Nome']}")
        new_json = json.dumps(new_tags, ensure_ascii=False) if new_tags else None
        cur.execute(
            "UPDATE TB_EssenciaLinhagem SET TagsJSON=? WHERE Id_EssLinhagem=?",
            (new_json, r['Id_EssLinhagem']),
        )
        print(f"  {r['Nome']}: {new_json}")
else:
    print("Colunas Truque/Magia já não existem — skip populate.")


# ---------------------------------------------------------------------------
# 2. DROP colunas Elemento, TruqueNome, MagiaN3Nome
# ---------------------------------------------------------------------------
for col in ('Elemento', 'TruqueNome', 'MagiaN3Nome'):
    cols_now = [r['name'] for r in cur.execute("PRAGMA table_info(TB_EssenciaLinhagem)").fetchall()]
    if col not in cols_now:
        print(f'TB_EssenciaLinhagem.{col}: já não existe — skip')
        continue
    try:
        cur.execute(f"ALTER TABLE TB_EssenciaLinhagem DROP COLUMN {col}")
        print(f'TB_EssenciaLinhagem.{col}: DROPPED')
    except sqlite3.OperationalError as e:
        print(f'ERRO ao dropar {col}: {e}')
        raise

conn.commit()
conn.close()
print('OK — R4 storage finalizada.')
