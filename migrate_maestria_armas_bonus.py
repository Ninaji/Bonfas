"""Adiciona tag acumuladora `+manobras` na hab Disciplina Marcial (Id_Habilidade=515).

Modela "Maestria de Armas" do Guerreiro como BÔNUS somado ao limite de
Manobras Conhecidas (princípio universal: tag prefixo `+` = acumulador).

Progressão: 3 (Nv 1-3) → 4 (Nv 4-9) → 5 (Nv 10-15) → 6 (Nv 16+).
Backend agregador soma tudo de qualquer fonte com a mesma chave — se o user
quiser distribuir entre múltiplas habs (3 cópias), o efeito acumula.

Mantém pick:estilo-de-luta:1 (correto). Idempotente.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

tags = [
    {"tag": "pick:estilo-de-luta", "n_por_nivel": {"1": 1}},
    {"tag": "+manobras",           "n_por_nivel": {"1": 3, "4": 4, "10": 5, "16": 6}},
]
tags_json = json.dumps(tags, ensure_ascii=False)

conn = sqlite3.connect(DB)
cur = conn.cursor()
r = cur.execute(
    "SELECT Id_Habilidade, Nome, TagsJSON FROM TB_ClasseHabilidade WHERE Id_Habilidade=515"
).fetchone()
if not r:
    raise SystemExit('ERRO: Id_Habilidade=515 nao existe.')
print(f'Antes: hab {r[0]} "{r[1]}" TagsJSON={r[2]!r}')
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=515", (tags_json,))
conn.commit()
print(f'Depois: TagsJSON={tags_json}')
conn.close()
print('OK')
