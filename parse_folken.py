"""Parsea folken.extracted.html -> emite estrutura {raca, linhagens[], tracos[], talentos[]}.

Usado pra popular TB_Raca/TB_Linhagem/TB_TracoRacial/TB_TalentoRacial via migration.
Não escreve no DB diretamente — só extrai e imprime/salva JSON.
"""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[áàâãä]", "a", s)
    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s)
    s = re.sub(r"[óòôõö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    out = {
        "raca": {"nome": "Folken", "slug": "folken"},
        "linhagens": [],
        "tracos_base": [],
        "tracos_linhagem": {},   # linhagem -> [{nome, descricao}]
        "talentos": [],
    }

    # Extrai texto após cada H5, parando no próximo H4/H3/H2/H5
    def text_after(tag) -> str:
        partes = []
        for sib in tag.next_siblings:
            if getattr(sib, "name", None) in ("h5", "h4", "h3", "h2", "h1"):
                break
            if hasattr(sib, "get_text"):
                partes.append(sib.get_text(" ", strip=True))
            elif isinstance(sib, str):
                partes.append(sib.strip())
        return " ".join(p for p in partes if p)[:1500]

    # Walk pelos headings em ordem
    state = None  # None | "tracos_base" | "linhagens" | "evolucao_racial"
    current_lin = None

    for h in soup.find_all(["h2", "h3", "h4", "h5"]):
        txt = h.get_text(strip=True)
        if not txt:
            continue
        if h.name == "h2":
            if "Folken" == txt:
                state = "raca_intro"
            elif "Diverg" in txt:
                state = "linhagens_intro"
        elif h.name == "h3":
            if "Tra" in txt and "Base" in txt:
                state = "tracos_base"
            elif "Linhagens Folken" in txt:
                state = "linhagens"
            elif "Evolu" in txt and "Racial" in txt:
                state = "evolucao_racial"
        elif h.name == "h4" and state == "linhagens":
            # ex: "Raizveloz (Folken da Floresta)"
            m = re.match(r"([^()]+)\(([^)]+)\)", txt)
            nome = (m.group(1) if m else txt).strip()
            tagline = (m.group(2) if m else "").strip()
            current_lin = nome
            out["linhagens"].append({"nome": nome, "slug": slugify(nome), "tagline": tagline})
            out["tracos_linhagem"][nome] = []
        elif h.name == "h5":
            desc = text_after(h)
            if state == "tracos_base":
                out["tracos_base"].append({"nome": txt, "descricao": desc})
            elif state == "linhagens" and current_lin:
                out["tracos_linhagem"][current_lin].append({"nome": txt, "descricao": desc})
            elif state == "evolucao_racial":
                out["talentos"].append({"nome": txt, "descricao": desc})

    return out


if __name__ == "__main__":
    src = Path(sys.argv[1] if len(sys.argv) > 1 else r"E:\Obsidian\_raw\folken.extracted.html")
    data = parse(src)
    out = Path("folken_parsed.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raça: {data['raca']['nome']}")
    print(f"Linhagens: {len(data['linhagens'])} -> {[l['nome'] for l in data['linhagens']]}")
    print(f"Traços base: {len(data['tracos_base'])} -> {[t['nome'] for t in data['tracos_base']]}")
    for lin, tracos in data['tracos_linhagem'].items():
        print(f"  {lin}: {len(tracos)} traços -> {[t['nome'] for t in tracos]}")
    print(f"Talentos: {len(data['talentos'])}")
    print(f"\n-> saved {out}")
