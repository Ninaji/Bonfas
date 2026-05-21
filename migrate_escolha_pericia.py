"""Cria TB_PersonagemEscolhaPericia + migra escolhas atuais do Frosty.

Modelo:
  - TB_PersonagemPericia.Proficiente/Expertise = "base" (classe + background)
  - TB_PersonagemEscolhaPericia = picks adicionais via traços/habs/talentos com tags pick:*
  - Backend merge: Proficiente_efetiva = base OR exists(escolha)

Frosty migration:
  - Investigação (Id_Pericia=9) e Natureza (Id_Pericia=11) estão em base.Proficiente=1
  - Esses são na verdade picks do Humano "Habilidoso" — mover pra escolha
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

# 1. Schema
cur.execute(
    """CREATE TABLE IF NOT EXISTS TB_PersonagemEscolhaPericia (
        Id_Personagem INTEGER NOT NULL,
        Origem        VARCHAR(100) NOT NULL,
        SlotIndex     INTEGER NOT NULL,
        Id_Pericia    INTEGER NOT NULL,
        Tipo          VARCHAR(20) DEFAULT 'proficiencia',
        PRIMARY KEY (Id_Personagem, Origem, SlotIndex),
        FOREIGN KEY (Id_Pericia) REFERENCES TB_PersonagemPericia(Id_Pericia)
    )"""
)
print('TB_PersonagemEscolhaPericia: criada (ou já existe)')

# 2. Frosty migration — só uma vez (idempotente: skip se já tem escolha Habilidoso)
exist = cur.execute(
    "SELECT COUNT(*) AS n FROM TB_PersonagemEscolhaPericia "
    "WHERE Id_Personagem=2 AND Origem='Habilidoso'"
).fetchone()
if exist['n'] > 0:
    print(f"Frosty já tem {exist['n']} escolhas Habilidoso — skip migration")
else:
    # Investigação=9, Natureza=11 estavam marcados Proficiente=1 (base) — mover pra escolha
    cur.execute(
        "INSERT INTO TB_PersonagemEscolhaPericia "
        "(Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo) VALUES (?,?,?,?,?)",
        (2, 'Habilidoso', 0, 9, 'proficiencia'),
    )
    cur.execute(
        "INSERT INTO TB_PersonagemEscolhaPericia "
        "(Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo) VALUES (?,?,?,?,?)",
        (2, 'Habilidoso', 1, 11, 'proficiencia'),
    )
    # zerar base prof dessas 2 (a derivada via escolha vai colocar Proficiente=1 no payload)
    cur.execute(
        "UPDATE TB_PersonagemPericia SET Proficiente=0 "
        "WHERE Id_Personagem=2 AND Id_Pericia IN (9, 11)"
    )
    print('Frosty: 2 escolhas Habilidoso (Investigação slot 0, Natureza slot 1) inseridas')

conn.commit()
conn.close()
print('OK')
