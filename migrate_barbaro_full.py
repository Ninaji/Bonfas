"""Popula Bárbaro (Id_Classe=3): TB_Classe metadata + 7 Caminhos (UPSERT) +
17 class features + 40 subclass features. Wipe + reinsert.

Tags especiais:
  - "Maestria em Armas" (Nv 1) → ["+maestrias-arma:2"] (flat). O texto diz
    "Escolha dois tipos de armas"; a progressão além disso está na "tabela do
    Bárbaro" (não extraível — Regra #0: não inventar). Fica em 2 até dump.
  - "Incremento de Atributo ou Talento" (Nv 4/8/12/16/19) → TemEscolha=1 +
    tag 'asi-feature' (esconde do bloco de habilidades de classe).

Backup automático.
"""
from __future__ import annotations
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_BARBARO = 3
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

META = json.loads(Path("barbaro_meta.json").read_text(encoding="utf-8"))
FEATS = json.loads(Path("barbaro_features.json").read_text(encoding="utf-8"))
SUBS = json.loads(Path("barbaro_subs.json").read_text(encoding="utf-8"))

# Equipamento Inicial Bárbaro (canônico Bonfire 5.5e — machado grande, machados
# de mão, pacote do explorador)
EQUIPAMENTO_INICIAL = [
    {"qtd": 1,  "nome": "Machado Grande",          "tipo": "weapon", "valor": "30 gp"},
    {"qtd": 4,  "nome": "Machadinha",              "tipo": "weapon", "valor": "5 gp"},
    {"qtd": 1,  "nome": "Pacote do Explorador",    "tipo": "pack",   "valor": "10 gp"},
    {"qtd": 1,  "nome": "Bolsa com 15 PO",         "tipo": "gold",   "valor": "15 gp"},
]

ASI_NIVEIS = [4, 8, 12, 16, 19]

# Tags por nome de feature de classe.
# Princípio do projeto: TAG > código hardcoded. A progressão de Maestria em
# Armas (3 em Nv 1-8, 4 em Nv 9-16, 5 em Nv 17-20 — valores canônicos Bonfire)
# é expressa via tag progressiva `+maestrias-arma` com n_por_nivel, igual ao
# Ladino. Os 20 rows hardcoded em TB_RecursoClasse (Id_Classe=3, 'Maestria
# com Armas') são DELETADOS abaixo pra evitar dupla contagem — a tag é a
# única fonte de verdade.
CLASSE_TAGS: dict[str, list] = {
    "Maestria em Armas": [
        {"tag": "+maestrias-arma", "n_por_nivel": {"1": 3, "9": 4, "17": 5}}
    ],
}

# Tags por nome de feature de subclasse (nenhuma especial — Bárbaro não tem
# picker dedicado como o Bardo da Dança)
SUB_TAGS: dict[str, list] = {}

conn = sqlite3.connect(DB)
cur = conn.cursor()

# === 1. TB_Classe metadata ===
print("=== TB_Classe Bárbaro metadata ===")
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
        ID_BARBARO,
    ),
)
print(f"  Saves: {META['saves']}")
print(f"  Skills: {META['skills']}")

# === 2. TB_Subclasse — 7 Caminhos (UPSERT) ===
print(f"\n=== TB_Subclasse (7 Caminhos) ===")
slug_to_sid: dict[str, int] = {}
for sub in SUBS:
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_BARBARO, sub["slug"]),
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
            (ID_BARBARO, sub["nome"], sub["slug"], sub["tagline"]),
        )
        sid = cur.lastrowid
        status = "ins (NEW)"
    slug_to_sid[sub["slug"]] = sid
    print(f"  sid={sid:>3} [{status}] {sub['slug']:<32} {sub['nome']}")

# === 3. WIPE TB_ClasseHabilidade Bárbaro ===
print(f"\n=== WIPE TB_ClasseHabilidade Bárbaro ===")
ndel = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (ID_BARBARO,)).rowcount
print(f"  deletadas: {ndel}")

# === 3b. DELETE rows hardcoded de Maestria em TB_RecursoClasse ===
# Princípio TAG > hardcoded: a progressão de maestria vem da tag
# +maestrias-arma (CLASSE_TAGS). Remover os rows evita dupla contagem
# (backend soma TB_RecursoClasse + tag).
nrec = cur.execute(
    "DELETE FROM TB_RecursoClasse WHERE Id_Classe=? AND Nome LIKE '%aestria%Arma%'",
    (ID_BARBARO,),
).rowcount
print(f"  TB_RecursoClasse maestria removidos: {nrec}")

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
        (ID_BARBARO, f["nome"], f["descricao"], f["nivel"], tem_esc, tags_json),
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
            (ID_BARBARO, sid, f["nome"], f["descricao"], f["nivel"], tags_json),
        )
        total_sub += 1
    print(f"  {sub['slug']:<32} sid={sid:>3}  {len(sub['features_sub'])} features")
print(f"  TOTAL: {total_sub}")

conn.commit()

# === Validação ===
tot_cls = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
    (ID_BARBARO,),
).fetchone()[0]
tot_sub = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade ch JOIN TB_Subclasse s "
    "ON s.Id_Subclasse=ch.Id_Subclasse WHERE s.Id_Classe=?",
    (ID_BARBARO,),
).fetchone()[0]
print(f"\n=== Validação ===")
print(f"  DB habs classe:    {tot_cls} (esperado {len(FEATS)})")
print(f"  DB habs subclasse: {tot_sub} (esperado {total_sub})")
dc = cur.execute(
    "SELECT Nome, TagsJSON FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Nome='Maestria em Armas'",
    (ID_BARBARO,),
).fetchone()
print(f"  Maestria em Armas TagsJSON: {dc[1] if dc else None}")

conn.close()
print("\nDONE.")
