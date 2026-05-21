"""Popula Bardo (Id_Classe=2): TB_Classe metadata + 8 Colégios (UPSERT) +
17 class features + 56 subclass features. Wipe + reinsert.

Tags especiais:
  - "Dança em Cena" (Colégio da Dança Nv 3) → tag progressiva
      `pick:estilo-danca:N` com n_por_nivel {"3":1, "6":2, "14":3, "18":4}
    Bardo da Dança escolhe 1 Estilo de Ki (catálogo TB_EstiloKi Catalogo='ki')
    como "Estilo de Dança", lendo "1 ponto de Ki" como "1 uso de Inspiração
    Bárdica" para fins de custo. Picks vão pra TB_PersonagemEscolhaTag
    (Tipo='estilo-danca').
  - Aprimoramento/Incremento de Atributo ou Talento → TemEscolha=1 + tag
      'asi-feature' (esconde do bloco de habilidades de classe).

Backup automático.
"""
from __future__ import annotations
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_BARDO = 2
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("bardo_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("bardo_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("bardo_subs.json").read_text(encoding="utf-8"))

# Equipamento Inicial Bardo (canônico Bonfire 5.5e — armadura leve, rapieira,
# instrumento, pacote de diplomata)
EQUIPAMENTO_INICIAL = [
    {"qtd": 1,  "nome": "Armadura de Couro",         "tipo": "armor",  "valor": "10 gp"},
    {"qtd": 1,  "nome": "Rapieira",                  "tipo": "weapon", "valor": "25 gp"},
    {"qtd": 1,  "nome": "Adaga",                     "tipo": "weapon", "valor": "2 gp"},
    {"qtd": 1,  "nome": "Instrumento Musical",       "tipo": "tool",   "valor": "30 gp"},
    {"qtd": 1,  "nome": "Pacote do Diplomata",       "tipo": "pack",   "valor": "39 gp"},
]

ASI_NIVEIS = [4, 8, 12, 16, 19]

# Tags por nome de feature de classe
CLASSE_TAGS = {
    "Inspiração Bárdica": [],  # placeholder se quiser tag específica no futuro
}

# Tags por nome de feature de subclasse (mapa absoluto)
SUB_TAGS = {
    # Bardo da Dança Nv 3 — picker progressivo de Estilos de Dança
    "Dança em Cena": [
        {"tag": "pick:estilo-danca",
         "n_por_nivel": {"3": 1, "6": 2, "14": 3, "18": 4}}
    ],
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe metadata ===
print("=== TB_Classe Bardo metadata ===")
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
        ID_BARDO,
    ),
)
print(f"  Saves: {META['saves']}")
print(f"  Skills: {META['skills']}")

# === 2. TB_Subclasse — 8 Colégios (UPSERT) ===
print(f"\n=== TB_Subclasse (8 Colégios) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_BARDO, sub["slug"]),
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
            (ID_BARDO, sub["nome"], sub["slug"], sub["tagline"]),
        )
        sid = cur.lastrowid
        status = "ins (NEW)"
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<28} {sub['nome']}")

# === 3. WIPE TB_ClasseHabilidade Bardo ===
print(f"\n=== WIPE TB_ClasseHabilidade Bardo ===")
ndel = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_BARDO,)).rowcount
print(f"  deletadas: {ndel}")

# === 4. INSERT class features ===
print(f"\n=== INSERT class features ({len(FEATS)}) ===")
for f in FEATS:
    is_asi = f["nome"] == "Incremento de Atributo ou Talento"
    tem_esc = 1 if is_asi else 0
    tags = list(CLASSE_TAGS.get(f["nome"]) or [])
    if is_asi:
        tags.append("asi-feature")
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?, NULL, ?, ?, ?, ?, 'classe', ?)""",
        (ID_BARDO, f["nome"], f["descricao"], f["nivel"], tem_esc, tags_json),
    )
print(f"  inseridas: {len(FEATS)}")

# === 5. INSERT subclass features ===
print(f"\n=== INSERT subclass features ===")
total_sub = 0
for sub in SUBS:
    sid = slug_to_sid[sub["slug"]]
    for f in sub["features_sub"]:
        tags = SUB_TAGS.get(f["nome"])
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
        cur.execute(
            """INSERT INTO TB_ClasseHabilidade
               (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
               VALUES (?, ?, ?, ?, ?, 0, 'subclasse', ?)""",
            (ID_BARDO, sid, f["nome"], f["descricao"], f["nivel"], tags_json),
        )
        total_sub += 1
    print(f"  {sub['slug']:<28} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  TOTAL: {total_sub}")

conn.commit()

# === Validação ===
tot_cls = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
    (ID_BARDO,),
).fetchone()[0]
tot_sub = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s "
    "ON s.Id_Subclasse=ch.Id_Subclasse WHERE s.Id_Classe=?",
    (ID_BARDO,),
).fetchone()[0]
print(f"\n=== Validação ===")
print(f"  DB habs classe:    {tot_cls} (esperado {len(FEATS)})")
print(f"  DB habs subclasse: {tot_sub} (esperado {total_sub})")
# Confirma tag em Dança em Cena
dc = cur.execute(
    "SELECT TagsJSON FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Nome='Dança em Cena'",
    (ID_BARDO,),
).fetchone()
print(f"  Dança em Cena TagsJSON: {dc[0] if dc else None}")

conn.close()
print("\nDONE.")
