"""
Cria uma cópia minimalista `bonfas_classes.db` com APENAS as 6 tabelas
do ER de classes (imagem de referência):

    TB_Classe ── TB_Subclasse
          │             │
          ├── TB_RecursoClasse (Id_Classe, Id_Subclasse FK)
          ├── TB_ClasseHabilidade
          └── TB_AcessoOpcao ── TB_OpcaoJogo

Não mexe em bonfas.db. Só lê.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
SRC  = BASE / "bonfas.db"              # banco principal (leitura)
DEST = BASE / "bonfas_classes.db"      # cópia mínima (recriada)

DDL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS TB_AcessoOpcao;
DROP TABLE IF EXISTS TB_ClasseHabilidade;
DROP TABLE IF EXISTS TB_RecursoClasse;
DROP TABLE IF EXISTS TB_OpcaoJogo;
DROP TABLE IF EXISTS TB_Subclasse;
DROP TABLE IF EXISTS TB_Classe;

CREATE TABLE TB_Classe (
    Id_Classe  INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome       VARCHAR(100) NOT NULL,
    Slug       VARCHAR(100) NOT NULL UNIQUE,
    Tagline    VARCHAR(255)
);

CREATE TABLE TB_Subclasse (
    Id_Subclasse INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe    INTEGER NOT NULL,
    Nome         VARCHAR(100) NOT NULL,
    Slug         VARCHAR(100) NOT NULL,
    Tagline      VARCHAR(255),
    FOREIGN KEY (Id_Classe) REFERENCES TB_Classe(Id_Classe) ON DELETE CASCADE,
    UNIQUE (Id_Classe, Slug)
);

CREATE TABLE TB_OpcaoJogo (
    Id_Opcao  INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome      VARCHAR(150) NOT NULL,
    Slug      VARCHAR(150) NOT NULL UNIQUE,
    Tipo      VARCHAR(50)  NOT NULL,
    Descricao TEXT
);

CREATE TABLE TB_RecursoClasse (
    Id_Recurso   INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe    INTEGER NOT NULL,
    Id_Subclasse INTEGER,
    Nome         VARCHAR(100) NOT NULL,
    Slug         VARCHAR(100) NOT NULL,
    Nivel        INTEGER NOT NULL,
    Valor        VARCHAR(50),
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE
);

CREATE TABLE TB_ClasseHabilidade (
    Id_Habilidade  INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Classe      INTEGER NOT NULL,
    Id_Subclasse   INTEGER,
    Nome           VARCHAR(150) NOT NULL,
    Descricao      TEXT NOT NULL,
    NivelAdquirido INTEGER NOT NULL,
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE
);

CREATE TABLE TB_AcessoOpcao (
    Id_AcessoOpcao INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Opcao       INTEGER NOT NULL,
    Id_Classe      INTEGER,
    Id_Subclasse   INTEGER,
    FOREIGN KEY (Id_Opcao)     REFERENCES TB_OpcaoJogo(Id_Opcao)     ON DELETE CASCADE,
    FOREIGN KEY (Id_Classe)    REFERENCES TB_Classe(Id_Classe)       ON DELETE CASCADE,
    FOREIGN KEY (Id_Subclasse) REFERENCES TB_Subclasse(Id_Subclasse) ON DELETE CASCADE,
    UNIQUE (Id_Opcao, Id_Classe, Id_Subclasse)
);

CREATE INDEX idx_subclasse_classe ON TB_Subclasse(Id_Classe);
CREATE INDEX idx_recurso_classe   ON TB_RecursoClasse(Id_Classe, Nivel);
CREATE INDEX idx_hab_classe       ON TB_ClasseHabilidade(Id_Classe, NivelAdquirido);
CREATE INDEX idx_hab_sub          ON TB_ClasseHabilidade(Id_Subclasse);
CREATE INDEX idx_acesso_classe    ON TB_AcessoOpcao(Id_Classe);
CREATE INDEX idx_acesso_sub       ON TB_AcessoOpcao(Id_Subclasse);
"""


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"fonte não encontrada: {SRC}")
    if DEST.exists():
        DEST.unlink()
        print(f"- removido {DEST.name} anterior")

    dest = sqlite3.connect(DEST)
    dest.executescript(DDL)

    src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    # ---------- TB_Classe (só 3 colunas além do PK) ----------
    for r in src.execute("SELECT Id_Classe, Nome, Slug, Tagline FROM TB_Classe"):
        dest.execute(
            "INSERT INTO TB_Classe (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
            (r["Id_Classe"], r["Nome"], r["Slug"], r["Tagline"]),
        )

    # ---------- TB_Subclasse ----------
    for r in src.execute("SELECT Id_Subclasse, Id_Classe, Nome, Slug, Tagline FROM TB_Subclasse"):
        dest.execute(
            "INSERT INTO TB_Subclasse (Id_Subclasse, Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?,?)",
            (r["Id_Subclasse"], r["Id_Classe"], r["Nome"], r["Slug"], r["Tagline"]),
        )

    # ---------- TB_RecursoClasse ----------
    for r in src.execute(
        "SELECT Id_Recurso, Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor FROM TB_RecursoClasse"
    ):
        dest.execute(
            """INSERT INTO TB_RecursoClasse
               (Id_Recurso, Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor)
               VALUES (?,?,?,?,?,?,?)""",
            tuple(r),
        )

    # ---------- TB_ClasseHabilidade ----------
    for r in src.execute(
        "SELECT Id_Habilidade, Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido FROM TB_ClasseHabilidade"
    ):
        dest.execute(
            """INSERT INTO TB_ClasseHabilidade
               (Id_Habilidade, Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido)
               VALUES (?,?,?,?,?,?)""",
            tuple(r),
        )

    # ---------- TB_OpcaoJogo ----------
    # se a tabela existe no src com dados, copia; senão, fica vazia
    try:
        for r in src.execute("SELECT Id_Opcao, Nome, Slug, Tipo, Descricao FROM TB_OpcaoJogo"):
            dest.execute(
                "INSERT INTO TB_OpcaoJogo (Id_Opcao, Nome, Slug, Tipo, Descricao) VALUES (?,?,?,?,?)",
                tuple(r),
            )
    except sqlite3.OperationalError:
        pass

    # ---------- TB_AcessoOpcao ----------
    try:
        for r in src.execute(
            "SELECT Id_AcessoOpcao, Id_Opcao, Id_Classe, Id_Subclasse FROM TB_AcessoOpcao"
        ):
            dest.execute(
                """INSERT INTO TB_AcessoOpcao
                   (Id_AcessoOpcao, Id_Opcao, Id_Classe, Id_Subclasse)
                   VALUES (?,?,?,?)""",
                tuple(r),
            )
    except sqlite3.OperationalError:
        pass

    dest.commit()
    src.close()

    # ---------- relatório ----------
    print(f"\nOK bonfas_classes.db criado em: {DEST}")
    print("=" * 58)
    for t in ("TB_Classe", "TB_Subclasse", "TB_OpcaoJogo",
              "TB_RecursoClasse", "TB_ClasseHabilidade", "TB_AcessoOpcao"):
        n = dest.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:25} {n:>5} registros")

    print("\n-- classes com subclasses e habilidades --")
    for r in dest.execute("""
        SELECT c.Nome,
               (SELECT COUNT(*) FROM TB_Subclasse       s WHERE s.Id_Classe=c.Id_Classe) subs,
               (SELECT COUNT(*) FROM TB_ClasseHabilidade h WHERE h.Id_Classe=c.Id_Classe) habs,
               (SELECT COUNT(*) FROM TB_RecursoClasse    r WHERE r.Id_Classe=c.Id_Classe) recs
          FROM TB_Classe c
      ORDER BY c.Nome
    """):
        print(f"  {r[0]:15}  subs={r[1]:2}  habs={r[2]:3}  recs={r[3]:4}")

    dest.close()


if __name__ == "__main__":
    main()
