"""Fix #1 — Marca Arcana grant tags.

Pattern (conforme docs/tags-e-cascata.md §2.1):
  - 'talento-origem' Marca Arcana da X: ao ser escolhida, grant a tag
    'marca-arcana-da-{x}' para o personagem. Isso destrava a Superior
    correspondente que tem essa tag como prereq.
  - 'talento-geral' Marca Arcana Superior da X: ao ser escolhida, grant
    'marca-superior' para destrava Marca Potente (que tem prereq marca-superior).

Idempotente. Backup automático.
"""
import json
import shutil
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

DB = 'bonfas.db'
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}\n')

# 12 Marcas Arcanas — slug do "thing" sem o sufixo -origem (= a tag prereq)
MARCAS = [
    "da-busca", "da-criacao", "da-escrita", "da-protecao", "da-restauracao",
    "da-revelacao", "da-tormenta", "da-travessia", "da-vigilia",
    "do-pastoreio", "do-refugio", "do-veu",
]

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== Origem talents (talento-origem): grant marca-arcana-{x} ===")
for marca_slug in MARCAS:
    full_slug = f"marca-arcana-{marca_slug}-origem"
    grant_tag = f"marca-arcana-{marca_slug}"
    r = cur.execute(
        "SELECT Id_Opcao, Nome, TagsJSON FROM TB_OpcaoJogo WHERE Slug=?",
        (full_slug,),
    ).fetchone()
    if not r:
        print(f"  MISSING: slug={full_slug!r}")
        continue
    current = json.loads(r["TagsJSON"] or "[]") or []
    if grant_tag in current:
        print(f"  skip   id={r['Id_Opcao']:>3} {r['Nome']:<40} já tem {grant_tag!r}")
        continue
    current.append(grant_tag)
    cur.execute(
        "UPDATE TB_OpcaoJogo SET TagsJSON=? WHERE Id_Opcao=?",
        (json.dumps(current, ensure_ascii=False), r["Id_Opcao"]),
    )
    print(f"  set    id={r['Id_Opcao']:>3} {r['Nome']:<40} → {current}")

print("\n=== Superior talents (talento-geral): adicionar marca-superior ===")
for marca_slug in MARCAS:
    superior_slug = f"marca-arcana-superior-{marca_slug}"
    r = cur.execute(
        "SELECT Id_Opcao, Nome, TagsJSON FROM TB_OpcaoJogo WHERE Slug=?",
        (superior_slug,),
    ).fetchone()
    if not r:
        print(f"  MISSING: slug={superior_slug!r}")
        continue
    current = json.loads(r["TagsJSON"] or "[]") or []
    if "marca-superior" in current:
        print(f"  skip   id={r['Id_Opcao']:>3} {r['Nome']:<55} já tem marca-superior")
        continue
    current.append("marca-superior")
    cur.execute(
        "UPDATE TB_OpcaoJogo SET TagsJSON=? WHERE Id_Opcao=?",
        (json.dumps(current, ensure_ascii=False), r["Id_Opcao"]),
    )
    print(f"  set    id={r['Id_Opcao']:>3} {r['Nome']:<55}")

# Bonus: Marca Anômala (origem) grants marca-anomala; Marca Anômala Maior (geral)
# tem prereq marca-anomala (mesma lógica). Verifica e aplica.
print("\n=== Marca Anômala (mesma lógica) ===")
r = cur.execute("SELECT Id_Opcao, Nome, TagsJSON FROM TB_OpcaoJogo WHERE Slug='marca-anomala-origem'").fetchone()
if r:
    current = json.loads(r["TagsJSON"] or "[]") or []
    if "marca-anomala" not in current:
        current.append("marca-anomala")
        cur.execute("UPDATE TB_OpcaoJogo SET TagsJSON=? WHERE Id_Opcao=?",
                    (json.dumps(current, ensure_ascii=False), r["Id_Opcao"]))
        print(f"  set    id={r['Id_Opcao']} Marca Anômala (origem) → {current}")
    else:
        print(f"  skip   id={r['Id_Opcao']} já tem marca-anomala")
# Marca Anômala Maior também deveria virar caminho pra Marca Potente
r = cur.execute("SELECT Id_Opcao, Nome, TagsJSON FROM TB_OpcaoJogo WHERE Slug='marca-anomala-maior'").fetchone()
if r:
    current = json.loads(r["TagsJSON"] or "[]") or []
    if "marca-superior" not in current:
        current.append("marca-superior")  # equivalência: anômala maior conta como superior
        cur.execute("UPDATE TB_OpcaoJogo SET TagsJSON=? WHERE Id_Opcao=?",
                    (json.dumps(current, ensure_ascii=False), r["Id_Opcao"]))
        print(f"  set    id={r['Id_Opcao']} Marca Anômala Maior → {current}")

conn.commit()

# Validação
print("\n=== Validação: o que cada Marca grants ===")
for r in cur.execute("""
    SELECT Id_Opcao, Nome, Slug, Tipo, TagsJSON FROM TB_OpcaoJogo
    WHERE Slug LIKE 'marca-arcana-%' OR Slug LIKE 'marca-anomala%' OR Slug='marca-potente'
    ORDER BY Tipo, Nome
"""):
    print(f"  [{r['Tipo']:<14}] {r['Nome']:<50} tags={r['TagsJSON']}")

conn.close()
print("\nDONE.")
