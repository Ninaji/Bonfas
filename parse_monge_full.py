"""Parser do Monge — extrai todas H3 'Nível N: Nome' + descrição.
Espelha parse_cacador_full.py mas pro monge.extracted.html."""
import json, re
from html import unescape
from pathlib import Path


def text_clean(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def parse(html_path: Path) -> tuple[list[dict], list[dict]]:
    """Retorna (subs, features).
    subs: [{nome, slug, tagline, offset_start, offset_end, sub_features_n3}]
    features: [{nivel, nome, descricao, offset_inicio, offset_fim}]
    """
    html = html_path.read_text(encoding="utf-8")

    # 1) H2 que são subclasses (entre H1 'Monge' e fim das tradições, antes do H3 Nv 4)
    h2_re = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
    h2_matches = list(h2_re.finditer(html))
    # Sublistas: Características de Classe / Habilidades de Monge / Estilos de Ki / Estilos Kensei são "section"
    excluded = {"características de classe", "habilidades de monge", "estilos de ki", "estilos kensei"}
    subs = []
    for i, m in enumerate(h2_matches):
        name = text_clean(m.group(1))
        if not name or name.lower() in excluded:
            continue
        # Parar antes do bloco Nv 4+ (Find your way! ou similar). Os H2 das subs vêm em sequência.
        end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(html)
        subs.append({"nome": name, "slug": slugify(name), "offset_start": m.start(), "offset_end": end})
    # Filtra: apenas subs antes do Nv 4 global. O 1º H3 'Nível 4' marca o fim das subs.
    nv4_match = re.search(r"<h3[^>]*>\s*N[íi]vel\s+4\s*:", html, re.IGNORECASE)
    nv4_off = nv4_match.start() if nv4_match else len(html)
    subs = [s for s in subs if s["offset_start"] < nv4_off]
    # Ajusta offset_end da última sub: até nv4
    if subs:
        subs[-1]["offset_end"] = min(subs[-1]["offset_end"], nv4_off)

    # 2) Todas as H3 'Nível N: <nome>' com descrições
    h3_re = re.compile(r"<h3[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
    stop_re = re.compile(r"<h[1234][^>]*>", re.IGNORECASE)
    features = []
    h3_matches = list(h3_re.finditer(html))
    for m in h3_matches:
        title_raw = text_clean(m.group(1))
        nv_match = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", title_raw)
        if not nv_match:
            continue
        nivel = int(nv_match.group(1))
        nome = nv_match.group(2).strip()
        body_start = m.end()
        next_match = stop_re.search(html, body_start)
        body_end = next_match.start() if next_match else len(html)
        body = text_clean(html[body_start:body_end])
        if len(body) > 1500:
            body = body[:1497] + "..."
        features.append({
            "nivel": nivel, "nome": nome, "descricao": body,
            "offset_inicio": m.start(), "offset_fim": body_end,
        })

    # 3) Para cada sub: pegar features cujo offset cai dentro dela = features Nv 3 da sub
    for sub in subs:
        sub["features_sub"] = [
            f for f in features
            if sub["offset_start"] <= f["offset_inicio"] < sub["offset_end"]
        ]
        # tagline curta = primeiro parágrafo após H2 sub, antes do 1º H3
        first_feat_off = min((f["offset_inicio"] for f in sub["features_sub"]), default=sub["offset_end"])
        tagline_html = html[sub["offset_start"]:first_feat_off]
        # Remove o próprio H2 título
        tagline_html = re.sub(r"<h2[^>]*>.*?</h2>", "", tagline_html, count=1, flags=re.IGNORECASE | re.DOTALL)
        sub["tagline"] = text_clean(tagline_html)[:250]

    return subs, features


def slugify(s: str) -> str:
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    out = s.lower()
    for k, v in repl.items(): out = out.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")


if __name__ == "__main__":
    subs, feats = parse(Path(r"E:\Obsidian\_raw\monge.extracted.html"))
    Path("monge_subs.json").write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("monge_features.json").write_text(json.dumps(feats, ensure_ascii=False, indent=2), encoding="utf-8")
    import sys; sys.stdout.reconfigure(encoding='utf-8')
    print(f"=== {len(subs)} subclasses ===")
    for s in subs:
        print(f"  {s['nome']:<20} ({s['slug']}) — {len(s['features_sub'])} feats Nv3")
    print(f"\n=== {len(feats)} features (todas as 'Nível N:' do arquivo) ===")
    by_nivel = {}
    for f in feats: by_nivel.setdefault(f["nivel"], []).append(f["nome"])
    for nv in sorted(by_nivel):
        print(f"  Nv{nv:>2}: {len(by_nivel[nv])} features")
