"""
Extrai o HTML real de um arquivo 'view-source' do Chrome DevTools
(cada linha fica dentro de um <td class="line-content">) e depois usa
o mesmo extractor de classes para popular o DB.

Uso:
    python parse_viewsource.py paginas/guerreiro.html
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class LineContentExtractor(HTMLParser):
    """Captura o texto de <td class='line-content'>... </td> por linha."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_td = False
        self.cur = []
        self.lines: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            cls = dict(attrs).get("class", "")
            if "line-content" in cls:
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


def extract_html(src: str) -> str:
    p = LineContentExtractor()
    p.feed(src)
    return "\n".join(p.lines)


def parse_classe(html: str) -> dict:
    """Parsing leve do HTML real para extrair nome/tagline/progressão/habilidades.
    Mesmo formato que o extractor JS no Chrome MCP usava."""
    TAG = re.compile(r"<[^>]+>")
    NBSP = re.compile(r"\s+")
    clean = lambda s: NBSP.sub(" ", TAG.sub(" ", s or "")).strip()

    # <h1> ... </h1>
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    nome = clean(m.group(1)) if m else None

    # tagline (og:description ou article-subtitle)
    m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html, re.I)
    tagline = (m.group(1) if m else "")[:250]

    # ---- tabela de progressão ----
    progressao = []
    for tbl in re.findall(r"<table.*?</table>", html, re.I | re.S):
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.I | re.S)
        if len(rows) < 3:
            continue
        head = [clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", rows[0], re.I | re.S)]
        if not head or not re.search(r"N[íi]vel", head[0] or "", re.I):
            continue
        for r in rows[1:]:
            cells = [clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.I | re.S)]
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
                row[head[i] if i < len(head) else f"col{i}"] = c
            progressao.append(row)
        break

    # ---- habilidades e subclasses (varre h2/h3/h4 com pós-conteúdo <p>/<ul>) ----
    SECS = list(re.finditer(
        r"<(h[234])[^>]*>(.*?)</\1>\s*((?:<(?:p|ul)[^>]*>.*?</(?:p|ul)>\s*)*)",
        html, re.I | re.S,
    ))
    START_RE = re.compile(r"(Habilidade|Caracter[íi]stica)s?\s+(de|do|da)\s+", re.I)
    STAT_RE = re.compile(r"^(STR|DEX|CON|INT|WIS|CHA|Ações|Ataques|Equipamento)$", re.I)

    started = False
    subclasses, habilidades = [], []
    mode = None
    current_sub = None
    for m in SECS:
        tag = m.group(1).lower()
        title = clean(m.group(2))
        body = clean(m.group(3))
        if tag == "h2":
            if not started:
                if START_RE.search(title):
                    started = True; mode = "princ"; current_sub = None
                continue
            if STAT_RE.match(title):
                break
            if START_RE.search(title):
                mode = "princ"; current_sub = None
                continue
            mode = "sub"
            current_sub = {"nome": title, "habilidades": []}
            subclasses.append(current_sub)
            continue
        if not started:
            continue
        if tag in ("h3", "h4") and title:
            nm = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", title, re.I)
            if nm:
                nivel = int(nm.group(1)); name = nm.group(2).strip()
            else:
                nivel = 1; name = title
            if not body:
                continue
            rec = {"nome": name[:150], "nivel": nivel, "descricao": body}
            if mode == "princ":
                habilidades.append(rec)
            elif current_sub:
                current_sub["habilidades"].append(rec)

    return {
        "nome": nome,
        "tagline": tagline,
        "progressao": progressao,
        "habilidades_principais": habilidades,
        "subclasses": subclasses,
    }


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("uso: python parse_viewsource.py <arquivo.html>")
    src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    html = extract_html(src)
    # salva debug
    dbg = Path(sys.argv[1]).with_suffix(".extracted.html")
    dbg.write_text(html, encoding="utf-8")
    print(f"[extraído] HTML real: {len(html):,} chars -> {dbg.name}")

    parsed = parse_classe(html)
    print(f"\n== {parsed['nome']!r} ==")
    print(f"  tagline:      {parsed['tagline'][:100]}")
    print(f"  progressão:   {len(parsed['progressao'])} níveis")
    print(f"  habs princ:   {len(parsed['habilidades_principais'])}")
    print(f"  subclasses:   {len(parsed['subclasses'])}")
    for s in parsed["subclasses"]:
        print(f"     - {s['nome']:30} ({len(s['habilidades'])} habs)")

    # salva JSON estruturado para ingest_classes.py
    import json
    out = Path("bonfas_classes_extra.json")
    existing = []
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8"))
    existing.append(parsed)
    out.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> adicionado a {out}  (total: {len(existing)})")


if __name__ == "__main__":
    main()
