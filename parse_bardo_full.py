"""Parser do Bardo — extrai class features Nv 1-20 + 8 Colégios com features
Nv 3/6/14/18 (alguns têm features extras como Segundo Ataque Mágico nas
subclasses marciais).

Whitelist por nome (CLASS_FEATURE_NAMES) decide se H3 vai pra class ou
subclasse. Subclasse atribuída pelo H2 mais próximo antes do H3.

Tag especial:
  - "Dança em Cena" (Colégio da Dança, Nv 3) → ['pick:estilo-danca:N'] com
    n_por_nivel {3:1, 6:2, 14:3, 18:4} — Bardo da Dança escolhe 1 Estilo de Ki
    da classe Monge como Estilo de Dança a cada nível-chave.
"""
from __future__ import annotations
import json, re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/bardo.html")
OUT_META = Path("bardo_meta.json")
OUT_FEATS = Path("bardo_features.json")
OUT_SUBS = Path("bardo_subs.json")

SUBCLASS_CANON = [
    {"slug": "colegio-do-conselho",       "nome": "Colégio do Conselho",
     "tagline": "Mestre da retórica e da diplomacia armada com palavras-bisturi."},
    {"slug": "colegio-da-conspiracao",    "nome": "Colégio da Conspiração",
     "tagline": "Sussurros venenosos, mentes manipuladas, segredos como moeda."},
    {"slug": "colegio-da-criacao",        "nome": "Colégio da Criação",
     "tagline": "Canta o mundo em existência — invoca objetos e companheiros do nada."},
    {"slug": "colegio-da-danca",          "nome": "Colégio da Dança",
     "tagline": "Performance vira combate. Estilos de Ki monástico bebem Inspiração."},
    {"slug": "colegio-dos-espiritos",     "nome": "Colégio dos Espíritos",
     "tagline": "Conta histórias dos mortos e canaliza poderes ancestrais."},
    {"slug": "colegio-do-fascinio",       "nome": "Colégio do Fascínio",
     "tagline": "Encanto, glamour e ilusões que prendem corações e mentes."},
    {"slug": "colegio-das-laminas",       "nome": "Colégio das Lâminas",
     "tagline": "Florete e canção — o duelista cuja arma é palco e ameaça."},
    {"slug": "colegio-skald",             "nome": "Colégio Skald",
     "tagline": "Bardo de batalha do norte: runas, brados e hidromel sagrado."},
]

CLASS_FEATURE_NAMES = {
    "Inspiração Bárdica", "Conjuração de Magias",
    "Especialização", "Pau Pra Toda Obra",
    "Colégio de Bardo",                       # Nv 3 anchor (subclass)
    "Incremento de Atributo ou Talento",      # Nv 4 master (clone p/ 8/12/16/19)
    "Fonte de Inspiração",
    "Característica de Colégio",              # Nv 6/14/18 anchor (subclass)
    "Contra-Canto",
    "Especialização (Aprimorada)",
    "Segredos Mágicos",
    "Dado de Inspiração (d12)",
    "Inspiração Superior",
    "Palavras da Criação",
}

NAME_ALIASES = {
    "Aprimoramento de Atributo ou Talento": "Incremento de Atributo ou Talento",
}

ASI_NIVEIS = [4, 8, 12, 16, 19]

H2_SUBCLASS_NAMES = {s["nome"] for s in SUBCLASS_CANON}

# Mapping FEATURE_NAME → slug do Colégio. Aplicado para features Nv 6/14/18
# (que o doc agrupa todas dentro do H2 "Ações" e "Colégio Skald"). Reconstruído
# manualmente lendo cada descrição em paginas/bardo.html — referências ao
# Nv 3 feature anchor do colégio (Ex: "aprimora Foco Espiritual" → Espíritos,
# "Floreio de Lâmina" → Lâminas, etc).
FEATURE_TO_SUB = {
    # Nv 6
    "Descobertas Mágicas":          "colegio-do-conselho",
    "Língua Ancestral":             "colegio-da-criacao",
    "Golpe Sorrateiro":             "colegio-da-conspiracao",
    "Visagem Roubada":              "colegio-da-conspiracao",
    "Dança da Criação":             "colegio-da-criacao",
    "Inspiração em Movimento":      "colegio-da-danca",
    "Abertura de Palco":            "colegio-do-fascinio",
    "Estilo de Fuga":               "colegio-da-danca",
    "Sessão de Tarô":               "colegio-dos-espiritos",
    "Foco Espiritual Aprimorado":   "colegio-dos-espiritos",
    "Visagem de Outro Mundo":       "colegio-do-fascinio",
    "Encanto Reflexo":              "colegio-do-fascinio",
    "Segundo Ataque Mágico":        "colegio-das-laminas",
    "Segundo Ataque (Mágico)":      "colegio-skald",
    "Brado de Investida":           "colegio-skald",
    # Nv 14
    "Perícia Inigualável":          "colegio-do-conselho",
    "Manipulação Sinistra":         "colegio-da-conspiracao",
    "Crescendo Criativo":           "colegio-da-criacao",
    "Evasão Coreografada":          "colegio-da-danca",
    "Magia em Passo":               "colegio-da-danca",
    "Conexão Mística":              "colegio-dos-espiritos",
    "Manto de Proteção":            "colegio-do-fascinio",
    "Ritmo Infindável":             "colegio-das-laminas",
    "Runas no Aço":                 "colegio-skald",
    "Hidromel do Valor":            "colegio-skald",
    # Nv 18
    "Palavras Contagiantes":        "colegio-do-conselho",
    "Angústia Mental":              "colegio-da-conspiracao",
    "Canção Verdadeira":            "colegio-da-criacao",
    "Cortesia da Plateia":          "colegio-da-danca",
    "Arcano Maior":                 "colegio-dos-espiritos",
    "Presença Majestosa":           "colegio-do-fascinio",
    "Represália Letal":             "colegio-das-laminas",
    "Coro das Sagas":               "colegio-skald",
}

