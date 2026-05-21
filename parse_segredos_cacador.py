"""Parser dos 19 Segredos de Caçador (Alquimia/Armadilhas/Conhecimentos).

Estrutura: H3 'Segredos de Caçador: <Linha>' agrupa H5 'Nome do Segredo' até próxima H3.
Cada H5 tem: flavor (1ª linha em itálico), Custo, Efeito.
"""
import json
import re
from html import unescape
from pathlib import Path


def slugify(s: str) -> str:
    s = s.lower().strip()
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    for k,v in repl.items(): s = s.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def cleantext(s: str, maxlen: int = 1500) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:maxlen]


def parse_section(html: str, start: int, end: int, linha_nome: str) -> list[dict]:
    chunk = html[start:end]
    out = []
    h5_matches = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", chunk, re.IGNORECASE | re.DOTALL))
    for i, m in enumerate(h5_matches):
        nome = cleantext(m.group(1), 100)
        body_start = m.end()
        body_end = h5_matches[i + 1].start() if i + 1 < len(h5_matches) else len(chunk)
        body = cleantext(chunk[body_start:body_end])
        # Custo: regex match "Custo: 1 Ponto de Segredo"
        custo_match = re.search(r"Custo:\s*(\d+)\s*Ponto", body, re.IGNORECASE)
        custo = int(custo_match.group(1)) if custo_match else 1
        # Acao: "Como Ação" / "Como Ação Bônus" / "Como Reação"
        acao_match = re.search(r"Como\s+(A[çc][ãa]o\s+B[ôo]nus|A[çc][ãa]o|Rea[çc][ãa]o)", body, re.IGNORECASE)
        acao = acao_match.group(1).strip() if acao_match else None
        # Flavor: texto antes de "Custo:"
        flavor = body.split("Custo:")[0].strip() if "Custo:" in body else ""
        out.append({
            "nome": nome,
            "slug": slugify(nome),
            "linha": linha_nome,
            "custo": custo,
            "acao": acao,
            "flavor": flavor[:500],
            "descricao": body,
        })
    return out


if __name__ == "__main__":
    src = Path(r"E:\Obsidian\_raw\caçador.extracted.html")
    html = src.read_text(encoding="utf-8")

    todos = []
    todos += parse_section(html, 67508, 75464, "Alquimia e Poções")
    todos += parse_section(html, 75464, 80265, "Armadilhas e Emboscadas")
    todos += parse_section(html, 80265, 86561, "Conhecimentos Ancestrais")

    out = Path("segredos_cacador.json")
    out.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Total: {len(todos)} segredos")
    by_linha: dict[str, list] = {}
    for s in todos:
        by_linha.setdefault(s["linha"], []).append(s["nome"])
    for linha, nomes in by_linha.items():
        print(f"  {linha}: {len(nomes)}")
        for n in nomes:
            print(f"    - {n}")
    print(f"\n-> saved {out}")
