"""ALTER TB_Classe + MulticlassReqJSON + MulticlassProfJSON.

Regras D&D 5e (2024) PHB:
  - Prereq: atributo primário ≥ 13 da classe nova E das classes atuais.
    Algumas classes têm 2 atributos primários (e exigem ambos: Paladino, Monge etc.).
  - Multiclass profs: subset da starting prof. Diferentes da primeira classe.

Slugs no DB (verificados): artifice, bardo, barbaro, cacador, clerigo, druida,
feiticeiro, guerreiro, ladino, mago, mistico (NULL?), monge, paladino.

Aplicado em todas. Idempotente.
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
cols = [r['name'] for r in cur.execute('PRAGMA table_info(TB_Classe)').fetchall()]
if 'MulticlassReqJSON' not in cols:
    cur.execute("ALTER TABLE TB_Classe ADD COLUMN MulticlassReqJSON TEXT NULL")
    print('+ MulticlassReqJSON adicionada')
if 'MulticlassProfJSON' not in cols:
    cur.execute("ALTER TABLE TB_Classe ADD COLUMN MulticlassProfJSON TEXT NULL")
    print('+ MulticlassProfJSON adicionada')

# Regras por classe — keys são Slug (case-insensitive match).
# req: {"min":13, "atribs":["Forca","Carisma"], "logica":"all"|"any"}
#   "all" = precisa TODOS os atribs >= min
#   "any" = precisa pelo menos UM dos atribs >= min
# prof: lista de proficiências (texto livre) que multiclass GANHA.
RULES = {
    'barbaro':    {'req': {'min': 13, 'atribs': ['Forca'],            'logica': 'all'},
                   'prof': ['Escudos', 'Armas Marciais']},
    'bardo':      {'req': {'min': 13, 'atribs': ['Carisma'],          'logica': 'all'},
                   'prof': ['Armadura Leve', '1 Perícia (qualquer)']},
    'clerigo':    {'req': {'min': 13, 'atribs': ['Sabedoria'],        'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos']},
    'druida':     {'req': {'min': 13, 'atribs': ['Sabedoria'],        'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos (sem metal)']},
    'guerreiro':  {'req': {'min': 13, 'atribs': ['Forca', 'Destreza'],'logica': 'any'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos', 'Armas Marciais']},
    'monge':      {'req': {'min': 13, 'atribs': ['Destreza', 'Sabedoria'], 'logica': 'all'},
                   'prof': []},  # PHB 2024: monge multi não dá prof extra
    'paladino':   {'req': {'min': 13, 'atribs': ['Forca', 'Carisma'], 'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos', 'Armas Marciais']},
    'cacador':    {'req': {'min': 13, 'atribs': ['Destreza', 'Sabedoria'], 'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos', 'Armas Marciais', '1 Perícia (do Caçador)']},
    'ladino':     {'req': {'min': 13, 'atribs': ['Destreza'],         'logica': 'all'},
                   'prof': ['Armadura Leve', '1 Perícia (do Ladino)', 'Ferramentas de Ladrão']},
    'feiticeiro': {'req': {'min': 13, 'atribs': ['Carisma'],          'logica': 'all'},
                   'prof': []},
    'bruxo':      {'req': {'min': 13, 'atribs': ['Carisma'],          'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armas Simples']},
    'mago':       {'req': {'min': 13, 'atribs': ['Inteligencia'],     'logica': 'all'},
                   'prof': []},
    'artifice':   {'req': {'min': 13, 'atribs': ['Inteligencia'],     'logica': 'all'},
                   'prof': ['Armadura Leve', 'Armadura Média', 'Escudos', 'Ferramentas de Ladrão']},
    'mistico':    {'req': {'min': 13, 'atribs': ['Carisma'],          'logica': 'all'},   # Bonfire: Místico = Bruxo/Warlock
                   'prof': ['Armadura Leve', 'Armas Simples']},
}

aplicados = 0
nao_encontrados = []
for slug, rule in RULES.items():
    r = cur.execute("SELECT Id_Classe, Nome FROM TB_Classe WHERE Slug=?", (slug,)).fetchone()
    if not r:
        nao_encontrados.append(slug)
        continue
    cur.execute(
        "UPDATE TB_Classe SET MulticlassReqJSON=?, MulticlassProfJSON=? WHERE Id_Classe=?",
        (json.dumps(rule['req'], ensure_ascii=False),
         json.dumps(rule['prof'], ensure_ascii=False),
         r['Id_Classe']),
    )
    aplicados += 1
    print(f"  {r['Nome']:14}: req={rule['req']}, prof={len(rule['prof'])} item(s)")

if nao_encontrados:
    print(f'\nClasses não encontradas no DB: {nao_encontrados}')

conn.commit()
conn.close()
print(f'\nTotal aplicado: {aplicados} classe(s)')
print('OK')
