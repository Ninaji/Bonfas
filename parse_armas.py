"""
Parser de armas + maestrias do _raw/armas bonfire.html (artigo Bonfire Tales).

Popula:
  TB_Arma     - cada linha de tabela em sections H3 (Armas Simples, Marciais, Fogo, etc.)
                MaestriasJSON = array com nomes (PT/EN) extraidos da coluna "Maestrias (Escolha 1)"
  TB_Maestria - linhas da tabela na H2 "Maestrias de Arma"

1:1 com a fonte (Regra #0). Idempotente por slug (UPDATE on conflict).

Uso:
    python parse_armas.py "E:/Obsidian/_raw/armas bonfire.html"
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_artigo import parse  # type: ignore

DB = Path(__file__).parent / "bonfas.db"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def clean(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s or "")).strip()


CATEGORIA_MAP = {
    "armas-simples": "simples-corpo",
    "armas-simples-a-distancia": "simples-distancia",
    "armas-marciais-corpo-a-corpo": "marcial-corpo",
    "armas-marciais-a-distancia": "marcial-distancia",
    "armas-de-fogo": "fogo",
}


def extract_table_rows(secao_html: str) -> list[list[str]]:
    """Extrai linhas (sem header) da primeira tabela da secao."""
    rows: list[list[str]] = []
    table_match = re.search(r"<table[^>]*>(.*?)</table>", secao_html, re.I | re.S)
    if not table_match:
        return rows
    table_html = table_match.group(1)
    tr_matches = re.finditer(r"<tr[^>]*>(.*?)</tr>", table_html, re.I | re.S)
    for tr in tr_matches:
        tr_html = tr.group(1)
        # pula header (tem <th>)
        if re.search(r"<th\b", tr_html, re.I):
            continue
        cells = [clean(td.group(1)) for td in re.finditer(r"<td[^>]*>(.*?)</td>", tr_html, re.I | re.S)]
        if cells:
            rows.append(cells)
    return rows


def parse_maestrias_str(s: str) -> list[dict]:
    """De 'Corte (Nick), Vexar (Vex)' -> [{nome:Corte, ingles:Nick}, {nome:Vexar, ingles:Vex}]."""
    out = []
    for part in re.split(r",\s*", s):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", part)
        if m:
            out.append({"nome": m.group(1).strip(), "ingles": m.group(2).strip()})
        else:
            out.append({"nome": part, "ingles": None})
    return out


def populate_armas(data: dict, conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    total = 0
    inserted = 0
    updated = 0

    for s in data["secoes"]:
        sec_slug = slug(s["titulo"])
        cat = CATEGORIA_MAP.get(sec_slug)
        if not cat:
            continue
        linhas = extract_table_rows(s["conteudo_html"])
        for linha in linhas:
            if len(linha) < 5:
                continue
            nome, preco, dano, propriedades, maestrias_str = linha[:5]
            if not nome:
                continue
            maestrias = parse_maestrias_str(maestrias_str)
            arma_slug = slug(nome)
            cur.execute("SELECT Id_Arma FROM TB_Arma WHERE Slug=?", (arma_slug,))
            existing = cur.fetchone()
            maestrias_json = json.dumps(maestrias, ensure_ascii=False)
            if existing:
                cur.execute(
                    "UPDATE TB_Arma SET Nome=?, Categoria=?, Preco=?, Dano=?, Propriedades=?, "
                    "MaestriasJSON=?, Fonte=? WHERE Id_Arma=?",
                    (nome, cat, preco, dano, propriedades, maestrias_json,
                     "armas bonfire.html", existing[0]),
                )
                updated += 1
            else:
                cur.execute(
                    "INSERT INTO TB_Arma (Nome, Slug, Categoria, Preco, Dano, Propriedades, "
                    "MaestriasJSON, Fonte) VALUES (?,?,?,?,?,?,?,?)",
                    (nome, arma_slug, cat, preco, dano, propriedades, maestrias_json,
                     "armas bonfire.html"),
                )
                inserted += 1
            total += 1

    conn.commit()
    print(f"[armas] total={total} inseridas={inserted} atualizadas={updated}")
    return total


def populate_maestrias(data: dict, conn: sqlite3.Connection) -> int:
    """Extrai a tabela da H2 'Maestrias de Arma'."""
    cur = conn.cursor()
    total = 0
    inserted = 0
    updated = 0

    sec = next((s for s in data["secoes"] if slug(s["titulo"]) == "maestrias-de-arma"), None)
    if not sec:
        print("WARN: secao 'Maestrias de Arma' nao encontrada")
        return 0

    linhas = extract_table_rows(sec["conteudo_html"])
    for linha in linhas:
        if len(linha) < 2:
            continue
        nome_full, efeito = linha[:2]
        # nome_full pode ser "Ágil (Agile)"
        m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", nome_full)
        if m:
            nome = m.group(1).strip()
            ingles = m.group(2).strip()
        else:
            nome = nome_full
            ingles = None
        if not nome:
            continue
        m_slug = slug(nome)
        cur.execute("SELECT Id_Maestria FROM TB_Maestria WHERE Slug=?", (m_slug,))
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE TB_Maestria SET Nome=?, NomeIngles=?, Efeito=?, Fonte=? WHERE Id_Maestria=?",
                (nome, ingles, efeito[:3000], "armas bonfire.html", existing[0]),
            )
            updated += 1
        else:
            cur.execute(
                "INSERT INTO TB_Maestria (Nome, NomeIngles, Slug, Efeito, Fonte) VALUES (?,?,?,?,?)",
                (nome, ingles, m_slug, efeito[:3000], "armas bonfire.html"),
            )
            inserted += 1
        total += 1

    conn.commit()
    print(f"[maestrias] total={total} inseridas={inserted} atualizadas={updated}")
    return total


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"ERRO: {src} nao existe", file=sys.stderr)
        return 1

    data = parse(src)
    conn = sqlite3.connect(str(DB))
    try:
        populate_armas(data, conn)
        populate_maestrias(data, conn)
    finally:
        conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
