"""Popula 6 subclasses do Caçador (Id_Classe=4) com Tagline + 2 habs Nv 3 cada.

Estado pre-migration:
  - Aliança Selvagem (id=21):  já tem 2 habs Nv 3, sem tagline
  - Exterminadores (id=124):    sem habs, sem tagline
  - Viajantes / Enxame / Sombras / Mutantes: NÃO existem ainda

Pós-migration:
  - 6 subs com Tagline curta + Slug consistente
  - 5 das 6 com 2 habs Nv 3 (Aliança já tem; só atualiza descrições/tagline da sub)
  - Habs novas com Origem='subclasse' e TemEscolha=0 (nenhuma exige escolha de jogador no Nv 3)

Idempotência: usa INSERT OR IGNORE pelo slug; UPDATE de Tagline. Habs detecta dup por (Id_Subclasse,Nome,NivelAdquirido).
"""
import json
import shutil
import sqlite3
import time
from pathlib import Path

DB = "bonfas.db"
ID_CACADOR = 4

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

PARSED = json.loads(Path("cacador_subclasses.json").read_text(encoding="utf-8"))
parsed_by_slug = {s["slug"]: s for s in PARSED}

# Subclasses canônicas: nome, slug-canonico, slug-do-parser, tagline curta
SUBS = [
    {
        "nome": "Ordem da Aliança Selvagem",
        "slug": "ordem-da-alianca-selvagem",
        "parser_slug": "ordem-da-alianca-selvagem",
        "tagline": "Caçadores ligados a um companheiro animal primordial que evolui ao seu lado.",
    },
    {
        "nome": "Ordem dos Exterminadores de Monstros",
        "slug": "ordem-exterminadores-monstros",
        "parser_slug": "ordem-dos-exterminadores-de-monstros",
        "tagline": "Caçadores especializados em criaturas de outros planos.",
    },
    {
        "nome": "Ordem dos Viajantes",
        "slug": "ordem-dos-viajantes",
        "parser_slug": "ordem-dos-viajantes",
        "tagline": "Caçadores que cruzam distâncias e fronteiras planares por runas e travessias.",
    },
    {
        "nome": "Ordem do Enxame",
        "slug": "ordem-do-enxame",
        "parser_slug": "ordem-do-enxame",
        "tagline": "Caçadores em simbiose com um enxame de criaturas menores.",
    },
    {
        "nome": "Ordem das Sombras",
        "slug": "ordem-das-sombras",
        "parser_slug": "ordem-das-sombras",
        "tagline": "Caçadores que se movem na umbra e atacam antes de serem vistos.",
    },
    {
        "nome": "Ordem dos Mutantes",
        "slug": "ordem-dos-mutantes",
        "parser_slug": "ordem-dos-mutantes",
        "tagline": "Caçadores que ingerem fórmulas mutagênicas e adaptam o próprio corpo.",
    },
]


def upsert_sub(cur, sub: dict) -> int:
    """Garante a sub no DB. Retorna Id_Subclasse. Atualiza Tagline."""
    row = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
        (ID_CACADOR, sub["slug"]),
    ).fetchone()
    if row:
        sid = row[0]
        cur.execute(
            "UPDATE TB_Subclasse SET Nome=?, Tagline=? WHERE Id_Subclasse=?",
            (sub["nome"], sub["tagline"], sid),
        )
        return sid
    cur.execute(
        """INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline)
           VALUES (?,?,?,?)""",
        (ID_CACADOR, sub["nome"], sub["slug"], sub["tagline"]),
    )
    return cur.lastrowid


def upsert_hab_nv3(cur, sid: int, nome: str, descricao: str) -> str:
    """Insere hab Nv 3 se não existir. Retorna 'inserted'/'skipped'."""
    exists = cur.execute(
        "SELECT 1 FROM TB_ClasseHabilidade WHERE Id_Subclasse=? AND Nome=? AND NivelAdquirido=3",
        (sid, nome),
    ).fetchone()
    if exists:
        return "skipped"
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?,?,?,?,?,0,'subclasse',NULL)""",
        (ID_CACADOR, sid, nome, descricao, 3),
    )
    return "inserted"


conn = sqlite3.connect(DB)
cur = conn.cursor()

for sub in SUBS:
    sid = upsert_sub(cur, sub)
    parsed = parsed_by_slug.get(sub["parser_slug"], {"habs": []})
    habs_nv3 = [h for h in parsed["habs"] if h["nivel"] == 3]
    print(f"\n  sub {sid:>3} {sub['nome']}")
    print(f"      tagline OK")
    for h in habs_nv3:
        status = upsert_hab_nv3(cur, sid, h["nome"], h["descricao"])
        print(f"      Nv3 {h['nome']:<26} [{status}]")

conn.commit()
conn.close()
print("\nDONE.")
