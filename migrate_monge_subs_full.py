"""Popula features Nv 6/11/17 das 9 subs restantes do Monge (Palma Aberta já feita).
Mapeamento por leitura textual (idem Caçador).

Imortal: 2 features Nv 11 (Maestria da Morte + Memórias Póstumas).
Misericórdia: 2 features Nv 11 (Rajada de Cura e Sangue + Cura Acelerada Aprimorada).
Demais subs: 1 feature por nível-marco (6/11/17)."""
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_MONGE = 12

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

FEATS = json.loads(Path("monge_features.json").read_text(encoding="utf-8"))
desc_by = {(f["nivel"], f["nome"]): f["descricao"] for f in FEATS}

# (nivel, nome) -> slug da sub
SUB_FEAT: dict[tuple[int, str], str] = {
    # ---- Nv 6 ----
    (6,  "Explosão de Alma"):                 "alma-ardente",
    (6,  "Aspecto da Alma Astral"):           "alma-astral",
    (6,  "Manipulação Elemental"):            "elemental",
    (6,  "Hora da Colheita"):                 "imortal",
    (6,  "Um com a Lâmina"):                  "kensei",
    (6,  "Toque do Médico"):                  "misericordia",
    (6,  "Gingado Cambaleante"):              "punho-bebado",
    (6,  "Aura Dracônica"):                   "punho-do-dragao",
    (6,  "Passo das Sombras"):                "sombras",
    # ---- Nv 11 ----
    (11, "Terceiro Ardor - Ascensão da Alma"):"alma-ardente",
    (11, "Corpo da Alma Astral"):             "alma-astral",
    (11, "Reabsorção Elemental"):             "elemental",
    (11, "Maestria da Morte"):                "imortal",
    (11, "Memórias Póstumas"):                "imortal",      # Imortal extra
    (11, "Aprimoramento de Precisão"):        "kensei",
    (11, "Rajada de Cura e Sangue"):          "misericordia",
    (11, "Cura Acelerada Aprimorada"):        "misericordia", # Misericórdia extra
    (11, "Fúria Intoxicada"):                 "punho-bebado",
    (11, "Baforada Aprimorada"):              "punho-do-dragao",
    (11, "Oportunista"):                      "sombras",
    # ---- Nv 17 ----
    (17, "Quarto Ardor - Apoteose da Alma"):  "alma-ardente",
    (17, "Despertar da Alma Astral"):         "alma-astral",
    (17, "Ascensão Primordial"):              "elemental",
    (17, "Toque da Morte Eterna"):            "imortal",
    (17, "Precisão Infalível"):               "kensei",
    (17, "Palma da Misericórdia Absoluta"):   "misericordia",
    (17, "Mestre do Punho Bêbado"):           "punho-bebado",
    (17, "Aspecto Ascendente"):               "punho-do-dragao",
    (17, "Duplicata das Sombras"):            "sombras",
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Lookup sids por slug
sid_by_slug = {
    r[1]: r[0]
    for r in cur.execute("SELECT Id_Subclasse, Slug FROM TB_Subclasse WHERE Id_Classe=?", (ID_MONGE,))
}
print(f"Subs Monge encontradas: {len(sid_by_slug)}")
print(sid_by_slug)
print()

ins_count = skip_count = nodesc_count = 0
by_sub: dict[str, int] = {}
for (nivel, nome), slug in SUB_FEAT.items():
    sid = sid_by_slug.get(slug)
    if sid is None:
        print(f"  WARN: sub slug {slug!r} não existe — pula ({nivel},{nome})")
        continue
    desc = desc_by.get((nivel, nome))
    if desc is None:
        print(f"  WARN: NO-DESC ({nivel},{nome}) — pula")
        nodesc_count += 1
        continue
    # Idempotência por (Id_Classe, Id_Subclasse, Nome, Nivel)
    if cur.execute(
        "SELECT 1 FROM TB_ClasseHabilidade "
        "WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND NivelAdquirido=?",
        (ID_MONGE, sid, nome, nivel),
    ).fetchone():
        skip_count += 1
        print(f"  sub {sid:>3} ({slug:<18}) Nv{nivel:>2} {nome:<46} [skip]")
        continue
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?,?,?,?,?,0,'subclasse',NULL)""",
        (ID_MONGE, sid, nome, desc, nivel),
    )
    ins_count += 1
    by_sub[slug] = by_sub.get(slug, 0) + 1
    print(f"  sub {sid:>3} ({slug:<18}) Nv{nivel:>2} {nome:<46} [ins]")

conn.commit()
print(f"\nSummary: {ins_count} inseridas, {skip_count} já existiam, {nodesc_count} sem descricão.")

print("\n=== STATS POR SUB (Monge) ===")
for slug, sid in sorted(sid_by_slug.items()):
    n = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse=?",
        (ID_MONGE, sid),
    ).fetchone()[0]
    print(f"  sub {sid:>3} {slug:<22} {n} habs")

conn.close()
print("\nDONE.")
