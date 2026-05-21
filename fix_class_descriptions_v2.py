"""Limpa descricoes de TB_ClasseHabilidade:
1. Decode HTML entities (&quot; → ", &nbsp; → espaço, etc.)
2. Reformata tabelas de progressao inline em HTML real.

A tabela de progressão do Cavaleiro Arcano vem como string achatada:
'Nível Truques Magias Preparadas 1º 2º 3º 4º 3 2 3 2 - - - 4 2 5 3 - - - ...'
Reformata para <table><tr><td>...</td></tr></table>.
"""
import html
import re
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"


def reformat_progression_table(desc: str) -> str:
    """Detecta tabela de progressao 'Nível Truques [colunas] N N N ...' e converte pra HTML."""
    # Pattern do header: "Nível ... 1º 2º [3º] [4º] [...]"
    m = re.search(
        r"(N[íi]vel(?:\s+\w[\wçãáéíóú]*)+?\s+1º(?:\s+\d+º)*)\s+(\d.+?)\s*$",
        desc,
        re.S,
    )
    if not m:
        return desc

    header_str = m.group(1)
    rows_str = m.group(2).strip()

    # Header: split by spaces but agrupar "Magias Preparadas" como 1 coluna
    # Heuristica: tokens que NÃO começam com dígito + º são parte do header anterior
    # Mais simples: assumir colunas conhecidas para Cavaleiro Arcano
    # ['Nível', 'Truques', 'Magias Preparadas', '1º', '2º', '3º', '4º']
    # Detecta numero de colunas '<n>º' no header
    cycle_cols = re.findall(r"\d+º", header_str)
    n_cycle = len(cycle_cols)
    # Outros: 'Nível' + 'Truques' + 'Magias Preparadas' = 3 fixos pre-cycle
    n_fixed = 3
    n_total = n_fixed + n_cycle
    headers = ["Nível", "Truques", "Magias Preparadas"] + cycle_cols

    # rows_str: tokens espaçados. n_total por linha.
    tokens = re.split(r"\s+", rows_str)
    # filtra '&nbsp;' residual e similares
    tokens = [t for t in tokens if t and t != "&nbsp;"]
    if len(tokens) % n_total != 0:
        # falha — abort, retorna original
        return desc
    rows = []
    for i in range(0, len(tokens), n_total):
        rows.append(tokens[i:i + n_total])

    # monta HTML
    table_html = '<table class="progression-table"><thead><tr>'
    for h in headers:
        table_html += f"<th>{h}</th>"
    table_html += "</tr></thead><tbody>"
    for row in rows:
        table_html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    table_html += "</tbody></table>"

    # Substitui no desc
    return desc[:m.start()] + table_html


def main() -> int:
    conn = sqlite3.connect(str(DB))
    conn.text_factory = str
    cur = conn.cursor()

    cur.execute("SELECT Id_Habilidade, Descricao FROM TB_ClasseHabilidade WHERE Descricao IS NOT NULL")
    cleaned = 0
    tabled = 0
    for hid, desc in cur.fetchall():
        novo = html.unescape(desc or "")
        # Reformata progressao SE tem 'Nível ... 1º' inline
        if re.search(r"N[íi]vel\s+\w+(?:\s+\w[\wçãáéíóú]*)*\s+1º", novo):
            antes = novo
            novo = reformat_progression_table(novo)
            if novo != antes:
                tabled += 1

        if novo != desc:
            cur.execute("UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?", (novo, hid))
            cleaned += 1

    conn.commit()
    print(f"Cleaned {cleaned} descriçoes (decode entities + table format)")
    print(f"Reformatted {tabled} tabelas de progressao inline")
    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
