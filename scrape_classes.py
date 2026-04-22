"""
Scraper de classes/subclasses/recursos para popular TB_Classe, TB_Subclasse,
TB_RecursoClasse, TB_ClasseHabilidade, TB_OpcaoJogo, TB_AcessoOpcao.

WorldAnvil bloqueia acesso automatizado (Cloudflare → 403). Soluções suportadas:

  MODO 1 — Cookies autenticados
     Faça login em worldanvil.com no navegador, abra DevTools → Application →
     Cookies → copie todos em um arquivo JSON (array de {name, value, domain}).
     Rode:  python scrape_classes.py --cookies cookies.json

  MODO 2 — Dumps HTML locais
     No navegador, abra cada página de classe e salve-a como HTML completo
     (Ctrl+S).  Coloque os arquivos em uma pasta e aponte:
       python scrape_classes.py --html-dir ./dumps

  MODO 3 — URL + cookies em linha de comando (testes rápidos)
       python scrape_classes.py --url https://... --cookie "sessionid=abc; ..."

Em qualquer modo, o parser tenta extrair:
  - Nome da classe (h1 ou og:title)
  - Tagline (subtítulo / og:description)
  - Tabela de progressão (se houver): nível → recursos/valores
  - Subclasses mencionadas (links para /c/<slug>-category-1 etc.)
  - Blocos de "Habilidades" / "Recursos de Classe"
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from urllib import request

try:
    from html.parser import HTMLParser
except ImportError:
    HTMLParser = None  # placeholder; we'll use regex fallback

DB_PATH = Path(__file__).parent / "bonfas.db"

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")


# ---------------------------------------------------------------------------
# util
# ---------------------------------------------------------------------------
def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "item"


def fetch(url: str, cookie: str | None = None, timeout: int = 25) -> str:
    req = request.Request(url, headers={
        "User-Agent": UA_DESKTOP,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "close",
    })
    if cookie:
        req.add_header("Cookie", cookie)
    with request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# parser (tolerante e orientado a heurísticas)
# ---------------------------------------------------------------------------
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(html: str) -> str:
    t = TAG_RE.sub(" ", html)
    return WS_RE.sub(" ", t).strip()


def extract_title(html: str) -> str | None:
    m = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    return clean(m.group(1)) if m else None


def extract_tagline(html: str) -> str | None:
    m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html, re.I)
    if m:
        return m.group(1).strip()[:255]
    return None


def find_subclass_links(html: str) -> list[dict]:
    # URLs tipo /w/.../c/<slug>-category-\d+
    out, seen = [], set()
    for m in re.finditer(
        r'href="(/w/[^"]+/c/[a-z0-9\-]+-category[^"]*)"[^>]*>([^<]+)</a>',
        html, re.I
    ):
        href, txt = m.group(1), clean(m.group(2))
        if href in seen or not txt:
            continue
        seen.add(href)
        out.append({"url": href, "nome": txt})
    return out


def find_progression_table(html: str) -> list[dict]:
    """Procura tabela com coluna 'Nível'/'Nivel' na primeira célula."""
    tables = re.findall(r"<table.*?</table>", html, re.I | re.S)
    for t in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.I | re.S)
        if len(rows) < 3:
            continue
        header = clean(rows[0])
        if not re.search(r"\bn[íi]vel\b", header, re.I):
            continue
        cols = [clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>",
                                             rows[0], re.I | re.S)]
        out = []
        for r in rows[1:]:
            cells = [clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>",
                                                  r, re.I | re.S)]
            if not cells or not cells[0]:
                continue
            try:
                nivel = int(re.sub(r"\D+", "", cells[0]) or 0)
            except ValueError:
                continue
            if not nivel:
                continue
            row = {"nivel": nivel}
            for i, c in enumerate(cells[1:], 1):
                key = cols[i] if i < len(cols) else f"col{i}"
                row[key] = c
            out.append(row)
        if out:
            return out
    return []


def find_habilidades(html: str) -> list[dict]:
    """Heurística: procura headings h2/h3 e bloco seguinte de parágrafos."""
    out = []
    for m in re.finditer(
        r"<h[23][^>]*>(.*?)</h[23]>\s*((?:<p[^>]*>.*?</p>\s*){0,6})",
        html, re.I | re.S
    ):
        nome = clean(m.group(1))
        desc = clean(m.group(2))
        if not nome or len(nome) > 80 or len(desc) < 30:
            continue
        # tenta extrair nível mencionado no título (ex.: "Cura Inspiradora (Nível 5)")
        nm = re.search(r"n[íi]vel\s+(\d+)", nome, re.I)
        nivel = int(nm.group(1)) if nm else 1
        out.append({"nome": nome, "descricao": desc[:2000], "nivel": nivel})
    return out


def parse_class_page(html: str, url: str | None = None) -> dict:
    return {
        "nome":        extract_title(html),
        "tagline":     extract_tagline(html),
        "url":         url,
        "subclasses":  find_subclass_links(html),
        "progressao":  find_progression_table(html),
        "habilidades": find_habilidades(html),
    }


# ---------------------------------------------------------------------------
# persistência
# ---------------------------------------------------------------------------
def save(parsed: dict, conn: sqlite3.Connection) -> dict:
    if not parsed.get("nome"):
        return {"inserido": 0, "erro": "sem nome"}
    cur = conn.cursor()
    sl = slug(parsed["nome"])
    cur.execute(
        """INSERT INTO TB_Classe (Nome, Slug, Tagline, SourceURL)
               VALUES (?, ?, ?, ?)
             ON CONFLICT(Slug) DO UPDATE SET
                   Nome=excluded.Nome, Tagline=excluded.Tagline,
                   SourceURL=excluded.SourceURL
           RETURNING Id_Classe""",
        (parsed["nome"], sl, parsed.get("tagline"), parsed.get("url")),
    )
    id_classe = cur.fetchone()[0]

    # subclasses
    id_sub_by_slug = {}
    for sc in parsed.get("subclasses", []):
        s = slug(sc["nome"])
        if not s:
            continue
        cur.execute(
            """INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, SourceURL)
                   VALUES (?, ?, ?, ?)
                 ON CONFLICT(Id_Classe, Slug) DO UPDATE SET
                       Nome=excluded.Nome, SourceURL=excluded.SourceURL
               RETURNING Id_Subclasse""",
            (id_classe, sc["nome"], s, sc.get("url")),
        )
        id_sub_by_slug[s] = cur.fetchone()[0]

    # recursos por nível (apaga antigos desta classe antes de inserir)
    cur.execute("DELETE FROM TB_RecursoClasse WHERE Id_Classe=?", (id_classe,))
    for row in parsed.get("progressao", []):
        nivel = row.get("nivel") or 0
        for k, v in row.items():
            if k == "nivel" or not v:
                continue
            cur.execute(
                """INSERT INTO TB_RecursoClasse
                       (Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor)
                       VALUES (?, NULL, ?, ?, ?, ?)""",
                (id_classe, k[:100], slug(k)[:100], nivel, str(v)[:50]),
            )

    # habilidades
    cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
                (id_classe,))
    for h in parsed.get("habilidades", []):
        cur.execute(
            """INSERT INTO TB_ClasseHabilidade
                   (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido)
                   VALUES (?, NULL, ?, ?, ?)""",
            (id_classe, h["nome"][:150], h["descricao"], h["nivel"]),
        )
    conn.commit()
    return {
        "id_classe": id_classe,
        "subclasses": len(id_sub_by_slug),
        "recursos": sum(len([k for k in r if k != "nivel"]) for r in parsed.get("progressao", [])),
        "habilidades": len(parsed.get("habilidades", [])),
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def load_cookies(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return "; ".join(f"{k}={v}" for k, v in data.items())
    if isinstance(data, list):
        return "; ".join(f"{c['name']}={c['value']}" for c in data if "name" in c)
    raise SystemExit("formato de cookies não reconhecido")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL de uma página de classe")
    ap.add_argument("--urls", help="Arquivo com uma URL por linha")
    ap.add_argument("--html-dir", help="Pasta com dumps HTML (*.html)")
    ap.add_argument("--cookies", help="JSON com cookies autenticados")
    ap.add_argument("--cookie", help="String de Cookie inline")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cookie = args.cookie
    if args.cookies:
        cookie = load_cookies(Path(args.cookies))

    sources: list[tuple[str, str | None]] = []   # (html, url)
    if args.url:
        sources.append((fetch(args.url, cookie), args.url))
    if args.urls:
        for line in Path(args.urls).read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            try:
                sources.append((fetch(url, cookie), url))
                print(f"ok: {url}")
            except Exception as e:
                print(f"falha {url}: {e}", file=sys.stderr)
    if args.html_dir:
        for p in sorted(Path(args.html_dir).glob("*.html")):
            sources.append((p.read_text(encoding="utf-8", errors="ignore"), p.name))

    if not sources:
        ap.error("use --url / --urls / --html-dir")

    if args.dry_run:
        for html, url in sources:
            print(json.dumps(parse_class_page(html, url), ensure_ascii=False, indent=2)[:4000])
            print("---")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        for html, url in sources:
            p = parse_class_page(html, url)
            r = save(p, conn)
            print(f"{p.get('nome')!r:30s} -> {r}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
