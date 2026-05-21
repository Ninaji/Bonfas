"""Migration: AumentoAtributo em TB_PersonagemTalento.

Idempotente. Tambem atualiza atributos da Frosty (id=2) pra base 15/8/15/15/8/8
conforme observacao do usuario sobre a ficha oficial.
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def col_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def main() -> int:
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    if not col_exists(cur, "TB_PersonagemTalento", "AumentoAtributo"):
        cur.execute("ALTER TABLE TB_PersonagemTalento ADD COLUMN AumentoAtributo VARCHAR(10) NULL")
        print("ALTER: TB_PersonagemTalento.AumentoAtributo")
    else:
        print("skip: AumentoAtributo já existe")

    # Reset Frosty base atributos (sem incluir bonuses de talentos/background)
    cur.execute(
        "UPDATE TB_PersonagemAtributo SET "
        "Forca=15, Destreza=8, Constituicao=15, Inteligencia=15, Sabedoria=8, Carisma=8 "
        "WHERE Id_Personagem=2"
    )
    print(f"UPDATE Frosty atributos base: {cur.rowcount} row(s)")

    conn.commit()
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
