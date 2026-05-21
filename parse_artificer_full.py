"""Parser do Artífice — class features Nv 1-20 + 6 subclasses (Nv 3/5/10/15).

Como Bardo/Bárbaro, o doc agrupa features de classe pooled na última H2
(Magiduelista/Infusões de Varinha). Usa-se CLASS_FEATURE_NAMES (whitelist)
para puxar as features de classe, e H2-pai para as de subclasse.

Folding de sub-seções:
  - "Infusões de Elixir"  → Alquimista
  - "Infusões de Varinha" → Magiduelista

NÃO inclui as 4 features-catálogo "Infusões de Xº Nível" (são o picker agora).
A tag pick:infusao-artificer e os asi-feature são re-aplicados na migração.
"""
from __future__ import annotations
import json, re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/artificer.html")
OUT_META = Path("artificer_meta.json")
OUT_FEATS = Path("artificer_features.json")
OUT_SUBS = Path("artificer_subs.json")

SUBCLASS_CANON = [
    {"slug": "alquimista",              "nome": "Alquimista",
     "tagline": "Elixires alquímicos e poções potentes — química arcana embotelhada."},
    {"slug": "armadurista",             "nome": "Armadurista",
     "tagline": "Veste uma armadura arcana modular: infiltrador ou colosso de guerra."},
    {"slug": "aprimorado",              "nome": "Aprimorado",
     "tagline": "Físico modular com armas integradas — o próprio corpo é a engenhoca."},
    {"slug": "engenheiro-de-construto", "nome": "Engenheiro de Construto",
     "tagline": "Comanda um Defensor de Aço que protege e repara o grupo."},
    {"slug": "ferreiro-de-batalha",     "nome": "Ferreiro de Batalha",
     "tagline": "Forja arcana na vanguarda: duplica infusões e desfere choque arcano."},
    {"slug": "magiduelista",            "nome": "Magiduelista",
     "tagline": "Arma arcana e raio arcano — duelista que canaliza varinha em combate."},
]

# Sub-seções que pertencem a uma subclasse-mãe
H2_FOLD = {
    "Infusões de Elixir":  "Alquimista",
    "Infusões de Varinha": "Magiduelista",
}

CLASS_FEATURE_NAMES = {
    "Conjuração de Magias", "Engenhoca Mágica",
    "Infusões", "Replicar Item Mágico",
    "Percepção do Artífice", "Recarga Arcana",
    "Especialização",                       # Nv 3/10/15 (Tool Expertise)
    "Aumento de Atributo",                  # Nv 4 master → clone 8/12/16/19
    "Lampejo de Gênio",
    "Artesão Exímio",
    "Maestria em Itens Mágicos",
    "Magnum Opus",
}

# 4 features-catálogo (scraper artifact) — NÃO reinserir (agora são o picker)
SKIP_FEATURE_NAMES = {
    "Infusões de 1º Nível", "Infusões de 5º Nível",
    "Infusões de 11º Nível", "Infusões de 17º Nível",
}

NAME_ALIASES = {
    "Incremento de Atributo ou Talento": "Aumento de Atributo",
    "Aprimoramento de Atributo ou Talento": "Aumento de Atributo",
}

ASI_NIVEIS = [4, 8, 12, 16, 19]

H2_SUBCLASS_NAMES = {s["nome"] for s in SUBCLASS_CANON} | set(H2_FOLD.keys())

SCRAPER_END_MARKERS = [
    "Site projetado pela equipe", "Article template", "Metadados",
    "server_timing", "cfCacheStatus", "container do-not-print", "header-title",
]


