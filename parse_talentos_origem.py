"""
Parser de Talentos de Origem do `_raw/processed/todos talentos.html`.

Cada talento e um <h5>Nome</h5> dentro da H2 'Talentos de Origem'.
Detecta automaticamente se o talento tem 'lista expandida' de magias
procurando por <table> com colunas que mencionam magia/circulo/nivel
DENTRO do bloco do talento (entre h5 atual e proximo h5).

Resultado:
- TB_OpcaoJogo Tipo='talento-origem' com Descricao + MagiaExpandidaJSON
- TB_AcessoOpcao universal (Id_Classe NULL, Id_Subclasse NULL)

Idempotente por slug.

Uso:
    python parse_talentos_origem.py "E:/Obsidian/_raw/processed/todos talentos.html"
"""
from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_artigo import parse  # type: ignore

DB = Path(__file__).parent / "bonfas.db"

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
TABLE_RE = re.compile(r"<table[^>]*>.*?</table>", re.I | re.S)


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def clean(s: str) -> str:
    """Strip HTML tags AND decode entities (&quot;, &amp;, &nbsp;, etc.)."""
    s = TAG.sub(" ", s or "")
    s = html.unescape(s)
    return WS.sub(" ", s).strip()


def extract_magia_expandida(body_html: str) -> list[dict]:
    """Procura tabelas dentro do body do talento e extrai magias.

    Estrategia: pega todas <table>. Cada linha (sem <th>) com 2+ celulas
    onde uma das celulas tem uma lista de magias (vargulas / nomes em italico ou
    seguidos de '[NomeIngles]'). Retorna lista plana de {nome, ingles, fonte_lista}.
    """
    out: list[dict] = []
    table_matches = list(re.finditer(r"<table[^>]*>(.*?)</table>", body_html, re.I | re.S))
    if not table_matches:
        return out

    for tbl_match in table_matches:
        tbl_html = tbl_match.group(1)
        # Header detection: pega th's da primeira <tr>
        header = None
        first_tr = re.search(r"<tr[^>]*>(.*?)</tr>", tbl_html, re.I | re.S)
        if first_tr:
            ths = re.findall(r"<th[^>]*>(.*?)</th>", first_tr.group(1), re.I | re.S)
            if ths:
                header = [clean(th) for th in ths]
        # Skip se nenhuma coluna mencionar magia/circulo/nivel
        if header and not any(re.search(r"magia|c[íi]rculo|n[íi]vel|truque|cantrip|spell",
                                         h, re.I) for h in header):
            continue

        # Para cada linha de dados
        for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", tbl_html, re.I | re.S):
            tr_html = tr.group(1)
            if re.search(r"<th\b", tr_html, re.I):
                continue
            cells = [clean(td.group(1)) for td in re.finditer(r"<td[^>]*>(.*?)</td>", tr_html, re.I | re.S)]
            if len(cells) < 2:
                continue
            # primeira celula: rotulo (Veste/Marca/Lista). demais celulas: magias
            label = cells[0]
            for cel in cells[1:]:
                if not cel or cel in ("-", "—", "N/A"):
                    continue
                # Quebra por virgula, ponto-e-virgula e " e "
                for raw in re.split(r"(?<!\()\s*[,;]\s*|\s+\bou\b\s+|\s+e\s+(?=[A-ZÁÉÍÓÚ])", cel):
                    raw = raw.strip(" .,;")
                    if not raw or len(raw) < 3:
                        continue
                    # Tenta extrair "Nome PT (Nome EN)" ou "Nome PT [Nome EN]"
                    m = re.match(r"^(.+?)\s*[\(\[]([^)\]]+)[\)\]]\s*$", raw)
                    if m:
                        nome_pt = m.group(1).strip()
                        nome_en = m.group(2).strip()
                    else:
                        nome_pt = raw
                        nome_en = None
                    out.append({
                        "nome": nome_pt[:120],
                        "nome_ingles": nome_en[:120] if nome_en else None,
                        "fonte_lista": label[:80] if label and len(label) <= 80 else None,
                    })
    return out


PROSE_PREPARED_RE = re.compile(
    r"sempre tem\s+([^()]{2,80}?)\s*\(\s*([^()]{2,60}?)\s*\)\s+preparada",
    re.I,
)
LEVEL_GATE_RE = re.compile(
    r"Ao alcan[çc]ar n[íi]vel de personagem\s+(\d+)",
    re.I,
)


def extract_prose_prepared(descricao_clean: str) -> list[dict]:
    """Detecta padroes 'sempre tem X (Y) preparada' na prosa.

    Retorna lista de {nome, nome_ingles, fonte_lista='auto-preparada',
                      nivel_personagem_min, auto_preparada=True}.
    nivel_personagem_min vem do gate 'Ao alcancar nivel de personagem N'
    mais proximo ANTES da menção da magia (default 1).
    """
    out: list[dict] = []
    # gates positions: list of (pos, n)
    gates = [(m.start(), int(m.group(1))) for m in LEVEL_GATE_RE.finditer(descricao_clean)]
    for m in PROSE_PREPARED_RE.finditer(descricao_clean):
        nome_pt = m.group(1).strip().rstrip(",.;")
        nome_en = m.group(2).strip().rstrip(",.;")
        if not nome_pt or len(nome_pt) > 80:
            continue
        # gate aplicavel: maior gate cuja pos < m.start()
        nivel_min = 1
        for pos, n in gates:
            if pos < m.start():
                nivel_min = n
        out.append({
            "nome": nome_pt,
            "nome_ingles": nome_en,
            "fonte_lista": "auto-preparada",
            "nivel_personagem_min": nivel_min,
            "auto_preparada": True,
        })
    return out


