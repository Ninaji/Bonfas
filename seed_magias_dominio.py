"""ALTER TB_Subclasse + popula MagiaExpandidaJSON pra Domínio da Guerra.

Regra: as Magias de Domínio são SEMPRE PREPARADAS quando o personagem atinge
o nível total ≥ nivel_personagem_min. Para multiclasse (ex.: Katherine
Pal 6 + Cle 3 = 9), todos os 4 tiers (3°/5°/7°/9° de clérigo) ficam unlocked.

Estrutura compatível com magia_expandida do talento_origem:
  fonte_lista: nível da magia ("1" a "9")
  auto_preparada: true (sempre preparada quando atinge o nível)
  nivel_personagem_min: nível total mínimo pra unlock
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ALTER (idempotente)
cols = [r['name'] for r in cur.execute('PRAGMA table_info(TB_Subclasse)').fetchall()]
if 'MagiaExpandidaJSON' not in cols:
    cur.execute('ALTER TABLE TB_Subclasse ADD COLUMN MagiaExpandidaJSON TEXT NULL')
    print('+ MagiaExpandidaJSON adicionada em TB_Subclasse')

# Magias de Domínio — Domínio da Guerra (Id_Subclasse=108)
# Tier do clérigo (3°/5°/7°/9°) → nivel_personagem_min
GUERRA_MAGIAS = [
    # Tier 3° (Pal+Cle total ≥ 3)
    {"nome": "Raio Guiador",         "nome_ingles": "Guiding Bolt",      "fonte_lista": "1", "auto_preparada": True, "nivel_personagem_min": 3},
    {"nome": "Escudo da Fé",         "nome_ingles": "Shield of Faith",   "fonte_lista": "1", "auto_preparada": True, "nivel_personagem_min": 3},
    {"nome": "Esquentar Metal",      "nome_ingles": "Heat Metal",        "fonte_lista": "2", "auto_preparada": True, "nivel_personagem_min": 3},
    {"nome": "Arma Mágica",          "nome_ingles": "Magic Weapon",      "fonte_lista": "2", "auto_preparada": True, "nivel_personagem_min": 3},
    # Tier 5°
    {"nome": "Manto do Cruzado",     "nome_ingles": "Crusader's Mantle", "fonte_lista": "3", "auto_preparada": True, "nivel_personagem_min": 5},
    {"nome": "Espíritos Guardiões",  "nome_ingles": "Spirit Guardians",  "fonte_lista": "3", "auto_preparada": True, "nivel_personagem_min": 5},
    # Tier 7°
    {"nome": "Escudo Flamejante",    "nome_ingles": "Fire Shield",       "fonte_lista": "4", "auto_preparada": True, "nivel_personagem_min": 7},
    {"nome": "Movimento Irrestrito", "nome_ingles": "Freedom of Movement","fonte_lista": "4", "auto_preparada": True, "nivel_personagem_min": 7},
    # Tier 9°
    {"nome": "Imobilizar Monstro",   "nome_ingles": "Hold Monster",      "fonte_lista": "5", "auto_preparada": True, "nivel_personagem_min": 9},
    {"nome": "Vendaval de Aço",      "nome_ingles": "Steel Wind Strike", "fonte_lista": "5", "auto_preparada": True, "nivel_personagem_min": 9},
]

cur.execute(
    "UPDATE TB_Subclasse SET MagiaExpandidaJSON=? WHERE Id_Subclasse=?",
    (json.dumps(GUERRA_MAGIAS, ensure_ascii=False), 108),
)
print(f'  Domínio da Guerra (Id 108): {len(GUERRA_MAGIAS)} magias auto-prep configuradas')

# Magias de Juramento — Juramento da Devoção (Paladino, Id_Subclasse=103)
# Tier de paladino (3°/5°/9°/13°/17°) → unlock no nivel_total do personagem.
DEVOCAO_MAGIAS = [
    # Tier 3°
    {"nome": "Proteção Contra o Bem e o Mal", "nome_ingles": "Protection from Evil and Good", "fonte_lista": "1", "auto_preparada": True, "nivel_personagem_min": 3},
    {"nome": "Escudo da Fé",                  "nome_ingles": "Shield of Faith",                "fonte_lista": "1", "auto_preparada": True, "nivel_personagem_min": 3},
    # Tier 5°
    {"nome": "Auxílio",                       "nome_ingles": "Aid",                            "fonte_lista": "2", "auto_preparada": True, "nivel_personagem_min": 5},
    {"nome": "Zona da Verdade",               "nome_ingles": "Zone of Truth",                  "fonte_lista": "2", "auto_preparada": True, "nivel_personagem_min": 5},
    # Tier 9°
    {"nome": "Farol da Esperança",            "nome_ingles": "Beacon of Hope",                 "fonte_lista": "3", "auto_preparada": True, "nivel_personagem_min": 9},
    {"nome": "Dissipar Magia",                "nome_ingles": "Dispel Magic",                   "fonte_lista": "3", "auto_preparada": True, "nivel_personagem_min": 9},
    # Tier 13°
    {"nome": "Aura da Vida",                  "nome_ingles": "Aura of Life",                   "fonte_lista": "4", "auto_preparada": True, "nivel_personagem_min": 13},
    {"nome": "Movimento Irrestrito",          "nome_ingles": "Freedom of Movement",            "fonte_lista": "4", "auto_preparada": True, "nivel_personagem_min": 13},
    # Tier 17°
    {"nome": "Comunhão",                      "nome_ingles": "Commune",                        "fonte_lista": "5", "auto_preparada": True, "nivel_personagem_min": 17},
    {"nome": "Alvorada",                      "nome_ingles": "Dawn",                           "fonte_lista": "5", "auto_preparada": True, "nivel_personagem_min": 17},
]
cur.execute(
    "UPDATE TB_Subclasse SET MagiaExpandidaJSON=? WHERE Id_Subclasse=?",
    (json.dumps(DEVOCAO_MAGIAS, ensure_ascii=False), 103),
)
print(f'  Juramento da Devoção (Id 103): {len(DEVOCAO_MAGIAS)} magias auto-prep configuradas')

conn.commit()
conn.close()
print('OK')
