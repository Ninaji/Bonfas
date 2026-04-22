"""
Parser v2 para artigo de classe — classifica H3 "Nível N: Nome" por:
  1. Lista de features UNIVERSAIS da classe (classe base)
  2. Keyword matching com subclasse quando possível
  3. Fallback: ignora (evita putar na subclasse errada)

Rode:
    python parse_classe_v2.py paginas/guerreiro.html guerreiro
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

from parse_artigo import parse, unwrap_viewsource

DB = Path(__file__).parent / "bonfas.db"
TAG = re.compile(r"<[^>]+>"); WS = re.compile(r"\s+")
clean = lambda s: WS.sub(" ", TAG.sub(" ", s or "")).strip()

def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# -----------------------------------------------------------------------------
# Tabela de classificação — 1 perfil por classe
# Cada classe tem:
#   base_names:  nomes de features UNIVERSAIS (case-insensitive, match por startswith)
#   sub_keywords: { subclasse_slug: [palavras-chave no nome] }
# -----------------------------------------------------------------------------
PERFIS = {
    "guerreiro": {
        "base_names": [
            "Disciplina Marcial",
            "Retomar Fôlego",
            "Fundamentos de Batalha",
            "Surto de Ação",
            "Mente Tática",
            "Incremento de Atributo ou Talento",
            "Ataque Extra",
            "Ataque Tático",
            "Terceiro Ataque",
            "Indomável",
            "Superioridade Marcial",
            "Ataque Estudado",
            "Surto de Ação Aprimorado",
            "Senhor da Guerra",
            # markers de subclasse — são anotados mas NÃO criam features
            "Arquétipo do Guerreiro",
        ],
        "marker_only": ["Arquétipo do Guerreiro"],
        "sub_keywords": {
            "atirador":              ["Tiro", "Disparo", "Arco", "Atirador Lendário", "Foco Mortal", "Reposicionamento Tático"],
            "campeao":               ["Campeão", "Guerreiro do Corpo", "Golpe Devastador", "Domínio Corporal", "Força Indomável", "Campeão Lendário"],
            "cavaleiro":             ["Fiel Montaria", "Sentinela Implacável", "Manobra Protetora", "Investida de Aço", "Vigilância Total"],
            "cavaleiro-arcano":      ["Conjuração", "Vínculo de Guerra", "Táticas Arcanas", "Instância da Lâmina", "Conhecimentos Arcanos",
                                      "Instância Arcana Superior", "Tecelagem de Guerra", "Dínamo de Combate"],
            "cavaleiro-das-sombras": ["Invocar Sombra", "Dança das Sombras", "Transferência de Consciência",
                                      "Sacrifício Sombrio", "Sombra Revigorante", "Maestria das Sombras"],
            "comandante":            ["Comandos de Batalha", "Reagrupar e Inspirar", "Comandos Aprimorados",
                                      "Inspiração do Comandante", "Surto Estratégico"],
            "guerreiro-psionico":    ["Potência Psíquica", "Adepto Telecinético", "Mente Blindada",
                                      "Barreira Mental", "Mestre da Telecinese"],
            "ronin":                 ["Espírito de Luta", "Cortesão Desonrado", "Frieza Imperturbável",
                                      "Golpe de Determinação", "Golpe ao Trocar", "Último Suspiro"],
            "guerreiro-runico":      ["Inscrição Rúnica", "Força Rúnica", "Escudo Rúnico",
                                      "Crescimento Ancestral", "Golpe Rápido", "Mestre das Runas", "Colosso Rúnico",
                                      "Reposicionamento Tático", "Tiro Poderoso"],  # últimos 2 podem conflitar — uso contexto abaixo
        },
    },
    # adicionar outras classes aqui no futuro
}


def classify(classe_slug: str, titulo_limpo: str) -> tuple[str, str | None]:
    """Retorna ('classe', None) | ('subclasse', sub_slug) | ('marker', None) | ('ignore', None).
    Ordem: marker → subclasse (mais específico) → classe (genérico) → ignore."""
    perfil = PERFIS.get(classe_slug, {})
    t = titulo_limpo.lower()

    # markers (Arquétipo do Guerreiro etc.)
    for mk in perfil.get("marker_only", []):
        if t == mk.lower() or t.startswith(mk.lower()):
            return ("marker", None)

    # subclasse — checar PRIMEIRO (mais específico, pega "Força Indomável" antes de "Indomável")
    for sub_slug, kws in perfil.get("sub_keywords", {}).items():
        for kw in kws:
            if kw.lower() in t:
                return ("subclasse", sub_slug)

    # classe base — match de nome universal
    for nm in perfil.get("base_names", []):
        if t == nm.lower() or t.startswith(nm.lower()):
            return ("classe", None)

    return ("ignore", None)


# regex para detectar escolha embutida na descrição
CHOICE_RE = re.compile(
    r"\b(escolha|selecione)\s+(um|uma|dois|duas|tr[êe]s|quatro)\b"
    r"|\bvoc[êe]\s+escolhe\b|\bao\s+seu\s+crit[ée]rio\b|\b(sua\s+escolha)\b",
    re.I,
)


def run(arq: Path, classe_slug: str):
    raw = arq.read_text(encoding="utf-8", errors="ignore")
    html = unwrap_viewsource(raw)

    # encontra todos os headings
    headers = list(re.finditer(r"<(h[234])[^>]*>(.*?)</\1>", html, re.I | re.S))

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    id_classe = cur.execute("SELECT Id_Classe FROM TB_Classe WHERE Slug=?", (classe_slug,)).fetchone()
    if not id_classe:
        sys.exit(f"Classe {classe_slug!r} não encontrada")
    id_classe = id_classe[0]

    # garante as subclasses existem
    sub_map = {r[0]: r[1] for r in cur.execute(
        "SELECT Slug, Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=?", (id_classe,),
    )}

    # apaga anteriores (classe + subclasses)
    cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (id_classe,))

    total_classe = 0
    total_sub = 0
    ignorados = []

    for i, h in enumerate(headers):
        titulo = clean(h.group(2))
        if h.group(1).lower() == "h2":
            continue   # ignora H2 (usados como marker visual no HTML)

        # Só nos interessam H3/H4 que começam com "Nível N:" ou com nome conhecido
        m = re.match(r"^N[íi]vel\s+(\d+)\s*:\s*(.+)$", titulo, re.I)
        if m:
            nivel = int(m.group(1))
            nome = m.group(2).strip()
        else:
            # pode ser H4 com nome direto (Dados de Manobra de Combate etc.)
            nivel = 1
            nome = titulo
            # se não parece com feature (é UI, footer, etc), skip
            if len(nome) > 120 or re.search(r"(find your way|resources|legal|reach)", nome, re.I):
                continue

        kind, sub_slug = classify(classe_slug, nome)
        if kind in ("marker", "ignore"):
            if kind == "ignore":
                ignorados.append(f"nv{nivel}: {nome}")
            continue

        # corpo = até próximo header
        start = h.end()
        end = headers[i+1].start() if i+1 < len(headers) else len(html)
        descricao = clean(html[start:end])[:5000]
        if not descricao:
            continue

        tem_escolha = 1 if CHOICE_RE.search(descricao) else 0

        id_sub = None
        origem = "classe"
        if kind == "subclasse":
            id_sub = sub_map.get(sub_slug)
            origem = "subclasse"
            if not id_sub:
                ignorados.append(f"nv{nivel}: {nome}  (sub-slug {sub_slug!r} sem id)")
                continue

        cur.execute(
            """INSERT INTO TB_ClasseHabilidade
                 (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id_classe, id_sub, nome[:150], descricao, nivel, tem_escolha, origem),
        )
        if kind == "classe":
            total_classe += 1
        else:
            total_sub += 1

    conn.commit()

    print(f"\nOK {classe_slug}:  {total_classe} classe base  +  {total_sub} subclasse")
    print("\nDistribuicao por subclasse:")
    for r in cur.execute(
        """SELECT s.Nome, COUNT(h.Id_Habilidade)
             FROM TB_Subclasse s LEFT JOIN TB_ClasseHabilidade h
               ON h.Id_Subclasse = s.Id_Subclasse
            WHERE s.Id_Classe = ?
         GROUP BY s.Id_Subclasse
         ORDER BY s.Nome""", (id_classe,),
    ):
        print(f"  {r[0]:28} {r[1]:3} habs")

    if ignorados:
        print(f"\nIgnorados ({len(ignorados)}):")
        for x in ignorados[:20]:
            print(f"  - {x}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("uso: python parse_classe_v2.py <arquivo.html> <slug>")
    run(Path(sys.argv[1]), sys.argv[2])
