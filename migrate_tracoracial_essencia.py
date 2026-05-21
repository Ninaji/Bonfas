"""
Migration: TB_TracoRacial passa a aceitar tracos puramente da essencia.

Mudancas:
- Id_Raca: agora NULLABLE (antes NOT NULL)
- +Id_EssLinhagem (nullable) para tracos especificos de sub-linhagem da essencia

Idempotente: detecta se ja foi aplicado pela presenca da coluna Id_EssLinhagem.
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

    if col_exists(cur, "TB_TracoRacial", "Id_EssLinhagem"):
        print("[skip] migration ja aplicada (Id_EssLinhagem ja existe)")
        return 0

    # Verifica se ha rows existentes
    cur.execute("SELECT COUNT(*) FROM TB_TracoRacial")
    n = cur.fetchone()[0]
    print(f"[1] Backup conceitual: {n} rows em TB_TracoRacial")

    cur.execute("BEGIN TRANSACTION")
    cur.execute("PRAGMA foreign_keys=OFF")

    cur.execute("""
        CREATE TABLE TB_TracoRacial_new (
            Id_Traco INTEGER PRIMARY KEY AUTOINCREMENT,
            Id_Raca INTEGER,
            Id_Linhagem INTEGER,
            Id_Essencia INTEGER,
            Id_EssLinhagem INTEGER,
            Nome VARCHAR(150) NOT NULL,
            Descricao TEXT NOT NULL,
            NivelRequisito INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (Id_Raca) REFERENCES TB_Raca(Id_Raca) ON DELETE CASCADE,
            FOREIGN KEY (Id_Linhagem) REFERENCES TB_Linhagem(Id_Linhagem) ON DELETE CASCADE,
            FOREIGN KEY (Id_Essencia) REFERENCES TB_Essencia(Id_Essencia) ON DELETE CASCADE,
            FOREIGN KEY (Id_EssLinhagem) REFERENCES TB_EssenciaLinhagem(Id_EssLinhagem) ON DELETE CASCADE
        )
    """)
    print("[2] Tabela nova criada")

    cur.execute("""
        INSERT INTO TB_TracoRacial_new (Id_Traco, Id_Raca, Id_Linhagem, Id_Essencia, Nome, Descricao, NivelRequisito)
        SELECT Id_Traco, Id_Raca, Id_Linhagem, Id_Essencia, Nome, Descricao, NivelRequisito FROM TB_TracoRacial
    """)
    print(f"[3] Migrados {cur.rowcount} rows")

    cur.execute("DROP TABLE TB_TracoRacial")
    cur.execute("ALTER TABLE TB_TracoRacial_new RENAME TO TB_TracoRacial")
    print("[4] Tabela renomeada")

    # indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_traco_raca ON TB_TracoRacial(Id_Raca)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_traco_linhagem ON TB_TracoRacial(Id_Linhagem)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_traco_essencia ON TB_TracoRacial(Id_Essencia)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_traco_esslinhagem ON TB_TracoRacial(Id_EssLinhagem)")

    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("COMMIT")

    print("[5] Verificacao")
    cur.execute("PRAGMA table_info(TB_TracoRacial)")
    for r in cur.fetchall():
        print(f"  {r}")
    cur.execute("SELECT COUNT(*) FROM TB_TracoRacial")
    print(f"  total rows: {cur.fetchone()[0]} (esperado {n})")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
