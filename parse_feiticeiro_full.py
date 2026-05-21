"""Parser do Feiticeiro — extrai proficiências, 5 Origens (subclasses),
class features Nv 1-20, e subclass features Nv 3/6/14/18.

Layout HTML do Feiticeiro tem H2 attribute section (STR/DEX/...) inserida
entre as últimas subs e os features Nv 4+. Tratamos com offsets em vez de
H2 boundaries (igual Mago). Whitelist define class vs subclass.

Class features:
  Nv 1: Conjuração, Feitiçaria Inata
  Nv 2: Fonte de Magia, Metamagia
  Nv 3: Origem de Linhagem (anchor)
  Nv 4: Incremento de Atributo ou Talento (ASI master — clones em 8/12/16/19)
  Nv 5: Restauração Feiticeira
  Nv 6: Característica de Linhagem (anchor)
  Nv 7: Feitiçaria Encarnada
  Nv 10: Metamagia Adicional e Dom da Criação
  Nv 14: Característica de Linhagem (anchor)
  Nv 17: Metamagia Suprema
  Nv 18: Característica de Linhagem (anchor)
  Nv 20: Apoteose Arcana

Distribuição subclass features (hardcoded por análise temática + ordem doc):
  Total: 34 features
"""
from __future__ import annotations
import json, re
from html import unescape
from pathlib import Path

HTML_PATH = Path("paginas/feiticeiro.html")
OUT_FEATS = Path("feiticeiro_features.json")
OUT_SUBS = Path("feiticeiro_subs.json")
OUT_META = Path("feiticeiro_meta.json")

CLASS_FEATURE_NAMES = {
    "Conjuração", "Feitiçaria Inata",
    "Fonte de Magia", "Metamagia",
    "Origem de Linhagem",                       # Nv 3 anchor
    "Incremento de Atributo ou Talento",        # Nv 4 master — clone p/ 8/12/16/19
    "Restauração Feiticeira",
    "Característica de Linhagem",               # Nv 6/14/18 anchors
    "Feitiçaria Encarnada",
    "Metamagia Adicional e Dom da Criação",
    "Metamagia Suprema",
    "Apoteose Arcana",
}

SUBCLASS_CANON = [
    {"slug": "origem-aberrante",    "nome": "Origem Aberrante"},
    {"slug": "origem-do-caos",      "nome": "Origem do Caos"},
    {"slug": "origem-divina",       "nome": "Origem Divina"},
    {"slug": "origem-draconica",    "nome": "Origem Dracônica"},
    {"slug": "origem-da-ordem",     "nome": "Origem da Ordem"},
    {"slug": "origem-da-tempestade","nome": "Origem da Tempestade"},
]

# Mapeamento EXPLÍCITO H3 nome → slug subclass. Hardcoded por análise
# temática + referências cruzadas (ex: "Revelação na Carne (Mente Dilatada)"
# refere feature Aberrante; "Forma Dracônica Ancestral" = Drac, etc).
# Total: 34 sub features (17 Nv3 + 5 Nv6 + 7 Nv14 + 5 Nv18).
FEATURE_TO_SUB: dict[str, str] = {
    # === Nv 3 (3 cada para 5 originais + 2 Tempestade) ===
    # Aberrante (3)
    "Telepatia Aberrante":                              "origem-aberrante",
    "Metamagia da Mente Velada":                        "origem-aberrante",
    "Mente Dilatada":                                   "origem-aberrante",
    # Caos (3)
    "Marca do Caos":                                    "origem-do-caos",
    "Potencializada":                                   "origem-do-caos",
    "Banco de Entropia":                                "origem-do-caos",
    # Divina (3)
    "Fala Celestial":                                   "origem-divina",
    "Metamagia Potencializada":                         "origem-divina",
    "Centelha dos Deuses":                              "origem-divina",
    # Dracônica (3)
    "Sangue e Escamas":                                 "origem-draconica",
    "Ascendência Dracônica":                            "origem-draconica",
    "Sopro Desperto":                                   "origem-draconica",
    # Ordem (3)
    "Léxico Modrônico":                                 "origem-da-ordem",
    "Metamagia — Magia Precisa (sempre preparada)":     "origem-da-ordem",
    "Ritmo Determinista (Rider da Feitiçaria Inata)":   "origem-da-ordem",
    # Tempestade (2)
    "Fala dos Ventos":                                  "origem-da-tempestade",
    "Metamagia — Feitiço Acelerado":                    "origem-da-tempestade",

    # === Nv 6 (5 features, Divina sem Nv 6) ===
    "Escudo da Anomalia":                               "origem-aberrante",
    "Asas Transcendentais":                             "origem-do-caos",   # chute — flag pra revisar
    "Sangue Resiliente":                                "origem-draconica",
    "Bastião Harmônico":                                "origem-da-ordem",
    "Coração do Trovão":                                "origem-da-tempestade",

    # === Nv 14 (7 features, Aberrante com 2: Revelação + Manto Umbral) ===
    "Revelação na Carne (Mente Dilatada)":              "origem-aberrante",   # ref explícita
    "Fenda Dupla":                                      "origem-do-caos",     # caos = fenda
    "Voz dos Bem-Aventurados":                          "origem-divina",
    "Herdeiro Alado":                                   "origem-draconica",
    "Marcha da Ordem":                                  "origem-da-ordem",
    "Manto Umbral":                                     "origem-aberrante",   # umbra/dimensional → Aberrante
    "Vestes do Vendaval (Feitiçaria Inata ativa)":      "origem-da-tempestade",

    # === Nv 18 (5 features, Tempestade sem Nv 18) ===
    "Anomalia Andante":                                 "origem-aberrante",
    "Eclipse Caótico":                                  "origem-do-caos",
    "Apoteose Divina":                                  "origem-divina",
    "Forma Dracônica Ancestral":                        "origem-draconica",
    "Axioma da Ordem":                                  "origem-da-ordem",
}

TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")
def clean(s: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub(" ", unescape(s or ""))).strip()

_ATR_NORMAL = {"Inteligência":"Inteligencia","Constituição":"Constituicao","Força":"Forca"}

def parse_proficiencias(secao_text: str) -> dict:
    """Extrai proficiências da seção Características. NÃO splita em 'Nível 1:'
    porque 'Dados de Vida no Nível 1: 6 + Mod' contém esse marker falso."""
    t = secao_text
    out: dict = {}
    m = re.search(r"Testes de Resistência\s*:\s*(.+?)\s*Perícias", t, re.I | re.S)
    if m:
        raw = re.sub(r"\.", "", m.group(1))
        items = [s.strip() for s in re.split(r",|\se\s", raw) if s.strip()]
        out["saves"] = [_ATR_NORMAL.get(s, s) for s in items]
    m = re.search(r"Perícias\s*:\s*Escolha\s+(\w+)\s*(?:dentre|de|:)?\s*([^.]+?)(?:\.|Multiclasse|Equipamento|Armas|$)", t, re.I)
    if m:
        n_str = m.group(1).strip().lower()
        n_map = {"uma":1,"duas":2,"três":3,"tres":3,"quatro":4}
        n = n_map.get(n_str, int(n_str) if n_str.isdigit() else 2)
        lista = re.split(r",|\se\s|\sou\s", m.group(2))
        out["skills"] = {"choose": n, "from": [s.strip().rstrip(".") for s in lista if s.strip() and len(s.strip())>2]}
    for fname, regex in [
        ("weapon_prof", r"Armas\s*:\s*([^.]+?)(?:\.|Ferramentas|Armaduras|Testes|Multiclasse|$)"),
        ("tool_prof",   r"Ferramentas\s*:\s*([^.]+?)(?:\.|Armas|Armaduras|Testes|Multiclasse|$)"),
        ("armor_prof",  r"Armaduras\s*:\s*([^.]+?)(?:\.|Armas|Ferramentas|$)"),
    ]:
        m = re.search(regex, t, re.I)
        if m:
            v = m.group(1).strip().rstrip(".")
            out[fname] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", v, re.I) else [v]
    m = re.search(r"Dados? de Vida\s*:\s*(\d?d\d+)", t, re.I)
    if m: out["dado_vida"] = m.group(1).lower()
    # Multiclass
    m = re.search(r"Profici[êe]ncias Adquiridas\s*:\s*([^.]+)", t, re.I)
    if m:
        v = m.group(1).strip().rstrip(".")
        out["multiclass_prof"] = [] if re.fullmatch(r"Nenhuma|Nenhum|—|-", v, re.I) else [v]
    m = re.search(r"Equipamento(s)?\s*(.*?)$", t, re.I | re.S)
    if m: out["equipamento_inicial_raw"] = clean(m.group(2))[:800]
    return out


