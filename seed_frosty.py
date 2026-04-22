"""Cria Frosty (Humana + Essência Infernal, Guerreiro 16/Cavaleiro Arcano).
Também insere a Essência Infernal no catálogo se não existir.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def upsert_essencia_infernal(cur: sqlite3.Cursor) -> int:
    cur.execute(
        """INSERT INTO TB_Essencia (Nome, Slug, LorePresentation, LoreRoleplay, LoreSociety)
               VALUES (?, ?, ?, ?, ?)
             ON CONFLICT(Slug) DO UPDATE SET
                   Nome=excluded.Nome, LorePresentation=excluded.LorePresentation
           RETURNING Id_Essencia""",
        (
            "Essência Infernal",
            "ess-infernal",
            "Os Herdeiros Diabólicos carregam marca de pacto ancestral com os infernos.",
            "Intenso, ambíguo, atraído por barganhas; carrega o peso do pacto do sangue.",
            "Vistos com desconfiança; alguns abraçam o mito, outros o escondem.",
        ),
    )
    return cur.fetchone()[0]


def ids_of(cur, sql, *args) -> int | None:
    r = cur.execute(sql, args).fetchone()
    return r[0] if r else None


def seed():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # pré-requisitos
    id_ess = upsert_essencia_infernal(cur)
    id_raca = ids_of(cur, "SELECT Id_Raca FROM TB_Raca WHERE Slug='humano'")
    id_linh = ids_of(cur, "SELECT Id_Linhagem FROM TB_Linhagem WHERE Id_Raca=? AND Slug LIKE '%padrao%' LIMIT 1", id_raca) \
            or ids_of(cur, "SELECT Id_Linhagem FROM TB_Linhagem WHERE Id_Raca=? LIMIT 1", id_raca)
    id_classe = ids_of(cur, "SELECT Id_Classe FROM TB_Classe WHERE Slug='guerreiro'")
    id_sub = ids_of(cur, "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug LIKE '%cavaleiro-arcano%'", id_classe)
    print(f"ids -> raca={id_raca} linh={id_linh} ess={id_ess} classe={id_classe} sub={id_sub}")

    # limpa Frosty se já existir
    old = ids_of(cur, "SELECT Id_Personagem FROM TB_Personagem WHERE Nome='Frosty'")
    if old:
        cur.execute("DELETE FROM TB_Personagem WHERE Id_Personagem=?", (old,))

    # cria personagem
    cur.execute("""
        INSERT INTO TB_Personagem
        (Nome, DonoUsuario, Tagline, Jogador, Nivel, Aventuras, ProximoNivel,
         PVAtual, PVMaximo, CA, Iniciativa, Velocidade, Patente,
         PercepcaoPassiva, BonusProficiencia, DadoVida)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "Frosty", "devmaster", "Arqueologo · Tiflino Herdeiro Diabólico",
        "Ninja", 16, 90, 3102, 164, 164, 20, -1, "9 m / 30 ft",
        "Esmeralda", 14, 5, "1d10",
    ))
    pid = cur.lastrowid

    cur.execute("""INSERT INTO TB_PersonagemEscolha
                   (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
                   VALUES (?,?,?,?,?,?)""",
                (pid, id_raca, id_linh, id_ess, id_classe, id_sub))

    cur.execute("""INSERT INTO TB_PersonagemAtributo
                   (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
                   VALUES (?,?,?,?,?,?,?)""",
                (pid, 20, 8, 18, 16, 8, 8))

    # perícias (18 do D&D 5e SRD, atributo fonte)
    PERICIAS = [
        ("Acrobacia",   "DES"), ("Adestrar Animais","SAB"), ("Arcanismo",  "INT"),
        ("Atletismo",   "FOR"), ("Enganação",       "CAR"), ("História",   "INT"),
        ("Intuição",    "SAB"), ("Intimidação",     "CAR"), ("Investigação","INT"),
        ("Medicina",    "SAB"), ("Natureza",        "INT"), ("Percepção",  "SAB"),
        ("Atuação",     "CAR"), ("Persuasão",       "CAR"), ("Religião",   "INT"),
        ("Prestidigitação","DES"), ("Furtividade",  "DES"), ("Sobrevivência","SAB"),
    ]
    # Frosty tem: Arcanismo +3, Atletismo (?+1C), História +8, Religião, Percepção +8 (passiva 14)
    # Com base na imagem interpreto proficiências: Arcanismo, Atletismo, História, Religião, Percepção
    PROFICIENTE = {"Arcanismo", "Atletismo", "História", "Religião", "Percepção"}
    for nome, atr in PERICIAS:
        cur.execute("""INSERT INTO TB_PersonagemPericia
                       (Id_Personagem, Nome, Atributo, Proficiente, Expertise)
                       VALUES (?,?,?,?,?)""",
                    (pid, nome, atr, 1 if nome in PROFICIENTE else 0, 0))

    # talentos — da imagem
    TALENTOS = [
        # Categoria, Nível, Nome, Detalhes
        ("geral", 1,  "Iniciado na ordem de cava...",   None),
        ("geral", 4,  "War Caster (int) 16",            "Int 16"),
        ("geral", 8,  "Mage Slayer (for) 19",           "For 19"),
        ("geral", 12, "Determinação da Cavalaria",      None),
        ("geral", 16, "Marca de cura superior (...)",   None),
        ("geral", 19, "Marca potente (con) 19",         "Con 19"),
        ("raca",  1,  "Tatuagem Arcana (humano)",       None),
        ("raca",  5,  "Transformação: Forma Infernal",  None),
        ("raca",  9,  "Eclosão do Pecado",              None),
        ("raca",  13, "Asas da Condenação",             None),
        ("raca",  17, "Flagelo dos Condenados",         None),
        ("extra", 6,  "NV6",                            None),
        ("extra", 8,  "GWM (FOR) 18",                   "Great Weapon Master"),
        ("extra", 14, "NV 14",                          None),
        ("extra", 16, "Marca da Cura Raízes +con",      None),
    ]
    for cat, niv, nome, det in TALENTOS:
        cur.execute("""INSERT INTO TB_PersonagemTalento
                       (Id_Personagem, Categoria, Nivel, Nome, Detalhes)
                       VALUES (?,?,?,?,?)""",
                    (pid, cat, niv, nome, det))

    # idiomas + ferramentas (texto livre conforme imagem)
    for nome in ["Comum", "Gigante", "Infernal", "Anão", "Silvestre"]:
        cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome) VALUES (?,?,?)",
                    (pid, "idioma", nome))
    for t in ["Kit de ferreiro", "Veículos terrestres", "Veículos aquáticos",
              "Todas armas menos de fogo", "Todas armaduras e escudos"]:
        cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome) VALUES (?,?,?)",
                    (pid, "ferramenta", t))

    # resistências
    for t, d in [("resistencia", "Fogo"), ("resistencia", "Necrótico")]:
        cur.execute("INSERT INTO TB_PersonagemResistencia (Id_Personagem, Tipo, DanoTipo) VALUES (?,?,?)",
                    (pid, t, d))

    # personalidade (da imagem, simplificado)
    PERSONALIDADE = [
        ("traco",   "You might think I'm a scholar, but I love a good brawl. These fists were made for punching."),
        ("ideal",   "Danger. With every great discovery comes great risk. The two walk hand in hand."),
        ("vinculo", "I won't sell an art object or other treasure that has historical significance or is one of a kind."),
        ("defeito", "I can't sleep except in total darkness."),
    ]
    for t, txt in PERSONALIDADE:
        cur.execute("INSERT INTO TB_PersonagemPersonalidade (Id_Personagem, Tipo, Texto) VALUES (?,?,?)",
                    (pid, t, txt))

    # inventário (da imagem 2)
    INV = [
        # qtd, item, custo, peso, sintonizado
        (1,  "Chain-mail",               None,     "55 lb", 0),
        (1,  "Greatsword",               None,     "6 lb",  0),
        (1,  "Lance",                    None,     "6 lb",  0),
        (1,  "Light crossbow",           None,     "5 lb",  0),
        (20, "Bolts",                    None,     "1.5 lb",0),
        (1,  "Backpack",                 None,     "5 lb",  0),
        (1,  "Bedroll",                  None,     "7 lb",  0),
        (1,  "Oil",                      None,     "1 lb",  0),
        (10, "Rações",                   None,     "2 lb",  0),
        (1,  "Corda",                    None,     "10 lb", 0),
        (1,  "Tinderbox",                None,     "1 lb",  0),
        (10, "Tochas",                   None,     "1 lb",  0),
        (1,  "Warterskin",               None,     "5 lb",  0),
        (1,  "Warm fungal Clothes",      "15 gp",  "4 lb",  0),
        (1,  "Bright Fungal Cloak",      "25 gp",  "1 lb",  0),
        (1,  "Livro Arcanismo",          "25 gp",  "5 lb",  0),
        (5,  "Shuriken",                 None,     "0 lb",  0),
        (1,  "Full-Plate Adamantine",    "4,000 gp", "65 lb", 0),
        (1,  "Vicious Weapon",           None,     None,     1),
        (1,  "Shield Guardian Amulet",   "12,000 gp","0 lb",  1),
        (1,  "Badge of the Watch",       "12,000 gp",None,    0),
        (1,  "Gauntlet of Flaming Fury", "2,000 gp", None,    0),
        (1,  "axe beak",                 "50 gp",  None,     0),
    ]
    for qtd, it, custo, peso, sint in INV:
        cur.execute("""INSERT INTO TB_PersonagemInventarioItem
                       (Id_Personagem, Qtd, Item, Custo, Peso, Sintonizado)
                       VALUES (?,?,?,?,?,?)""",
                    (pid, qtd, it, custo, peso, sint))

    # magias do Cavaleiro Arcano (placeholder das da imagem de Eldritch Knight)
    MAGIAS = [
        # nível, nome, preparada
        (0, "Absorb Elements",    0),  # sample truques/magias
        (0, "Mind Sliver",        0),
        (0, "Mage Hand",          0),
        (0, "Booming Blade",      0),
        (0, "Green Flame Blade",  0),
        (1, "Shield",             1),
        (1, "Absorb Elements",    1),
        (1, "Find Familiar",      1),
        (1, "Magic Missile",      1),
        (2, "Misty Step",         1),
        (2, "Mirror Image",       1),
        (3, "Counterspell",       1),
        (3, "Fireball",           1),
        (4, "Banishment",         1),
        (4, "Greater Invisibility", 1),
    ]
    for niv, nm, prep in MAGIAS:
        cur.execute("""INSERT INTO TB_PersonagemMagia
                       (Id_Personagem, Nivel, Nome, Preparada)
                       VALUES (?,?,?,?)""",
                    (pid, niv, nm, prep))

    # técnicas (Fighter)
    TECNICAS = [
        ("Ataque de Manobra",     "Quando você atingir uma criatura com um ataque de arma, você pode gastar 1 Dado de Combate."),
        ("Ataque de Derrubada",   "Quando você atingir uma criatura com um ataque de arma, você pode gastar 1 Dado de Combate para derrubar."),
        ("Ataque de Investida",   "Como uma Ação Bônus, você pode gastar 1 Dado de Combate para realizar uma investida."),
        ("Ataque Preciso",        "Quando você fizer uma jogada de ataque com arma, você pode gastar 1 Dado de Combate."),
        ("Ataque Preparado",      "Quando uma criatura que você pode ver se mover para dentro de 1,5 m de você."),
        ("Golpe do Comandante",   "Quando você realiza a Ação de Ataque no seu turno..."),
        ("Alternar Posição",      "No seu turno, quando estiver a até 1,5 m de um aliado..."),
    ]
    for n, d in TECNICAS:
        cur.execute("""INSERT INTO TB_PersonagemTecnica
                       (Id_Personagem, Nome, Descricao)
                       VALUES (?,?,?)""",
                    (pid, n, d))

    conn.commit()
    conn.close()
    print(f"OK Frosty criada (id={pid})")


if __name__ == "__main__":
    seed()
