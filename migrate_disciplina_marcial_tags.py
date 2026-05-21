"""Adiciona TagsJSON na hab Disciplina Marcial (Id_Habilidade=515).

Tags:
  - pick:estilo-de-luta:1  — 1 escolha no Nv 1 (TB_OpcaoJogo Tipo='estilo-de-luta').

NOTA HISTÓRICA: versão anterior incluía também `pick:maestria-arma`,
modelando-a como pick. Errado — Maestria de Armas é um VALOR somado às
Manobras Conhecidas, não uma escolha. Tag removida em 2026-05-06 via
migrate_remove_pick_maestria_arma.py. Modelagem correta de "valor somado"
pendente (provavelmente `manobras-bonus:N` com n_por_nivel).

Forma objeto com n_por_nivel — primeira hab a usar resolução por nível de
classe (ver regra-tags-universais.md §4.0).

Esta tag NÃO substitui o sistema legado (OpcaoTipoJSON + manobras_slots/
maestrias_armas_slots). Roda em paralelo. Renderização da ficha continua via
sistema legado; tag aqui é dado portável conforme regra de tags universais.
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
]
tags_json = json.dumps(tags, ensure_ascii=False)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Verifica que a hab existe e mostra estado atual.
cur.execute(
    "SELECT Id_Habilidade, Nome, NivelAdquirido, TagsJSON "
    "FROM TB_ClasseHabilidade WHERE Id_Habilidade=515"
)
row = cur.fetchone()
if not row:
    raise SystemExit('ERRO: Id_Habilidade=515 (Disciplina Marcial) nao existe.')
print(f'Antes: hab {row[0]} "{row[1]}" Nv {row[2]} TagsJSON={row[3]!r}')

cur.execute(
    "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=515",
    (tags_json,),
)
conn.commit()

cur.execute(
    "SELECT TagsJSON FROM TB_ClasseHabilidade WHERE Id_Habilidade=515"
)
print(f'Depois: TagsJSON={cur.fetchone()[0]}')

conn.close()
print('OK')
