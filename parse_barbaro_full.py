"""Parser do Bárbaro — class features Nv 1-20 + 7 Caminhos (Nv 3/6/10/14/18).

Como Bardo: o doc agrupa todas as features Nv 4+ dentro do último H2
("Caminho da Feitiçaria Selvagem"), então usa-se FEATURE_TO_SUB hardcoded
(mapeado por tema de conteúdo) para distribuir nos 7 Caminhos.

ASI: doc usa "Aprimoramento de Atributo ou Talento" (Nv 4) e "Incremento de
Atributo ou Talento" (Nv 19) — normalizados para um nome único; master Nv 4
clonado para 8/12/16/19 (canônico Bárbaro 5.5e).
"""
from __future__ import annotations
import json, re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/barbaro.html")
OUT_META = Path("barbaro_meta.json")
OUT_FEATS = Path("barbaro_features.json")
OUT_SUBS = Path("barbaro_subs.json")

SUBCLASS_CANON = [
    {"slug": "caminho-do-arauto-runico",      "nome": "Caminho do Arauto Rúnico",
     "tagline": "Grava runas no corpo e na arma — fúria que queima em sigilos elementais."},
    {"slug": "caminho-do-coracao-selvagem",   "nome": "Caminho do Coração Selvagem",
     "tagline": "A fera interior desperta: instinto predatório, empatia animal, caçada."},
    {"slug": "caminho-do-guardiao-ancestral", "nome": "Caminho do Guardião Ancestral",
     "tagline": "Espíritos dos antepassados cercam e protegem quem você ama."},
    {"slug": "caminho-do-berserker",          "nome": "Caminho do Berserker",
     "tagline": "Fúria pura que atravessa dor — luta até além da queda."},
    {"slug": "caminho-do-zelote",             "nome": "Caminho do Zelote",
     "tagline": "Fé fanática como combustível: o voto encarna no corpo em chamas."},
    {"slug": "caminho-do-colosso-de-batalha", "nome": "Caminho do Colosso de Batalha",
     "tagline": "Armadura reforjada vira parte do corpo — investida de titã."},
    {"slug": "caminho-da-feiticaria-selvagem","nome": "Caminho da Feitiçaria Selvagem",
     "tagline": "A Fúria solta magia caótica — cada surto escolhe seu próprio rumo."},
]

CLASS_FEATURE_NAMES = {
    "Fúria", "Guerreiro Desprotegido", "Maestria em Armas",
    "Sentido de Perigo", "Ataque Imprudente",
    "Caminho do Bárbaro",                       # Nv 3 anchor (subclass)
    "Incremento de Atributo ou Talento",        # Nv 4 master → clone 8/12/16/19
    "Ataque Extra", "Conhecimento Primitivo",
    "Característica de Caminho",                # Nv 6/10/14/18 anchor (subclass)
    "Ímpeto Selvagem",
    "Fôlego Furioso",
    "Fúria Devastadora",
    "Instinto Brutal",
    "Ira Incontrolável",
    "Força Indomável",
    "Avatar da Fúria",
}

NAME_ALIASES = {
    "Aprimoramento de Atributo ou Talento": "Incremento de Atributo ou Talento",
}

ASI_NIVEIS = [4, 8, 12, 16, 19]

H2_SUBCLASS_NAMES = {s["nome"] for s in SUBCLASS_CANON}

