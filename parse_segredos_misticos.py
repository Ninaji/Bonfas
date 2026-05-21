"""Extrai todos os Segredos Místicos do mistico.extracted.html.
Estrutura: H4 'Seção' + <table.table-striped> com <tr><td><b>Nome</b></td><td>Desc</td></tr>."""
import json, re, sys
from html import unescape
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def slugify(s: str) -> str:
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    out = s.lower()
    for k, v in repl.items(): out = out.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")


def cleantext(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s); s = unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse():
    html = Path(r"E:\Obsidian\_raw\mistico.extracted.html").read_text(encoding="utf-8")
    chunk = html[80379:95734]  # bloco Segredos Místicos

    # Itera H4s e captura tabelas dentro
    h4_re = re.compile(r"<h4[^>]*>(.*?)</h4>", re.IGNORECASE | re.DOTALL)
    tab_re = re.compile(r"<table[^>]*>([\s\S]*?)</table>", re.IGNORECASE)
    row_re = re.compile(r"<tr[^>]*>\s*<td[^>]*>\s*<b>(.*?)</b>\s*</td>\s*<td[^>]*>(.*?)</td>\s*</tr>",
                        re.IGNORECASE | re.DOTALL)

    matches = list(h4_re.finditer(chunk))
    out = []
    for i, m in enumerate(matches):
        secao = cleantext(m.group(1))
        bs = m.end()
        be = matches[i + 1].start() if i + 1 < len(matches) else len(chunk)
        body = chunk[bs:be]
        tbl = tab_re.search(body)
        if not tbl:
            continue
        for r in row_re.finditer(tbl.group(1)):
            nome = cleantext(r.group(1))
            desc = cleantext(r.group(2))
            if not nome:
                continue
            out.append({
                "secao": secao,
                "nome": nome,
                "slug": slugify(nome),
                "descricao": desc[:1500],
            })
    return out


if __name__ == "__main__":
    segs = parse()
    Path("mistico_segredos.json").write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")
    by_secao: dict[str, list] = {}
    for s in segs:
        by_secao.setdefault(s["secao"], []).append(s["nome"])
    print(f"Total: {len(segs)} segredos místicos\n")
    for sec, nomes in by_secao.items():
        print(f"  {sec} ({len(nomes)}):")
        for n in nomes:
            print(f"    - {n}")
        print()