def parse_talentos_origem(html: str) -> list[dict]:
    """Quebra por <h5>Nome</h5> e extrai cada talento."""
    h5_matches = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", html, re.I | re.S))
    out: list[dict] = []
    for i, m in enumerate(h5_matches):
        nome = clean(m.group(1))
        if not nome or len(nome) > 120:
            continue
        start = m.end()
        end = h5_matches[i + 1].start() if i + 1 < len(h5_matches) else len(html)
        body_html = html[start:end]
        # extrai magias DA tabela primeiro (antes de remover ela do body)
        magia_exp = extract_magia_expandida(body_html)
        # Para a descricao: remove <table>...</table> blocks, ja que o conteudo
        # delas vai pra MagiaExpandida e nao deve duplicar no texto.
        body_no_tables = TABLE_RE.sub(" ", body_html)
        descricao = clean(body_no_tables)[:5000]
        if not descricao:
            continue
        # Extrai magias auto-preparadas da prosa (Curar Ferimentos preparada, etc.)
        prose_prep = extract_prose_prepared(descricao)
        # Mescla na lista de magias expandidas (formato unificado)
        magia_exp = magia_exp + prose_prep
        out.append({
            "nome": nome,
            "slug": slug(nome) + "-origem",
            "descricao": descricao,
            "magia_expandida": magia_exp,
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
    sec = next((s for s in data["secoes"] if s["titulo"] == "Talentos de Origem"), None)
    if not sec:
        print("ERRO: secao 'Talentos de Origem' nao encontrada", file=sys.stderr)
        return 1

    talentos = parse_talentos_origem(sec["conteudo_html"])
    print(f"[1] {len(talentos)} talentos de origem extraidos")

    com_lista = sum(1 for t in talentos if t["magia_expandida"])
    print(f"    com lista expandida: {com_lista}")
    print(f"    sem lista expandida: {len(talentos) - com_lista}")

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    inseridos = 0
    atualizados = 0
    for t in talentos:
        cur.execute("SELECT Id_Opcao FROM TB_OpcaoJogo WHERE Slug=?", (t["slug"],))
        existing = cur.fetchone()
        magia_json = json.dumps(t["magia_expandida"], ensure_ascii=False) if t["magia_expandida"] else None
        if existing:
            id_opcao = existing[0]
            cur.execute(
                "UPDATE TB_OpcaoJogo SET Nome=?, Tipo=?, Descricao=?, MagiaExpandidaJSON=?, "
                "SourceURL=? WHERE Id_Opcao=?",
                (t["nome"], "talento-origem", t["descricao"], magia_json,
                 "Bonfire Tales — Talentos de Origem (todos talentos.html)", id_opcao),
            )
            atualizados += 1
        else:
            cur.execute(
                "INSERT INTO TB_OpcaoJogo (Nome, Slug, Tipo, Descricao, MagiaExpandidaJSON, SourceURL) "
                "VALUES (?,?,?,?,?,?)",
                (t["nome"], t["slug"], "talento-origem", t["descricao"], magia_json,
                 "Bonfire Tales — Talentos de Origem (todos talentos.html)"),
            )
            id_opcao = cur.lastrowid
            inseridos += 1
        # acesso universal
        cur.execute(
            "SELECT 1 FROM TB_AcessoOpcao "
            " WHERE Id_Opcao=? AND Id_Classe IS NULL AND Id_Subclasse IS NULL",
            (id_opcao,),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO TB_AcessoOpcao (Id_Opcao, Id_Classe, Id_Subclasse) VALUES (?, NULL, NULL)",
                (id_opcao,),
            )

    conn.commit()
    print(f"[2] inseridos={inseridos} atualizados={atualizados}")

    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-origem'")
    total_origem = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo='talento-origem' AND MagiaExpandidaJSON IS NOT NULL")
    com_lista_db = cur.fetchone()[0]
    print(f"[3] DB final: {total_origem} talentos de origem, {com_lista_db} com lista expandida")

    print("\n[4] Sample com lista:")
    cur.execute(
        "SELECT Nome, MagiaExpandidaJSON FROM TB_OpcaoJogo "
        " WHERE Tipo='talento-origem' AND MagiaExpandidaJSON IS NOT NULL LIMIT 3"
    )
    for nome, mej in cur.fetchall():
        try:
            magias = json.loads(mej)
            print(f"  - {nome}: {len(magias)} magias")
            for m in magias[:5]:
                print(f"      * {m.get('nome')} [{m.get('nome_ingles') or '-'}] (fonte={m.get('fonte_lista')})")
        except json.JSONDecodeError:
            print(f"  - {nome}: invalid JSON")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
