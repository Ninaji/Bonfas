"""Parser do Druida — extrai class features Nv 1-20 + 7 subclasses (Círculos)
com features Nv 3/6/10/14/18.

Estrutura HTML:
  H2 "Habilidades de Classe" → features de classe (todos os H3 "Nível N: X")
  H2 "Círculo dos Esporos" / "...Estrelas" / etc → features de subclasse
  Ações, STR/DEX/CON... → stat blocks, ignorar

Subclasses (7):
  - Círculo dos Esporos, das Estrelas, da Lua, das Marés, do Pastor Elemental,
    dos Sonhos, da Terra

ND Máximo de Forma Selvagem (Surto Selvagem):
  - Druida padrão: Nv2=1/4, Nv4=1/2, Nv8=1 (até nv20)
  - Druida da Lua: ⌈nivel/3⌉ — texto da feature "Formas Lunares"
"""
from __future__ import annotations
import json, re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/druida.html")
OUT_META = Path("druida_meta.json")
OUT_FEATS = Path("druida_features.json")
OUT_SUBS = Path("druida_subs.json")

SUBCLASS_CANON = [
    {"slug": "circulo-dos-esporos",         "nome": "Círculo dos Esporos",
     "tagline": "Mestre da decomposição e renascimento. Comanda esporos que dominam ou apodrecem inimigos."},
    {"slug": "circulo-das-estrelas",        "nome": "Círculo das Estrelas",
     "tagline": "Lê as constelações para canalizar formas estelares de luta, cura ou conhecimento."},
    {"slug": "circulo-da-lua",              "nome": "Círculo da Lua",
     "tagline": "A Forma Selvagem é o coração. Bestas mais poderosas, mais resistentes, sob qualquer fase lunar."},
    {"slug": "circulo-das-mares",           "nome": "Círculo das Marés",
     "tagline": "Domina o fluxo das águas — caça em ondas, drena vida, controla o sal do oceano."},
    {"slug": "circulo-do-pastor-elemental", "nome": "Círculo do Pastor Elemental",
     "tagline": "Comanda um Familiar Primal elemental que evolui ao seu lado."},
    {"slug": "circulo-dos-sonhos",          "nome": "Círculo dos Sonhos",
     "tagline": "Caminha entre o véu do mundo onírico — telepatia, refúgios sutis, mensageiros."},
    {"slug": "circulo-da-terra",            "nome": "Círculo da Terra",
     "tagline": "O elo ancestral com o terreno. Regenera, prepara magias de bioma, conjura como mago."},
]

# === CLASS FEATURE NAMES (1-20) ===
# Nomes canônicos. Normaliza "Aprimoramento de Atributo ou Talento" ←→
# "Incremento de Atributo ou Talento" (doc usa ambos) para o nome
# consistente "Aprimoramento de Atributo ou Talento" (5.5e oficial).
CLASS_FEATURE_NAMES = {
    "Conjuração Druídica", "Vínculo Natural",
    "Ordem Primal", "Surto Selvagem",
    "Círculo Druídico",                         # Nv3 anchor (subclass)
    "Aprimoramento de Atributo ou Talento",     # Nv4 master (clone 8/12/16/19)
    "Intuição Selvagem",
    "Característica de Círculo",                # Nv6/10/18 anchor (subclass)
    "Fúria Elemental",
    "Guardião da Terra",
    "Alma da Natureza",
    "Arquidruida",
}

# Nomes alternativos do doc → nome canônico
NAME_ALIASES = {
    "Incremento de Atributo ou Talento": "Aprimoramento de Atributo ou Talento",
}

# ASI master at Nv4 — clones at 8/12/16/19 (canônico 5.5e)
ASI_NIVEIS = [4, 8, 12, 16, 19]

# H2 names that are class features bucket OR subclass bucket
H2_CLASS_BUCKET = "Habilidades de Classe"
H2_SUBCLASS_NAMES = {s["nome"] for s in SUBCLASS_CANON}

# H2 que devem ser ignoradas (stat blocks, ações, etc.)
H2_SKIP_PREFIXES = ("class=", "Ações", "STR", "DEX", "CON", "INT", "WIS", "CHA")


