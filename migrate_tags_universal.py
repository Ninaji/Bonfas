"""Adiciona TagsJSON em todas as tabelas-mãe e cria TB_PersonagemEscolhaTag.

Implementa Fase 1 da Regra de Tags Universais — toda tag deve funcionar idêntico
em qualquer fonte: classe, subclasse, raça, linhagem, essência, sub-linhagem
da essência, item.

Operações:
  1. ALTER TABLE TB_Raca              ADD COLUMN TagsJSON TEXT NULL
  2. ALTER TABLE TB_Linhagem          ADD COLUMN TagsJSON TEXT NULL
  3. ALTER TABLE TB_Classe            ADD COLUMN TagsJSON TEXT NULL
  4. ALTER TABLE TB_Subclasse         ADD COLUMN TagsJSON TEXT NULL
  5. ALTER TABLE TB_Essencia          ADD COLUMN TagsJSON TEXT NULL
  6. ALTER TABLE TB_EssenciaLinhagem  ADD COLUMN TagsJSON TEXT NULL
  7. ALTER TABLE TB_Item              ADD COLUMN TagsJSON TEXT NULL
  8. CREATE TABLE TB_PersonagemEscolhaTag (storage genérico de pick em traço)

Idempotente: verifica PRAGMA table_info antes de cada ALTER. Backup automático.

Ver: docs/regra-tags-universais.md §3 (matriz de fontes).
"""
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


def has_column(table: str, column: str) -> bool:
    rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r['name'] == column for r in rows)


# ---------------------------------------------------------------------------
# 1-6. ALTER TABLE ... ADD COLUMN TagsJSON TEXT NULL (idempotente)
# ---------------------------------------------------------------------------
TABELAS_TAGS = [
    'TB_Raca',
    'TB_Linhagem',
    'TB_Classe',
    'TB_Subclasse',
    'TB_Essencia',
    'TB_EssenciaLinhagem',
    'TB_Item',
]

for tbl in TABELAS_TAGS:
    if has_column(tbl, 'TagsJSON'):
        print(f'{tbl}.TagsJSON: já existe — skip')
        continue
    cur.execute(f'ALTER TABLE {tbl} ADD COLUMN TagsJSON TEXT NULL')
    print(f'{tbl}.TagsJSON: ADICIONADO')


# ---------------------------------------------------------------------------
# 7. TB_PersonagemEscolhaTag — storage genérico de picks vindos de tags
#    Resolve a pendência §7 da regra-tags-universais.md (storage de pick em
#    traço para save-prof-vontade: e qualquer pick:* futuro com cascata).
#
#    Schema:
#      Id_Personagem  — FK lógica para TB_Personagem
#      Origem         — nome literal do traço/hab/talento que emitiu o pick
#                       (string para casar com convenção de TB_PersonagemEscolhaPericia)
#      Tipo           — prefixo da tag que gerou o pick (ex: 'save-prof-vontade')
#      SlotIndex      — posição linear quando a tag pede N picks
#      Valor          — valor escolhido (ex: 'Sabedoria', 'Atletismo')
#      PK composta — um valor por (personagem, origem, tipo, slot)
# ---------------------------------------------------------------------------
cur.execute(
    """CREATE TABLE IF NOT EXISTS TB_PersonagemEscolhaTag (
        Id_Personagem INTEGER     NOT NULL,
        Origem        VARCHAR(150) NOT NULL,
        Tipo          VARCHAR(50)  NOT NULL,
        SlotIndex     INTEGER      NOT NULL,
        Valor         VARCHAR(150) NOT NULL,
        PRIMARY KEY (Id_Personagem, Origem, Tipo, SlotIndex)
    )"""
)
print('TB_PersonagemEscolhaTag: criada (ou já existia)')

cur.execute(
    'CREATE INDEX IF NOT EXISTS idx_pet_pid_tipo '
    'ON TB_PersonagemEscolhaTag(Id_Personagem, Tipo)'
)
print('idx_pet_pid_tipo: criado (ou já existia)')


conn.commit()
conn.close()
print('OK')
