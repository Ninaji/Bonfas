"""
Extrai catálogo de Manobras de Combate do artigo do Guerreiro.
Popula TB_Manobra com tags [grau, classe].

Uso:
    python parse_manobras.py paginas/guerreiro.html guerreiro
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

from parse_artigo import parse

DB = Path(__file__).parent / "bonfas.db"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s or "")).strip()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def extract_manobras_grau(secao_html: str, grau: int, fonte: str) -> list[dict]:
    """Cada H5 é uma manobra; corpo até próximo H5 é Flavor+Descricao."""
    out = []
    h5s = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", secao_html, re.I | re.S))
    for i, m in enumerate(h5s):
        nome = clean(m.group(1))
        if not nome:
            continue
        start = m.end()
        end = h5s[i+1].start() if i+1 < len(h5s) else len(secao_html)
        body = secao_html[start:end]
        # flavor = primeiro <em>...</em>
        flavor_m = re.search(r"<em[^>]*>(.*?)</em>", body, re.I | re.S)
        flavor = clean(flavor_m.group(1)) if flavor_m else ""
        # descricao = tudo em texto limpo, sem o flavor
        desc = clean(body)
        if flavor and desc.startswith(flavor):
            desc = desc[len(flavor):].strip()
        out.append({
            "nome": nome,
            "grau": grau,
            "flavor": flavor,
            "descricao": desc,
            "tags": [fonte, f"{grau}grau"],
        })
    return out


def run(arq: Path, fonte: str):
    p = parse(arq)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # apaga manobras anteriores dessa fonte
    cur.execute("DELETE FROM TB_Manobra WHERE Fonte=?", (fonte,))

    total = 0
    for s in p["secoes"]:
        m = re.match(r"^Manobras de Combate de\s+(\d+)[ºo°\s]*Grau", s["titulo"], re.I)
        if not m:
            continue
        grau = int(m.group(1))
        manobras = extract_manobras_grau(s["conteudo_html"], grau, fonte)
        for mn in manobras:
            cur.execute(
                """INSERT INTO TB_Manobra (Nome, Slug, Grau, TagsJSON, Flavor, Descricao, Fonte)
                       VALUES (?,?,?,?,?,?,?)
                     ON CONFLICT(Slug) DO UPDATE SET
                           Grau=excluded.Grau, TagsJSON=excluded.TagsJSON,
                           Flavor=excluded.Flavor, Descricao=excluded.Descricao""",
                (mn["nome"][:150], slug(mn["nome"]), mn["grau"],
                 json.dumps(mn["tags"]), mn["flavor"][:500], mn["descricao"][:3000], fonte),
            )
            total += 1
        print(f"  grau {grau}: {len(manobras)} manobras")
    conn.commit()
    print(f"OK total = {total}")
    for r in cur.execute("SELECT Grau, COUNT(*) FROM TB_Manobra GROUP BY Grau ORDER BY Grau"):
        print(f"  grau {r[0]}: {r[1]} manobras no DB")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("uso: python parse_manobras.py <arquivo.html> <fonte_slug>")
    run(Path(sys.argv[1]), sys.argv[2])
