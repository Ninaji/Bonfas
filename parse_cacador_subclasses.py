"""Extrai subclasses do Caçador e suas habs do caçador.extracted.html.

Estrutura: H2 "Ordem ..." é o nome da sub. H3 "Nível N: Nome" são habs com nível.
Tagline curta vem do primeiro parágrafo após o H2.
"""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[áàâãä]", "a", s); s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s); s = re.sub(r"[óòôõö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s); s = re.sub(r"[ç]", "c", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def text_until(tag, stop_names=("h1","h2","h3","h4","h5","h6")) -> str:
    out = []
    for sib in tag.next_siblings:
        if getattr(sib, "name", None) in stop_names:
            break
        if hasattr(sib, "get_text"):
            out.append(sib.get_text(" ", strip=True))
        elif isinstance(sib, NavigableString):
            out.append(str(sib).strip())
    return " ".join(p for p in out if p)


def parse(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    subs = []
    cur_sub = None
    for el in soup.find_all(["h2", "h3"]):
        txt = el.get_text(strip=True)
        if not txt:
            continue
        if el.name == "h2":
            if txt.lower().startswith("ordem"):
                cur_sub = {
                    "nome": txt,
                    "slug": slugify(txt),
                    "tagline": text_until(el, stop_names=("h2","h3"))[:200],
                    "habs": [],
                }
                subs.append(cur_sub)
            else:
                cur_sub = None
        elif el.name == "h3" and cur_sub:
            m = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", txt)
            if m:
                nivel = int(m.group(1))
                nome = m.group(2).strip()
                desc = text_until(el)
                cur_sub["habs"].append({"nivel": nivel, "nome": nome[:150], "descricao": desc[:1500]})
    return subs


if __name__ == "__main__":
    src = Path(sys.argv[1] if len(sys.argv) > 1 else r"E:\Obsidian\_raw\caçador.extracted.html")
    subs = parse(src)
    out = Path("cacador_subclasses.json")
    out.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Subclasses: {len(subs)}")
    for s in subs:
        print(f"  - {s['nome']} ({len(s['habs'])} habs)")
        for h in s['habs']:
            print(f"      Nv{h['nivel']:>2} {h['nome']}")
    print(f"\n-> saved {out}")
