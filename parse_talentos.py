"""
Extrai talentos da seção 'Evolução Racial' / 'Evolução da Essência' dos
artigos de raça/essência salvos em paginas/. Popula TB_TalentoRacial 1:1.

Padrão esperado no texto:
   Nível X+
   <Nome do Talento>
   [Cadeia: <cadeia>]
   Pré-requisito: <texto>
   Efeito: <descrição longa>

Uso:
    python parse_talentos.py paginas/humano.html    humano
    python parse_talentos.py paginas/infernal.html  infernal
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

from parse_artigo import parse

DB = Path(__file__).parent / "bonfas.db"


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# regex auxiliares
RE_NIVEL = re.compile(r"N[íi]vel\s+(\d+)\+?\b", re.I)
RE_PREREQ = re.compile(r"Pr[ée]-requisito[s]?:\s*([^\n]+?)(?=\s+Efeito:|\s*$)", re.I)
RE_CADEIA = re.compile(r"Cadeia:\s*([^\n]+?)(?=\s+Pr[ée]-|\s+Efeito:|$)", re.I)
RE_EFEITO = re.compile(r"Efeito:\s*(.+?)(?=(?:Pr[ée]-requisito|N[íi]vel\s+\d+\+?|Cadeia:|$))", re.I | re.S)


def _parse_tags_from_prereq(texto: str, fonte_tag: str) -> list[str]:
    """De 'Humano (Erthari, Goruun)' → ['humano','erthari','goruun'].
       De 'Essência Infernal' → ['infernal'] (fonte já garante)."""
    t = texto.lower()
    tags = set([fonte_tag])   # sempre inclui a tag-fonte
    # encontra referência à própria fonte e extrai sub-tags entre parênteses
    m = re.search(r"(humano|essência\s+infernal|infernal)\s*(?:\(([^)]+)\))?", t)
    if m and m.group(2):
        for sub in re.split(r"[,;/]| ou ", m.group(2)):
            sub = slug(sub.strip())
            if sub:
                tags.add(sub)
    return sorted(tags)


TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
def _txt(s: str) -> str: return WS.sub(" ", TAG.sub(" ", s or "")).strip()


def extract_talentos(secao_html: str, fonte_tag: str) -> list[dict]:
    """Usa a estrutura HTML: <h5>Nome</h5> ... <b>Pré-requisito:</b> ... <b>Efeito:</b> ...
       Retorna lista de {nome, nivel, prereq, efeito, cadeia, tags}."""
    # encontra todos os <h5> de talento e o bloco que segue até próximo <h5> ou </section>
    talentos = []
    h5_matches = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", secao_html, re.I | re.S))
    for i, m in enumerate(h5_matches):
        nome = _txt(m.group(1))
        if not nome or len(nome) > 120:
            continue
        start = m.end()
        end = h5_matches[i+1].start() if i+1 < len(h5_matches) else len(secao_html)
        bloco_html = secao_html[start:end]
        bloco_txt = _txt(bloco_html)
        # extrai prereq (até aparecer "Efeito:" ou "Cadeia:") e efeito
        prereq_m = re.search(r"Pr[ée]-requisito[s]?:\s*(.+?)(?=\s*(?:Cadeia:|Efeito:|$))", bloco_txt, re.I | re.S)
        cadeia_m = re.search(r"Cadeia:\s*(.+?)(?=\s*(?:Pr[ée]-requisito|Efeito:|$))", bloco_txt, re.I | re.S)
        efeito_m = re.search(r"Efeito:\s*(.+)$", bloco_txt, re.I | re.S)
        if not prereq_m and not efeito_m:
            continue
        prereq_txt = (prereq_m.group(1).strip()[:400] if prereq_m else "")
        efeito_txt = (efeito_m.group(1).strip()[:4000] if efeito_m else "")
        # tira trailing "Requisito: próximo nome" caso tenha escapado
        efeito_txt = re.split(r"\s+Pr[ée]-requisito:", efeito_txt)[0]

        # nível: do prereq ("Nível 5+") se houver; senão 1
        nv_m = re.search(r"N[íi]vel\s+(\d+)", prereq_txt, re.I)
        nivel = int(nv_m.group(1)) if nv_m else 1

        tags = _parse_tags_from_prereq(prereq_txt, fonte_tag)
        talentos.append({
            "nome": nome,
            "nivel": nivel,
            "prereq": prereq_txt,
            "efeito": efeito_txt,
            "cadeia": (cadeia_m.group(1).strip()[:150] if cadeia_m else None),
            "tags": tags,
        })
    return talentos


def run(file_path: Path, fonte_tag: str):
    p = parse(file_path)
    sec_nome = "Evolução Racial" if fonte_tag == "humano" else "Evolução da Essência"
    secao = next((s for s in p["secoes"] if sec_nome.split()[0] in s["titulo"]), None)
    if not secao:
        sys.exit(f"Seção {sec_nome!r} não encontrada em {file_path}")

    talentos = extract_talentos(secao["conteudo_html"], fonte_tag)
    print(f"[{file_path.name}] {len(talentos)} talentos extraídos")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # apaga talentos anteriores dessa fonte
    cur.execute("DELETE FROM TB_TalentoRacial WHERE Fonte=?", (fonte_tag,))
    for t in talentos:
        try:
            cur.execute(
                """INSERT INTO TB_TalentoRacial
                       (Nome, Slug, TagsJSON, NivelMinimo, PreReqTexto, Cadeia, Descricao, Fonte)
                       VALUES (?,?,?,?,?,?,?,?)""",
                (t["nome"][:200], slug(t["nome"]),
                 json.dumps(t["tags"]), t["nivel"],
                 t["prereq"], t["cadeia"], t["efeito"], fonte_tag),
            )
        except sqlite3.IntegrityError as e:
            print(f"  ! ignorado (slug duplicado?) {t['nome']!r}: {e}")
    conn.commit()
    for r in cur.execute("SELECT Nome, NivelMinimo, TagsJSON FROM TB_TalentoRacial WHERE Fonte=? ORDER BY NivelMinimo", (fonte_tag,)):
        print(f"  nv{r[1]:2}  {r[0]:45}  tags={r[2]}")


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    run(Path(sys.argv[1]), sys.argv[2])


if __name__ == "__main__":
    main()
