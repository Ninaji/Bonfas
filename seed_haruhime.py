"""Cria Haruhime Mitsuki (pid=7) — Kitsune Místico 9 sub O Celestial.

Fonte: E:\\Obsidian\\_raw\\Haruhime Mitsuki - LOG.csv (parcial).
Kitsune: criada como raça mínima placeholder (id=3) — popular detalhes via debug depois.
"""
import json, shutil, sqlite3, time

DB = "bonfas.db"
PID = 7
ID_MISTICO = 11
ID_SUB_CELESTIAL = 142

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Garante raça Kitsune (placeholder mínima)
existing = cur.execute("SELECT Id_Raca FROM TB_Raca WHERE LOWER(Nome)='kitsune'").fetchone()
if existing:
    ID_RACA_KITSUNE = existing[0]
    print(f"Kitsune já existe (id={ID_RACA_KITSUNE})")
else:
    cur.execute(
        "INSERT INTO TB_Raca (Nome, Slug, Tagline) VALUES (?,?,?)",
        ("Kitsune", "kitsune", "Espíritos zorros do mundo Bonfire — astutos, místicos, com forma humanoide-vulpina."),
    )
    ID_RACA_KITSUNE = cur.lastrowid
    print(f"Kitsune criada (id={ID_RACA_KITSUNE})")

# 2) Idempotência: limpa Haruhime anterior
cur.execute("PRAGMA foreign_keys=OFF")
for tbl in ("TB_PersonagemEscolha", "TB_PersonagemAtributo", "TB_PersonagemTalento",
            "TB_PersonagemPericia", "TB_PersonagemEscolhaPericia", "TB_PersonagemEscolhaTag",
            "TB_PersonagemIdioma", "TB_PersonagemPersonalidade", "TB_PersonagemResistencia",
            "TB_PersonagemMagia", "TB_PersonagemTecnica", "TB_PersonagemMaestriaArma",
            "TB_PersonagemInventarioItem", "TB_PersonagemSegredo",
            "TB_PersonagemInimigoFavorito", "TB_PersonagemEvolucaoTotemica",
            "TB_PersonagemEstiloKi", "TB_PersonagemClasse"):
    try: cur.execute(f"DELETE FROM {tbl} WHERE Id_Personagem=?", (PID,))
    except sqlite3.OperationalError: pass
cur.execute("DELETE FROM TB_Personagem WHERE Id_Personagem=?", (PID,))
cur.execute("PRAGMA foreign_keys=ON")

# 3) TB_Personagem
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (PID, "Haruhime Mitsuki", "devmaster",
     "Místico 9 (Patrono O Celestial) — Kitsune Espiritualista",
     "player-haruhime", 9, 35, 42,
     58, 58,
     12, 2, "9 m / 30 ft",
     "Topázio",
     14, 4, "d8",
     "Espiritualista",
     json.dumps({"Carisma": 2, "Sabedoria": 1}, ensure_ascii=False)),
)
print(f"Haruhime criada pid={PID}")

# 4) Escolha
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_KITSUNE, None, None, ID_MISTICO, ID_SUB_CELESTIAL),
)

# 5) Classe
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_MISTICO, ID_SUB_CELESTIAL, 9, 0),
)

# 6) Atributos — Kitsune Místico Nv 9, CAR principal (CSV dá CAR 18)
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 8, 14, 14, 10, 14, 18),
)

# 7) Perícias padrão
PERICIAS = [
    ("Acrobacia", "DES"), ("Adestrar Animais", "SAB"), ("Arcanismo", "INT"),
    ("Atletismo", "FOR"), ("Atuação", "CAR"), ("Enganação", "CAR"),
    ("Furtividade", "DES"), ("História", "INT"), ("Intimidação", "CAR"),
    ("Intuição", "SAB"), ("Investigação", "INT"), ("Medicina", "SAB"),
    ("Natureza", "INT"), ("Percepção", "SAB"), ("Persuasão", "CAR"),
    ("Prestidigitação", "DES"), ("Religião", "INT"), ("Sobrevivência", "SAB"),
]
for nome, atr in PERICIAS:
    cur.execute(
        "INSERT INTO TB_PersonagemPericia (Id_Personagem, Nome, Atributo, Proficiente, Expertise) VALUES (?,?,?,0,0)",
        (PID, nome, atr),
    )

# 8) Picks de perícia (CSV indica Persuasão, Enganação, Intimidação, Medicina, Sobrevivência, Acrobacia)
ESCOLHAS = [
    ("Místico", 0, "Persuasão"),
    ("Místico", 1, "Enganação"),
    ("Místico", 2, "Intimidação"),
    ("Místico", 3, "Medicina"),
]
for origem, slot, nome in ESCOLHAS:
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome),
    ).fetchone()[0]
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, origem, slot, pid_per),
    )

# 9) Idiomas (CSV: Comum, Élfico, Infernal, Celestial, Abissal)
IDIOMAS = [
    ("Comum",     "Kitsune (base)"),
    ("Élfico",    "background"),
    ("Infernal",  "background"),
    ("Celestial", "essencia"),
    ("Abissal",   "aprendido"),
]
for nome, origem in IDIOMAS:
    cur.execute(
        "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
        (PID, "idioma", nome, origem),
    )

# 10) Ferramentas (CSV: Suprimentos de Caligrafia, Jewelry/Joalheiro)
FERRAMENTAS = [
    ("Kit de Caligrafista", "background"),
    ("Kit de Joalheiro",    "background"),
]
for nome, origem in FERRAMENTAS:
    cur.execute(
        "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
        (PID, "ferramenta", nome, origem),
    )

conn.commit()
conn.close()
print("OK — Haruhime pid=7 Místico 9 sub O Celestial criada.")
