"""
Popula TB_Raca (Humano) + TB_Linhagem + TB_Essencia (Infernal) + TB_EssenciaLinhagem
A PARTIR DOS HTMLs OFICIAIS salvos em paginas/.  1:1, sem inventar nomes.
"""
import sqlite3
import re
from pathlib import Path
from parse_artigo import parse, slug

DB = Path(__file__).parent / "bonfas.db"


def upsert(cur, sql, args):
    cur.execute(sql, args)
    return cur.fetchone()[0]


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # ============ HUMANO ============
    humano = parse(Path("paginas/humano.html"))
    intro_secao  = next((s for s in humano["secoes"] if s["nivel"] == 2 and "Humano" in s["titulo"]), None)
    cur.execute(
        """INSERT INTO TB_Raca (Nome, Slug, Tagline, LorePresentation, PermiteEssencia)
               VALUES (?, ?, ?, ?, 1)""",
        ("Humano", "humano",
         "Versatilidade e ambição — a raça matriz de Cineria.",
         (intro_secao["conteudo_txt"][:2000] if intro_secao else None)),
    )
    id_humano = cur.lastrowid

    # Linhagens humanas — 4 oficiais: Erthari, Sólarin, Durkarn, Goruun (em H4 sob H3 "Opção A: Linhagens Humanas")
    LIN_H4_START = False
    for s in humano["secoes"]:
        if s["nivel"] == 3 and "Linhagens Humanas" in s["titulo"]:
            LIN_H4_START = True; continue
        if s["nivel"] == 3 and LIN_H4_START:   # próximo H3 → saiu
            break
        if s["nivel"] == 4 and LIN_H4_START:
            nome = s["titulo"]
            cur.execute(
                """INSERT INTO TB_Linhagem (Id_Raca, Nome, Slug, Descricao)
                       VALUES (?, ?, ?, ?)""",
                (id_humano, nome, slug(nome)[:100], s["conteudo_txt"][:2000]),
            )

    # ============ ESSÊNCIA INFERNAL ============
    inf = parse(Path("paginas/infernal.html"))
    intro = next((s for s in inf["secoes"] if s["nivel"] == 2 and "Infernal" in s["titulo"]), None)
    cur.execute(
        """INSERT INTO TB_Essencia (Nome, Slug, LorePresentation)
               VALUES (?, ?, ?)""",
        ("Essência Infernal", "essencia-infernal",
         (intro["conteudo_txt"][:2000] if intro else None)),
    )
    id_ess = cur.lastrowid

    # Sub-linhagens do Infernal: extraídas da tabela "Legado dos Círculos"
    # formato: Linhagem | Elemento (Resistência) | Truque (Nível 1) | Magia (Nível 3)
    legado = next((s for s in inf["secoes"] if "Legado dos C" in s["titulo"]), None)
    if not legado:
        raise SystemExit("Não achei 'Legado dos Círculos' no infernal.html")

    # lista na ordem oficial do texto
    LINHAGENS_OFICIAIS = [
        # (linhagem, elemento, truque, magia_n3)
        ("Soberba",    "Trovão",   "Golpe Trovejante [Thunderclap]", "Onda Trovejante [Thunderwave]"),
        ("Orgulho",    "Fogo",     "Raio de Fogo [Fire Bolt]",       "Golpe Incandescente [Searing Smite]"),
        ("Ira",        "Fogo",     "Raio de Fogo [Fire Bolt]",       "Mãos Flamejantes [Burning Hands]"),
        ("Gula",       "Ácido",    "Bolha Ácida [Acid Splash]",      "Infusão Cáustica [Tasha's Caustic Brew]"),
        ("Manipulação","Trovão",   "Amizade [Friends]",              "Comando [Command]"),
        ("Luxúria",    "Elétrico", "Amizade [Friends]",              "Enfeitiçar Pessoa [Charm Person]"),
        ("Inveja",     "Frio",     "Raio de Gelo [Ray of Frost]",    "Faca de Gelo [Ice Knife]"),
        ("Ganância",   "Ácido",    "Taumaturgia [Thaumaturgy]",      "Compreender Idiomas [Comprehend Languages]"),
        ("Exílio",     "Frio",     "Raio de Gelo [Ray of Frost]",    "Armadura de Agathys [Armor of Agathys]"),
    ]
    for nome, elem, truque, magia in LINHAGENS_OFICIAIS:
        desc = (f"Elemento: {elem} (resistência). "
                f"Truque (nv 1): {truque}. "
                f"Magia (nv 3, 1x por descanso longo): {magia}.")
        cur.execute(
            """INSERT INTO TB_EssenciaLinhagem (Id_Essencia, Nome, Slug, Descricao)
                   VALUES (?, ?, ?, ?)""",
            (id_ess, nome, slug(nome), desc),
        )

    # religa Frosty: Humano + Essência Infernal + Orgulho
    id_org = cur.execute(
        "SELECT Id_EssLinhagem FROM TB_EssenciaLinhagem WHERE Id_Essencia=? AND Slug='orgulho'",
        (id_ess,),
    ).fetchone()[0]
    cur.execute(
        """UPDATE TB_PersonagemEscolha
              SET Id_Raca=?, Id_Essencia=?, Id_EssLinhagem=?, Id_Linhagem=NULL
            WHERE Id_Personagem=(SELECT Id_Personagem FROM TB_Personagem WHERE Nome='Frosty')""",
        (id_humano, id_ess, id_org),
    )

    conn.commit()

    print("=== Raças ===")
    for r in cur.execute("SELECT Slug, Nome FROM TB_Raca"):
        print(" ", r)
    print("\n=== Linhagens Humanas ===")
    for r in cur.execute("SELECT Slug, Nome FROM TB_Linhagem WHERE Id_Raca=?", (id_humano,)):
        print(" ", r)
    print("\n=== Essência Infernal — Linhagens (Legado dos Círculos) ===")
    for r in cur.execute("SELECT Nome, Descricao FROM TB_EssenciaLinhagem WHERE Id_Essencia=?", (id_ess,)):
        print(f"  {r[0]:12}  {r[1][:80]}")


if __name__ == "__main__":
    main()
