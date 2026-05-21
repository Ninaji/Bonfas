"""Popula Feiticeiro (Id_Classe=7): TB_Classe metadata + 6 Origens (taglines)
+ 18 class features + 34 subclass features. Wipe + reinsert (estado atual mínimo).
Backup automático. Inclui Origem da Tempestade (6ª subclass, faltando no DB)."""
from __future__ import annotations
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_FEIT = 7
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("feiticeiro_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("feiticeiro_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("feiticeiro_subs.json").read_text(encoding="utf-8"))

# Equipamento inicial Feiticeiro (canônico Bonfire 5.5e)
EQUIPAMENTO_INICIAL = [
    {"qtd": 1,  "nome": "Besta Leve",              "tipo": "weapon", "valor": "25 gp"},
    {"qtd": 20, "nome": "Virote",                  "tipo": "weapon", "valor": "1 gp"},
    {"qtd": 1,  "nome": "Foco Arcano",             "tipo": "gear",   "valor": "—"},
    {"qtd": 1,  "nome": "Pacote de Masmorra",      "tipo": "pack",   "valor": "12 gp"},
    {"qtd": 2,  "nome": "Adaga",                   "tipo": "weapon", "valor": "2 gp"},
]

WEAPON_PROF = ["Adagas", "Dardos", "Fundas", "Bastões", "Bestas Leves"]
ARMOR_PROF: list[str] = []
TOOL_PROF: list[str] = []
MULTICLASS_PROF: list[str] = []
ASI_NIVEIS = [4, 8, 12, 16, 19]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. TB_Classe metadata
print("=== TB_Classe Feiticeiro metadata ===")
cur.execute(
    """UPDATE TB_Classe SET SkillsJSON=?, ArmorProfJSON=?, WeaponProfJSON=?,
              ToolProfJSON=?, EquipamentoInicialJSON=?, MulticlassProfJSON=?,
              SavesJSON=?, ASINiveisJSON=?
       WHERE Id_Classe=?""",
    (
        json.dumps(META.get("skills"), ensure_ascii=False),
        json.dumps(ARMOR_PROF, ensure_ascii=False),
        json.dumps(WEAPON_PROF, ensure_ascii=False),
        json.dumps(TOOL_PROF, ensure_ascii=False),
        json.dumps(EQUIPAMENTO_INICIAL, ensure_ascii=False),
        json.dumps(MULTICLASS_PROF, ensure_ascii=False),
        json.dumps(META.get("saves") or ["Constituicao", "Carisma"], ensure_ascii=False),
        json.dumps(ASI_NIVEIS, ensure_ascii=False),
        ID_FEIT,
    ),
)
print(f"  SkillsJSON: {META.get('skills')}")
print(f"  WeaponProf: {WEAPON_PROF}")
print(f"  ASINiveis: {ASI_NIVEIS}")

# 2. TB_Subclasse — 6 Origens (UPSERT + Origem da Tempestade pode ser NOVA)
print(f"\n=== TB_Subclasse (6 Origens) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    row = cur.execute("SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
                      (ID_FEIT, sub["slug"])).fetchone()
    if row:
        sid = row[0]
        cur.execute("UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
                    (sub["nome"], sub["tagline"], sid))
        status = "upd"
    else:
        cur.execute("INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline) VALUES (?,?,?,?)",
                    (ID_FEIT, sub["nome"], sub["slug"], sub["tagline"]))
        sid = cur.lastrowid
        status = "ins (NEW)"
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<22} {sub['nome']}")

# 3. WIPE TB_ClasseHabilidade Feiticeiro (estado atual mínimo/parcial)
print(f"\n=== WIPE TB_ClasseHabilidade Feiticeiro ===")
ndel = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_FEIT,)).rowcount
print(f"  deletadas: {ndel}")

# 4. INSERT class features
print(f"\n=== INSERT class features ({len(FEATS)}) ===")
for f in FEATS:
    tem_esc = 1 if f["nome"] == "Incremento de Atributo ou Talento" else 0
    cur.execute("""INSERT INTO TB_ClasseHabilidade
                   (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
                   VALUES (?,NULL,?,?,?,?,'classe',NULL)""",
                (ID_FEIT, f["nome"], f["descricao"], f["nivel"], tem_esc))

# 5. INSERT subclass features
print(f"\n=== INSERT subclass features ===")
total_sub = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        cur.execute("""INSERT INTO TB_ClasseHabilidade
                       (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
                       VALUES (?,?,?,?,?,0,'subclasse',NULL)""",
                    (ID_FEIT, sid, f["nome"], f["descricao"], f["nivel"]))
        total_sub += 1
    print(f"  {sub['slug']:<22} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  TOTAL: {total_sub}")

conn.commit()

# Validação
tot_cls = cur.execute("SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",(ID_FEIT,)).fetchone()[0]
tot_sub = cur.execute("SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s ON s.Id_Subclasse=ch.Id_Subclasse WHERE s.Id_Classe=?",(ID_FEIT,)).fetchone()[0]
print(f"\n=== Validação ===")
print(f"  DB habs classe:    {tot_cls} (esperado {len(FEATS)})")
print(f"  DB habs subclasse: {tot_sub} (esperado {total_sub})")
conn.close()
print("\nDONE.")
