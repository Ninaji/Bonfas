"""
Parser de "Talentos Gerais" da H2 de `todos talentos.html`.

Estrutura:
  H2 "Talentos Gerais"
   H3 "<atributos>" (Qualquer Atributo, Força ou Destreza, etc.)
    H5 "<Nome do Talento>"  --> body do talento

Para cada H5:
  - extrai descrição (sem tags HTML)
  - parseia "Pré Requisito" / "Etiqueta" / "Tag" se presentes em forma de bullet ou prosa
  - pré-req atributo do H3 ancestor é adicionado às tags se talento não declarar próprio
  - aplica extract_prereq_tags do parse_talentos_gerais

Insert/UPDATE em TB_OpcaoJogo Tipo='talento-geral' (idempotente por Slug).
Diff vs já-existentes (do talentos_nivel4.txt) pra sair só os novos.

Uso:
    python parse_talentos_gerais_html.py "E:/Obsidian/_raw/processed/todos talentos.html"
"""
from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_artigo import parse  # type: ignore
from parse_talentos_gerais import slug, extract_prereq_tags, ATRIBUTO_ABREV  # type: ignore

DB = Path(__file__).parent / "bonfas.db"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(s: str) -> str:
    s = TAG.sub(" ", s or "")
    s = html.unescape(s)
    return WS.sub(" ", s).strip()


def parse_h3_atributos(titulo: str) -> list[str]:
    """De 'Força, Destreza ou Constituição' -> ['for','dex','con']."""
    if not titulo:
        return []
    if "qualquer atributo" in titulo.lower():
        return []
    out: list[str] = []
    for parte in re.split(r"[,]\s*|\s+ou\s+", titulo, flags=re.I):
        parte = parte.strip().lower()
        abv = ATRIBUTO_ABREV.get(parte)
        if abv:
            out.append(abv)
    return out


