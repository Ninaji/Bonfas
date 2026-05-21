"""Apaga Katherine (pid=4) e recria 1:1 com a ficha exemplo.

Fonte: E:\\Obsidian\\_raw\\Katherine Von Aulitz - LOG.csv

Perfil:
  - Multiclasse: Paladino 6 (Devoção) / Clérigo 3 (Domínio da Guerra) = Nv 9
  - Humano (Erthari), Background Soldier
  - Atributos base: For 12, Des 8, Con 14, Int 10, Sab 13, Car 16
    (com BG Soldier +1/+1/+1 + Resilient Con +1 + ASI Cha+2 → final 13/8/16/10/14/18)
  - PV 100, CA 18, Velocidade 30ft, Patente Topázio
  - Talentos: Tough (geral 1), Tatuagens Arcanas (raça 1), Magic Initiate (extra),
    Resilient Constitution (geral 4 con), Tatuagens Aprimoradas (raça 5),
    Charisma +2 (geral 8), Vontade de Ferro (raça 9 int)
  - Perícias prof: Atletismo, Intuição, Percepção, Persuasão, Religião, Sobrevivência
  - Idiomas: Comum, Celestial, Feérico, Folken, Draconico
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
PID = 4

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# FK off pra deletar tabela-pai mesmo sem cascade configurado em todas as filhas.
cur.execute("PRAGMA foreign_keys=OFF")

# 1. APAGAR — primeiro filhas, depois pai (defensivo).
for tbl in (
    "TB_PersonagemEscolha", "TB_PersonagemAtributo", "TB_PersonagemTalento",
    "TB_PersonagemPericia", "TB_PersonagemEscolhaPericia", "TB_PersonagemEscolhaTag",
    "TB_PersonagemIdioma", "TB_PersonagemPersonalidade", "TB_PersonagemResistencia",
    "TB_PersonagemMagia", "TB_PersonagemTecnica", "TB_PersonagemMaestriaArma",
    "TB_PersonagemInventarioItem", "TB_PersonagemClasse",
):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE Id_Personagem=?", (PID,))
        if cur.rowcount > 0:
            print(f"  cleanup {tbl}: {cur.rowcount} rows")
    except sqlite3.OperationalError:
        pass  # tabela pode não existir
cur.execute("DELETE FROM TB_Personagem WHERE Id_Personagem=?", (PID,))
print(f"DELETE TB_Personagem id={PID}: {cur.rowcount} row")
cur.execute("PRAGMA foreign_keys=ON")

# 2. RECRIAR personagem base — Multiclasse Paladino 6 / Clérigo 3 (Nv total 9)
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (
        PID, "Katherine Von Aulitz", "devmaster",
        "Paladino 6 (Devoção) / Clérigo 3 (Domínio da Guerra)",
        "Rhogar", 9, 33, 35, 100, 100, 18, -1, "9 m / 30 ft",
        "Topázio", 16, 4, "d10",  # BP +4 pra Nv 9, Percepção passiva = 10+SAB(2)+BP(4)=16
        "Soldier", json.dumps({"Forca": 1, "Constituicao": 1, "Sabedoria": 1}, ensure_ascii=False),
    ),
)
print(f"INSERT TB_Personagem id={PID}: criado (Nv 9)")

# Pré-requisitos
id_raca = cur.execute("SELECT Id_Raca FROM TB_Raca WHERE Slug='humano'").fetchone()['Id_Raca']
id_lin = cur.execute("SELECT Id_Linhagem FROM TB_Linhagem WHERE Id_Raca=? LIMIT 1", (id_raca,)).fetchone()['Id_Linhagem']
id_paladino = cur.execute("SELECT Id_Classe FROM TB_Classe WHERE Slug='paladino'").fetchone()['Id_Classe']
id_clerigo = cur.execute("SELECT Id_Classe FROM TB_Classe WHERE Slug='clerigo'").fetchone()['Id_Classe']
id_sub_pal = 103   # Devoção (Paladino)
id_sub_cle = 108   # Domínio da Guerra (Clérigo)
print(f"  raca={id_raca} linhagem={id_lin} paladino={id_paladino} clerigo={id_clerigo} sub_pal={id_sub_pal} sub_cle={id_sub_cle}")

# 3. TB_PersonagemEscolha — primária = Paladino sub Devoção
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, id_raca, id_lin, None, id_paladino, id_sub_pal),
)

# 4. TB_PersonagemClasse — multiclasse Paladino 6 + Clérigo 3
cur.execute(
    """INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem)
       VALUES (?,?,?,?,?)""",
    (PID, id_paladino, id_sub_pal, 6, 0),
)
cur.execute(
    """INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem)
       VALUES (?,?,?,?,?)""",
    (PID, id_clerigo, id_sub_cle, 3, 1),
)

# 5. TB_PersonagemAtributo — base. Atributos finais 13/8/16/10/14/18 são alcançados via:
#    +1/+1/+1 do Soldier (For/Con/Sab) + Resilient Con (+1) + ASI Cha+2.
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 12, 8, 14, 10, 13, 16),
)

# 6. Perícias padrão (18) — todas Proficiente=0/Expertise=0.
# Proficiências derivam de TB_PersonagemEscolhaPericia (regra: prof rastreável via Origem).
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
        """INSERT INTO TB_PersonagemPericia
           (Id_Personagem, Nome, Atributo, Proficiente, Expertise)
           VALUES (?,?,?,0,0)""",
        (PID, nome, atr),
    )

# 6.b TB_PersonagemEscolhaPericia — 6 prof distribuídas em 3 fontes (Soldier/Paladino/Habilidoso),
# cada uma com 2 picks. Backend agrega: Proficiente=1 derivado.
ESCOLHAS_PER = [
    ("Soldier",    0, "Atletismo"),
    ("Soldier",    1, "Sobrevivência"),
    ("Paladino",   0, "Persuasão"),
    ("Paladino",   1, "Religião"),
    ("Habilidoso", 0, "Intuição"),
    ("Habilidoso", 1, "Percepção"),
]
for origem, slot, nome_per in ESCOLHAS_PER:
    pid_pericia = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome_per),
    ).fetchone()['Id_Pericia']
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, origem, slot, pid_pericia),
    )

# 7. Idiomas — todos com Origem rastreável (regra: via picks/fontes).
# Comum é default humano. 2 picks via Poliglota. 2 outros via Soldier (background militar).
IDIOMAS = [
    ("Humano (base)",     "Comum"),
    ("pick:Poliglota:0",  "Celestial"),
    ("pick:Poliglota:1",  "Feérico"),
    ("pick:Soldier:0",    "Folken"),
    ("pick:Soldier:1",    "Dracônico"),
]
for origem, nome in IDIOMAS:
    cur.execute(
        "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
        (PID, "idioma", nome, origem),
    )

# 8. Save Int via Vontade de Ferro: como Katherine tem Sab default (Paladino),
# o picker save-prof-vontade dispara entre Int/Car. CSV mostra Int prof → escolha Int.
cur.execute(
    """INSERT INTO TB_PersonagemEscolhaTag
       (Id_Personagem, Origem, Tipo, SlotIndex, Valor)
       VALUES (?,'Vontade de Ferro','save-prof-vontade',0,'Inteligencia')""",
    (PID,),
)

# 9. Talentos — Categoria/Nivel/Nome/Detalhes/AumentoAtributo/TagsJSON
# IMPORTANTE: ASIs (Nv 4/8) usam Categoria='classe' pq _atributos_efetivos
# só processa AumentoAtributo de talentos categoria 'classe' ou 'extra'.
# Resilient Constitution: também ganha tag save-prof:Constituicao (efeito do talento).
# IDs dos TalentoRacial pra vincular (puxa TagsJSON do catálogo via Id_TalentoRacial)
ID_TR_TATUAGENS = 7    # Tatuagens Arcanas
ID_TR_TATUAGENS_APR = 11  # Tatuagens Aprimoradas
ID_TR_VONTADE = 19     # Vontade de Ferro (TagsJSON ["humano", "save-prof-vontade:..."])

TALENTOS = [
    # (cat, nv, nome, aum, tags, id_talento_racial)
    ("extra",  1,  "Tough",                              None,    None,                              None),
    ("extra",  1,  "Magic Initiate (Wizard)",            None,    None,                              None),
    ("raca",   1,  "Tatuagens Arcanas",                  None,    None,                              ID_TR_TATUAGENS),
    ("classe", 4,  "Resilient (Constitution)",           "con",   '["save-prof:Constituicao"]',       None),
    ("raca",   5,  "Tatuagens Aprimoradas",              None,    None,                              ID_TR_TATUAGENS_APR),
    ("classe", 8,  "Aumento de Atributo (+2 Carisma)",   "car,car", None,                            None),
    ("raca",   9,  "Vontade de Ferro",                   "int",   None,                              ID_TR_VONTADE),
]
for cat, niv, nome, aum, tags, id_tr in TALENTOS:
    cur.execute(
        """INSERT INTO TB_PersonagemTalento
           (Id_Personagem, Categoria, Nivel, Nome, Detalhes, AumentoAtributo, TagsJSON, Id_TalentoRacial)
           VALUES (?,?,?,?,?,?,?,?)""",
        (PID, cat, niv, nome, None, aum, tags, id_tr),
    )

conn.commit()
conn.close()
print('OK — Katherine 1:1 com CSV (Paladino 6 Devoção / Clérigo 3 Guerra, Nv 9).')
