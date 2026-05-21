"""Modelar Doutrina Marcial como `pick:doutrina-marcial:1` cuja escolha
ATIVA tags da opção via TB_OpcaoJogo.TagsJSON.

Estrutura:
  - Hab 1230 "Doutrina Marcial": TagsJSON = ["pick:doutrina-marcial:1"]
    (só a escolha primária; tags-efeito vêm da opção escolhida)
  - TB_OpcaoJogo Tipo='doutrina-marcial' (3 rows):
      "Estilo de Luta"      → ["pick:estilo-de-luta:1"]
      "Armas Treinadas"     → ["+maestrias-arma:3"]
      "Guerreiro Abençoado" → ["guerreiro-abencoado"]   (categorica)

Backend (próximo passo, paralelo) lê TagsJSON da opção escolhida e propaga.

Idempotente. Backup automático.
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


# ---------------------------------------------------------------------------
# 1. Hab 1230 Doutrina Marcial — apenas pick:doutrina-marcial:1
# ---------------------------------------------------------------------------
hab_tags = [{"tag": "pick:doutrina-marcial", "n_por_nivel": {"1": 1}}]
cur.execute(
    "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=1230",
    (json.dumps(hab_tags, ensure_ascii=False),),
)
print(f'Hab 1230 Doutrina Marcial: TagsJSON = {json.dumps(hab_tags, ensure_ascii=False)}')


# ---------------------------------------------------------------------------
# 2. TB_OpcaoJogo Tipo='doutrina-marcial' — popular TagsJSON
# ---------------------------------------------------------------------------
TAGS_POR_NOME = {
    "Estilo de Luta":      ["pick:estilo-de-luta:1"],
    "Armas Treinadas":     ["+maestrias-arma:3"],
    "Guerreiro Abençoado": ["guerreiro-abencoado"],
}
for nome, tags in TAGS_POR_NOME.items():
    cur.execute(
        "UPDATE TB_OpcaoJogo SET TagsJSON=? WHERE Tipo='doutrina-marcial' AND Nome=?",
        (json.dumps(tags, ensure_ascii=False), nome),
    )
    if cur.rowcount > 0:
        print(f"  TB_OpcaoJogo '{nome}': TagsJSON = {tags}")
    else:
        print(f"  AVISO: opção '{nome}' não encontrada (Tipo='doutrina-marcial').")


conn.commit()
conn.close()
print('OK')
