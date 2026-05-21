"""
Migration: Talento de Origem.

- Adiciona Id_TalentoOrigem em TB_PersonagemEscolha (FK para TB_OpcaoJogo).
- Adiciona MagiaExpandidaJSON em TB_OpcaoJogo (lista de {nome, nome_ingles, nivel, fonte_lista}).

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
    if not DB.exists():
        print(f"ERRO: {DB} nao existe", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    if not col_exists(cur, "TB_PersonagemEscolha", "Id_TalentoOrigem"):
        cur.execute("ALTER TABLE TB_PersonagemEscolha ADD COLUMN Id_TalentoOrigem INTEGER NULL")
        print("ALTER: TB_PersonagemEscolha.Id_TalentoOrigem")
    else:
        print("skip: Id_TalentoOrigem ja existe")

    if not col_exists(cur, "TB_OpcaoJogo", "MagiaExpandidaJSON"):
        cur.execute("ALTER TABLE TB_OpcaoJogo ADD COLUMN MagiaExpandidaJSON TEXT NULL")
        print("ALTER: TB_OpcaoJogo.MagiaExpandidaJSON")
    else:
        print("skip: MagiaExpandidaJSON ja existe")

    conn.commit()
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
