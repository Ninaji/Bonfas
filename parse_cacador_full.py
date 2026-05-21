"""Parser v2: extrai TODAS as H3 'Nível N: Nome' + descrição do caçador.extracted.html.

Saída: cacador_full.json com lista plana { nivel, nome, descricao, offset_inicio, offset_fim }.
O mapeamento (qual sub recebe cada feature) é explícito na migration, não no parser.

Trata corpo e descrição: pega o texto desde o H3 até o próximo H3/H2/H1, normalizando entidades.
"""
import json
import re
from html import unescape
from pathlib import Path


def text_clean(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def parse(html_path: Path) -> list[dict]:
    html = html_path.read_text(encoding="utf-8")
    h3_re = re.compile(r"<h3[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
    stop_re = re.compile(r"<h[123][^>]*>", re.IGNORECASE)

    out = []
    matches = list(h3_re.finditer(html))
    for i, m in enumerate(matches):
        title_raw = text_clean(m.group(1))
        nv_match = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", title_raw)
        if not nv_match:
            continue
        nivel = int(nv_match.group(1))
        nome = nv_match.group(2).strip()

        # Pegar conteúdo até o próximo H1/H2/H3
        body_start = m.end()
        next_match = stop_re.search(html, body_start)
        body_end = next_match.start() if next_match else len(html)
        body = text_clean(html[body_start:body_end])

        # Cortar body em até 1500 chars pra não estourar TEXT
        if len(body) > 1500:
            body = body[:1497] + "..."

        out.append({
            "nivel": nivel,
            "nome": nome,
            "descricao": body,
            "offset_inicio": m.start(),
            "offset_fim": body_end,
        })
    return out


if __name__ == "__main__":
    src = Path(r"E:\Obsidian\_raw\caçador.extracted.html")
    feats = parse(src)
    out = Path("cacador_full.json")
    out.write_text(json.dumps(feats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Total features (H3 'Nível X'): {len(feats)}")
    by_nivel: dict[int, list[str]] = {}
    for f in feats:
        by_nivel.setdefault(f["nivel"], []).append(f["nome"])
    for nv in sorted(by_nivel):
        print(f"  Nv{nv:>2}: {by_nivel[nv]}")
    print(f"\n-> saved {out}")
