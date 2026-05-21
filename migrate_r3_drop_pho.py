"""R3 — DROP TB_PersonagemHabilidadeOpcao + remover coluna OpcaoTipoJSON.

Parte do plano de remoção do código legado. R1 migrou os dados para
TB_PersonagemEscolhaTag; R2 atualizou _processa_vontade_tags pra ler de lá;
fmtHab/endpoints removidos no código. Esta migration finaliza a remoção
dropando o storage legado.

ROLLBACK: backup do DB em bonfas.db.bak.<ts>. Pra reverter, restaurar arquivo.
Adicionalmente, antes do DROP, exporta o conteúdo de PHO em
`_legacy_pho_dump.sql` pra inspeção/rollback granular.

Idempotente — se a tabela ou coluna já não existem, skipa silenciosamente.
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

# ---------------------------------------------------------------------------
# 1. Dump TB_PersonagemHabilidadeOpcao para arquivo (rollback granular)
# ---------------------------------------------------------------------------
exists = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='TB_PersonagemHabilidadeOpcao'"
).fetchone()
if exists:
    rows = cur.execute(
        "SELECT * FROM TB_PersonagemHabilidadeOpcao ORDER BY Id"
    ).fetchall()
    dump_path = f'_legacy_pho_dump_{ts}.sql'
    with open(dump_path, 'w', encoding='utf-8') as f:
        f.write('-- Dump pré-DROP de TB_PersonagemHabilidadeOpcao\n')
        f.write(f'-- Timestamp: {ts}\n')
        f.write(f'-- Total rows: {len(rows)}\n\n')
        for r in rows:
            d = dict(r)
            cols = ", ".join(d.keys())
            vals = ", ".join(
                "NULL" if v is None else
                str(v) if isinstance(v, (int, float)) else
                "'" + str(v).replace("'", "''") + "'"
                for v in d.values()
            )
            f.write(f"INSERT INTO TB_PersonagemHabilidadeOpcao ({cols}) VALUES ({vals});\n")
    print(f'Dump PHO: {dump_path} ({len(rows)} rows)')

    cur.execute("DROP TABLE TB_PersonagemHabilidadeOpcao")
    print('TB_PersonagemHabilidadeOpcao: DROPPED')
else:
    print('TB_PersonagemHabilidadeOpcao: já não existe — skip')


# ---------------------------------------------------------------------------
# 2. Remover coluna TB_ClasseHabilidade.OpcaoTipoJSON
#    (SQLite 3.35+ suporta ALTER TABLE DROP COLUMN; Python 3.14 vem com 3.46+)
# ---------------------------------------------------------------------------
cols = [r['name'] for r in cur.execute(
    "PRAGMA table_info(TB_ClasseHabilidade)"
).fetchall()]
if 'OpcaoTipoJSON' in cols:
    try:
        cur.execute("ALTER TABLE TB_ClasseHabilidade DROP COLUMN OpcaoTipoJSON")
        print('TB_ClasseHabilidade.OpcaoTipoJSON: DROPPED via ALTER')
    except sqlite3.OperationalError as e:
        # SQLite antigo — fallback recreate-table.
        print(f'ALTER falhou ({e}) — fallback recreate-table.')
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("BEGIN")
        # Recreate sem OpcaoTipoJSON, preservando outras colunas e dados
        cur.execute("""
            CREATE TABLE TB_ClasseHabilidade_new (
                Id_Habilidade   INTEGER PRIMARY KEY AUTOINCREMENT,
                Id_Classe       INTEGER NOT NULL,
                Id_Subclasse    INTEGER,
                Nome            VARCHAR(150) NOT NULL,
                Descricao       TEXT NOT NULL,
                NivelAdquirido  INTEGER NOT NULL,
                TemEscolha      INTEGER,
                TagsJSON        TEXT,
                FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
                FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            INSERT INTO TB_ClasseHabilidade_new
                (Id_Habilidade, Id_Classe, Id_Subclasse, Nome, Descricao,
                 NivelAdquirido, TemEscolha, TagsJSON)
            SELECT Id_Habilidade, Id_Classe, Id_Subclasse, Nome, Descricao,
                   NivelAdquirido, TemEscolha, TagsJSON
            FROM TB_ClasseHabilidade
        """)
        cur.execute("DROP TABLE TB_ClasseHabilidade")
        cur.execute("ALTER TABLE TB_ClasseHabilidade_new RENAME TO TB_ClasseHabilidade")
        cur.execute("CREATE INDEX idx_habil_classe ON TB_ClasseHabilidade(Id_Classe, NivelAdquirido)")
        cur.execute("PRAGMA foreign_keys=ON")
        print('TB_ClasseHabilidade.OpcaoTipoJSON: DROPPED via recreate')
else:
    print('TB_ClasseHabilidade.OpcaoTipoJSON: já não existe — skip')


conn.commit()
conn.close()
print('OK — R3 storage finalizada.')
