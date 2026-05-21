"""Adiciona `cond-immune:Enfeitiçado` na Aura da Devoção (hab 1266, Paladino sub Nv 7).

Sub-classe "Juramento da Devoção" do Paladino — Aura of Devotion 5.5e dá imunidade
a Enfeitiçado (Charmed) pro Paladino e aliados na aura. Modelagem mínima: tag no
Paladino dono. Aliados ficam fora (sistema não modela auras-de-grupo).

Nota: condição canônica do projeto é "Enfeitiçado" (PT-BR 5.5e BR), não "Encantado"
(nome de outras edições). User pediu "encantado" → tag canônica equivalente.

Idempotente: preserva tags existentes.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'
HID = 1266
NOVA_TAG = "cond-immune:Enfeitiçado"

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

r = cur.execute(
    "SELECT Id_Habilidade, Nome, NivelAdquirido, TagsJSON "
    "FROM TB_ClasseHabilidade WHERE Id_Habilidade=?",
    (HID,),
).fetchone()
if not r:
    raise SystemExit(f'Hab {HID} nao encontrada')
print(f"Antes: hab {r['Id_Habilidade']} '{r['Nome']}' Nv{r['NivelAdquirido']} TagsJSON={r['TagsJSON']!r}")

try:
    tags = json.loads(r['TagsJSON'] or "[]") or []
except (json.JSONDecodeError, TypeError):
    tags = []
ja_tem = any(
    (t == NOVA_TAG) or (isinstance(t, dict) and t.get("tag") == NOVA_TAG)
    for t in tags
)
if ja_tem:
    print("Ja tem tag — skip")
else:
    tags.append(NOVA_TAG)
    cur.execute(
        "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
        (json.dumps(tags, ensure_ascii=False), HID),
    )
    print(f"Depois: TagsJSON={json.dumps(tags, ensure_ascii=False)}")

conn.commit()
conn.close()
print('OK')
