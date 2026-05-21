"""Parser do Mago — extrai proficiências, 13 subclasses (Tradições Arcanas),
class features Nv 1-20, e subclass features Nv 3/6/10/14.

Estratégia de atribuição de features (importante):
  - H3 "Nível N: <Nome>" são features.
  - CLASS_FEATURE_NAMES é whitelist hardcoded — qualquer H3 cujo nome bate é class feature.
  - O resto é subclass feature. Atribuição: dentro de cada "batch" (mesmo Nv N),
    as features aparecem em ordem canônica das 13 subclasses, com contagem
    declarada em SUBCLASS_FEATURE_COUNTS por (subclass, nivel).

Uso: python parse_mago_full.py
Saídas:
  - mago_features.json (lista de class features com nivel/nome/descricao)
  - mago_subs.json     (13 subclasses com tagline + features_sub aninhadas)
  - mago_meta.json     (proficiências, equipamento, multiclass, dado de vida, etc.)
"""
from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/mago.html")
OUT_FEATS = Path("mago_features.json")
OUT_SUBS = Path("mago_subs.json")
OUT_META = Path("mago_meta.json")

# Class features whitelist (H3 que NÃO são subclass features).
# Inclui as features anchor "Tradição Arcana", "Proficiência da Tradição",
# "Maestria da Tradição", "Ápice da Tradição" — essas introduzem o batch
# de cada nível e são class features por si só (cada subclasse herda o nome
# canônico e adiciona seus features próprios listados depois).
CLASS_FEATURE_NAMES = {
    "Conjuração de Magias",
    "Estudo Arcano",
    "Recuperação Arcana",
    "Tradição Arcana",          # Nv 3 anchor
    "Aumento de Atributo",      # ASI (aparece em vários níveis na tabela, mas só 1 H3)
    "Memorizar Magia",
    "Proficiência da Tradição", # Nv 6 anchor
    "Magia Assinatura",         # Nv 7
    "Mente Afiada",
    "Maestria da Tradição",     # Nv 10 anchor
    "Magia Assinatura (2ª)",    # Nv 11 — feminine ordinal (U+00AA) per fonte oficial
    "Ápice da Tradição",        # Nv 14 anchor
    "Magia Assinatura (3ª)",    # Nv 15 — idem
    "Arquimago",
    "Maestria Arcana",
}

# Canonical order das 13 subclasses (ordem em que aparecem como H2 e nos batches).
SUBCLASS_CANON = [
    {"slug": "abjurador",       "nome": "Abjurador"},
    {"slug": "adivinho",        "nome": "Adivinho"},
    {"slug": "conjurador",      "nome": "Conjurador"},
    {"slug": "cronoturgista",   "nome": "Cronoturgista"},
    {"slug": "danca-da-lamina", "nome": "Dança da Lâmina"},
    {"slug": "encantador",      "nome": "Encantador"},
    {"slug": "escriba",         "nome": "Escriba"},
    {"slug": "evocador",        "nome": "Evocador"},
    {"slug": "graviturgista",   "nome": "Graviturgista"},
    {"slug": "guerra",          "nome": "Guerra"},
    {"slug": "ilusionista",     "nome": "Ilusionista"},
    {"slug": "necromante",      "nome": "Necromante"},
    {"slug": "transmutador",    "nome": "Transmutador"},
]

