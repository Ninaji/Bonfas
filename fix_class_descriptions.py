"""Limpa descriçoes de habilidades de classe que tem lixo de parser:
- 'Senhor da Guerra' (Nv 20 Guerreiro): trim no lixo do site (Metadados, JS, etc.)
- Habilidades de subclasse com leak: trim em nomes de subclasses adjacentes.
"""
import re
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"

# Markers que indicam inicio de lixo / conteudo de OUTRA seção.
# Trim a descrição no PRIMEIRO match.
LIXO_MARKERS = [
    r"\s*Site\s+projetado\s+pela\s+equipe",
    r"\s*Metadados\s+Article\s+template",
    r"\s*if\s*\(\s*\"\"",
    r"\s*var\s+find_article_url",
    r"\s*Hello!\s*$",
]

# Subclass names usadas como markers de leak (nome da próxima H4 vazou pro fim da hab).
SUBCLASS_NAMES = [
    "Atirador", "Campeão", "Campeao", "Cavaleiro Arcano", "Cavaleiro das Sombras",
    "Cavaleiro", "Comandante", "Guerreiro Psiônico", "Guerreiro Psionico",
    "Ronin", "Guerreiro Rúnico", "Guerreiro Runico",
]
# Markers regex finais (combina lixo + nome subclasse no fim)
ALL_PATTERNS = [re.compile(p, re.I) for p in LIXO_MARKERS] + [
    # nome de subclasse imediatamente antes do fim, com no max 5 chars apos (ex: ".", " ")
    re.compile(rf"\s+{re.escape(name)}\s*\.?\s*$", re.I) for name in SUBCLASS_NAMES
]


def cleanup(desc: str) -> str:
    if not desc:
        return desc
    out = desc
    # itera ate nao haver mais matches
    for _ in range(5):
        cut_at = len(out)
        for pat in ALL_PATTERNS:
            m = pat.search(out)
            if m and m.start() < cut_at:
                cut_at = m.start()
        if cut_at < len(out):
            out = out[:cut_at].rstrip()
        else:
            break
    return out


def main() -> int:
    conn = sqlite3.connect(str(DB))
    conn.text_factory = str
    cur = conn.cursor()

    cur.execute("SELECT Id_Habilidade, Nome, Descricao FROM TB_ClasseHabilidade")
    afetadas = []
    for hid, nome, desc in cur.fetchall():
        novo = cleanup(desc)
        if novo != desc:
            cut = len(desc) - len(novo)
            afetadas.append((hid, nome, len(desc), len(novo), cut))
            cur.execute("UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?", (novo, hid))

    conn.commit()
    print(f"Cleaned {len(afetadas)} habilidades:")
    for hid, nome, ant, novo, cut in afetadas:
        print(f"  id={hid:3} {nome[:40]:40} {ant} -> {novo} (cortou {cut} chars)")

    conn.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
