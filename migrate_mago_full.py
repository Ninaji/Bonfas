"""Popula Mago: TB_Classe (profs/multiclass/equip/skills) + 13 Tradições Arcanas
(taglines) + 19 class features + 70 subclass features. Idempotente.

Não inventa conteúdo (Regra #0): tudo vem de mago_features.json + mago_subs.json
+ mago_meta.json gerados por parse_mago_full.py.

Uso: python migrate_mago_full.py
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
ID_MAGO = 10  # confirmado no DB

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META  = json.loads(Path("mago_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("mago_features.json").read_text(encoding="utf-8"))
SUBS  = json.loads(Path("mago_subs.json").read_text(encoding="utf-8"))

# Equipamento Inicial — opção A canônica (lista estruturada), B = 150 PO em alt_b
# (a UI/backend ainda não suporta toggle A/B; armazena A como default).
EQUIPAMENTO_INICIAL = [
    {"qtd": 1, "nome": "Livro de Magias (Spellbook)", "tipo": "gear",   "valor": "—"},
    {"qtd": 1, "nome": "Orbe [Foco Arcano]",          "tipo": "gear",   "valor": "—"},
    {"qtd": 2, "nome": "Adaga",                       "tipo": "weapon", "valor": "2 gp"},
    {"qtd": 1, "nome": "Pacote de Estudioso",         "tipo": "pack",   "valor": "40 gp"},
    {"qtd": 1, "nome": "Tinta",                       "tipo": "gear",   "valor": "10 gp"},
    {"qtd": 1, "nome": "Estojo de Pergaminhos",       "tipo": "gear",   "valor": "1 gp"},
    {"qtd": 1, "nome": "Manto",                       "tipo": "gear",   "valor": "—"},
    {"qtd": 1, "nome": "Bolsa com 24 PO",             "tipo": "gold",   "valor": "24 gp"},
    # Alternativa B: 150 PO. Modelada como nota — UI pode adicionar toggle depois.
    {"qtd": 0, "nome": "ALT: 150 PO (Opção B)",       "tipo": "alt",    "valor": "150 gp"},
]


def upsert_classe_metadata(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """UPDATE TB_Classe SET
              SkillsJSON          = ?,
              ArmorProfJSON       = ?,
              WeaponProfJSON      = ?,
              ToolProfJSON        = ?,
              EquipamentoInicialJSON = ?,
              MulticlassProfJSON  = ?,
              SavesJSON           = ?
           WHERE Id_Classe = ?""",
        (
            json.dumps(META["skills"], ensure_ascii=False),
            json.dumps(META["armor_prof"], ensure_ascii=False),
            json.dumps(META["weapon_prof"], ensure_ascii=False),
            json.dumps(META["tool_prof"], ensure_ascii=False),
            json.dumps(EQUIPAMENTO_INICIAL, ensure_ascii=False),
            json.dumps(META["multiclass_prof"], ensure_ascii=False),
            json.dumps(META["saves"], ensure_ascii=False),
            ID_MAGO,
        ),
    )


def upsert_sub_tagline(cur: sqlite3.Cursor, sub: dict) -> tuple[int, str]:
    """Garante Nome+Slug corretos (corrige eventual mojibake do seed antigo)
    e seta Tagline. Retorna (Id_Subclasse, status)."""
    row = cur.execute(
        "SELECT Id_Subclasse, Nome, Tagline FROM TB_Subclasse "
        "WHERE Id_Classe=? AND Slug=?",
        (ID_MAGO, sub["slug"]),
    ).fetchone()
    if row:
        sid, nome_atual, tagline_atual = row
        # Força Nome canônico (corrige mojibake) e Tagline
        cur.execute(
            "UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
            (sub["nome"], sub["tagline"], sid),
        )
        return sid, "upd" if (nome_atual != sub["nome"] or not tagline_atual) else "ok"
    # Não deveria acontecer (DB já tem as 13), mas insere como safety
    cur.execute(
        "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
        (ID_MAGO, sub["nome"], sub["slug"], sub["tagline"]),
    )
    return cur.lastrowid, "ins"


def upsert_hab(cur: sqlite3.Cursor, id_sub: int | None, nome: str, nivel: int,
               descricao: str, origem: str) -> str:
    """Idempotente: pula se (Id_Classe, Id_Subclasse, Nome, NivelAdquirido) já existe."""
    if id_sub is None:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND NivelAdquirido=?",
            (ID_MAGO, nome, nivel),
        ).fetchone()
    else:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
            "WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND NivelAdquirido=?",
            (ID_MAGO, id_sub, nome, nivel),
        ).fetchone()
    if row:
        # Atualiza descrição (caso parser tenha sido refinado entre runs)
        cur.execute(
            "UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?",
            (descricao, row[0]),
        )
        return "upd"
    tem_escolha = 1 if nome == "Aumento de Atributo" else 0
    cur.execute(
        "INSERT INTO TB_ClasseHabilidade "
        "(Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON) "
        "VALUES (?,?,?,?,?,?,?,NULL)",
        (ID_MAGO, id_sub, nome, descricao, nivel, tem_escolha, origem),
    )
    return "ins"


conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe (profs / multiclass / equip / skills / saves) ===
print("=== TB_Classe metadata ===")
upsert_classe_metadata(cur)
print(f"  SkillsJSON          = {META['skills']}")
print(f"  ArmorProfJSON       = {META['armor_prof']}")
print(f"  WeaponProfJSON      = {META['weapon_prof']}")
print(f"  ToolProfJSON        = {META['tool_prof']}")
print(f"  MulticlassProfJSON  = {META['multiclass_prof']}")
print(f"  SavesJSON           = {META['saves']}")
print(f"  EquipamentoInicialJSON = {len(EQUIPAMENTO_INICIAL)} items (incl. ALT B)")

# === 2. TB_Subclasse (tagline + fix mojibake do seed antigo) ===
print("\n=== TB_Subclasse (13 Tradições Arcanas) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    sid, status = upsert_sub_tagline(cur, sub)
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<18} {sub['nome']}")

# === 3. TB_ClasseHabilidade — class features (Id_Subclasse NULL) ===
print(f"\n=== TB_ClasseHabilidade — Mago classe ({len(FEATS)}) ===")
counts_class = {"ins": 0, "upd": 0}
for f in FEATS:
    status = upsert_hab(cur, None, f["nome"], f["nivel"], f["descricao"], "classe")
    counts_class[status] = counts_class.get(status, 0) + 1
    print(f"  Nv{f['nivel']:>2} [{status}] {f['nome']}")

# === 4. TB_ClasseHabilidade — subclass features ===
print(f"\n=== TB_ClasseHabilidade — subclasses ===")
counts_sub = {"ins": 0, "upd": 0}
total_sub_feats = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        status = upsert_hab(cur, sid, f["nome"], f["nivel"], f["descricao"], "subclasse")
        counts_sub[status] = counts_sub.get(status, 0) + 1
        total_sub_feats += 1
    print(f"  {sub['slug']:<18} sid={sid:>3}  {len(sub['features_sub'])} features")

conn.commit()

# === STATS ===
print("\n=== STATS ===")
print(f"  TB_Classe Mago: 1 row atualizada")
print(f"  TB_Subclasse:   {len(SUBS)} subs (tagline+nome canônico)")
print(f"  Habs classe:    {counts_class} (total esperado: {len(FEATS)})")
print(f"  Habs sub:       {counts_sub} (total esperado: {total_sub_feats})")

# Validação final
tot_classe = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
    (ID_MAGO,),
).fetchone()[0]
tot_sub = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s ON s.Id_Subclasse=ch.Id_Subclasse "
    "WHERE s.Id_Classe=?", (ID_MAGO,),
).fetchone()[0]
print(f"\n  DB total Mago habs classe:    {tot_classe}")
print(f"  DB total Mago habs subclasse: {tot_sub}")

if META.get("pending_review"):
    print(f"\n⚠ Pendências sinalizadas pelo parser (Regra #0 — não inseridas no DB):")
    for p in META["pending_review"]:
        print(f"  - {p['item']}: {p['motivo'][:120]}...")

conn.close()
print("\nDONE.")
