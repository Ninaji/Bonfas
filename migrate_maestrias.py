"""
Cria tabelas para Maestrias de Armas:
  TB_Arma                    - catalogo de armas (Adaga, Espada Longa, etc.)
  TB_Maestria                - catalogo de maestrias (Cortar/Nick, Vexar/Vex, etc.)
  TB_PersonagemMaestriaArma  - escolhas do personagem (arma + maestria + slot)

Idempotente: usa CREATE TABLE IF NOT EXISTS.
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def main() -> int:
    if not DB.exists():
        print(f"ERRO: {DB} nao existe", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS TB_Arma (
            Id_Arma     INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome        VARCHAR(150) NOT NULL,
            Slug        VARCHAR(150) NOT NULL UNIQUE,
            Categoria   VARCHAR(50)  NOT NULL,
            Preco       VARCHAR(40),
            Dano        VARCHAR(60),
            Propriedades TEXT,
            MaestriasJSON TEXT NOT NULL DEFAULT '[]',
            Fonte       VARCHAR(100)
        )
    """)
    print("[1] TB_Arma ok")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS TB_Maestria (
            Id_Maestria INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome        VARCHAR(100) NOT NULL,
            NomeIngles  VARCHAR(100),
            Slug        VARCHAR(150) NOT NULL UNIQUE,
            Efeito      TEXT NOT NULL,
            Fonte       VARCHAR(100)
        )
    """)
    print("[2] TB_Maestria ok")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS TB_PersonagemMaestriaArma (
            Id            INTEGER PRIMARY KEY AUTOINCREMENT,
            Id_Personagem INTEGER NOT NULL,
            Id_Arma       INTEGER NOT NULL,
            Id_Maestria   INTEGER,
            SlotIndex     INTEGER,
            FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE,
            FOREIGN KEY (Id_Arma)       REFERENCES TB_Arma(Id_Arma) ON DELETE CASCADE,
            FOREIGN KEY (Id_Maestria)   REFERENCES TB_Maestria(Id_Maestria) ON DELETE CASCADE
        )
    """)
    print("[3] TB_PersonagemMaestriaArma ok")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_arma_categoria ON TB_Arma(Categoria)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_maestria_slug ON TB_Maestria(Slug)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pma_pid_slot ON TB_PersonagemMaestriaArma(Id_Personagem, SlotIndex)")

    conn.commit()
    print("[4] Indexes ok")

    cur.execute("SELECT COUNT(*) FROM TB_Arma")
    print(f"  TB_Arma rows: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM TB_Maestria")
    print(f"  TB_Maestria rows: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM TB_PersonagemMaestriaArma")
    print(f"  TB_PersonagemMaestriaArma rows: {cur.fetchone()[0]}")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