def strip_html(s: str) -> str:
    s = re.sub(r'<script\b[^>]*>.*?</script>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<style\b[^>]*>.*?</style>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<[a-zA-Z/!][^>]*>', ' ', s)
    s = re.sub(r'<\s*[a-zA-Z][^<\s]*', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    earliest = len(s)
    for marker in SCRAPER_END_MARKERS:
        p = s.find(marker)
        if 0 <= p < earliest:
            earliest = p
    s = s[:earliest].strip()
    s = re.sub(r'\bclass\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\bstyle\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\bdata-[a-z-]+\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\bhref\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def get_text(html: str) -> str:
    return unescape(unescape(html))


def parent_sub(real: str, h3_pos: int, nome_to_canonsub: dict) -> str | None:
    matches = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', real[:h3_pos], re.S | re.I))
    for m in reversed(matches):
        label = strip_html(m.group(1))
        if label in nome_to_canonsub:
            return nome_to_canonsub[label]   # nome canônico (após fold)
    return None


def main():
    raw = HTML_PATH.read_text(encoding='utf-8')
    real = get_text(raw)

    # mapeia H2-label → nome canônico de subclasse (aplicando fold)
    nome_to_canonsub = {s["nome"]: s["nome"] for s in SUBCLASS_CANON}
    nome_to_canonsub.update(H2_FOLD)
    canon_to_slug = {s["nome"]: s["slug"] for s in SUBCLASS_CANON}

    class_feats = []
    sub_feats_by_slug: dict[str, list[dict]] = {s["slug"]: [] for s in SUBCLASS_CANON}
    seen_class = set()
    seen_sub = {s["slug"]: set() for s in SUBCLASS_CANON}

    h3_matches = list(re.finditer(r'<h3[^>]*>(.*?)</h3>', real, re.S | re.I))
    for i, m in enumerate(h3_matches):
        title = strip_html(m.group(1))
        if re.match(r'^\d+\s', title) or 'class=' in title or 'rolldice' in title:
            continue
        mlvl = re.match(r'N[íi]vel\s+(\d+):?\s*(.+)', title)
        if not mlvl:
            continue
        nivel = int(mlvl.group(1))
        nome = NAME_ALIASES.get(mlvl.group(2).strip(), mlvl.group(2).strip())
        if nome in SKIP_FEATURE_NAMES:
            continue

        start = m.end()
        next_h3 = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(real)
        next_h2 = re.search(r'<h2[^>]*>', real[start:next_h3])
        end = start + (next_h2.start() if next_h2 else next_h3 - start)
        descr = strip_html(real[start:end])

        if nome in CLASS_FEATURE_NAMES:
            key = (nome, nivel)
            if key in seen_class:
                continue
            seen_class.add(key)
            class_feats.append({"nome": nome, "nivel": nivel, "descricao": descr})
        else:
            canon = parent_sub(real, m.start(), nome_to_canonsub)
            if canon is None:
                continue
            slug = canon_to_slug[canon]
            if (nome, nivel) in seen_sub[slug]:
                continue
            seen_sub[slug].add((nome, nivel))
            sub_feats_by_slug[slug].append({"nome": nome, "nivel": nivel, "descricao": descr})

    # ASI clones (Nv 4 master → 8/12/16/19)
    asi_master = next((f for f in class_feats if f["nome"] == "Aumento de Atributo"), None)
    if asi_master:
        for nv in ASI_NIVEIS:
            if nv == asi_master["nivel"]:
                continue
            if not any(f["nome"] == "Aumento de Atributo" and f["nivel"] == nv for f in class_feats):
                class_feats.append({"nome": "Aumento de Atributo", "nivel": nv,
                                    "descricao": asi_master["descricao"]})
    class_feats.sort(key=lambda f: (f["nivel"], f["nome"]))

    META = {
        "slug": "artifice",
        "nome": "Artífice",
        "saves": ["Constituicao", "Inteligencia"],
        "armor_prof": ["Armaduras Leves", "Armaduras Médias", "Escudos"],
        "weapon_prof": ["Armas Simples"],
        "tool_prof": ["Ferramentas de Ladrão", "Ferramentas de Funileiro",
                      "1 Ferramenta de Artesão à escolha"],
        "multiclass_prof": ["Armaduras Leves", "Armaduras Médias", "Escudos",
                            "Ferramentas de Ladrão"],
        "skills": {
            "n": 2,
            "options": ["Arcanismo", "História", "Investigação", "Medicina",
                        "Natureza", "Percepção", "Prestidigitação"],
        },
    }
    OUT_META.write_text(json.dumps(META, ensure_ascii=False, indent=2), encoding='utf-8')

    subs_out = [{"slug": s["slug"], "nome": s["nome"], "tagline": s["tagline"],
                 "features_sub": sub_feats_by_slug[s["slug"]]} for s in SUBCLASS_CANON]
    OUT_SUBS.write_text(json.dumps(subs_out, ensure_ascii=False, indent=2), encoding='utf-8')
    OUT_FEATS.write_text(json.dumps(class_feats, ensure_ascii=False, indent=2), encoding='utf-8')

    print("=== Class features ===")
    for f in class_feats:
        print(f"  Nv{f['nivel']:>2} {f['nome']}")
    print("\n=== Subclasses ===")
    for s in SUBCLASS_CANON:
        feats = sub_feats_by_slug[s["slug"]]
        print(f"  {s['slug']:<26} {len(feats)}: {[(f['nivel'], f['nome']) for f in feats]}")


if __name__ == "__main__":
    main()