SCRAPER_END_MARKERS = [
    "Site projetado pela equipe",
    "Article template",
    "Metadados",
    "server_timing",
    "cfCacheStatus",
    "container do-not-print",
    "header-title",
    "rolldice",
]


def strip_html(s: str) -> str:
    """Strip HTML tags + scraper artifacts. Trunca em qualquer marker conhecido
    de fim-de-conteúdo (rodapé WorldAnvil, scripts Cloudflare, etc.)."""
    # 1a. Remove SCRIPT/STYLE blocks com conteúdo
    s = re.sub(r'<script\b[^>]*>.*?</script>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<style\b[^>]*>.*?</style>', ' ', s, flags=re.I | re.S)
    # 1b. Estratégia 2-passes: primeiro tags bem formadas, depois fragmentos.
    # Tags bem formadas: <X...>
    s = re.sub(r'<[a-zA-Z/!][^>]*>', ' ', s)
    # 1c. Fragmentos órfãos: `<span` sem `>` no final, etc.
    # Remove `<<word>` até próximo espaço/`<` ou fim — pega `<span` solto.
    s = re.sub(r'<\s*[a-zA-Z][^<\s]*', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # 2. Trunca no primeiro marker de scraper junk
    earliest = len(s)
    for marker in SCRAPER_END_MARKERS:
        p = s.find(marker)
        if p >= 0 and p < earliest:
            earliest = p
    s = s[:earliest].strip()
    # 3. Tira fragmentos de atributos órfãos tipo `class =" ... ">` que
    # sobraram de tags com `>` aninhado em valores de atributo
    s = re.sub(r'\bclass\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\bstyle\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\bdata-[a-z-]+\s*=\s*"[^"]*"\s*>?', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def get_text(html: str) -> str:
    """unescape duas vezes (view-source duplo-escapa)"""
    return unescape(unescape(html))


def parse_h2_sections(real: str) -> list[tuple[str, str]]:
    """Retorna [(h2_label, body_html), ...]. Body é o texto entre este H2 e o próximo."""
    matches = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', real, re.S | re.I))
    sections = []
    for i, m in enumerate(matches):
        label = strip_html(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(real)
        body = real[start:end]
        sections.append((label, body))
    return sections


def parse_h3_blocks(body: str) -> list[tuple[str, int | None, str]]:
    """Retorna [(nome_canonico, nivel, descricao), ...] para cada H3 no body."""
    out = []
    matches = list(re.finditer(r'<h3[^>]*>(.*?)</h3>', body, re.S | re.I))
    for i, m in enumerate(matches):
        title = strip_html(m.group(1))
        # Pula H3s de stat block (números puros, "class=" leak, etc.)
        if re.match(r'^\d+\s', title) or 'class=' in title:
            continue
        # Match "Nível N: Nome" ou "Nível N: Nome, Outra"
        mlvl = re.match(r'N[íi]vel\s+(\d+):?\s*(.+)', title)
        if mlvl:
            nivel = int(mlvl.group(1))
            nome = mlvl.group(2).strip()
        else:
            nivel = None
            nome = title.strip()
        # body do H3 = até o próximo H3 OU até H2/H4 maior
        start = m.end()
        next_h3 = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        next_h2 = re.search(r'<h2[^>]*>', body[start:next_h3])
        end = start + (next_h2.start() if next_h2 else next_h3 - start)
        descr_html = body[start:end]
        descr = strip_html(descr_html)
        # canonicaliza nome
        nome = NAME_ALIASES.get(nome, nome)
        out.append((nome, nivel, descr))
    return out


def find_current_subclass(real: str, h3_pos: int) -> str | None:
    """Para H3 em h3_pos, encontra o H2 mais próximo ANTES que seja uma subclasse."""
    # Encontra todos os H2 antes da posição
    matches = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', real[:h3_pos], re.S | re.I))
    for m in reversed(matches):
        label = strip_html(m.group(1))
        if label in H2_SUBCLASS_NAMES:
            return label
    return None


def main():
    raw = HTML_PATH.read_text(encoding='utf-8')
    real = get_text(raw)

    class_feats = []                # [{nome, nivel, descricao}]
    sub_feats_by_slug: dict[str, list[dict]] = {s["slug"]: [] for s in SUBCLASS_CANON}
    nome_to_slug = {s["nome"]: s["slug"] for s in SUBCLASS_CANON}

    seen_class = set()
    seen_sub = {s: set() for s in nome_to_slug.values()}

    # Itera por TODOS H3 do doc inteiro, com pos absoluta para descobrir o H2-pai
    h3_matches = list(re.finditer(r'<h3[^>]*>(.*?)</h3>', real, re.S | re.I))
    for i, m in enumerate(h3_matches):
        title = strip_html(m.group(1))
        # Skip stat blocks / dice / classes etc
        if re.match(r'^\d+\s', title) or 'class=' in title or 'rolldice' in title:
            continue
        mlvl = re.match(r'N[íi]vel\s+(\d+):?\s*(.+)', title)
        if not mlvl:
            continue
        nivel = int(mlvl.group(1))
        nome = mlvl.group(2).strip()
        nome = NAME_ALIASES.get(nome, nome)

        # descrição = body entre este H3 e o próximo H3 (ou próximo H2)
        start = m.end()
        next_h3 = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(real)
        next_h2 = re.search(r'<h2[^>]*>', real[start:next_h3])
        end = start + (next_h2.start() if next_h2 else next_h3 - start)
        descr = strip_html(real[start:end])

        # Whitelist por nome
        if nome in CLASS_FEATURE_NAMES:
            key = (nome, nivel)
            if key in seen_class:
                continue
            seen_class.add(key)
            class_feats.append({"nome": nome, "nivel": nivel, "descricao": descr})
        else:
            # subclasse — usa o H2 mais próximo antes do H3
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
    asi_master = next((f for f in class_feats if f["nome"] == "Aprimoramento de Atributo ou Talento"), None)
    if asi_master:
        for nv in ASI_NIVEIS:
            if nv == asi_master["nivel"]:
                continue
            if not any(f["nome"] == asi_master["nome"] and f["nivel"] == nv for f in class_feats):
                class_feats.append({"nome": asi_master["nome"], "nivel": nv,
                                    "descricao": asi_master["descricao"]})

    class_feats.sort(key=lambda f: (f["nivel"], f["nome"]))

    # === META ===
    META = {
        "slug": "druida",
        "nome": "Druida",
        "saves": ["Inteligencia", "Sabedoria"],
        "armor_prof": ["Armaduras Leves", "Armaduras Médias", "Escudos (não-metálicos)"],
        "weapon_prof": ["Armas Simples"],
        "tool_prof": ["Kit de Herbalismo"],
        "multiclass_prof": ["Armaduras Leves", "Armaduras Médias", "Escudos (não-metálicos)"],
        "skills": {
            "n": 2,
            "options": ["Arcanismo", "Intuição", "Medicina", "Natureza",
                        "Percepção", "Religião", "Sobrevivência", "Lidar com Animais"],
        },
    }
    OUT_META.write_text(json.dumps(META, ensure_ascii=False, indent=2), encoding='utf-8')

    # === SUBS ===
    subs_out = []
    for s in SUBCLASS_CANON:
        subs_out.append({
            "slug": s["slug"],
            "nome": s["nome"],
            "tagline": s["tagline"],
            "features_sub": sub_feats_by_slug[s["slug"]],
        })
    OUT_SUBS.write_text(json.dumps(subs_out, ensure_ascii=False, indent=2), encoding='utf-8')

    # === FEATS ===
    OUT_FEATS.write_text(json.dumps(class_feats, ensure_ascii=False, indent=2), encoding='utf-8')

    # Resumo
    print(f"\n=== Resumo ===")
    print(f"Class features ({len(class_feats)}):")
    for f in class_feats:
        print(f"  Nv{f['nivel']:>2} {f['nome']}")
    print(f"\nSubclass features por círculo:")
    for s in SUBCLASS_CANON:
        feats = sub_feats_by_slug[s["slug"]]
        print(f"  {s['slug']:<32} {len(feats)} features: "
              f"{[(f['nivel'], f['nome']) for f in feats]}")


if __name__ == "__main__":
    main()
