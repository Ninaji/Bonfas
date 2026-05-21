"""Popula Ladino: TB_Classe (profs/multiclass/equip/skills/ASIs) + 8 Trilhas
(taglines) + 27 class features + 55 subclass features.

Wipe + reinsert porque o estado atual está corrompido — Trapaceiro Arcano tem
50 habs erradas (class features que deveriam ser Id_Subclasse=NULL).

Backup automático. NÃO inventa nada — tudo vem dos JSONs gerados por parse_ladino_full.py.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_LADINO = 9  # confirmado no DB

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("ladino_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("ladino_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("ladino_subs.json").read_text(encoding="utf-8"))

# ASINiveisJSON: [4, 8, 10, 12, 16, 19] — Ladino tem ASI extra Nv 10 (canônico 5e/5.5e)
ASI_NIVEIS = [4, 8, 10, 12, 16, 19]

# Equipamento Inicial canônico (opção A) + ALT B = 100 PO
EQUIPAMENTO_INICIAL = [
    {"qtd": 1,  "nome": "Armadura de Couro",        "tipo": "armor",  "valor": "10 gp"},
    {"qtd": 2,  "nome": "Adaga",                    "tipo": "weapon", "valor": "2 gp"},
    {"qtd": 1,  "nome": "Espada Curta",             "tipo": "weapon", "valor": "10 gp"},
    {"qtd": 1,  "nome": "Arco Curto",               "tipo": "weapon", "valor": "25 gp"},
    {"qtd": 20, "nome": "Flecha",                   "tipo": "weapon", "valor": "1 gp"},
    {"qtd": 1,  "nome": "Aljava",                   "tipo": "gear",   "valor": "1 gp"},
    {"qtd": 1,  "nome": "Ferramentas de Ladrão",    "tipo": "tool",   "valor": "25 gp"},
    {"qtd": 1,  "nome": "Pacote de Assaltante",     "tipo": "pack",   "valor": "16 gp"},
    {"qtd": 1,  "nome": "Bolsa com 8 PO",           "tipo": "gold",   "valor": "8 gp"},
    {"qtd": 0,  "nome": "ALT: 100 PO (Opção B)",    "tipo": "alt",    "valor": "100 gp"},
]

# WeaponProf: decompõe a frase canônica em 3 entries semânticas
WEAPON_PROF = [
    "Armas Simples",
    "Armas Marciais com Acuidade ou Leve",
    "Armas de Fogo",
]


def upsert_classe_metadata(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """UPDATE TB_Classe SET
              SkillsJSON              = ?,
              ArmorProfJSON           = ?,
              WeaponProfJSON          = ?,
              ToolProfJSON            = ?,
              EquipamentoInicialJSON  = ?,
              MulticlassProfJSON      = ?,
              SavesJSON               = ?,
              ASINiveisJSON           = ?
           WHERE Id_Classe = ?""",
        (
            json.dumps(META["skills"], ensure_ascii=False),
            json.dumps(META["armor_prof"], ensure_ascii=False),
            json.dumps(WEAPON_PROF, ensure_ascii=False),
            json.dumps(META["tool_prof"], ensure_ascii=False),
            json.dumps(EQUIPAMENTO_INICIAL, ensure_ascii=False),
            json.dumps(META["multiclass_prof"], ensure_ascii=False),
            json.dumps(META["saves"], ensure_ascii=False),
            json.dumps(ASI_NIVEIS, ensure_ascii=False),
            ID_LADINO,
        ),
    )


def upsert_sub_tagline(cur: sqlite3.Cursor, sub: dict) -> tuple[int, str]:
    """Garante Nome+Slug+Tagline corretos. Retorna (Id_Subclasse, status)."""
    row = cur.execute(
        "SELECT Id_Subclasse, Nome, Tagline FROM TB_Subclasse "
        "WHERE Id_Classe=? AND Slug=?",
        (ID_LADINO, sub["slug"]),
    ).fetchone()
    if row:
        sid, nome_atual, tagline_atual = row
        cur.execute(
            "UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
            (sub["nome"], sub["tagline"], sid),
        )
        return sid, "upd"
    cur.execute(
        "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
        (ID_LADINO, sub["nome"], sub["slug"], sub["tagline"]),
    )
    return cur.lastrowid, "ins"


def insert_hab(cur: sqlite3.Cursor, id_sub: int | None, nome: str, nivel: int,
               descricao: str, origem: str) -> None:
    """Insert direto (não idempotente — usa após DELETE em massa)."""
    tem_escolha = 1 if nome == "Aprimoramento de Habilidade" else 0
    cur.execute(
        "INSERT INTO TB_ClasseHabilidade "
        "(Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON) "
        "VALUES (?,?,?,?,?,?,?,NULL)",
        (ID_LADINO, id_sub, nome, descricao, nivel, tem_escolha, origem),
    )


conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe metadata ===
print("=== TB_Classe metadata (Ladino) ===")
upsert_classe_metadata(cur)
print(f"  SkillsJSON              = {META['skills']}")
print(f"  ArmorProfJSON           = {META['armor_prof']}")
print(f"  WeaponProfJSON          = {WEAPON_PROF}")
print(f"  ToolProfJSON            = {META['tool_prof']}")
print(f"  MulticlassProfJSON      = {META['multiclass_prof']}")
print(f"  SavesJSON               = {META['saves']}")
print(f"  ASINiveisJSON           = {ASI_NIVEIS}  (Nv 10 ASI extra do Ladino)")
print(f"  EquipamentoInicialJSON  = {len(EQUIPAMENTO_INICIAL)} items (incl. ALT B)")

# === 2. TB_Subclasse (Tagline) ===
print(f"\n=== TB_Subclasse (8 Trilhas) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    sid, status = upsert_sub_tagline(cur, sub)
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<32} {sub['nome']}")

# === 3. WIPE habs Ladino existentes (corruptas) ===
print(f"\n=== WIPE TB_ClasseHabilidade Ladino (estado corrompido) ===")
ndel = cur.execute(
    "DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_LADINO,),
).rowcount
print(f"  deletadas: {ndel}")

# === 4. INSERT class features ===
print(f"\n=== INSERT class features ({len(FEATS)}) ===")
for f in FEATS:
    insert_hab(cur, None, f["nome"], f["nivel"], f["descricao"], "classe")
print(f"  inseridas: {len(FEATS)} habs classe")

# === 5. INSERT subclass features ===
print(f"\n=== INSERT subclass features ===")
total_sub = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        insert_hab(cur, sid, f["nome"], f["nivel"], f["descricao"], "subclasse")
        total_sub += 1
    print(f"  {sub['slug']:<32} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  Total subclass features: {total_sub}")

conn.commit()

# === Validação ===
print(f"\n=== Validação ===")
tot_classe = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
    (ID_LADINO,),
).fetchone()[0]
tot_sub = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s ON s.Id_Subclasse=ch.Id_Subclasse "
    "WHERE s.Id_Classe=?", (ID_LADINO,),
).fetchone()[0]
print(f"  DB total habs classe:    {tot_classe} (esperado {len(FEATS)})")
print(f"  DB total habs subclasse: {tot_sub} (esperado {total_sub})")

conn.close()
print("\nDONE.")
