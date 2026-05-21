"""Popula Artífice (Id_Classe=1) — full: TB_Classe metadata + 6 subclasses
(UPSERT; Ferreiro de Batalha e Magiduelista são NOVAS) + class features Nv 1-20
+ subclass features Nv 3/5/10/15. Wipe + reinsert.

PRESERVA o campo de infusões (não toca TB_OpcaoJogo Tipo='infusao-artificer'
nem o talento). Re-aplica no reinsert:
  - "Infusões" (Nv 2) → pick:infusao-artificer n_por_nivel {2:4,6:5,10:6,14:7,18:8}
  - "Aumento de Atributo" (ASI) → asi-feature

NÃO reinsere as 4 features-catálogo (excluídas no parser; viraram o picker).
Backup automático.
"""
from __future__ import annotations
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_ARTIFICE = 1
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("artificer_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("artificer_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("artificer_subs.json").read_text(encoding="utf-8"))

EQUIPAMENTO_INICIAL = [
    {"qtd": 1, "nome": "Armadura de Couro Batido",   "tipo": "armor",  "valor": "45 gp"},
    {"qtd": 1, "nome": "Besta Leve",                 "tipo": "weapon", "valor": "25 gp"},
    {"qtd": 20,"nome": "Virote",                     "tipo": "weapon", "valor": "1 gp"},
    {"qtd": 2, "nome": "Adaga",                       "tipo": "weapon", "valor": "2 gp"},
    {"qtd": 1, "nome": "Ferramentas de Ladrão",       "tipo": "tool",   "valor": "25 gp"},
    {"qtd": 1, "nome": "Ferramentas de Funileiro",    "tipo": "tool",   "valor": "50 gp"},
    {"qtd": 1, "nome": "Pacote do Estudioso",         "tipo": "pack",   "valor": "40 gp"},
]
ASI_NIVEIS = [4, 8, 12, 16, 19]
N_POR_NIVEL_INFUSAO = {"2": 4, "6": 5, "10": 6, "14": 7, "18": 8}

CLASSE_TAGS = {
    "Conjuração de Magias": ["conjurador"],  # half-caster INT — ativa seção de magias
    "Infusões": [{"tag": "pick:infusao-artificer", "n_por_nivel": N_POR_NIVEL_INFUSAO}],
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe metadata ===
print("=== TB_Classe Artífice metadata ===")
cur.execute(
    """UPDATE TB_Classe SET SkillsJSON=?, ArmorProfJSON=?, WeaponProfJSON=?,
              ToolProfJSON=?, EquipamentoInicialJSON=?, MulticlassProfJSON=?,
              SavesJSON=?, ASINiveisJSON=? WHERE Id_Classe=?""",
    (json.dumps(META["skills"], ensure_ascii=False),
     json.dumps(META["armor_prof"], ensure_ascii=False),
     json.dumps(META["weapon_prof"], ensure_ascii=False),
     json.dumps(META["tool_prof"], ensure_ascii=False),
     json.dumps(EQUIPAMENTO_INICIAL, ensure_ascii=False),
     json.dumps(META["multiclass_prof"], ensure_ascii=False),
     json.dumps(META["saves"], ensure_ascii=False),
     json.dumps(ASI_NIVEIS, ensure_ascii=False), ID_ARTIFICE),
)
print(f"  Saves: {META['saves']}  Skills: {META['skills']}")

# === 2. TB_Subclasse (6, UPSERT) ===
print("\n=== TB_Subclasse (6 subclasses) ===")
slug_to_sid = {}
for sub in SUBS:
    row = cur.execute("SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
                      (ID_ARTIFICE, sub["slug"])).fetchone()
    if row:
        sid = row[0]
        cur.execute("UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
                    (sub["nome"], sub["tagline"], sid)); status = "upd"
    else:
        cur.execute("INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
                    (ID_ARTIFICE, sub["nome"], sub["slug"], sub["tagline"])); sid = cur.lastrowid; status = "ins (NEW)"
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<26} {sub['nome']}")

# === 3. WIPE habs Artífice ===
print("\n=== WIPE TB_ClasseHabilidade Artífice ===")
ndel = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_ARTIFICE,)).rowcount
print(f"  deletadas: {ndel}")

# === 4. INSERT class features (re-aplica tags de infusão/asi) ===
print(f"\n=== INSERT class features ({len(FEATS)}) ===")
for f in FEATS:
    is_asi = f["nome"] == "Aumento de Atributo"
    tem_esc = 1 if is_asi else 0
    tags = list(CLASSE_TAGS.get(f["nome"]) or [])
    if is_asi:
        tags.append("asi-feature")
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    cur.execute(
        "INSERT INTO TB_ClasseHabilidade (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON) "
        "VALUES (?, NULL, ?, ?, ?, ?, 'classe', ?)",
        (ID_ARTIFICE, f["nome"], f["descricao"], f["nivel"], tem_esc, tags_json),
    )
print(f"  inseridas: {len(FEATS)}")

# === 5. INSERT subclass features ===
print("\n=== INSERT subclass features ===")
total_sub = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        cur.execute(
            "INSERT INTO TB_ClasseHabilidade (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON) "
            "VALUES (?, ?, ?, ?, ?, 0, 'subclasse', NULL)",
            (ID_ARTIFICE, sid, f["nome"], f["descricao"], f["nivel"]),
        )
        total_sub += 1
    print(f"  {sub['slug']:<26} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  TOTAL: {total_sub}")

conn.commit()

# === Validação ===
tot_cls = cur.execute("SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL", (ID_ARTIFICE,)).fetchone()[0]
tot_sub = cur.execute("SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s ON s.Id_Subclasse=ch.Id_Subclasse WHERE s.Id_Classe=?", (ID_ARTIFICE,)).fetchone()[0]
inf_tag = cur.execute("SELECT TagsJSON FROM TB_ClasseHabilidade WHERE Id_Classe=1 AND Nome='Infusões' AND Id_Subclasse IS NULL").fetchone()
cat = cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='infusao-artificer'").fetchone()[0]
print(f"\n=== Validação ===")
print(f"  habs classe={tot_cls} (esperado {len(FEATS)})  sub={tot_sub} (esperado {total_sub})")
print(f"  Infusões TagsJSON (preservada): {inf_tag[0] if inf_tag else None}")
print(f"  Catálogo de infusões (intacto): {cat}")
conn.close()
print("\nDONE.")
