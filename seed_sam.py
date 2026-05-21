"""Cria Sam (pid=6) — Humano Monge 20 sub Palma Aberta. Seed básico:
ajuste fino (talentos por nível, idiomas extras, magic items) via UI no debug.

Fonte: E:\\Obsidian\\_raw\\Sam - LOG.csv (parcial — CSV é referência cruzada).
"""
import json, shutil, sqlite3, time

DB = "bonfas.db"
PID = 6

ID_RACA_HUMANO = 1
ID_MONGE = 12
ID_SUB_PALMA_ABERTA = 135  # criado pelo migrate_monge_full.py

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Idempotência: limpa Sam anterior se existir
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

# 1) TB_Personagem
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (PID, "Sam", "devmaster",
     "Monge 20 — Tradição da Palma Aberta · Humano",
     "Sam-player", 20, 140, 0,  # Nv 20 = 0 próximo
     243, 243,    # PV — CSV mostra 243
     20, 5,        # CA placeholder + Iniciativa (vai ser sobrescrita por calc)
     "21 m / 70 ft",  # Vel CSV
     "Rubi",     # Patente Lv 20
     19, 6, "d8",   # Percepção passiva, Bônus Prof (Nv 20), DadoVida Monge
     "Viajante",   # Background CSV mostra "VIAJANTE"
     json.dumps({"Destreza": 1, "Sabedoria": 1, "Constituicao": 1}, ensure_ascii=False)),
)
print(f"Sam criado pid={PID}")

# 2) Escolha primária (raça/classe/sub)
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_HUMANO, None, None, ID_MONGE, ID_SUB_PALMA_ABERTA),
)

# 3) Classes
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_MONGE, ID_SUB_PALMA_ABERTA, 20, 0),
)

# 4) Atributos — placeholder Nv 20 com ASIs + bg + talentos. Final estimado:
#    FOR 12, DES 20, CON 18, INT 14, SAB 20, CAR 10 (CSV indica DES/SAB altos)
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 12, 18, 16, 14, 18, 10),  # base — ASIs + bg vão somar pra chegar nos finais
)

# 5) Perícias padrão (18) — todas Proficiente=0
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

# 6) Picks de perícia padrão Monge (escolhe 2 de Acrobacia/Atletismo/História/Intuição/Religião/Furtividade)
ESCOLHAS_PER = [("Monge", 0, "Acrobacia"), ("Monge", 1, "Furtividade")]
for origem, slot, nome in ESCOLHAS_PER:
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?", (PID, nome),
    ).fetchone()[0]
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, origem, slot, pid_per),
    )

# 7) Idiomas — Comum default + Druídico (CSV mostra)
cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
            (PID, "idioma", "Comum", "Humano (base)"))
cur.execute("INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
            (PID, "idioma", "Druídico", "aprendido"))

conn.commit()
conn.close()
print("OK — Sam pid=6 Monge 20 Palma Aberta criado.")
