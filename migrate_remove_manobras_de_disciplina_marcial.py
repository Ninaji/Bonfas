"""Remove tag `+manobras` errônea da Disciplina Marcial (hab 515).

Erro de domínio: interpretei "Maestria de Armas" como soma a Manobras
Conhecidas. São contadores DIFERENTES no PHB 2024 / Bonfire Tales:
  - Manobras Conhecidas: ações táticas catalogadas (TB_Manobra). Fighter Nv 20 = 8.
  - Maestrias de Armas: armas com propriedade "mastery" (Vex/Sap/Push/etc).
    Fighter Nv 20 = 6. Sistema legado em TB_PersonagemMaestriaArma cuida disso.

A tag `+manobras:N` em si continua válida como princípio universal pra
qualquer fonte que CONCEDE manobras adicionais — só não é o caso de
Maestria de Armas.

Idempotente. Backup automático.
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


def _is_more_manobras(tag) -> bool:
    """Detecta tag '+manobras:*' (string ou objeto)."""
    if isinstance(tag, str):
        return tag.startswith("+manobras:") or tag == "+manobras"
    if isinstance(tag, dict):
        t = tag.get("tag")
        return isinstance(t, str) and (t.startswith("+manobras:") or t == "+manobras")
    return False


# Remove `+manobras` de QUALQUER hab que tenha. Hoje só hab 515 está com.
afetadas = 0
removidas_total = 0
rows = cur.execute(
    "SELECT Id_Habilidade, Nome, TagsJSON FROM TB_ClasseHabilidade WHERE TagsJSON IS NOT NULL"
).fetchall()
for r in rows:
    try:
        tags = json.loads(r['TagsJSON']) or []
    except (json.JSONDecodeError, TypeError):
        continue
    novo = [t for t in tags if not _is_more_manobras(t)]
    if len(novo) == len(tags):
        continue
    afetadas += 1
    removidas_total += (len(tags) - len(novo))
    novo_json = json.dumps(novo, ensure_ascii=False) if novo else None
    cur.execute(
        "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
        (novo_json, r['Id_Habilidade']),
    )
    print(f"  hab {r['Id_Habilidade']:3} '{r['Nome']}': removidas {len(tags)-len(novo)} tag(s) +manobras")

conn.commit()
conn.close()
print(f'OK - {afetadas} hab(s) atualizada(s), {removidas_total} tag(s) removida(s).')
