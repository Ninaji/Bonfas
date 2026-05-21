"""Cria Lynn (pid=10) — Humano Artífice 16 sub Alquimista. Seed básico a
partir de E:\\Obsidian\\_raw\\Lynn - LOG.csv (planilha Pathbuilder Bonfire).
Ajuste fino (infusões escolhidas, talentos, magias) via UI no debug.

No Nv 16: 7 Infusões Conhecidas, 5 Itens Infundidos. Testa o campo
"Infusões de Artificer".
"""
import json, shutil, sqlite3, time

DB = "bonfas.db"
PID = 10

ID_RACA_HUMANO = 1
ID_ARTIFICE = 1
ID_SUB_ALQUIMISTA = 1

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

for tbl in ("TB_PersonagemEscolha", "TB_PersonagemAtributo", "TB_PersonagemTalento",
            "TB_PersonagemPericia", "TB_PersonagemEscolhaPericia", "TB_PersonagemEscolhaTag",
            "TB_PersonagemIdioma", "TB_PersonagemPersonalidade", "TB_PersonagemResistencia",
            "TB_PersonagemMagia", "TB_PersonagemTecnica", "TB_PersonagemMaestriaArma",
            "TB_PersonagemInventarioItem", "TB_PersonagemSegredo",
            "TB_PersonagemInimigoFavorito", "TB_PersonagemEvolucaoTotemica",
            "TB_PersonagemClasse"):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE Id_Personagem=?", (PID,))
    except sqlite3.OperationalError:
        pass
cur.execute("DELETE FROM TB_Personagem WHERE Id_Personagem=?", (PID,))
cur.execute("PRAGMA foreign_keys=ON")

# 1) TB_Personagem — CSV: Artífice 16, PV 163, Vel 30ft, jogador Yuyu
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (PID, "Lynn", "devmaster",
     "Artífice 16 — Alquimista · Humano",
     "Yuyu", 16, 94, 102,
     163, 163,
     16, 2,                              # CA placeholder + Inic (DES +2)
     "9 m / 30 ft",
     "Esmeralda",                        # Patente Nv 16
     10, 5, "d8",                        # Perc passiva, BP Nv16 = +5, d8
     "Estudioso",                        # Background
     json.dumps({"Inteligencia": 1, "Constituicao": 1, "Destreza": 1},
                ensure_ascii=False)),
)
print(f"Lynn criada pid={PID}")

# 2) Escolha primária
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_HUMANO, None, None, ID_ARTIFICE, ID_SUB_ALQUIMISTA),
)

# 3) Classes
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_ARTIFICE, ID_SUB_ALQUIMISTA, 16, 0),
)

# 4) Atributos (CSV finais: INT 20 com Headband? não — CSV mostra INT 20 base)
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 8, 14, 16, 20, 11, 8),
)

# 5) Perícias — Proficiente conforme CSV (◉)
PERICIAS = [
    ("Acrobacia", "DES", 0), ("Adestrar Animais", "SAB", 0), ("Arcanismo", "INT", 1),
    ("Atletismo", "FOR", 0), ("Atuação", "CAR", 0), ("Enganação", "CAR", 0),
    ("Furtividade", "DES", 0), ("História", "INT", 1), ("Intimidação", "CAR", 0),
    ("Intuição", "SAB", 0), ("Investigação", "INT", 1), ("Medicina", "SAB", 1),
    ("Natureza", "INT", 1), ("Percepção", "SAB", 0), ("Persuasão", "CAR", 1),
    ("Prestidigitação", "DES", 0), ("Religião", "INT", 0), ("Sobrevivência", "SAB", 1),
]
for nome, atr, prof in PERICIAS:
    cur.execute(
        "INSERT INTO TB_PersonagemPericia (Id_Personagem, Nome, Atributo, Proficiente, Expertise) VALUES (?,?,?,?,0)",
        (PID, nome, atr, prof),
    )

# 6) Picks de perícia Artífice (escolhe 2 base) — Arcanismo + Investigação
for slot, nome in ((0, "Arcanismo"), (1, "Investigação")):
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome),
    ).fetchone()[0]
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, "Artífice", slot, pid_per),
    )

# 7) Idiomas
cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
            (PID, "idioma", "Comum", "Humano (base)"))

# 8) Itens sintonizados (CSV)
for item in ("Shield Guardian Amulet", "Ring of Spell Storing", "Ring of Amity"):
    cur.execute(
        "INSERT INTO TB_PersonagemInventarioItem (Id_Personagem, Qtd, Item, Sintonizado) VALUES (?,?,?,1)",
        (PID, 1, item),
    )

conn.commit()
conn.close()
print("OK — Lynn pid=10 Artífice 16 Alquimista criada (7 Infusões Conhecidas no Nv 16).")
