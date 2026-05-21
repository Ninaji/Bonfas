"""ALTER UNIQUE constraint em TB_PersonagemHabilidadeOpcao.

Antes: UNIQUE(Id_Personagem, Id_Habilidade) — bloqueia múltiplos slots da
mesma hab pelo mesmo personagem. Necessário pra cascade (Doutrina Marcial
slot 0 + slot 1 são da MESMA hab).

Depois: UNIQUE(Id_Personagem, Id_Habilidade, SlotIndex).
"""
import shutil
import sqlite3
import time

DB = 'bonfas.db'
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
cur = conn.cursor()

# SQLite não suporta ALTER UNIQUE direto — recria a tabela.
cur.execute("PRAGMA foreign_keys=OFF")
cur.execute("BEGIN")
try:
    cur.execute("""
        CREATE TABLE TB_PersonagemHabilidadeOpcao_new (
            Id             INTEGER PRIMARY KEY AUTOINCREMENT,
            Id_Personagem  INTEGER NOT NULL,
            Id_Habilidade  INTEGER NOT NULL,
            Texto          TEXT NOT NULL,
            Id_Opcao       INTEGER NULL,
            SlotIndex      INTEGER NULL,
            FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE,
            FOREIGN KEY (Id_Habilidade) REFERENCES TB_ClasseHabilidade(Id_Habilidade) ON DELETE CASCADE,
            UNIQUE (Id_Personagem, Id_Habilidade, SlotIndex)
        )
    """)
    cur.execute("""
        INSERT INTO TB_PersonagemHabilidadeOpcao_new
            (Id, Id_Personagem, Id_Habilidade, Texto, Id_Opcao, SlotIndex)
        SELECT Id, Id_Personagem, Id_Habilidade, Texto, Id_Opcao, SlotIndex
        FROM TB_PersonagemHabilidadeOpcao
    """)
    cur.execute("DROP TABLE TB_PersonagemHabilidadeOpcao")
    cur.execute("ALTER TABLE TB_PersonagemHabilidadeOpcao_new RENAME TO TB_PersonagemHabilidadeOpcao")
    cur.execute("CREATE INDEX idx_pho_id_opcao ON TB_PersonagemHabilidadeOpcao(Id_Opcao)")
    cur.execute("CREATE INDEX idx_pho_pid_hid_slot ON TB_PersonagemHabilidadeOpcao(Id_Personagem, Id_Habilidade, SlotIndex)")
    conn.commit()
    print('UNIQUE atualizado pra (Id_Personagem, Id_Habilidade, SlotIndex)')
except Exception as e:
    conn.rollback()
    print(f'ERRO: {e}')
    raise
finally:
    cur.execute("PRAGMA foreign_keys=ON")

conn.close()
print('OK')
