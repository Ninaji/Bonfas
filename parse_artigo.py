"""
Parser genérico para artigos do Bonfire Tales salvos via Chrome (view-source).
Extrai H1/H2/H3, tabelas e parágrafos EM ORDEM — preserva 1:1 o conteúdo do site.

Uso:
    python parse_artigo.py paginas/humano.html       # imprime estrutura
    python parse_artigo.py paginas/humano.html --json # dump JSON estruturado
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path


# --- desembrulha view-source do Chrome -----------------------------------
class LineContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_td = False
        self.cur = []
        self.lines = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            if "line-content" in dict(attrs).get("class", ""):
                self.in_td = True
                self.cur = []
        elif tag == "br" and self.in_td:
            self.cur.append("\n")

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            self.lines.append("".join(self.cur))
            self.cur = []
            self.in_td = False

    def handle_data(self, data):
        if self.in_td:
            self.cur.append(data)


def unwrap_viewsource(src: str) -> str:
    if "line-content" in src[:3000]:
        p = LineContentExtractor()
        p.feed(src)
        return "\n".join(p.lines)
    return src


# --- parser do artigo real -----------------------------------------------
TAG = re.compile(r"<[^>]+>")
WS  = re.compile(r"\s+")

def clean(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s or "")).strip()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def extract_h1(html: str) -> str | None:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m: return clean(m.group(1))
    # fallback: primeiro <h2> que não seja de UI (Mapas/Linhas do Tempo)
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S):
        t = clean(m.group(1))
        if t and not re.match(r"^(Mapas|Linhas do Tempo)$", t, re.I):
            return t
    return None


def extract_tagline(html: str) -> str | None:
    m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html, re.I)
    if m:
        return m.group(1).strip()[:300]
    # tenta <h2>/<em> logo após o h1
    m = re.search(r"<h1[^>]*>.*?</h1>\s*(?:<\w+[^>]*>)*\s*<(?:h2|em|i)[^>]*>([^<]+)", html, re.I | re.S)
    if m:
        return clean(m.group(1))[:300]
    return None


def split_sections(html: str) -> list[dict]:
    """Varre o documento em ordem e retorna lista [{level:2|3, titulo, conteudo_html, conteudo_txt}]."""
    secs = []
    # captura H1 inicial (título principal) + depois blocos H2/H3 até o próximo header
    positions = []
    for m in re.finditer(r"<(h[234])[^>]*>(.*?)</\1>", html, re.I | re.S):
        positions.append({
            "lvl": int(m.group(1)[1]),
            "titulo": clean(m.group(2)),
            "start": m.end(),
            "head_start": m.start(),
        })
    # conteúdo de cada seção vai até o próximo header de mesmo ou menor nível
    for i, p in enumerate(positions):
        end = len(html)
        for j in range(i + 1, len(positions)):
            if positions[j]["lvl"] <= p["lvl"]:
                end = positions[j]["head_start"]
                break
            # se é subheader, só para em próximo de mesmo/menor nível
        body = html[p["start"]:end]
        secs.append({
            "nivel": p["lvl"],
            "titulo": p["titulo"],
            "conteudo_html": body,
            "conteudo_txt": clean(body),
        })
    return secs


def parse_tables(html: str) -> list[list[list[str]]]:
    out = []
    for tbl in re.findall(r"<table.*?</table>", html, re.I | re.S):
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.I | re.S)
        parsed = []
        for r in rows:
            cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.I | re.S)
            parsed.append([clean(c) for c in cells])
        if parsed:
            out.append(parsed)
    return out


def parse(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    html = unwrap_viewsource(raw)
    titulo = extract_h1(html)
    return {
        "arquivo": path.name,
        "titulo": titulo,
        "slug": slug(titulo) if titulo else None,
        "tagline": extract_tagline(html),
        "secoes": split_sections(html),
        "tabelas": parse_tables(html),
        "html_len": len(html),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    p = parse(Path(sys.argv[1]))
    if "--json" in sys.argv:
        print(json.dumps(p, ensure_ascii=False, indent=2))
        return
    print(f"=== {p['titulo']} ===  slug={p['slug']}  (html={p['html_len']:,})")
    print(f"tagline: {p['tagline']!r}")
    print(f"secoes: {len(p['secoes'])}  tabelas: {len(p['tabelas'])}\n")
    for s in p["secoes"][:40]:
        t = s["titulo"][:70].replace("\n", " ")
        print(f"  H{s['nivel']}  {t}  ({len(s['conteudo_txt'])} chars)")


if __name__ == "__main__":
    main()
