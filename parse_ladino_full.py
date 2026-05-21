"""Parser do Ladino — extrai proficiências, 8 subclasses (Trilhas), class features
Nv 1-20, e subclass features Nv 3/6/9/13/17.

Estratégia (mesma do Mago):
  - H3 "Nível N: <Nome>" são features. Whitelist define class vs subclass.
  - Subclass features atribuídas por ordem-no-batch contra SUBCLASS_FEATURE_COUNTS.
  - ASI clones (Aprimoramento de Habilidade) Nv 4 → 8, 10, 12, 16, 19 (6 ASIs total,
    Ladino tem ASI extra Nv 10 vs. classes padrão).

Uso: python parse_ladino_full.py
Saídas:
  - ladino_features.json (class features Nv 1-20)
  - ladino_subs.json     (8 subclasses com tagline + features_sub aninhadas)
  - ladino_meta.json     (proficiências + multiclass + equipamento)
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/ladino.html")
OUT_FEATS = Path("ladino_features.json")
OUT_SUBS = Path("ladino_subs.json")
OUT_META = Path("ladino_meta.json")

# Class features whitelist (H3 names que NÃO são subclass features).
# As anchors "Trilha do Ladino" Nv 3/9/13/17 + "Características de Trilha" Nv 6
# são class features (introduzem o batch de cada nível).
CLASS_FEATURE_NAMES = {
    "Perícia Especializada",        # Nv 1 (+ clone Nv 6 "Perícia Especializada (2)")
    "Ataque Furtivo",
    "Maestria em Armas do Ladino",
    "Técnica de Furtividade",       # Nv 1 (distingue dos "Técnica de Furtividade — X" do Nv 6)
    "Ação Ardilosa",
    "Mira Cravada",
    "Trilha do Ladino",             # Nv 3 / 9 / 13 / 17 anchors
    "Aprimoramento de Habilidade",  # Nv 4 → clone Nv 8/10/12/16/19
    "Esquiva Instintiva",
    "Primeiro Golpe",
    "Características de Trilha",    # Nv 6 anchor
    "Evasão",
    "Talento Confiável",
    "Golpe de Abertura",
    "Técnica de Furtividade Aprimorada",
    "Mente Escorregadia",
    "Inatingível",
    "Momento Perfeito",
}

# Canonical order das 8 subclasses (ordem em que aparecem como H2 e nos batches).
SUBCLASS_CANON = [
    {"slug": "alma-sombria",                "nome": "Alma Sombria"},
    {"slug": "trilha-do-assassino",         "nome": "Trilha do Assassino"},
    {"slug": "trilha-do-batedor",           "nome": "Trilha do Batedor"},
    {"slug": "trilha-do-detetive",          "nome": "Trilha do Detetive"},
    {"slug": "trilha-do-duelista",          "nome": "Trilha do Duelista"},
    {"slug": "trilha-do-fantasma",          "nome": "Trilha do Fantasma"},
    {"slug": "trilha-do-ladrao",            "nome": "Trilha do Ladrão"},
    {"slug": "trilha-do-trapaceiro-arcano", "nome": "Trilha do Trapaceiro Arcano"},
]

# Quantos H3 subclass-features cada Trilha tem em cada batch de nível.
# Baseado em análise temática dos H2 intros + ordem dos H3 no documento.
# Totais: Nv 3=17, Nv 6=8 (1 por Trilha), Nv 9=10, Nv 13=11, Nv 17=9.
SUBCLASS_FEATURE_COUNTS: dict[str, dict[int, int]] = {
    "alma-sombria":                {3: 4, 6: 1, 9: 1, 13: 1, 17: 1},  # = 8
    "trilha-do-assassino":         {3: 2, 6: 1, 9: 1, 13: 1, 17: 1},  # = 6
    "trilha-do-batedor":           {3: 2, 6: 1, 9: 2, 13: 1, 17: 1},  # = 7
    "trilha-do-detetive":          {3: 2, 6: 1, 9: 1, 13: 2, 17: 1},  # = 7
    "trilha-do-duelista":          {3: 2, 6: 1, 9: 1, 13: 2, 17: 2},  # = 8
    "trilha-do-fantasma":          {3: 1, 6: 1, 9: 1, 13: 1, 17: 1},  # = 5
    "trilha-do-ladrao":            {3: 2, 6: 1, 9: 2, 13: 1, 17: 1},  # = 7
    "trilha-do-trapaceiro-arcano": {3: 2, 6: 1, 9: 1, 13: 2, 17: 1},  # = 7
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(s: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub(" ", unescape(s or ""))).strip()


def parse_proficiencias(secao_text: str) -> dict:
    """Extrai SkillsJSON, ArmorProf, WeaponProf, ToolProf, Saves, Equipamento, Multiclass."""
    t = secao_text
    out: dict = {}

    # Normalização canônica de atributos (sem acentos no DB)
    _ATR_NORMAL = {"Inteligência": "Inteligencia", "Constituição": "Constituicao", "Força": "Forca"}

    # Saves
    m = re.search(r"Testes de Resistência\s*:\s*(.+?)\s*Perícias", t, re.I | re.S)
    if m:
        raw = re.sub(r"\.", "", m.group(1))
        items = [s.strip() for s in re.split(r",|\se\s", raw) if s.strip()]
        out["saves"] = [_ATR_NORMAL.get(s, s) for s in items]

    # Perícias (Escolha N: A, B, C, ...)
    m = re.search(r"Perícias\s*:\s*Escolha\s+(\w+)\s+dentre\s+([^.]+?)\s*(?:Multiclasse|Equipamento|\.|$)", t, re.I)
    if m:
        n_str = m.group(1).strip().lower()
        n_map = {"uma": 1, "duas": 2, "tres": 3, "três": 3, "quatro": 4, "cinco": 5}
        n = n_map.get(n_str, int(n_str) if n_str.isdigit() else 2)
        lista = re.split(r",|\se\s", m.group(2))
        from_list = [s.strip().rstrip(".") for s in lista if s.strip() and len(s.strip()) > 1]
        out["skills"] = {"choose": n, "from": from_list}

    # Armas
    m = re.search(r"Armas\s*:\s*([^.]+?)(?:\.|Ferramentas|Testes|Multiclasse|$)", t, re.I)
    if m:
        arm = m.group(1).strip().rstrip(".")
        # Splita em vírgulas mas preserva expressões complexas
        out["weapon_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", arm, re.I) else [arm]

    # Ferramentas
    m = re.search(r"Ferramentas\s*:\s*([^.]+?)(?:\.|Testes|Multiclasse|$)", t, re.I)
    if m:
        fer = m.group(1).strip().rstrip(".")
        out["tool_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", fer, re.I) else [fer]

    # Armaduras
    m = re.search(r"Armaduras\s*:\s*([^.]+?)(?:\.|Armas|Ferramentas|$)", t, re.I)
    if m:
        arm = m.group(1).strip().rstrip(".")
        out["armor_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", arm, re.I) else [arm]

    # Dado de Vida
    m = re.search(r"Dados de Vida\s*:\s*(\d?d\d+)", t, re.I)
    if m:
        out["dado_vida"] = m.group(1).lower()

    # Multiclasse — Proficiências adquiridas (Armaduras + Ferramentas + Perícia)
    m = re.search(r"Proficiências de Multiclasse(.*?)(?:Equipamento|$)", t, re.I | re.S)
    if m:
        mc_text = m.group(1)
        out["multiclass_text"] = clean(mc_text)[:500]
        # Extrai lista de profs adquiridas
        adq = []
        m_arm = re.search(r"Armaduras\s*:\s*([^.;]+?)(?:Armas|Ferramentas|Perícias|$)", mc_text, re.I)
        if m_arm:
            v = m_arm.group(1).strip().rstrip(".")
            if not re.fullmatch(r"Nenhuma|Nenhum|—|-", v, re.I):
                adq.append(v)
        m_fer = re.search(r"Ferramentas\s*:\s*([^.;]+?)(?:Armas|Armaduras|Perícias|$)", mc_text, re.I)
        if m_fer:
            v = m_fer.group(1).strip().rstrip(".")
            if not re.fullmatch(r"Nenhuma|Nenhum|—|-", v, re.I):
                adq.append(v)
        m_per = re.search(r"Perícias\s*:\s*Escolha\s+(\w+)\s+dentre", mc_text, re.I)
        if m_per:
            adq.append(f"1 Perícia (escolha do Ladino)")
        out["multiclass_prof"] = adq

    # Equipamento (texto livre — pra revisão humana)
    m = re.search(r"Equipamento(s)?\s*(.*?)$", t, re.I | re.S)
    if m:
        out["equipamento_inicial_raw"] = clean(m.group(2))[:800]

    return out


def parse() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    h2s = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S))
    # H2 layout: [0]=Ladino, [1]=Características, [2]=Habilidades de Classe, [3..10]=8 subs.
    fim_caracteristicas = h2s[2].start()  # antes do "Habilidades de Classe"

    # === Meta ===
    secao_caracteristicas = clean(html[h2s[1].end():fim_caracteristicas])
    meta = parse_proficiencias(secao_caracteristicas)
    meta["_raw_text"] = secao_caracteristicas

    # === Subclasses (tagline = corpo do H2 da sub até o primeiro H3 ou próximo H2) ===
    subs = []
    for i, sub_canon in enumerate(SUBCLASS_CANON):
        h2_idx = 3 + i
        if h2_idx >= len(h2s):
            break
        m_h2 = h2s[h2_idx]
        nome_html = clean(m_h2.group(1))
        end_block = h2s[h2_idx + 1].start() if h2_idx + 1 < len(h2s) else len(html)
        next_h3 = re.search(r"<h3", html[m_h2.end():end_block], re.I)
        tagline_end = m_h2.end() + (next_h3.start() if next_h3 else end_block - m_h2.end())
        tagline = clean(html[m_h2.end():tagline_end])[:400]
        subs.append({
            "slug": sub_canon["slug"],
            "nome": sub_canon["nome"],
            "nome_html": nome_html,
            "tagline": tagline,
            "features_sub": [],
        })

    # === Class features + Subclass features ===
    h_re = re.compile(r"<h3[^>]*>(.*?)</h3>", re.I | re.S)
    stop_re = re.compile(r"<h[1234][^>]*>", re.I)

    all_h3 = []
    for m in h_re.finditer(html):
        title_raw = clean(m.group(1))
        nv = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", title_raw, re.I)
        if not nv:
            continue
        nivel = int(nv.group(1))
        nome = nv.group(2).strip()
        bs = m.end()
        nm = stop_re.search(html, bs)
        be = nm.start() if nm else len(html)
        body = clean(html[bs:be])
        # Cap em 2500 pra descrições longas
        if len(body) > 2500:
            body = body[:2497] + "..."
        all_h3.append({"nivel": nivel, "nome": nome, "descricao": body, "offset": m.start()})

    # Classificar: class vs subclass
    class_features: list[dict] = []
    by_nv: dict[int, list[dict]] = {}
    for h in all_h3:
        by_nv.setdefault(h["nivel"], []).append(h)

    # Class features (whitelist)
    for h in all_h3:
        if h["nome"] in CLASS_FEATURE_NAMES:
            class_features.append({"nivel": h["nivel"], "nome": h["nome"], "descricao": h["descricao"]})

    # ASI clones — Aprimoramento de Habilidade no Nv 4 cobre 8, 10, 12, 16, 19 também.
    asi_master = next((f for f in class_features if f["nome"] == "Aprimoramento de Habilidade"), None)
    if asi_master:
        for nv_asi in (8, 10, 12, 16, 19):
            if not any(f["nivel"] == nv_asi and f["nome"] == "Aprimoramento de Habilidade" for f in class_features):
                class_features.append({
                    "nivel": nv_asi,
                    "nome": "Aprimoramento de Habilidade",
                    "descricao": asi_master["descricao"],
                })

    # Clone "Perícia Especializada (2)" no Nv 6 — tabela diz que Nv 6 dá uma segunda
    # perícia especializada. Não tem H3 dedicado; reusa a descrição do Nv 1.
    per_master = next((f for f in class_features if f["nome"] == "Perícia Especializada"), None)
    if per_master:
        class_features.append({
            "nivel": 6,
            "nome": "Perícia Especializada (2)",
            "descricao": per_master["descricao"],
        })

    class_features.sort(key=lambda f: (f["nivel"], f["nome"]))

    # Subclass features: distribui por ordem-no-batch contra SUBCLASS_FEATURE_COUNTS
    sub_by_slug = {s["slug"]: s for s in subs}
    # Nv 6 é especial: 8 H3 "Técnica de Furtividade — X" são subclass features (1 por Trilha)
    for nivel in (3, 6, 9, 13, 17):
        batch = []
        for h in by_nv.get(nivel, []):
            if h["nome"] in CLASS_FEATURE_NAMES:
                continue
            if nivel == 6 and h["nome"].startswith("Técnica de Furtividade — "):
                batch.append(h)
            elif nivel != 6:
                batch.append(h)
        idx = 0
        for sub_canon in SUBCLASS_CANON:
            slug = sub_canon["slug"]
            count = SUBCLASS_FEATURE_COUNTS.get(slug, {}).get(nivel, 0)
            for _ in range(count):
                if idx >= len(batch):
                    print(f"  WARN: batch Nv{nivel} ran out at {slug} idx={idx}")
                    break
                h = batch[idx]
                sub_by_slug[slug]["features_sub"].append({
                    "nivel": h["nivel"], "nome": h["nome"], "descricao": h["descricao"],
                })
                idx += 1
        if idx < len(batch):
            sobra = [h["nome"] for h in batch[idx:]]
            print(f"  WARN: batch Nv{nivel} sobra {len(batch) - idx} h3 não atribuídos: {sobra}")

    # === Output ===
    OUT_FEATS.write_text(json.dumps(class_features, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SUBS.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # === Report ===
    print(f"\n=== LADINO PARSER REPORT ===")
    print(f"Arquivo: {HTML_PATH} ({HTML_PATH.stat().st_size:,} bytes)\n")
    print("Proficiências extraídas:")
    for k in ["dado_vida", "saves", "skills", "weapon_prof", "tool_prof",
              "armor_prof", "multiclass_prof"]:
        print(f"  {k}: {meta.get(k)}")
    print(f"\n{len(class_features)} class features (incluindo ASI clones + Perícia Especializada Nv 6):")
    for f in class_features:
        print(f"  Nv{f['nivel']:>2}  {f['nome']}")
    print(f"\n{len(subs)} subclasses:")
    for s in subs:
        print(f"\n  {s['slug']:<32} {s['nome']} ({len(s['features_sub'])} features)")
        feats_by_nv: dict[int, list[str]] = {}
        for f in s["features_sub"]:
            feats_by_nv.setdefault(f["nivel"], []).append(f["nome"])
        for nv in sorted(feats_by_nv):
            for nome in feats_by_nv[nv]:
                print(f"      Nv{nv:>2}  {nome}")
    print(f"\nOutputs:\n  - {OUT_FEATS}\n  - {OUT_SUBS}\n  - {OUT_META}")


if __name__ == "__main__":
    parse()
