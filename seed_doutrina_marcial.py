"""Seed: Doutrina Marcial (Paladino Nv 2) — cascade picker.

Adiciona 3 opções em TB_OpcaoJogo (Tipo='doutrina-marcial'):
  - Estilo de Luta — desbloqueia escolha de Estilo de Luta (cascade 2-stage)
  - Guerreiro Abençoado — só descrição (sem cascade adicional)
  - Armas Treinadas — desbloqueia 3 escolhas de Maestria de Armas

Configura Doutrina Marcial:
  TemEscolha=1, OpcaoTipoJSON=[{"tipo":"doutrina-marcial","quantidade":1}]

Vincula opções ao Paladino (Id_Classe=13) via TB_AcessoOpcao.
Estilo de Luta também adiciona acesso ao Paladino se não tiver (era só Guerreiro).
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

# 1. Adiciona 3 opções de Doutrina Marcial em TB_OpcaoJogo
DOUTRINAS = [
    {
        'nome': 'Estilo de Luta',
        'slug': 'estilo-de-luta-doutrina',
        'descricao': 'Você ganha um Talento de Estilo de Luta à sua escolha (Defesa, Duelo, Proteção, Combate com Armas Grandes, etc.). Desbloqueia escolha em sub-cascata.',
    },
    {
        'nome': 'Guerreiro Abençoado',
        'slug': 'guerreiro-abencoado',
        'descricao': 'Você aprende dois truques da lista de Clérigo (sugestões: Chama Sagrada, Orientação). Esses truques contam como magias de Paladino para você, e Carisma é sua habilidade de conjuração para eles.',
    },
    {
        'nome': 'Armas Treinadas',
        'slug': 'armas-treinadas',
        'descricao': 'Você ganha 3 escolhas de Maestrias de Armas com as quais você tenha proficiência. Desbloqueia 3 slots de Maestria.',
    },
]

opcao_ids = {}
for d in DOUTRINAS:
    r = cur.execute(
        "SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Tipo='doutrina-marcial' AND Nome=?",
        (d['nome'],),
    ).fetchone()
    if r:
        opcao_ids[d['nome']] = r['Id_Opcao']
        print(f'  já existe: {d["nome"]} (Id={r["Id_Opcao"]})')
        continue
    cur.execute(
        "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, SourceURL) "
        "VALUES (?, ?, 'doutrina-marcial', ?, ?)",
        (d['nome'], d['slug'], d['descricao'],
         'Bonfire Tales — Paladino Doutrina Marcial'),
    )
    new_id = cur.lastrowid
    opcao_ids[d['nome']] = new_id
    print(f'  + {d["nome"]} (Id={new_id})')

# 2. Vincula ao Paladino via TB_AcessoOpcao
for nome, oid in opcao_ids.items():
    r = cur.execute(
        "SELECT 1 FROM TB_AcessoOpcao WHERE Id_Opcao=? AND Id_Classe=13",
        (oid,),
    ).fetchone()
    if not r:
        cur.execute(
            "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, 13, NULL)",
            (oid,),
        )
        print(f'  Acesso: Paladino → {nome}')

# 3. Vincula TODOS os estilos de luta ao Paladino (originalmente só Guerreiro)
estilos = cur.execute(
    "SELECT Id_Opcao, Nome FROM TB_OpcaoJogo WHERE Tipo='estilo-de-luta'"
).fetchall()
for e in estilos:
    r = cur.execute(
        "SELECT 1 FROM TB_AcessoOpcao WHERE Id_Opcao=? AND Id_Classe=13",
        (e['Id_Opcao'],),
    ).fetchone()
    if not r:
        cur.execute(
            "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, 13, NULL)",
            (e['Id_Opcao'],),
        )
print(f'  Estilos de luta: {len(estilos)} vinculados ao Paladino')

# 4. Configura Doutrina Marcial: TemEscolha=1 + OpcaoTipoJSON com cascade.
# 5 slots no total: 1 doutrina + 1 estilo-de-luta + 3 maestria-arma.
# Frontend mostra só os slots relevantes baseado na escolha do slot 0.
opcao_tipo = [
    {"tipo": "doutrina-marcial", "quantidade": 1},
    {"tipo": "estilo-de-luta",   "quantidade": 1, "_se_slot0": "Estilo de Luta"},
    # "Armas Treinadas" não tem slot na hab — os +3 maestria-arma já são integrados
    # no widget principal "Maestrias de Armas" via TB_PersonagemHabilidadeOpcao
    # (slot do tipo armas-treinadas é detectado pelo backend).
]
cur.execute(
    "UPDATE TB_ClasseHabilidade SET TemEscolha=1, OpcaoTipoJSON=? "
    "WHERE Nome='Doutrina Marcial' AND Id_Classe=13",
    (json.dumps(opcao_tipo, ensure_ascii=False),),
)
print(f'\n  Doutrina Marcial: 5 slots cascata (1 doutrina + 1 estilo + 3 maestria)')

conn.commit()
conn.close()
print('\nOK')
