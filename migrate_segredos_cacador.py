"""Fase 1 — Schema + catálogo + tag para Segredos de Caçador.

Cria 2 tabelas:
  - TB_Segredo (catálogo): espelha TB_Manobra com campos extras Linha/Custo/Acao
  - TB_PersonagemSegredo (escolhas): espelha TB_PersonagemTecnica

Popula 19 entries de segredos_cacador.json.

Adiciona tag '+segredos-cacador:N' na hab id=119 (Caçador Nv 2 Segredos de Caçador) com
n_por_nivel: Nv 2=2; Nv 5/9/13/17 = +2 cada (total Nv 17 = 10 segredos).
"""
import json
import shutil
import sqlite3
import time
from pathlib import Path

DB = "bonfas.db"
ID_HAB_SEGREDOS = 119  # Caçador Nv 2

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_Segredo (
    Id_Segredo INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome       VARCHAR(150) NOT NULL,
    Slug       VARCHAR(150) UNIQUE NOT NULL,
    Linha      VARCHAR(60)  NOT NULL,
    Custo      INTEGER NOT NULL DEFAULT 1,
    Acao       VARCHAR(40),
    Flavor     TEXT,
    Descricao  TEXT,
    Fonte      VARCHAR(50) DEFAULT 'cacador',
    TagsJSON   TEXT
);

CREATE TABLE IF NOT EXISTS TB_PersonagemSegredo (
    Id            INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem INTEGER NOT NULL,
    Id_Segredo    INTEGER NOT NULL,
    Id_Habilidade INTEGER,
    UNIQUE (Id_Personagem, Id_Segredo),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem),
    FOREIGN KEY (Id_Segredo) REFERENCES TB_Segredo(Id_Segredo)
);
""")
print("Schema OK")

# 2) Catálogo
data = json.loads(Path("segredos_cacador.json").read_text(encoding="utf-8"))
inserted = 0
for s in data:
    exists = cur.execute("SELECT Id_Segredo FROM TB_Segredo WHERE Slug=?", (s["slug"],)).fetchone()
    if exists:
        cur.execute(
            "UPDATE TB_Segredo SET Nome=?, Linha=?, Custo=?, Acao=?, Flavor=?, Descricao=? WHERE Slug=?",
            (s["nome"], s["linha"], s["custo"], s["acao"], s["flavor"], s["descricao"], s["slug"]),
        )
    else:
        cur.execute(
            """INSERT INTO TB_Segredo (Nome, Slug, Linha, Custo, Acao, Flavor, Descricao, Fonte, TagsJSON)
               VALUES (?,?,?,?,?,?,?,'cacador', NULL)""",
            (s["nome"], s["slug"], s["linha"], s["custo"], s["acao"], s["flavor"], s["descricao"]),
        )
        inserted += 1
print(f"Catálogo: {inserted} inseridos / {len(data) - inserted} atualizados (total {len(data)})")

# 3) Tag na hab id=119: +segredos-cacador progressão Nv 2/5/9/13/17 (+2 cada).
# Usa formato n_por_nivel objeto-tag (suporte já existente no agregador).
tag_obj = {
    "tag": "+segredos-cacador",
    "n_por_nivel": {"2": 2, "5": 4, "9": 6, "13": 8, "17": 10},
}
tags_json = json.dumps([tag_obj], ensure_ascii=False)
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?", (tags_json, ID_HAB_SEGREDOS))
print(f"\nHab id={ID_HAB_SEGREDOS} TagsJSON: {tags_json}")

conn.commit()

# 4) Stats finais
print("\n=== STATS ===")
total = cur.execute("SELECT COUNT(*) FROM TB_Segredo").fetchone()[0]
print(f"  TB_Segredo: {total} entries")
for r in cur.execute("SELECT Linha, COUNT(*) FROM TB_Segredo GROUP BY Linha"):
    print(f"    {r[0]}: {r[1]}")

conn.close()
print("\nDONE.")
