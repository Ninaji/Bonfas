"""Insere o talento 'Aumento de Atributo (+1 +1)' no catalogo TB_OpcaoJogo.

Este talento existe para que o usuario possa, em um slot ASI, optar por bumpar
atributos em vez de pegar um talento normal. PHB 2024 permite '+2 em um' ou
'+1 +1 em dois diferentes' — esta entrada cobre o segundo caso.
"""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"

NOME = "Aumento de Atributo (+1 +1)"
SLUG = "aumento-de-atributo-1-1"
DESC = (
    "Pré-requisito: Nível 4+. "
    "Aumento de Atributo: +1 em dois atributos diferentes à sua escolha. "
    "Esta é a opção 'ASI puro' — sem talento, apenas bonus de atributos. "
    "Cada um dos dois atributos escolhidos não pode passar de 20 com este aumento."
)
TAGS = ["asi", "atributo", "nv4"]


def main() -> int:
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (SLUG,))
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE TB_OpcaoJogo SET Nome=?, Tipo=?, Descricao=?, TagsJSON=?, NivelMinimo=4, "
            "PreReqTexto=?, SourceURL=? WHERE Id_Opcao=?",
            (NOME, "talento-geral", DESC, json.dumps(TAGS),
             "Nível 4+", "Bonfire/PHB 2024 — opção ASI standalone", existing[0]),
        )
        id_opcao = existing[0]
        print(f"UPDATE Id_Opcao={id_opcao}")
    else:
        cur.execute(
            "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, TagsJSON, NivelMinimo, PreReqTexto, SourceURL) "
            "VALUES (?,?,?,?,?,4,?,?)",
            (NOME, SLUG, "talento-geral", DESC, json.dumps(TAGS),
             "Nível 4+", "Bonfire/PHB 2024 — opção ASI standalone"),
        )
        id_opcao = cur.lastrowid
        print(f"INSERT Id_Opcao={id_opcao}")

    cur.execute("SELECT 1 FROM TB_AcessoOpcao WHERE Id_Opcao=? AND Id_Classe IS NULL AND Id_Subclasse IS NULL", (id_opcao,))
    if not cur.fetchone():
        cur.execute("INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, NULL, NULL)", (id_opcao,))
        print("ACESSO universal")

    conn.commit()
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
