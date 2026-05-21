"""Cria Kenji Yamamoto (pid=9) — Humano Bárbaro 18 sub Caminho do Coração
Selvagem. Seed básico a partir de E:\\Obsidian\\_raw\\Kenji Yamamoto - LOG.csv
(planilha Pathbuilder Bonfire Tales). Ajuste fino (talentos por nível,
maestrias, magic items detalhados) via UI no debug.

Idempotente: limpa Kenji anterior se existir.
"""
import json, shutil, sqlite3, time

DB = "bonfas.db"
PID = 9

ID_RACA_HUMANO = 1
ID_BARBARO = 3
ID_SUB_CORACAO_SELVAGEM = 15  # criado por migrate_barbaro_full.py

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Idempotência
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

# 1) TB_Personagem — CSV: PV 257, Vel 40ft, Nv 18, jogador Pedro Forte
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (PID, "Kenji Yamamoto", "devmaster",
     "Bárbaro 18 — Caminho do Coração Selvagem · Humano",
     "Pedro Forte", 18, 117, 127,        # Aventuras/PróximoNível (CSV cols 117/127)
     257, 257,                           # PV — CSV mostra 257
     20, 4,                              # CA (10+DES4+CON5+Ring1; engine recalc) + Inic
     "12 m / 40 ft",                     # Vel CSV (40 ft)
     "Âmbar",                            # Patente Nv 18 (auto pelo frontend)
     16, 6, "d12",                       # Percepção passiva, BP Nv18 = +6, DadoVida d12
     "Viajante",                         # Background CSV (VIAJANTE)
     json.dumps({"Forca": 1, "Constituicao": 1, "Sabedoria": 1},
                ensure_ascii=False)),    # Humano: choose 3 +1
)
print(f"Kenji criado pid={PID}")

# 2) Escolha primária (raça/classe/sub)
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_HUMANO, None, None, ID_BARBARO, ID_SUB_CORACAO_SELVAGEM),
)

# 3) Classes
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_BARBARO, ID_SUB_CORACAO_SELVAGEM, 18, 0),
)

# 4) Atributos — finais da planilha (Belt of Fire Giant Strenght→FOR 25,
#    Headband of Intellect→INT 19). Seed básico: valores da CSV; itens que
#    setam atributo são modelados aqui diretamente (ajuste fino via UI).
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 25, 18, 20, 19, 10, 10),
)

# 5) Perícias padrão (18) — Proficiente marcado conforme CSV (◉)
PERICIAS = [
    ("Acrobacia", "DES", 0), ("Adestrar Animais", "SAB", 0), ("Arcanismo", "INT", 0),
    ("Atletismo", "FOR", 1), ("Atuação", "CAR", 0), ("Enganação", "CAR", 0),
    ("Furtividade", "DES", 1), ("História", "INT", 0), ("Intimidação", "CAR", 1),
    ("Intuição", "SAB", 1), ("Investigação", "INT", 1), ("Medicina", "SAB", 0),
    ("Natureza", "INT", 1), ("Percepção", "SAB", 1), ("Persuasão", "CAR", 0),
    ("Prestidigitação", "DES", 1), ("Religião", "INT", 0), ("Sobrevivência", "SAB", 1),
]
for nome, atr, prof in PERICIAS:
    cur.execute(
        "INSERT INTO TB_PersonagemPericia (Id_Personagem, Nome, Atributo, Proficiente, Expertise) VALUES (?,?,?,?,0)",
        (PID, nome, atr, prof),
    )

# 6) Picks de perícia Bárbaro (escolhe 2 da lista do 1º nível). CSV: muitas
#    perícias proficientes vêm de Conhecimento Primitivo (Nv5/10) + talentos.
#    Picks de classe base: Atletismo + Intimidação.
for slot, nome in ((0, "Atletismo"), (1, "Intimidação")):
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome),
    ).fetchone()[0]
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, "Bárbaro", slot, pid_per),
    )

# 7) Idiomas — Comum default (Humano)
cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
            (PID, "idioma", "Comum", "Humano (base)"))

# 8) Personalidade (CSV)
PERSONALIDADE = [
    ("traco",   "Introspectivo, impaciente, agressivo"),
    ("ideal",   "Força, Honra, Irmandade"),
    ("vinculo", "Clã Yamamoto"),
    ("defeito", "Violento"),
]
for tipo, txt in PERSONALIDADE:
    cur.execute(
        "INSERT INTO TB_PersonagemPersonalidade (Id_Personagem, Tipo, Texto) VALUES (?,?,?)",
        (PID, tipo, txt),
    )

# 9) Itens sintonizados (CSV — 3 magic items)
ITENS = [
    ("Belt of Fire Giant Strength", 1),
    ("Headband of Intellect", 1),
    ("Ring of Protection", 1),
]
for item, sint in ITENS:
    cur.execute(
        "INSERT INTO TB_PersonagemInventarioItem (Id_Personagem, Qtd, Item, Sintonizado) VALUES (?,?,?,?)",
        (PID, 1, item, sint),
    )

conn.commit()
conn.close()
print("OK — Kenji Yamamoto pid=9 Bárbaro 18 Coração Selvagem criado.")