def extract_h5_talentos(secao_html: str, atributos_h3: list[str]) -> list[dict]:
    """Quebra a section H3 em talentos por <h5>."""
    out: list[dict] = []
    h5_matches = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", secao_html, re.I | re.S))
    for i, m in enumerate(h5_matches):
        nome = clean(m.group(1))
        if not nome or len(nome) > 120:
            continue
        start = m.end()
        end = h5_matches[i + 1].start() if i + 1 < len(h5_matches) else len(secao_html)
        body_html = secao_html[start:end]
        body_text = clean(body_html)

        # Procura linhas: "Etiqueta: <x>", "Tag: <csv>", "Pré Requisito: <texto>"
        etiqueta = ""
        tag_csv = ""
        prereq = ""
        m_eti = re.search(r"Etiqueta\s*:\s*([^\n.]{1,80})", body_text, re.I)
        if m_eti: etiqueta = m_eti.group(1).strip()
        m_tag = re.search(r"\bTags?\s*:\s*([^\n.]{1,200})", body_text, re.I)
        if m_tag: tag_csv = m_tag.group(1).strip()
        m_pre = re.search(r"Pr[ée]\s*-?\s*Requisitos?\s*:\s*([^\n]{1,300}?)(?=\s*(?:Aumento|Etiqueta|Descri[çc]|$))", body_text, re.I)
        if m_pre: prereq = m_pre.group(1).strip().rstrip(",.;")

        # nivel a partir do prereq (default 1)
        m_nv = re.search(r"N[íi]vel\s+(\d+)", prereq, re.I)
        nivel = int(m_nv.group(1)) if m_nv else 1

        # Descricao: tudo ou body limpo
        descricao = body_text[:5000]
        if not descricao:
            continue

        # Tags: etiqueta + tag csv + nv + extract_prereq_tags + atributos do H3 (fallback)
        tags: set[str] = set()
        if etiqueta:
            tags.add(slug(etiqueta))
        for t in re.split(r"[,;/]", tag_csv):
            s = slug(t.strip())
            if s:
                tags.add(s)
        tags.add(f"nv{nivel}")
        for t in extract_prereq_tags(prereq):
            tags.add(t)
        # H3 ancestor: se prereq não tem nenhuma tag de atributo, adiciona as do H3
        ja_tem_atr = any(t.startswith(("for", "dex", "con", "int", "sab", "car"))
                         and t[3:].isdigit() for t in tags)
        if not ja_tem_atr and atributos_h3:
            for atr in atributos_h3:
                tags.add(f"{atr}13")  # default 13+ (convenção PHB 2024 minimum)

        out.append({
            "nome": nome,
            "slug": slug(nome),
            "nivel_minimo": nivel,
            "etiqueta": etiqueta,
            "prereq": prereq,
            "descricao": descricao,
            "tags": sorted(tags),
        })
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"ERRO: {src} nao existe", file=sys.stderr)
        return 1

    data = parse(src)

    # Encontra a H2 "Talentos Gerais"
    secoes = data["secoes"]
    idx_inicio = None
    for i, s in enumerate(secoes):
        if s["nivel"] == 2 and slug(s["titulo"]) == "talentos-gerais":
            idx_inicio = i
            break
    if idx_inicio is None:
        print("ERRO: H2 'Talentos Gerais' nao encontrada", file=sys.stderr)
        return 1

    # As H3 que vem depois ate proxima H2 sao os grupos de atributo
    todos: list[dict] = []
    grupo_atual_atr: list[str] = []
    for s in secoes[idx_inicio + 1:]:
        if s["nivel"] == 2:
            break  # próxima H2 (footer/etc.)
        if s["nivel"] == 3:
            grupo_atual_atr = parse_h3_atributos(s["titulo"])
            secao_talentos = extract_h5_talentos(s["conteudo_html"], grupo_atual_atr)
            for t in secao_talentos:
                t["_h3_titulo"] = s["titulo"]
            todos.extend(secao_talentos)

    print(f"[1] Talentos Gerais extraidos do HTML: {len(todos)}")

    if not todos:
        return 0

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    inseridos = 0
    atualizados = 0
    seen: set[str] = set()
    for t in todos:
        if t["slug"] in seen:
            continue
        seen.add(t["slug"])
        cur.execute("SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (t["slug"],))
        existing = cur.fetchone()
        tags_json = json.dumps(t["tags"], ensure_ascii=False)
        if existing:
            id_opcao = existing[0]
            cur.execute(
                "UPDATE TB_OpcaoJogo SET Nome=?, Tipo=?, Descricao=?, TagsJSON=?, "
                "PreReqTexto=?, NivelMinimo=? WHERE Id_Opcao=?",
                (t["nome"], "talento-geral", t["descricao"], tags_json,
                 t["prereq"], t["nivel_minimo"], id_opcao),
            )
            atualizados += 1
        else:
            cur.execute(
                "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, TagsJSON, "
                "PreReqTexto, NivelMinimo, SourceURL) VALUES (?,?,?,?,?,?,?,?)",
                (t["nome"], t["slug"], "talento-geral", t["descricao"], tags_json,
                 t["prereq"], t["nivel_minimo"],
                 "Bonfire Tales — Talentos Gerais (todos talentos.html)"),
            )
            id_opcao = cur.lastrowid
            inseridos += 1
        cur.execute(
            "SELECT 1 FROM TB_AcessoOpcao "
            " WHERE Id_Opcao=? AND Id_Classe IS NULL AND Id_Subclasse IS NULL",
            (id_opcao,),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) "
                "VALUES (?, NULL, NULL)",
                (id_opcao,),
            )

    conn.commit()
    print(f"[2] inseridos={inseridos} atualizados={atualizados}")

    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-geral'")
    print(f"[3] DB total talento-geral: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-geral' AND TagsJSON LIKE '%for13%'")
    print(f"    com for13: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-geral' AND TagsJSON LIKE '%dex13%'")
    print(f"    com dex13: {cur.fetchone()[0]}")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
