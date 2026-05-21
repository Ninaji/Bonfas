"""Cria Arthus Burrows (pid=8) — Humano Erthari, Mago 20 Transmutador.

Fonte: E:\\Obsidian\\_raw\\Arthus Burrows - LOG.csv (CSV em Nv 9, talentos
mapeados até Nv 19 — popula Mago 20 conforme pedido do user).

Decisões editoriais (declaradas — Regra #0):
  - Subclasse: TRANSMUTADOR. CSV não diz explicitamente a Tradição Arcana, mas
    talentos têm tema biomancia/cura/dragão ("Estudante de Biomancia",
    "Marca Superior da Cura", "Marca do Dragão Potente", "Boon of Syberis
    Regeneração"). Transmutador é a melhor amarra. Se errar, ajustar via:
      UPDATE TB_PersonagemEscolha SET Id_Subclasse=<novo> WHERE Id_Personagem=8;
      UPDATE TB_PersonagemClasse SET Id_Subclasse=<novo> WHERE Id_Personagem=8;
  - HP/CA/BP: projetados pro Nv 20 (CSV trazia Nv 9). Mago d6 médio 4 × 20 +
    CON_mod*20 = base ~80 com Resiliente Constituição (Nv 16) levando CON 8→9.

Perfil:
  - Mago 20 (Transmutador) — full caster INT
  - Humano Erthari
  - Atributos base 8/10/8/16/14/10 → final 8/11/9/18/14/10 com BG INT+2 DES+1
    e Resiliente Constituição CON+1 (Nv 16)
  - Patente: Topázio (linha 32 c47 do CSV)
  - Background: Estudante de Biomancia
  - Talentos: 6 gerais (Nv 1/4/8/12/16/19) + 5 raciais (Nv 1/5/9/13/17) +
    2 extras (Nv 1/13). Tudo do CSV — nada inventado.
  - Idiomas: Comum, Erthari, Sinais, Dracônico, Herbalismo, Alquimia

Regra do user: TUDO via picks com Origem rastreável.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
PID = 8

# IDs verificados via SELECT no DB:
ID_RACA_HUMANO = 1
ID_LIN_ERTHARI = 1     # Humano Erthari
ID_MAGO = 10
ID_SUB_TRANSMUTADOR = 61

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys=OFF")

# Idempotência: apaga TUDO de pid=8 antes de inserir
for tbl in ("TB_PersonagemEscolha", "TB_PersonagemAtributo", "TB_PersonagemTalento",
            "TB_PersonagemPericia", "TB_PersonagemEscolhaPericia", "TB_PersonagemEscolhaTag",
            "TB_PersonagemIdioma", "TB_PersonagemPersonalidade", "TB_PersonagemResistencia",
            "TB_PersonagemMagia", "TB_PersonagemTecnica", "TB_PersonagemMaestriaArma",
            "TB_PersonagemInventarioItem", "TB_PersonagemClasse",
            "TB_EquipamentoPersonagem"):
    try:
        cur.execute(f"DELETE FROM {tbl} WHERE Id_Personagem=?" if tbl != "TB_EquipamentoPersonagem"
                    else f"DELETE FROM {tbl} WHERE CharacterId=?",
                    (PID if tbl != "TB_EquipamentoPersonagem" else str(PID),))
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
    (PID, "Arthus Burrows", "devmaster",
     "Mago Transmutador — Humano Erthari · Estudante de Biomancia",
     "Mozart Prado da Silva", 20, 100, 999, 80, 80, 13, 1, "9 m / 30 ft",
     "Topázio", 9, 6, "d6",
     "Estudante de Biomancia",
     json.dumps({"Inteligencia": 2, "Destreza": 1}, ensure_ascii=False)),
)
print(f"Arthus criado (pid={PID})")

# 2. TB_PersonagemEscolha — primária
cur.execute(
    """INSERT INTO TB_PersonagemEscolha
       (Id_Personagem, Id_Raca, Id_Linhagem, Id_Essencia, Id_Classe, Id_Subclasse)
       VALUES (?,?,?,?,?,?)""",
    (PID, ID_RACA_HUMANO, ID_LIN_ERTHARI, None, ID_MAGO, ID_SUB_TRANSMUTADOR),
)

# 3. TB_PersonagemClasse — Mago 20 / Transmutador
cur.execute(
    "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) "
    "VALUES (?,?,?,?,?)",
    (PID, ID_MAGO, ID_SUB_TRANSMUTADOR, 20, 0),
)

# 4. TB_PersonagemAtributo — base 8/10/8/16/14/10
# BG aplica via BackgroundBonusJSON (Int+2 Dex+1): final 8/11/8/18/14/10.
# Resiliente Constituição (Nv 16 geral) tradicional dá +1 CON e prof CON saves —
# o ASI fica no talento; CON base permanece 8 e o agregador soma +1 via TagsJSON.
cur.execute(
    """INSERT INTO TB_PersonagemAtributo
       (Id_Personagem, Forca, Destreza, Constituicao, Inteligencia, Sabedoria, Carisma)
       VALUES (?,?,?,?,?,?,?)""",
    (PID, 8, 10, 8, 16, 14, 10),
)

# 5. Perícias padrão (18) — todas Proficiente=0; picks via TB_PersonagemEscolhaPericia
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
        "INSERT INTO TB_PersonagemPericia (Id_Personagem, Nome, Atributo, Proficiente, Expertise) "
        "VALUES (?,?,?,0,0)",
        (PID, nome, atr),
    )

# 6. TB_PersonagemEscolhaPericia — Origem rastreável
# Mago choose 2 (Arcanismo, História do CSV) +
# BG "Estudante de Biomancia" (Arcanismo+Natureza expertise) +
# Talentos (Religião e Medicina via "Habilidoso") +
# Mente Afiada - Medicina (Mago Nv 9 — expertise em Medicina)
ESCOLHAS = [
    ("Mago",                 0, "Arcanismo",    "proficiencia"),
    ("Mago",                 1, "História",     "proficiencia"),
    ("BG-Biomancia",         0, "Investigação", "proficiencia"),
    ("BG-Biomancia",         1, "Natureza",     "proficiencia"),
    ("BG-Biomancia",         2, "Arcanismo",    "expertise"),
    ("BG-Biomancia",         3, "Natureza",     "expertise"),
    ("Habilidoso",           0, "Religião",     "proficiencia"),
    ("Habilidoso",           1, "Medicina",     "proficiencia"),
    ("Mente Afiada",         0, "Medicina",     "expertise"),
]
for origem, slot, nome_per, tipo in ESCOLHAS:
    pid_per = cur.execute(
        "SELECT Id_Pericia FROM TB_PersonagemPericia WHERE Id_Personagem=? AND Nome=?",
        (PID, nome_per),
    ).fetchone()['Id_Pericia']
    cur.execute(
        """INSERT INTO TB_PersonagemEscolhaPericia
           (Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo)
           VALUES (?,?,?,?,?)""",
        (PID, origem, slot, pid_per, tipo),
    )

# 7. Talentos — todos do CSV (col 17 Geral, col 25 Raça, col 33 Extras)
TALENTOS = [
    # Categoria, Nível, Nome, Detalhes, AumentoAtributo, TagsJSON
    # GERAL
    ("geral",  1,  "Iniciado em Alta Feitiçaria",                  None, None, None),
    ("geral",  4,  "Adepto dos Mantos Vermelhos",                  None, None, None),
    ("geral",  8,  "Marca Superior da Cura",                       None, None, None),
    ("geral",  12, "Marca do Dragão Potente",                      None, None, None),
    ("geral",  16, "Resiliente Constituição",                      "con", "con", None),  # +1 CON + prof saves CON
    ("geral",  19, "Boon of Syberis — Marca da Cura — Regeneração", None, None, None),
    # RAÇA (Humano Erthari)
    ("raca",   1,  "Tatuagens Arcanas",                            None, None, None),
    ("raca",   5,  "Tatuagens Aprimoradas",                        None, None, None),
    ("raca",   9,  "Tatuagens Virtuosas",                          None, None, None),
    ("raca",   13, "Multi Talentoso",                              None, None, None),
    ("raca",   17, "Frio e Calculista",                            None, None, None),
    # EXTRAS
    ("extra",  1,  "Marca da Cura — Origem Humano",                None, None, None),
    ("extra",  13, "Conjurador de Guerra",                         None, None, None),
]
for cat, niv, nome, det, aum, tags in TALENTOS:
    cur.execute(
        """INSERT INTO TB_PersonagemTalento
           (Id_Personagem, Categoria, Nivel, Nome, Detalhes, AumentoAtributo, TagsJSON)
           VALUES (?,?,?,?,?,?,?)""",
        (PID, cat, niv, nome, det, aum, tags),
    )

# 8. Idiomas (CSV menciona Sinais e Dracônico via Poliglota, e Herbalismo+Alquimia via Jeitinho Humano)
IDIOMAS = [
    ("idioma", "Comum",     "base"),
    ("idioma", "Erthari",   "linhagem Erthari"),
    ("idioma", "Sinais",    "Poliglota"),
    ("idioma", "Dracônico", "Poliglota"),
    ("ferramenta", "Herbalismo", "Jeitinho Humano"),
    ("ferramenta", "Alquimia",   "Jeitinho Humano"),
    ("ferramenta", "Caligrafia", "BG Estudante de Biomancia"),
    ("ferramenta", "Cartografia", "BG Estudante de Biomancia"),
]
for tipo, nome, origem in IDIOMAS:
    cur.execute(
        "INSERT INTO TB_PersonagemIdioma (Id_Personagem, Tipo, Nome, Origem) VALUES (?,?,?,?)",
        (PID, tipo, nome, origem),
    )

# 9. Inventário (campos visíveis no CSV)
INVENTARIO = [
    (1, "Cajado Farryn do Bosque Verdejante (Evento)", None, None, 1),
    (1, "Grimório +1",                                  None, None, 1),
    (1, "Adaga",                                        "2 gp", "1 lb", 0),
    (1, "Pacote de Estudioso",                          "40 gp", "—", 0),
    (1, "Tinta",                                        "10 gp", "—", 0),
    (1, "Estojo de Pergaminhos",                        "1 gp", "—", 0),
    (1, "Manto",                                        None, None, 0),
]
for qtd, item, custo, peso, sint in INVENTARIO:
    cur.execute(
        """INSERT INTO TB_PersonagemInventarioItem
           (Id_Personagem, Qtd, Item, Custo, Peso, Sintonizado)
           VALUES (?,?,?,?,?,?)""",
        (PID, qtd, item, custo, peso, sint),
    )

conn.commit()
conn.close()
print(f'OK — Arthus Burrows pid={PID} criado.')
print(f'  Classe: Mago 20 (Transmutador) — full caster INT')
print(f'  Atributos base: FOR 8 DES 10 CON 8 INT 16 SAB 14 CAR 10')
print(f'  + BG (INT+2, DES+1) → final 8/11/8/18/14/10')
print(f'  + Resiliente Constituição (Nv 16) → CON 9 (via aggregator de tag "con")')
print(f'  Talentos: {len(TALENTOS)} (6 geral + 5 raça + 2 extra)')
print(f'  Perícias prof: {len(ESCOLHAS)} picks (Origem rastreável)')
print(f'  Idiomas/Ferramentas: {len(IDIOMAS)}')
