"""Modela hab 'Ordem Sagrada' (1306, Clérigo Nv 1) como pick:ordem-sagrada:1
com 2 opções: Protetor e Taumaturgo.

Cada opção carrega TagsJSON própria (tag categórica por agora; efeitos
mecânicos detalhados — prof:armas-marciais, +truque-mago, etc — ficam pra
próxima iteração quando o user pedir).

Idempotente: usa Slug pra detectar duplicatas.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
ID_CLASSE_CLERIGO = 5
HID = 1306

OPCOES = [
    {
        "Nome": "Protetor",
        "Slug": "ordem-sagrada-protetor",
        "Tipo": "ordem-sagrada",
        "Descricao": "Treinado para a linha de frente. Você ganha proficiência com Armas Marciais e treinamento com Armadura Pesada.",
        "TagsJSON": json.dumps(["protetor"], ensure_ascii=False),
    },
    {
        "Nome": "Taumaturgo",
        "Slug": "ordem-sagrada-taumaturgo",
        "Tipo": "ordem-sagrada",
        "Descricao": "Você aprende um truque adicional da lista de magias do Mago (conta como magia de Clérigo). Sempre que fizer um teste de Inteligência (Arcanismo), adicione bônus igual ao seu modificador de Sabedoria (mínimo +1).",
        "TagsJSON": json.dumps(["taumaturgo"], ensure_ascii=False),
    },
]
HAB_TAGS = [{"tag": "pick:ordem-sagrada", "n_por_nivel": {"1": 1}}]

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Insert/update opções (idempotente via Slug)
for o in OPCOES:
    existing = cur.execute(
        "SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?",
        (o["Slug"],),
    ).fetchone()
    if existing:
        cur.execute(
            "UPDATE TB_OpcaoJogo SET Nome=?, Tipo=?, Descricao=?, TagsJSON=? WHERE Slug=?",
            (o["Nome"], o["Tipo"], o["Descricao"], o["TagsJSON"], o["Slug"]),
        )
        id_opcao = existing["Id_Opcao"]
        print(f"  TB_OpcaoJogo '{o['Nome']}' (id {id_opcao}): atualizada")
    else:
        cur.execute(
            "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, TagsJSON) VALUES (?,?,?,?,?)",
            (o["Nome"], o["Slug"], o["Tipo"], o["Descricao"], o["TagsJSON"]),
        )
        id_opcao = cur.lastrowid
        print(f"  TB_OpcaoJogo '{o['Nome']}' (id {id_opcao}): INSERIDA")
    # Acesso: vincular à classe Clérigo
    cur.execute(
        "INSERT OR IGNORE INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?,?,NULL)",
        (id_opcao, ID_CLASSE_CLERIGO),
    )
    if cur.rowcount > 0:
        print(f"    + acesso vinculado a Clérigo (Id_Classe={ID_CLASSE_CLERIGO})")

# 2. Atualizar hab 1306 com TagsJSON
cur.execute(
    "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
    (json.dumps(HAB_TAGS, ensure_ascii=False), HID),
)
print(f"\nHab {HID} 'Ordem Sagrada': TagsJSON={json.dumps(HAB_TAGS, ensure_ascii=False)}")

conn.commit()
conn.close()
print('OK')
