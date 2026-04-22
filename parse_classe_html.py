"""
Parser HTML-based para artigo de classe (WorldAnvil).
Extrai TODAS as características principais + subclasses com suas habilidades 1:1.
Popula TB_ClasseHabilidade (apaga as anteriores dessa classe).

Padrão encontrado no HTML:
  <h2>Nome da Classe</h2>
  <h2>Características de Classe</h2>  ← marcador de início
  <h3>Nível X: Nome da Habilidade</h3>
  <p>descrição</p>...
  <h2>Nome da Subclasse</h2>         ← cada H2 posterior = subclasse
    <h3>Nível X: Nome</h3> ...

Uso:
    python parse_classe_html.py paginas/guerreiro.html guerreiro
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

from parse_artigo import parse, slug

DB = Path(__file__).parent / "bonfas.db"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

def clean(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s or "")).strip()


START_RE = re.compile(r"^(Habilidade|Caracter[íi]stica)s?\s+(de|do|da)\s+", re.I)
STAT_RE  = re.compile(r"^(STR|DEX|CON|INT|WIS|CHA|Ações|Ataques|Equipamento)$", re.I)
# Detecta se uma habilidade oferece ESCOLHA ao usuário
CHOICE_RE = re.compile(
    r"\b(escolha|selecione)\s+(um|uma|dois|duas|tr[êe]s|quatro)\b"
    r"|\bvoc[êe]\s+escolhe\b"
    r"|\bao\s+seu\s+crit[ée]rio\b"
    r"|\b(sua\s+escolha)\b",
    re.I,
)

# Spellcasting não gera submenu (já tem grid de magias)
SPELL_NAMES = {"Conjuração de Magias", "Conjuração", "Magia"}


def parse_classe(html: str) -> dict:
    """Extrai {nome, tagline, secoes_principais:[...], subclasses:[{nome, habs:[...]}]}
       usando o DOM HTML direto (não o texto limpo)."""
    # H1 ou primeiro H2 que bate com nome de classe (parse_artigo já detecta)
    m = re.search(r"<h2[^>]*>(Guerreiro|Bardo|B[áa]rbaro|Clérigo|Druida|Feiticeiro|Mago|Monge|Paladino|Ladino|Artificer|Art[íi]fice|Ca[çc]ador|M[íi]stico)</h2>", html, re.I)
    if not m:
        m2 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
        nome = clean(m2.group(1)) if m2 else None
    else:
        nome = clean(m.group(1))

    # Encontra TODOS os headings h2/h3/h4 e usa o texto entre cada um
    # e o próximo heading como corpo.
    headings = list(re.finditer(r"<(h2|h3|h4)[^>]*>(.*?)</\1>", html, re.I | re.S))

    started = False
    mode = None        # 'princ' | 'sub'
    current_sub = None
    principais = []
    subclasses = []

    for i, m in enumerate(headings):
        tag = m.group(1).lower()
        titulo = clean(m.group(2))
        start = m.end()
        end = headings[i+1].start() if i+1 < len(headings) else len(html)
        corpo_html = html[start:end]
        corpo_txt = clean(corpo_html)

        if tag == "h2":
            if not started:
                if START_RE.search(titulo):
                    started = True; mode = "princ"; current_sub = None
                continue
            if STAT_RE.match(titulo):
                break
            # outro "Habilidades/Características de X" = retorna para principal
            if START_RE.search(titulo):
                mode = "princ"; current_sub = None
                continue
            mode = "sub"
            current_sub = {"nome": titulo, "habs": []}
            subclasses.append(current_sub)
            continue

        if not started: continue
        if tag not in ("h3", "h4"): continue
        if STAT_RE.match(titulo): break

        # Extrai "Nível X: Nome"
        nm = re.match(r"^N[íi]vel\s+(\d+)\s*:\s*(.+)$", titulo, re.I)
        if nm:
            nivel_adq = int(nm.group(1))
            hab_nome = nm.group(2).strip()
        else:
            nivel_adq = 1
            hab_nome = titulo

        if not corpo_txt or len(hab_nome) < 2:
            continue

        tem_escolha = bool(CHOICE_RE.search(corpo_txt)) and hab_nome not in SPELL_NAMES
        rec = {
            "nome": hab_nome[:150],
            "nivel": nivel_adq,
            "descricao": corpo_txt[:5000],
            "tem_escolha": tem_escolha,
        }
        if mode == "princ":
            principais.append(rec)
        elif current_sub:
            current_sub["habs"].append(rec)

    return {"nome": nome, "principais": principais, "subclasses": subclasses}


def popular(classe_slug: str, dados: dict):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    id_classe = cur.execute("SELECT Id_Classe FROM TB_Classe WHERE Slug=?", (classe_slug,)).fetchone()
    if not id_classe:
        sys.exit(f"Classe com slug={classe_slug!r} não encontrada em TB_Classe")
    id_classe = id_classe[0]

    # apaga habilidades anteriores dessa classe
    cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=?", (id_classe,))

    for h in dados["principais"]:
        cur.execute(
            """INSERT INTO TB_ClasseHabilidade
                   (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem)
                   VALUES (?, NULL, ?, ?, ?, ?, 'classe')""",
            (id_classe, h["nome"], h["descricao"], h["nivel"], 1 if h["tem_escolha"] else 0),
        )

    # subclasses
    for sc in dados["subclasses"]:
        sc_slug = slug(sc["nome"])
        # encontra ou cria subclasse
        id_sub = cur.execute(
            "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
            (id_classe, sc_slug),
        ).fetchone()
        if id_sub:
            id_sub = id_sub[0]
        else:
            cur.execute(
                "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug) VALUES (?,?,?)",
                (id_classe, sc["nome"][:100], sc_slug[:100]),
            )
            id_sub = cur.lastrowid

        for h in sc["habs"]:
            cur.execute(
                """INSERT INTO TB_ClasseHabilidade
                       (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem)
                       VALUES (?, ?, ?, ?, ?, ?, 'subclasse')""",
                (id_classe, id_sub, h["nome"], h["descricao"], h["nivel"],
                 1 if h["tem_escolha"] else 0),
            )
    conn.commit()

    # relatório
    n_princ = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL", (id_classe,),
    ).fetchone()[0]
    n_sub = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NOT NULL", (id_classe,),
    ).fetchone()[0]
    n_esc = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND TemEscolha=1", (id_classe,),
    ).fetchone()[0]
    print(f"OK {dados['nome']}: {n_princ} principais + {n_sub} subclasses | {n_esc} com submenu de escolha")
    for sc in dados["subclasses"]:
        print(f"    - {sc['nome']}: {len(sc['habs'])} habilidades")


def main():
    if len(sys.argv) < 3:
        sys.exit("uso: python parse_classe_html.py <arquivo.html> <slug>")
    p = Path(sys.argv[1])
    from parse_artigo import unwrap_viewsource
    raw = p.read_text(encoding="utf-8", errors="ignore")
    html = unwrap_viewsource(raw)
    dados = parse_classe(html)
    popular(sys.argv[2], dados)


if __name__ == "__main__":
    main()
