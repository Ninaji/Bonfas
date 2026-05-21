"""Migration: TB_PersonagemEscolha.Id_TalentoOrigemExtra (bonus de Raízes Profundas).

Idempotente.
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
    if not col_exists(cur, "TB_PersonagemEscolha", "Id_TalentoOrigemExtra"):
        cur.execute("ALTER TABLE TB_PersonagemEscolha ADD COLUMN Id_TalentoOrigemExtra INTEGER NULL")
        print("ALTER: TB_PersonagemEscolha.Id_TalentoOrigemExtra")
    else:
        print("skip: já existe")
    conn.commit()
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
