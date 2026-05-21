"""Cria Russ, o Rotundo (pid=5) — Caçador 5 (Exterminadores) / Guerreiro 2, Folken Subterraneus.

Fonte: E:\\Obsidian\\_raw\\Russ, o Rotundo - LOG.csv

Perfil:
  - Multiclasse: Caçador 5 (Ordem dos Exterminadores de Monstros) / Guerreiro 2 = Nv 7
  - Folken Subterraneus
  - Atributos base 8/17/14/17/14/8 → final 8/18/14/18/15/8 com BG +1 Dex/+1 Int/+1 Sab
  - PV 72, CA 17, BP +3, Velocidade 30ft
  - 6 perícias prof: Investigação, Natureza, Sobrevivência (Caçador choose 3) +
    Percepção (Folken Mente Genial) + Prestidigitação, Furtividade (manual/extra)

Regra do user: TUDO via picks com Origem rastreável. Nada Proficiente=1 direto.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
PID = 5  # novo personagem

ID_RACA_FOLKEN = 2
ID_LIN_SUBTERRANEUS = 8
ID_CACADOR = 4
ID_SUB_EM = 124  # Ordem dos Exterminadores de Monstros
ID_GUERREIRO = 8

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Apagar Russ existente (idempotência)
for tbl in ("TB_PersonagemEscolha", "TB_PersonagemAtributo", "TB_PersonagemTalento",
            "TB_PersonagemPericia", "TB_PersonagemEscolhaPericia", "TB_PersonagemEscolhaTag",
            "TB_PersonagemIdioma", "TB_PersonagemPersonalidade", "TB_PersonagemResistencia",
            "TB_PersonagemMagia", "TB_PersonagemTecnica", "TB_PersonagemMaestriaArma",
            "TB_PersonagemInventarioItem", "TB_PersonagemClasse"):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE Id_Personagem=?", (PID,))
    except sqlite3.OperationalError:
        pass
cur.execute("DELETE FROM TB_Personagem WHERE Id_Personagem=?", (PID,))
cur.execute("PRAGMA foreign_keys=ON")

# 1. TB_Personagem
cur.execute(
    """INSERT INTO TB_Personagem
       (Id_Personagem, Nome, DonoUsuario, Tagline, Jogador, Nivel,
        Aventuras, ProximoNivel, PVAtual, PVMaximo, CA, Iniciativa, Velocidade,
        Patente, PercepcaoPassiva, BonusProficiencia, DadoVida,
        BackgroundNome, BackgroundBonusJSON)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (PID, "Russ, o Rotundo", "devmaster",
     "Caçador 5 (Exterminador de Monstros) / Guerreiro 2 — Folken Subterraneus",
     "Seu Clóvis", 7, 17, 22, 72, 72, 17, 4, "9 m / 30 ft",
     "Topázio", 16, 3, "d10",
     "Outlander",  # background placeholder — ajustar quando souber
     json.dumps({"Destreza": 1, "Inteligencia": 1, "Sabedoria": 1}, ensure_ascii=False)),
)
print(f"Russ criado (pid={PID})")

# 2. TB_PersonagemEscolha — primária = Caçador sub Exterminadores
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_FOLKEN, ID_LIN_SUBTERRANEUS, None, ID_CACADOR, ID_SUB_EM),
)

# 3. TB_PersonagemClasse — Caçador 5 (primary) + Guerreiro 2
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_CACADOR, ID_SUB_EM, 5, 0),
)
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) VALUES (?,?,?,?,?)",
    (PID, ID_GUERREIRO, None, 2, 1),
)

# 4. TB_PersonagemAtributo — base 8/16/14/17/14/8. Final 8/18/14/18/15/8 via:
#    BG +1 Dex/+1 Int/+1 Sab → 8/17/14/18/15/8
#    Sharpshooter (ASI Caçador Nv 4) +1 Dex → 8/18/14/18/15/8
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 8, 16, 14, 17, 14, 8),
)

# 5. Perícias padrão (18) — todas Proficiente=0
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

# 6. TB_PersonagemEscolhaPericia — TUDO via picks com Origem rastreável.
# 3 do Caçador (choose 3) + 1 do Folken + 2 manuais.
ESCOLHAS = [
    ("Caçador",  0, "Investigação"),
    ("Caçador",  1, "Natureza"),
    ("Caçador",  2, "Sobrevivência"),
    ("Folken",   0, "Percepção"),
    ("manual",   0, "Prestidigitação"),
    ("manual",   1, "Furtividade"),
]
for origem, slot, nome_per in ESCOLHAS:
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome_per),
    ).fetchone()['Id_Pericia']
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,'proficiencia')""",
        (PID, origem, slot, pid_per),
    )

# 7. Idiomas — Comum default + 1 manual (Russ não tem CSV detalhado de idiomas).
cur.execute(
    "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
    (PID, "idioma", "Comum", "Folken (base)"),
)

# 8. Talentos — Folken Subterraneus tem traços/talentos racial.
# Russ Nv 1 raca: traços base Folken. Nv 5 raca: Escalador Astuto (CSV linha 51 col 26).
TALENTOS = [
    ("raca",   1,  "Subterraneus (linhagem)",            None,       None),
    ("classe", 4,  "Sharpshooter",                       "dex",      None),  # ASI Caçador Nv 4
    ("raca",   5,  "Escalador Astuto",                   None,       None),
]
for cat, niv, nome, aum, tags in TALENTOS:
    cur.execute(
        """INSERT INTO TB_PersonagemTalento
           (Id_Personagem, Categoria, Nivel, Nome, Detalhes, AumentoAtributo, TagsJSON)
           VALUES (?,?,?,?,?,?,?)""",
        (PID, cat, niv, nome, None, aum, tags),
    )

conn.commit()
conn.close()
print('OK — Russ pid=5 criado via picks (regra: tags+origem).')