def parse() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    h2s = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S))
    # H2[0] Características, H2[1] Habilidades, H2[2..6] 5 subs, H2[7]= STR (fim)
    fim_carac = h2s[1].start()
    sec_carac = clean(html[h2s[0].end():fim_carac])
    meta = parse_proficiencias(sec_carac)
    meta["_raw_text"] = sec_carac

    # Subclasses — lookup H2 por NOME (Tempestade está em H2[15], não contíguo)
    h2_by_name = {clean(m.group(1)): (i, m) for i, m in enumerate(h2s)}
    subs = []
    for sub_canon in SUBCLASS_CANON:
        h2_idx_m = h2_by_name.get(sub_canon["nome"])
        if not h2_idx_m:
            print(f"  WARN: H2 da subclasse '{sub_canon['nome']}' não encontrado")
            subs.append({"slug": sub_canon["slug"], "nome": sub_canon["nome"],
                         "nome_html": sub_canon["nome"], "tagline": "", "features_sub": []})
            continue
        h2_idx, m_h2 = h2_idx_m
        end_block = h2s[h2_idx+1].start() if h2_idx+1 < len(h2s) else len(html)
        next_h3 = re.search(r"<h3", html[m_h2.end():end_block], re.I)
        tagline_end = m_h2.end() + (next_h3.start() if next_h3 else end_block - m_h2.end())
        subs.append({
            "slug": sub_canon["slug"], "nome": sub_canon["nome"],
            "nome_html": clean(m_h2.group(1)),
            "tagline": clean(html[m_h2.end():tagline_end])[:400],
            "features_sub": [],
        })

    # Walk all H3 Nv:Nome em ordem do documento
    h_re = re.compile(r"<h3[^>]*>(.*?)</h3>", re.I | re.S)
    stop_re = re.compile(r"<h[1234][^>]*>", re.I)
    all_h3 = []
    for m in h_re.finditer(html):
        title = clean(m.group(1))
        nv = re.match(r"N[íi]vel\s+(\d+)\s*:\s*(.+)", title, re.I)
        if not nv: continue
        nivel = int(nv.group(1)); nome = nv.group(2).strip()
        bs = m.end()
        nm = stop_re.search(html, bs)
        be = nm.start() if nm else len(html)
        body = clean(html[bs:be])
        if len(body) > 2500: body = body[:2497] + "..."
        all_h3.append({"nivel": nivel, "nome": nome, "descricao": body, "offset": m.start()})

    # Class features (whitelist)
    class_features = []
    for h in all_h3:
        if h["nome"] in CLASS_FEATURE_NAMES:
            class_features.append({"nivel": h["nivel"], "nome": h["nome"], "descricao": h["descricao"]})

    # ASI clones (Nv 4 master → 8/12/16/19)
    asi_master = next((f for f in class_features if f["nome"] == "Incremento de Atributo ou Talento"), None)
    if asi_master:
        for nv_asi in (8, 12, 16, 19):
            if not any(f["nivel"]==nv_asi and f["nome"]=="Incremento de Atributo ou Talento" for f in class_features):
                class_features.append({"nivel": nv_asi, "nome": "Incremento de Atributo ou Talento", "descricao": asi_master["descricao"]})
    class_features.sort(key=lambda f: (f["nivel"], f["nome"]))

    # Subclass features: distribui via FEATURE_TO_SUB (mapeamento explícito por nome).
    # Cada H3 sub-feature deve ter uma entrada no FEATURE_TO_SUB; warning se não.
    sub_by_slug = {s["slug"]: s for s in subs}
    for h in all_h3:
        if h["nome"] in CLASS_FEATURE_NAMES:
            continue
        slug = FEATURE_TO_SUB.get(h["nome"])
        if not slug:
            print(f"  WARN: Nv{h['nivel']} '{h['nome']}' sem mapeamento em FEATURE_TO_SUB — IGNORADO")
            continue
        if slug not in sub_by_slug:
            print(f"  WARN: slug '{slug}' não existe em SUBCLASS_CANON — IGNORADO")
            continue
        sub_by_slug[slug]["features_sub"].append({
            "nivel": h["nivel"], "nome": h["nome"], "descricao": h["descricao"],
        })

    OUT_FEATS.write_text(json.dumps(class_features, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_SUBS.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== FEITICEIRO PARSER REPORT ===")
    print(f"Arquivo: {HTML_PATH}")
    print(f"\nProficiências:")
    for k in ["dado_vida","saves","skills","weapon_prof","tool_prof","armor_prof","multiclass_prof"]:
        print(f"  {k}: {meta.get(k)}")
    print(f"\n{len(class_features)} class features:")
    for f in class_features: print(f"  Nv{f['nivel']:>2}  {f['nome']}")
    print(f"\n{len(subs)} subclasses:")
    for s in subs:
        print(f"\n  {s['slug']:<22} {s['nome']} ({len(s['features_sub'])} features)")
        for f in s["features_sub"]: print(f"      Nv{f['nivel']:>2}  {f['nome']}")
    print(f"\nOutputs: {OUT_FEATS}, {OUT_SUBS}, {OUT_META}")


if __name__ == "__main__":
    parse()
