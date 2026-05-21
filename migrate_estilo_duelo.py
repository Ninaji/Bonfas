"""Adiciona estilo de luta "Duelo" (Dueling) ao catálogo TB_OpcaoJogo.

PHB 2024 tem 10 fighting styles — o catálogo atual omitiu Duelo. Adicionado
com acesso universal (Id_Classe=NULL, Id_Subclasse=NULL) — qualquer classe
que conceda estilo-de-luta via pick:estilo-de-luta:N pode escolher.

Idempotente via Slug UNIQUE.
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

NOME = "Duelo"
SLUG = "duelo-phb2024"
DESC = (
    "Quando você segura uma arma corpo-a-corpo em uma das mãos e nenhuma outra arma, "
    "você ganha +2 de bônus em rolagens de dano com aquela arma. "
    "[FONTE: PHB 2024 - verificar quando Bonfire Tales oficializar a lista de Estilos de Luta]"
)

existing = cur.execute("SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (SLUG,)).fetchone()
if existing:
    print(f"'{NOME}' já existe (Id={existing['Id_Opcao']}) — skip insert.")
    id_opcao = existing['Id_Opcao']
else:
    cur.execute(
        "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, SourceURL) "
        "VALUES (?,?,?,?,?)",
        (NOME, SLUG, "estilo-de-luta", DESC, "PHB 2024 (D&D 5.5e)"),
    )
    id_opcao = cur.lastrowid
    print(f"INSERT '{NOME}' Id={id_opcao}")

# Acesso universal (NULL/NULL) — todas as classes que oferecem estilo-de-luta veem.
cur.execute(
    "INSERT OR IGNORE INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) "
    "VALUES (?, NULL, NULL)",
    (id_opcao,),
)
if cur.rowcount > 0:
    print(f"  + acesso universal (NULL/NULL) vinculado")

conn.commit()
conn.close()
print('OK')
