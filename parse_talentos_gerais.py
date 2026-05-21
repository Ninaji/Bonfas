"""
Parser de talentos gerais (nivel-based) a partir de _raw/talentos_nivel4.txt.

Formato esperado (por talento, separados por linha em branco):
    <Nome>

    Etiqueta: <categoria>
    Tag: <tags csv>

    Pre Requisito: <texto>
    Aumento de Atributo: <texto>

    Descricao:
    *<flavor italico>*

    <body com listas '- **<sub>**: ...'>


Popula TB_OpcaoJogo (Tipo='talento-geral') 1:1 com nomes da fonte.
Acesso: TB_AcessoOpcao (Id_Classe NULL, Id_Subclasse NULL) = universal.

Idempotente: detecta por Slug e atualiza/skipa.

Uso:
    python parse_talentos_gerais.py "E:/Obsidian/_raw/processed/talentos_nivel4.txt"
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# Mapeamento PT → abreviação canônica usada nas tags
ATRIBUTO_ABREV = {
    "forca": "for", "força": "for",
    "destreza": "dex",
    "constituicao": "con", "constituição": "con",
    "inteligencia": "int", "inteligência": "int",
    "sabedoria": "sab",
    "carisma": "car",
}


def extract_prereq_tags(prereq_text: str) -> list[str]:
    """Extrai tags de pré-requisito de uma linha tipo:
        'Nível 4+, Força 13+ ou Destreza 13+, Capacidade de Conjuração.'

    Retorna ex.: ['nv4', 'for13', 'dex13', 'conjuracao'].

    OBS sobre OR semantics: alternativas são listadas como tags separadas
    (ex.: 'for13' E 'dex13'). O subset filter atual NÃO impõe OR — quem usar
    como filtro precisa lembrar que prereq de atributo costuma ser OR.
    Tag começa com nome do atributo (3 letras) + número.
    """
    tags: list[str] = []
    if not prereq_text:
        return tags
    text_low = prereq_text.lower()
    # nível
    m_nv = re.search(r"n[íi]vel\s+(\d+)", text_low)
    if m_nv:
        tags.append(f"nv{m_nv.group(1)}")
    # atributos: <nome> <num>+
    pat_atr = re.compile(r"\b(forca|força|destreza|constituicao|constituição|inteligencia|inteligência|sabedoria|carisma)\s+(\d+)\+?", re.I)
    for m in pat_atr.finditer(text_low):
        atr = ATRIBUTO_ABREV.get(m.group(1).lower())
        if atr:
            tags.append(f"{atr}{m.group(2)}")
    # capacidade de conjuração / magia de pacto
    if re.search(r"\bcapacidade de conjura", text_low):
        tags.append("conjuracao")
    if re.search(r"\bmagia de pacto\b", text_low):
        tags.append("magia-de-pacto")
    if re.search(r"\bcentelha de fogo espiritual\b", text_low):
        tags.append("centelha-fogo-espiritual")
    # marcas, ordens, juramentos — extrai como sub-tags do tipo "iniciado-X"
    m_iniciado = re.search(r"iniciado\s+(?:no|na|do|da)\s+([a-zçãáéíóú\-\s]{3,80}?)(?=[\.,]|\s+ou\b|$)", text_low)
    if m_iniciado:
        tags.append("iniciado-" + slug(m_iniciado.group(1)))
    m_marca = re.search(r"\bmarca\s+([a-zçãáéíóú\-\s]{3,40}?)(?=[\.,]|\s+ou\b|$)", text_low)
    if m_marca:
        tags.append("marca-" + slug(m_marca.group(1)))
    # dedupe preservando ordem
    seen = set()
    out = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_talentos(content: str) -> list[dict]:
    """Quebra em blocos por dupla quebra de linha, extrai metadados."""
    talentos: list[dict] = []
    # split em blocos: 2+ newlines de espaco
    blocos = re.split(r"\n\s*\n\s*\n+", content.strip())
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        linhas = bloco.split("\n")
        if not linhas:
            continue

        nome = linhas[0].strip()
        if not nome or len(nome) > 120 or nome.startswith(("-", "*", "#", "{", "}")):
            continue

        etiqueta = ""
        tag_csv = ""
        prereq = ""
        atributo_bonus = ""
        descricao_lines: list[str] = []
        em_descricao = False

        for linha in linhas[1:]:
            l = linha.strip()
            low = l.lower()
            if low.startswith("etiqueta:"):
                etiqueta = l.split(":", 1)[1].strip()
            elif low.startswith("tag:") or low.startswith("tags:"):
                tag_csv = l.split(":", 1)[1].strip()
            elif "requisito" in low and ":" in l:
                prereq = l.split(":", 1)[1].strip()
            elif low.startswith("aumento de atributo:"):
                atributo_bonus = l.split(":", 1)[1].strip()
            elif low.startswith("descricao:") or low.startswith("descrição:"):
                em_descricao = True
            elif em_descricao:
                descricao_lines.append(linha)

        descricao = "\n".join(descricao_lines).strip()
        if not descricao or not etiqueta:
            # bloco nao parece ser um talento (pode ser intro do arquivo)
            continue

        # extrai nivel minimo do prereq ("Nivel 4+" -> 4)
        nv_m = re.search(r"N[íi]vel\s+(\d+)", prereq, re.I)
        nivel = int(nv_m.group(1)) if nv_m else 1

        # tags: combina etiqueta + tag-csv + pré-requisitos parseados
        tags: set[str] = set()
        if etiqueta:
            tags.add(slug(etiqueta))
        for t in re.split(r"[,;/]", tag_csv):
            s = slug(t.strip())
            if s:
                tags.add(s)
        if nivel:
            tags.add(f"nv{nivel}")
        # pré-requisito: nv + atributos + flags especiais
        for t in extract_prereq_tags(prereq):
            tags.add(t)

        talentos.append({
            "nome": nome,
            "slug": slug(nome),
            "nivel_minimo": nivel,
            "etiqueta": etiqueta,
            "tags": sorted(tags),
            "prereq": prereq,
            "atributo_bonus": atributo_bonus,
            "descricao": descricao,
        })

    return talentos


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"ERRO: {src} nao existe", file=sys.stderr)
        return 1

    content = src.read_text(encoding="utf-8")
    talentos = parse_talentos(content)
    print(f"[1] Parseados {len(talentos)} talentos de {src.name}")

    if not talentos:
        return 1

    # TagsJSON em TB_OpcaoJogo: precisa adicionar coluna se nao existir
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(TB_OpcaoJogo)")
    cols = [r[1] for r in cur.fetchall()]
    if "TagsJSON" not in cols:
        cur.execute("ALTER TABLE TB_OpcaoJogo ADD COLUMN TagsJSON TEXT NULL")
        print("  ALTER: TB_OpcaoJogo.TagsJSON adicionado")
    if "PreReqTexto" not in cols:
        cur.execute("ALTER TABLE TB_OpcaoJogo ADD COLUMN PreReqTexto VARCHAR(400) NULL")
        print("  ALTER: TB_OpcaoJogo.PreReqTexto adicionado")
    if "NivelMinimo" not in cols:
        cur.execute("ALTER TABLE TB_OpcaoJogo ADD COLUMN NivelMinimo INTEGER NULL")
        print("  ALTER: TB_OpcaoJogo.NivelMinimo adicionado")

    print("[2] Inserir/atualizar")
    inseridos = 0
    atualizados = 0
    duplicados_skipped = 0
    seen_slugs: set[str] = set()
    for t in talentos:
        if t["slug"] in seen_slugs:
            duplicados_skipped += 1
            continue
        seen_slugs.add(t["slug"])
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
                 "Bonfire Tales — Talentos Gerais (importado de _raw/talentos_nivel4.txt)"),
            )
            id_opcao = cur.lastrowid
            inseridos += 1

        # acesso universal (Id_Classe NULL, Id_Subclasse NULL)
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
    print(f"  inseridos: {inseridos}, atualizados: {atualizados}, slugs duplicados ignorados: {duplicados_skipped}")

    print("[3] Verificacao")
    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-geral'")
    print(f"  TB_OpcaoJogo talento-geral: {cur.fetchone()[0]}")
    cur.execute(
        "SELECT COUNT(*) FROM TB_AcessoOpcao a "
        "  JOIN TB_OpcaoJogo o ON o.Id_Opcao=a.Id_Opcao "
        " WHERE o.Tipo='talento-geral' AND a.Id_Classe IS NULL AND a.Id_Subclasse IS NULL"
    )
    print(f"  Acesso universal: {cur.fetchone()[0]}")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