SCRAPER_END_MARKERS = [
    "Site projetado pela equipe",
    "Article template",
    "Metadados",
    "server_timing",
    "cfCacheStatus",
    "container do-not-print",
    "header-title",
]


def strip_html(s: str) -> str:
    # script/style
    s = re.sub(r'<script\b[^>]*>.*?</script>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<style\b[^>]*>.*?</style>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<[a-zA-Z/!][^>]*>', ' ', s)
    s = re.sub(r'<\s*[a-zA-Z][^<\s]*', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    earliest = len(s)
    for marker in SCRAPER_END_MARKERS:
        p = s.find(marker)
        if p >= 0 and p < earliest:
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


def find_current_subclass(real: str, h3_pos: int) -> str | None:
    matches = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', real[:h3_pos], re.S | re.I))
    for m in reversed(matches):
        label = strip_html(m.group(1))
        if label in H2_SUBCLASS_NAMES:
            return label
    return None


def main():
    raw = HTML_PATH.read_text(encoding='utf-8')
    real = get_text(raw)

    class_feats = []
    sub_feats_by_slug: dict[str, list[dict]] = {s["slug"]: [] for s in SUBCLASS_CANON}
    nome_to_slug = {s["nome"]: s["slug"] for s in SUBCLASS_CANON}

    seen_class = set()
    seen_sub = {s: set() for s in nome_to_slug.values()}

    h3_matches = list(re.finditer(r'<h3[^>]*>(.*?)</h3>', real, re.S | re.I))
    for i, m in enumerate(h3_matches):
        title = strip_html(m.group(1))
        if re.match(r'^\d+\s', title) or 'class=' in title or 'rolldice' in title:
            continue
        mlvl = re.match(r'N[íi]vel\s+(\d+):?\s*(.+)', title)
        if not mlvl:
            continue
        nivel = int(mlvl.group(1))
        nome = mlvl.group(2).strip()
        nome = NAME_ALIASES.get(nome, nome)

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
            # Prioridade 1: hardcoded mapping (features Nv 6/14/18 do "Ações")
            slug = FEATURE_TO_SUB.get(nome)
            if slug is None:
                # Prioridade 2: H2 mais próximo antes (funciona para Nv 3)
                sub_h2 = find_current_subclass(real, m.start())
                if sub_h2 is None:
                    continue
                slug = nome_to_slug[sub_h2]
            if nome in seen_sub[slug]:
                continue
            seen_sub[slug].add(nome)
            sub_feats_by_slug[slug].append({
                "nome": nome, "nivel": nivel, "descricao": descr
            })

    # ASI clones — Nv4 master existe? Se sim, clona para 8/12/16/19
    asi_master = next((f for f in class_feats if f["nome"] == "Incremento de Atributo ou Talento"), None)
    if asi_master:
        for nv in ASI_NIVEIS:
            if nv == asi_master["nivel"]:
                continue
            if not any(f["nome"] == asi_master["nome"] and f["nivel"] == nv for f in class_feats):
                class_feats.append({"nome": asi_master["nome"], "nivel": nv,
                                    "descricao": asi_master["descricao"]})

    class_feats.sort(key=lambda f: (f["nivel"], f["nome"]))

    META = {
        "slug": "bardo",
        "nome": "Bardo",
        "saves": ["Destreza", "Carisma"],
        "armor_prof": ["Armaduras Leves"],
        "weapon_prof": ["Armas Simples", "Bestas de Mão", "Espada Longa",
                        "Espada Curta", "Estoque", "Rapieira"],
        "tool_prof": ["3 Instrumentos Musicais à escolha"],
        "multiclass_prof": ["Armaduras Leves", "1 Instrumento Musical"],
        "skills": {
            "n": 3,
            "options": ["Atletismo", "Acrobacia", "Furtividade", "Prestidigitação",
                        "Arcanismo", "História", "Investigação", "Natureza",
                        "Religião", "Lidar com Animais", "Intuição", "Medicina",
                        "Percepção", "Sobrevivência", "Atuação", "Enganação",
                        "Intimidação", "Persuasão"],
        },
    }
    OUT_META.write_text(json.dumps(META, ensure_ascii=False, indent=2), encoding='utf-8')

    subs_out = []
    for s in SUBCLASS_CANON:
        subs_out.append({
            "slug": s["slug"],
            "nome": s["nome"],
            "tagline": s["tagline"],
            "features_sub": sub_feats_by_slug[s["slug"]],
        })
    OUT_SUBS.write_text(json.dumps(subs_out, ensure_ascii=False, indent=2), encoding='utf-8')

    OUT_FEATS.write_text(json.dumps(class_feats, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n=== Resumo ===")
    print(f"Class features ({len(class_feats)}):")
    for f in class_feats:
        print(f"  Nv{f['nivel']:>2} {f['nome']}")
    print(f"\nSubclass features por colégio:")
    for s in SUBCLASS_CANON:
        feats = sub_feats_by_slug[s["slug"]]
        print(f"  {s['slug']:<28} {len(feats)} features: "
              f"{[(f['nivel'], f['nome']) for f in feats]}")


if __name__ == "__main__":
    main()