# Quantos H3 features cada subclasse tem em cada batch de nível.
# Derivado da contagem real no HTML (85 H3 total - 15 class = 70 subclass).
# Default {3:2, 6:1, 10:1, 14:1} = 5 features/sub = 65; 5 extras vão pros casos abaixo.
SUBCLASS_FEATURE_COUNTS: dict[str, dict[int, int]] = {
    "abjurador":       {3: 2, 6: 1, 10: 1, 14: 1},
    "adivinho":        {3: 2, 6: 1, 10: 1, 14: 1},
    "conjurador":      {3: 2, 6: 1, 10: 1, 14: 1},
    "cronoturgista":   {3: 3, 6: 1, 10: 1, 14: 1},  # +1 Nv 3
    "danca-da-lamina": {3: 2, 6: 1, 10: 1, 14: 1},
    "encantador":      {3: 3, 6: 1, 10: 1, 14: 1},  # +1 Nv 3
    "escriba":         {3: 3, 6: 1, 10: 1, 14: 1},  # +1 Nv 3
    "evocador":        {3: 2, 6: 1, 10: 1, 14: 1},
    "graviturgista":   {3: 2, 6: 1, 10: 1, 14: 1},
    "guerra":          {3: 3, 6: 1, 10: 2, 14: 1},  # +1 Nv 3, +1 Nv 10 (Fortitude+Táticas)
    "ilusionista":     {3: 2, 6: 1, 10: 1, 14: 1},
    "necromante":      {3: 2, 6: 1, 10: 1, 14: 1},
    "transmutador":    {3: 2, 6: 1, 10: 1, 14: 1},
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(s: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub(" ", unescape(s or ""))).strip()


def slugify(s: str) -> str:
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    out = s.lower()
    for k, v in repl.items():
        out = out.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")


def parse_proficiencias(secao_text: str) -> dict:
    """Extrai SkillsJSON, ArmorProf, WeaponProf, ToolProf, Saves, Equipamento,
    Multiclass do texto da seção 'Características de Classe'."""
    t = secao_text
    out: dict = {}

    # Saves (Testes de Resistência) — captura até "Perícias" (next field)
    # Normaliza pra convenção canônica do Bonfire (sem acentos): "Inteligência" →
    # "Inteligencia". Outras classes do DB usam essa forma; renderer/agg comparam
    # contra ela. Sem essa normalização, save da classe não cai no saves_proficientes.
    _ATR_NORMAL = {
        "Inteligência": "Inteligencia",
        "Constituição": "Constituicao",
        "Força":        "Forca",
    }
    m = re.search(r"Testes de Resistência\s*:\s*(.+?)\s*Perícias", t, re.I | re.S)
    if m:
        raw = re.sub(r"\.", "", m.group(1))
        items = [s.strip() for s in re.split(r",|\se\s", raw) if s.strip()]
        out["saves"] = [_ATR_NORMAL.get(s, s) for s in items]

    # Perícias (Escolha N: A, B, C, ...)
    m = re.search(r"Perícias\s*:\s*Escolha\s+(\d+)\s*:\s*([^.]+?)(?:\.|Armas|Ferramentas|$)", t, re.I)
    if m:
        n = int(m.group(1))
        lista = re.split(r",|\sou\s", m.group(2))
        from_list = [s.strip().rstrip(".") for s in lista if s.strip()]
        out["skills"] = {"choose": n, "from": from_list}

    # Armas
    m = re.search(r"Armas\s*:\s*([^.]+?)(?:\.|Ferramentas|Armaduras|$)", t, re.I)
    if m:
        arm = m.group(1).strip().rstrip(".")
        out["weapon_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", arm, re.I) else [arm]

    # Ferramentas
    m = re.search(r"Ferramentas\s*:\s*([^.]+?)(?:\.|Armaduras|$)", t, re.I)
    if m:
        fer = m.group(1).strip().rstrip(".")
        out["tool_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", fer, re.I) else [fer]

    # Armaduras
    m = re.search(r"Armaduras\s*:\s*([^.]+?)(?:\.|Equipamento|$)", t, re.I)
    if m:
        arm = m.group(1).strip().rstrip(".")
        out["armor_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", arm, re.I) else [arm]

    # Dado de Vida
    m = re.search(r"Dado de Vida\s*:\s*(\d?d\d+)", t, re.I)
    if m:
        out["dado_vida"] = m.group(1).lower()

    # Atributo Primário
    m = re.search(r"Atributo Primário\s*:\s*([A-Za-zÀ-ÿ]+)", t, re.I)
    if m:
        out["atributo_primario"] = m.group(1).strip()

    # Equipamento Inicial (texto livre — preserva pra revisão humana)
    m = re.search(r"Equipamento Inicial(.*?)(?:Multiclasse|$)", t, re.I | re.S)
    if m:
        out["equipamento_inicial_raw"] = clean(m.group(1))[:600]

    # Multiclasse → Proficiências Adquiridas
    m = re.search(r"Profici[êe]ncias Adquiridas\s*:\s*([^.]+)", t, re.I)
    if m:
        adq = m.group(1).strip().rstrip(".")
        out["multiclass_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", adq, re.I) else [adq]

    return out


def parse() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    h2s = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S))
    if len(h2s) < 15:
        raise SystemExit(f"Esperava >=15 H2, achei {len(h2s)}")
    fim_caracteristicas = h2s[1].start()  # antes do "Habilidades de Classe"
    fim_intro_subs = h2s[2].start()       # antes do primeiro H2 de subclasse

    # === Meta ===
    secao_caracteristicas = clean(html[h2s[0].end():fim_caracteristicas])
    meta = parse_proficiencias(secao_caracteristicas)
    meta["_raw_text"] = secao_caracteristicas

    # === Subclasses (tagline = corpo do H2 da sub até o próximo H2 ou início de H3 Nv 3) ===
    # Primeiro bloco de 13 H2s (índices 2..14) traz nome+tagline.
    subs = []
    for i, sub_canon in enumerate(SUBCLASS_CANON):
        h2_idx = 2 + i
        if h2_idx >= len(h2s):
            break
        m_h2 = h2s[h2_idx]
        nome_html = clean(m_h2.group(1))
        # tagline: tudo entre fim do H2 e início do próximo H2 OU do primeiro H3
        end_block = h2s[h2_idx + 1].start() if h2_idx + 1 < len(h2s) else len(html)
        next_h3 = re.search(r"<h3", html[m_h2.end():end_block], re.I)
        tagline_end = m_h2.end() + (next_h3.start() if next_h3 else end_block - m_h2.end())
        tagline = clean(html[m_h2.end():tagline_end])[:400]
        subs.append({
            "slug": sub_canon["slug"],
            "nome": sub_canon["nome"],
            "nome_html": nome_html,      # pra detectar mismatch
            "tagline": tagline,
            "features_sub": [],          # populado depois
        })

    # === Class features + Subclass features ===
    # Walk all H3 "Nível N: ..." em ordem do documento.
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
        if len(body) > 2000:
            body = body[:1997] + "..."
        all_h3.append({"nivel": nivel, "nome": nome, "descricao": body, "offset": m.start()})

    # Classificar: class vs subclass; subclass walks por batch+ordem canônica.
    class_features: list[dict] = []
    # Para subclass attribution: agrupa h3 por nível "batch". Dentro de um batch,
    # exclui as anchor class features (Tradição Arcana, Proficiência da Tradição,
    # Maestria da Tradição, Ápice da Tradição) e o que sobra são as subclass features
    # em ordem canônica das subclasses.
    by_nv: dict[int, list[dict]] = {}
    for h in all_h3:
        by_nv.setdefault(h["nivel"], []).append(h)

    # Class features primeiro
    for h in all_h3:
        if h["nome"] in CLASS_FEATURE_NAMES:
            class_features.append({"nivel": h["nivel"], "nome": h["nome"], "descricao": h["descricao"]})

    # Clonar ASI ("Aumento de Atributo") nos níveis 8/12/16/19 — só 1 H3 no HTML
    # (Nv 4) cobre os 5 níveis da progressão. Mesmo padrão do Místico.
    asi_master = next((f for f in class_features if f["nome"] == "Aumento de Atributo"), None)
    if asi_master:
        for nv_asi in (8, 12, 16, 19):
            if not any(f["nivel"] == nv_asi and f["nome"] == "Aumento de Atributo" for f in class_features):
                class_features.append({
                    "nivel": nv_asi,
                    "nome": "Aumento de Atributo",
                    "descricao": asi_master["descricao"],
                })
        class_features.sort(key=lambda f: (f["nivel"], f["nome"]))

    # Subclass features: para cada nível com SUBCLASS_FEATURE_COUNTS, walk as features
    # não-class em ordem do documento e distribui pelas subs canônicas.
    sub_by_slug = {s["slug"]: s for s in subs}
    for nivel in (3, 6, 10, 14):
        batch = [h for h in by_nv.get(nivel, []) if h["nome"] not in CLASS_FEATURE_NAMES]
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

    # Pendências flagadas (Regra #0 — não inventar)
    pending = []
    if "Escolas de Foco" not in {f["nome"] for f in class_features}:
        pending.append({
            "campo": "TB_ClasseHabilidade Mago Nv 1",
            "item": "Escolas de Foco",
            "motivo": "Aparece na coluna 'Características' da tabela de progressão Nv 1, mas NÃO tem H3 dedicado no corpo do artigo. Provável sinônimo de 'Tradição Arcana' (Nv 3) ou conceito não-explicado. Decisão do user.",
        })
    if "Escola de Foco Adicional" not in {f["nome"] for f in class_features}:
        pending.append({
            "campo": "TB_ClasseHabilidade Mago Nv 10",
            "item": "Escola de Foco Adicional",
            "motivo": "Tabela menciona segunda Tradição/Escola no Nv 10 mas sem H3 dedicado. Possivelmente 'Maestria da Tradição' por outro nome.",
        })

    meta["pending_review"] = pending

    # === Output ===
    OUT_FEATS.write_text(json.dumps(class_features, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SUBS.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # === Report ===
    print(f"\n=== MAGO PARSER REPORT ===")
    print(f"Arquivo: {HTML_PATH} ({HTML_PATH.stat().st_size:,} bytes)")
    print(f"\nProficiências extraídas:")
    for k in ["atributo_primario", "dado_vida", "saves", "skills",
              "weapon_prof", "tool_prof", "armor_prof", "multiclass_prof"]:
        print(f"  {k}: {meta.get(k)}")
    print(f"\n{len(class_features)} class features:")
    for f in class_features:
        print(f"  Nv{f['nivel']:>2}  {f['nome']}")
    print(f"\n{len(subs)} subclasses:")
    for s in subs:
        n_feats = len(s["features_sub"])
        feats_by_nv = {}
        for f in s["features_sub"]:
            feats_by_nv.setdefault(f["nivel"], []).append(f["nome"])
        print(f"  {s['slug']:<18} {s['nome']:<20} ({n_feats} features)")
        for nv in sorted(feats_by_nv):
            for nome in feats_by_nv[nv]:
                print(f"      Nv{nv:>2}  {nome}")
    if pending:
        print(f"\n{len(pending)} pendências sinalizadas (Regra #0):")
        for p in pending:
            print(f"  - [{p['campo']}] {p['item']}: {p['motivo'][:80]}...")
    print(f"\nOutputs:\n  - {OUT_FEATS}\n  - {OUT_SUBS}\n  - {OUT_META}")


if __name__ == "__main__":
    parse()