# Mapping FEATURE_NAME → slug do Caminho. Reconstruído lendo cada descrição
# em paginas/barbaro.html (tema de conteúdo: runas→Arauto, fera→Coração,
# espíritos→Guardião, dor/fúria→Berserker, fé/voto→Zelote, armadura→Colosso,
# magia caótica→Feitiçaria).
FEATURE_TO_SUB = {
    # Nv 3
    "Runas Elementais":              "caminho-do-arauto-runico",
    "Despertar Bestial":             "caminho-do-coracao-selvagem",
    "Empatia Selvagem":              "caminho-do-coracao-selvagem",
    "Guardiões Ancestrais":          "caminho-do-guardiao-ancestral",
    "Selo do Fanatismo":             "caminho-do-zelote",
    "Armadura Reforjada":            "caminho-do-colosso-de-batalha",
    "Investida Colossal":            "caminho-do-colosso-de-batalha",
    "Faro Arcano":                   "caminho-da-feiticaria-selvagem",
    "Magia Selvagem":                "caminho-da-feiticaria-selvagem",
    # Nv 6
    "Essência Rúnica Entrelaçada":   "caminho-do-arauto-runico",
    "Armamento Rúnico Aprimorado":   "caminho-do-arauto-runico",
    "Habilidade Bestial":            "caminho-do-coracao-selvagem",
    "Escudo dos Antepassados":       "caminho-do-guardiao-ancestral",
    "Fúria Inconsciente":            "caminho-do-berserker",
    "Obsessão Inquebrável":          "caminho-do-zelote",
    "Colosso Armadurado":            "caminho-do-colosso-de-batalha",
    "Ruptura Arcana":                "caminho-da-feiticaria-selvagem",
    # Nv 10
    "Égide Primordial":              "caminho-do-arauto-runico",
    "Instinto Predatório":           "caminho-do-coracao-selvagem",
    "Instinto Ancestral":            "caminho-do-coracao-selvagem",
    "Consultar os Espíritos":        "caminho-do-guardiao-ancestral",
    "Eco Curativo":                  "caminho-do-guardiao-ancestral",
    "Presença Intimidante":          "caminho-do-berserker",
    "Grito de Cruzada":              "caminho-do-zelote",
    "Investida Colossal Aprimorada": "caminho-do-colosso-de-batalha",
    "Magia Instável":                "caminho-da-feiticaria-selvagem",
    # Nv 14
    "Despertar Rúnico":              "caminho-do-arauto-runico",
    "Chamado da Caçada":             "caminho-do-coracao-selvagem",
    "Espíritos Vingadores":          "caminho-do-guardiao-ancestral",
    "Sede de Sangue":                "caminho-do-berserker",
    "Forma do Guerreiro Sagrado":    "caminho-do-zelote",
    "Retribuição Anã":               "caminho-do-colosso-de-batalha",
    "Caos Encarnado":                "caminho-da-feiticaria-selvagem",
    # Nv 18
    "Campeão das Runas":             "caminho-do-arauto-runico",
    "Domínio da Fera Primordial":    "caminho-do-coracao-selvagem",
    "Legião dos Ancestrais":         "caminho-do-guardiao-ancestral",
    "Além da Queda":                 "caminho-do-berserker",
    "Retaliação":                    "caminho-do-zelote",
    "Avanço de Titã":                "caminho-do-colosso-de-batalha",
    "Golpe Dissipador":              "caminho-da-feiticaria-selvagem",
}

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
            slug = FEATURE_TO_SUB.get(nome)
            if slug is None:
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
        "slug": "barbaro",
        "nome": "Bárbaro",
        "saves": ["Forca", "Constituicao"],
        "armor_prof": ["Armaduras Leves", "Armaduras Médias", "Escudos"],
        "weapon_prof": ["Armas Simples", "Armas Marciais"],
        "tool_prof": [],
        "multiclass_prof": ["Escudos", "Armas Simples", "Armas Marciais"],
        "skills": {
            "n": 2,
            "options": ["Atletismo", "Intimidação", "Natureza", "Percepção",
                        "Sobrevivência", "Lidar com Animais"],
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
    print(f"\nSubclass features por caminho:")
    for s in SUBCLASS_CANON:
        feats = sub_feats_by_slug[s["slug"]]
        print(f"  {s['slug']:<32} {len(feats)}: "
              f"{[(f['nivel'], f['nome']) for f in feats]}")


if __name__ == "__main__":
    main()
