"""Popula Druida (Id_Classe=6): TB_Classe metadata + 7 Círculos
(taglines, incluindo 2 NOVOS: Sonhos + Terra) + 18 class features
+ ~45 subclass features. Wipe + reinsert.

Tags especiais:
  - Feature "Surto Selvagem" (Nv 2 classe)            → ["surto-selvagem"]
  - Feature "Formas Lunares" (Nv 3 sub Lua)           → ["druida-lua"]
  - Feature "Forma Selvagem Anciã" (Nv 10 sub Lua)    → ["druida-lua"]
  - Feature "Avatar da Lua" (Nv 18 sub Lua)           → ["druida-lua"]
  - Feature "Aprimoramento de Atributo ou Talento"    → TemEscolha=1

Backup automático.
"""
from __future__ import annotations
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_DRUIDA = 6
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("druida_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("druida_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("druida_subs.json").read_text(encoding="utf-8"))

# Equipamento Inicial Druida (canônico Bonfire 5.5e — escudo de madeira/couro,
# armadura de couro, foice, e foco druídico)
EQUIPAMENTO_INICIAL = [
    {"qtd": 1,  "nome": "Armadura de Couro",      "tipo": "armor",  "valor": "10 gp"},
    {"qtd": 1,  "nome": "Escudo (madeira)",       "tipo": "armor",  "valor": "10 gp"},
    {"qtd": 1,  "nome": "Foice",                  "tipo": "weapon", "valor": "1 gp"},
    {"qtd": 1,  "nome": "Foco Druídico",          "tipo": "gear",   "valor": "—"},
    {"qtd": 1,  "nome": "Pacote do Explorador",   "tipo": "pack",   "valor": "10 gp"},
    {"qtd": 1,  "nome": "Kit de Herbalismo",      "tipo": "tool",   "valor": "5 gp"},
    {"qtd": 2,  "nome": "Adaga",                  "tipo": "weapon", "valor": "2 gp"},
]

ASI_NIVEIS = [4, 8, 12, 16, 19]

# === Tagging por nome de feature ===
TAGS_BY_FEATURE_NAME = {
    "Surto Selvagem": ["surto-selvagem"],
}
# Subclass features que precisam druida-lua tag
LUA_SUB_FEATURES = {"Formas Lunares", "Forma Selvagem Anciã", "Avatar da Lua",
                    "Maré de Caça"}  # Maré de Caça é sub Lua per parser

conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe metadata ===
print("=== TB_Classe Druida metadata ===")
cur.execute(
    """UPDATE TB_Classe SET SkillsJSON=?, ArmorProfJSON=?, WeaponProfJSON=?,
              ToolProfJSON=?, EquipamentoInicialJSON=?, MulticlassProfJSON=?,
              SavesJSON=?, ASINiveisJSON=?
       WHERE Id_Classe=?""",
    (
        json.dumps(META["skills"], ensure_ascii=False),
        json.dumps(META["armor_prof"], ensure_ascii=False),
        json.dumps(META["weapon_prof"], ensure_ascii=False),
        json.dumps(META["tool_prof"], ensure_ascii=False),
        json.dumps(EQUIPAMENTO_INICIAL, ensure_ascii=False),
        json.dumps(META["multiclass_prof"], ensure_ascii=False),
        json.dumps(META["saves"], ensure_ascii=False),
        json.dumps(ASI_NIVEIS, ensure_ascii=False),
        ID_DRUIDA,
    ),
)
print(f"  Saves: {META['saves']}")
print(f"  ASINiveis: {ASI_NIVEIS}")
print(f"  Skills: {META['skills']}")

# === 2. TB_Subclasse — 7 Círculos (UPSERT) ===
print(f"\n=== TB_Subclasse (7 Círculos) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_DRUIDA, sub["slug"]),
    ).fetchone()
    if row:
        sid = row[0]
        cur.execute(
            "UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
            (sub["nome"], sub["tagline"], sid),
        )
        status = "upd"
    else:
        cur.execute(
            "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
            (ID_DRUIDA, sub["nome"], sub["slug"], sub["tagline"]),
        )
        sid = cur.lastrowid
        status = "ins (NEW)"
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<32} {sub['nome']}")

# === 3. WIPE TB_ClasseHabilidade Druida ===
print(f"\n=== WIPE TB_ClasseHabilidade Druida ===")
ndel = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_DRUIDA,)).rowcount
print(f"  deletadas: {ndel}")

# === 4. INSERT class features ===
print(f"\n=== INSERT class features ({len(FEATS)}) ===")
for f in FEATS:
    tem_esc = 1 if f["nome"] == "Aprimoramento de Atributo ou Talento" else 0
    tags = TAGS_BY_FEATURE_NAME.get(f["nome"])
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?, NULL, ?, ?, ?, ?, 'classe', ?)""",
        (ID_DRUIDA, f["nome"], f["descricao"], f["nivel"], tem_esc, tags_json),
    )
print(f"  inseridas: {len(FEATS)}")

# === 5. INSERT subclass features ===
print(f"\n=== INSERT subclass features ===")
total_sub = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        tags = None
        if sub["slug"] == "circulo-da-lua" and f["nome"] in LUA_SUB_FEATURES:
            tags = ["druida-lua"]
        elif sub["slug"] == "circulo-da-lua":
            # Toda feature da Lua precisa propagar druida-lua para o aggregator
            # (a feature de subclass anchor Nv3 'Formas Lunares' já basta tecnicamente,
            #  mas marcar todas garante presença mesmo se o jogador apagar)
            tags = ["druida-lua"]
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        cur.execute(
            """INSERT INTO TB_ClasseHabilidade
               (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
               VALUES (?, ?, ?, ?, ?, 0, 'subclasse', ?)""",
            (ID_DRUIDA, sid, f["nome"], f["descricao"], f["nivel"], tags_json),
        )
        total_sub += 1
    print(f"  {sub['slug']:<32} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  TOTAL: {total_sub}")

conn.commit()

# === Validação ===
tot_cls = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
    (ID_DRUIDA,),
).fetchone()[0]
tot_sub = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s "
    "ON s.Id_Subclasse=ch.Id_Subclasse WHERE s.Id_Classe=?",
    (ID_DRUIDA,),
).fetchone()[0]
print(f"\n=== Validação ===")
print(f"  DB habs classe:    {tot_cls} (esperado {len(FEATS)})")
print(f"  DB habs subclasse: {tot_sub} (esperado {total_sub})")
print(f"  Lua features com druida-lua:")
rows = cur.execute(
    "SELECT Nome, NivelAdquirido, TagsJSON FROM TB_ClasseHabilidade "
    "WHERE Id_Classe=? AND Id_Subclasse=? ORDER BY NivelAdquirido",
    (ID_DRUIDA, slug_to_sid["circulo-da-lua"]),
).fetchall()
for r in rows:
    print(f"    Nv{r[1]:>2} {r[0]:<30} tags={r[2]}")

conn.close()
print("\nDONE.")
