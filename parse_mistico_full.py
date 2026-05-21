"""Parser do Místico — extrai todas H3 'Nível N: Nome' + descrições + lista de Patronos (H2)."""
import json, re
from html import unescape
from pathlib import Path


def text_clean(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html); txt = unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def slugify(s: str) -> str:
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    out = s.lower()
    for k, v in repl.items(): out = out.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")


def parse(html_path: Path) -> tuple[list[dict], list[dict]]:
    html = html_path.read_text(encoding="utf-8")

    # Subclasses (Patronos): H2 entre o 1º Nv 4+ e descobre cada um
    h2_re = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
    excluded = {
        "características de classe", "lista de magias expandidas",
        "segredos místicos", "ações", "str","dex","con","int","wis","cha",
    }
    subs = []
    h2_matches = list(h2_re.finditer(html))
    for i, m in enumerate(h2_matches):
        nome = text_clean(m.group(1))
        if not nome or nome.lower() in excluded:
            continue
        end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(html)
        subs.append({"nome": nome, "slug": slugify(nome), "offset_start": m.start(), "offset_end": end})

    # Filtra: subs só após o 1º "Nível 3: Patrono Transcendental" (H4 marker da seção subs)
    h4_pat = re.search(r"<h4[^>]*>\s*N[íi]vel\s+3:\s*Patrono\s+Transcendental", html, re.IGNORECASE)
    if h4_pat:
        subs = [s for s in subs if s["offset_start"] > h4_pat.start()]
    # Filtra: nada antes do bloco "Nível 4:" (que marca fim das subs)
    nv4_match = re.search(r"<h3[^>]*>\s*N[íi]vel\s+4\s*:", html, re.IGNORECASE)
    nv4_off = nv4_match.start() if nv4_match else len(html)
    subs = [s for s in subs if s["offset_start"] < nv4_off]
    if subs:
        subs[-1]["offset_end"] = min(subs[-1]["offset_end"], nv4_off)

    # H3 + H4 que tem 'Nível N:' — body até próximo H1/H2/H3/H4
    h_re = re.compile(r"<h([34])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
    stop_re = re.compile(r"<h[1234][^>]*>", re.IGNORECASE)
    features = []
    for m in h_re.finditer(html):
        title = text_clean(m.group(2))
        nv = re.match(r"N[íi]vel\s+(\d+)\s*:?\s*[—\-]?\s*(.+)", title)
        if not nv:
            continue
        nivel = int(nv.group(1))
        nome = nv.group(2).strip()
        bs = m.end()
        nm = stop_re.search(html, bs)
        be = nm.start() if nm else len(html)
        body = text_clean(html[bs:be])
        if len(body) > 1500: body = body[:1497] + "..."
        features.append({
            "nivel": nivel, "nome": nome, "descricao": body,
            "offset_inicio": m.start(), "offset_fim": be,
        })

    # Atribui features a cada sub
    for sub in subs:
        sub["features_sub"] = [
            f for f in features
            if sub["offset_start"] <= f["offset_inicio"] < sub["offset_end"]
        ]
        first_feat_off = min((f["offset_inicio"] for f in sub["features_sub"]), default=sub["offset_end"])
        tagline_html = html[sub["offset_start"]:first_feat_off]
        tagline_html = re.sub(r"<h2[^>]*>.*?</h2>", "", tagline_html, count=1, flags=re.IGNORECASE | re.DOTALL)
        sub["tagline"] = text_clean(tagline_html)[:250]

    return subs, features


if __name__ == "__main__":
    import sys; sys.stdout.reconfigure(encoding="utf-8")
    subs, feats = parse(Path(r"E:\Obsidian\_raw\mistico.extracted.html"))
    Path("mistico_subs.json").write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("mistico_features.json").write_text(json.dumps(feats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== {len(subs)} subclasses (Patronos) ===")
    for s in subs:
        print(f"  {s['nome']:<22} ({s['slug']}) — {len(s['features_sub'])} feats")
    print(f"\n=== {len(feats)} features ===")
    by_nv = {}
    for f in feats: by_nv.setdefault(f["nivel"], []).append(f["nome"])
    for nv in sorted(by_nv):
        print(f"  Nv{nv:>2}: {len(by_nv[nv])} -> {by_nv[nv]}")
