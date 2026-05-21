"""
Popula catalogo de Estilo de Luta com os 10 estilos do PHB 2024 (D&D 5.5e).

USO COMO EXCECAO A REGRA #0: o usuario autorizou explicitamente em 2026-05-03
que esta tabela use o PHB 2024 como base ate o Bonfire Tales oficializar a
lista. Cada Descricao marca '[FONTE: PHB 2024 - verificar quando homebrew
oficializar]'.

Idempotente: roda multiplas vezes sem efeito acumulado.
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"

ESTILOS = [
    (
        "Arquearia",
        "arquearia-phb2024",
        "Voce ganha um bonus +2 nas jogadas de ataque com armas a distancia.",
    ),
    (
        "Combate Cego",
        "combate-cego-phb2024",
        "Voce tem percepcao apurada que permite combater efetivamente sem visao. "
        "Dentro de 3 metros voce enxerga criaturas mesmo cego ou na escuridao, desde que nao estejam Encobertas de voce.",
    ),
    (
        "Combate Corpo-a-Corpo Defensivo",
        "combate-corpo-a-corpo-defensivo-phb2024",
        "Quando uma criatura erra um ataque corpo-a-corpo contra voce, voce pode usar a Reacao "
        "para impor desvantagem na proxima jogada de ataque dela contra voce ate o fim do seu proximo turno.",
    ),
    (
        "Defesa",
        "defesa-phb2024",
        "Enquanto vestir armadura, voce ganha +1 na CA.",
    ),
    (
        "Combate com Arma de Duas Maos",
        "combate-arma-duas-maos-phb2024",
        "Quando voce rola um 1 ou 2 num dado de dano de uma arma corpo-a-corpo que esta empunhando "
        "com duas maos, pode rolar o dado novamente e usar o novo resultado, mesmo que seja 1 ou 2.",
    ),
    (
        "Intercepcao",
        "intercepcao-phb2024",
        "Quando uma criatura que voce ve atinge um alvo a ate 1,5m de voce, voce pode usar a Reacao "
        "para reduzir o dano em 1d10 + seu bonus de proficiencia (minimo 0).",
    ),
    (
        "Protecao",
        "protecao-phb2024",
        "Quando uma criatura que voce ve ataca um alvo (que nao voce) a ate 1,5m de voce, voce pode "
        "usar a Reacao para impor desvantagem na jogada de ataque desde que esteja segurando um escudo.",
    ),
    (
        "Combate com Arma de Arremesso",
        "combate-arma-arremesso-phb2024",
        "Voce pode sacar uma arma com a propriedade Arremesso como parte do mesmo ataque que a usa. "
        "Quando acerta um alvo com uma arma de arremesso a distancia, voce ganha +2 no dano.",
    ),
    (
        "Combate com Duas Armas",
        "combate-duas-armas-phb2024",
        "Quando ataca com duas armas, voce pode adicionar seu modificador de atributo ao dano "
        "do segundo ataque (que normalmente nao recebe).",
    ),
    (
        "Combate Desarmado",
        "combate-desarmado-phb2024",
        "Seus golpes desarmados causam 1d6 (ou 1d8 se nao estiver empunhando armas/escudo). "
        "Quando agarra uma criatura, no inicio de cada turno em que ela continua agarrada, "
        "ela sofre 1d4 de dano de impacto.",
    ),
]

SOURCE_FLAG = "[FONTE: PHB 2024 - verificar quando Bonfire Tales oficializar a lista de Estilos de Luta]"


def main() -> int:
    if not DB.exists():
        print(f"ERRO: {DB} nao existe", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    print("[1] Inserir/atualizar estilos em TB_OpcaoJogo")
    inserted = 0
    skipped = 0
    for nome, slug, descricao_base in ESTILOS:
        cur.execute("SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (slug,))
        existing = cur.fetchone()
        descricao_full = f"{descricao_base}\n\n{SOURCE_FLAG}"
        if existing:
            id_opcao = existing[0]
            cur.execute(
                "UPDATE TB_OpcaoJogo SET Nome=?, Tipo=?, Descricao=? WHERE Id_Opcao=?",
                (nome, "estilo-de-luta", descricao_full, id_opcao),
            )
            print(f"  UPDATE: {nome} (Id_Opcao={id_opcao})")
            skipped += 1
        else:
            cur.execute(
                "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, SourceURL) VALUES (?,?,?,?,?)",
                (nome, slug, "estilo-de-luta", descricao_full, "PHB 2024 (D&D 5.5e)"),
            )
            id_opcao = cur.lastrowid
            inserted += 1
            print(f"  INSERT: {nome} -> Id_Opcao={id_opcao}")

        # acesso por Id_Classe=8 (Guerreiro) — toda a classe tem o estilo de luta
        cur.execute(
            "SELECT 1 FROM TB_AcessoOpcao WHERE Id_Opcao=? AND Id_Classe=8 AND Id_Subclasse IS NULL",
            (id_opcao,),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, 8, NULL)",
                (id_opcao,),
            )
            print(f"  ACESSO: Id_Opcao={id_opcao} -> Classe 8 (Guerreiro)")

    conn.commit()

    print()
    print("[2] Verificacao")
    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='estilo-de-luta'")
    print(f"  TB_OpcaoJogo estilo-de-luta: {cur.fetchone()[0]} rows (esperado {len(ESTILOS)})")
    cur.execute(
        "SELECT COUNT(*) FROM TB_AcessoOpcao a "
        "  JOIN TB_OpcaoJogo o ON o.Id_Opcao=a.Id_Opcao "
        " WHERE o.Tipo='estilo-de-luta' AND a.Id_Classe=8"
    )
    print(f"  TB_AcessoOpcao classe Guerreiro: {cur.fetchone()[0]} rows (esperado {len(ESTILOS)})")
    print(f"  inserted: {inserted}, updated/skipped: {skipped}")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
