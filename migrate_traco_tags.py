"""Adiciona TagsJSON em TB_TracoRacial + tags em traços de escolha conhecidos.

Tags pra escolhas:
  - pick:pericia:N    → personagem escolhe N perícias livremente (ganha proficiência)
  - pick:ferramenta:N → idem para ferramentas (frontend ainda não implementa)
  - pick:idioma:N     → idem para idiomas
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

cols = [r['name'] for r in cur.execute('PRAGMA table_info(TB_TracoRacial)').fetchall()]
if 'TagsJSON' not in cols:
    cur.execute('ALTER TABLE TB_TracoRacial ADD COLUMN TagsJSON TEXT NULL')
    print('TagsJSON adicionada em TB_TracoRacial')

# Tags por nome do traço (idempotente)
TAGS_BY_NOME = {
    'Habilidoso':              ['pick:pericia:2'],
    'Jeitinho Humano':         ['pick:ferramenta:2'],
    'Poliglota':               ['pick:idioma:2'],
    # === Elementos de dano (resist/immune/vuln) ===
    'Sangue da Umbra e Fogo':  ['resist:Necrótico'],
    'Resiliência da Pedra':    ['resist:Veneno', 'adv-cond:Envenenado'],
    # === Condições (cond-immune / adv-cond) ===
    'Instinto Humano':         ['adv-cond:Exaustão'],
    'Ancestralidade Feérica':  ['adv-cond:Enfeitiçado'],
}
for nome, tags in TAGS_BY_NOME.items():
    cur.execute(
        'UPDATE TB_TracoRacial SET TagsJSON=? WHERE Nome=?',
        (json.dumps(tags, ensure_ascii=False), nome),
    )
    if cur.rowcount > 0:
        print(f'  Tag em "{nome}": {tags}')

conn.commit()
conn.close()
print('OK')
