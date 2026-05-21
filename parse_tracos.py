"""
Parser de Tracos Raciais (TB_TracoRacial) a partir de paginas/<raca>.html
e paginas/<essencia>.html.

Extrai:
- "Tracos da Raca Base" -> traits ligados a Id_Raca (sem linhagem nem essencia)
- Sections H4 de cada linhagem racial -> traits ligados a Id_Linhagem
- "Tracos da Essencia Base" / similar em essencia.html -> traits ligados a Id_Essencia

Cada trait = <h5>Nome</h5> + texto subsequente ate o proximo <h5> ou final.

Idempotente por raca/essencia (deleta os existentes antes de re-inserir).

Uso:
    python parse_tracos.py paginas/humano.html humano
    python parse_tracos.py paginas/infernal.html infernal
"""
from __future__ import annotations

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


TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def _txt(s: str) -> str:
    return WS.sub(" ", TAG.sub(" ", s or "")).strip()


def extract_h5_traits(secao_html: str) -> list[dict]:
    """Quebra um conteudo de secao em traits {nome, descricao} pelos <h5>."""
    out: list[dict] = []
    h5_matches = list(re.finditer(r"<h5[^>]*>(.*?)</h5>", secao_html, re.I | re.S))
    for i, m in enumerate(h5_matches):
        nome = _txt(m.group(1))
        if not nome or len(nome) > 120:
            continue
        start = m.end()
        end = h5_matches[i + 1].start() if i + 1 < len(h5_matches) else len(secao_html)
        bloco_html = secao_html[start:end]
        # Para no proximo <hr> ou inicio de outra secao se houver
        bloco_html = re.split(r"<hr\b", bloco_html, maxsplit=1, flags=re.I)[0]
        descricao = _txt(bloco_html)
        if descricao:
            out.append({"nome": nome, "descricao": descricao[:3000]})
    return out


def find_section_by_slug(data: dict, target_slug: str) -> dict | None:
    """Busca seção pelo slug (case + acento insensitivo)."""
    for s in data["secoes"]:
        if slug(s["titulo"]) == target_slug:
            return s
    return None


def find_section_starts_with(data: dict, prefix_slug: str) -> dict | None:
    for s in data["secoes"]:
        if slug(s["titulo"]).startswith(prefix_slug):
            return s
    return None


def populate_humano(file_path: Path) -> int:
    data = parse(file_path)
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    # mapping de linhagem por slug-prefix do titulo
    cur.execute("SELECT Id_Raca FROM TB_Raca WHERE Slug=?", ("humano",))
    row = cur.fetchone()
    if not row:
        print("ERRO: TB_Raca humano nao encontrada", file=sys.stderr)
        return 1
    id_raca = row[0]

    cur.execute("SELECT Id_Linhagem, Slug FROM TB_Linhagem WHERE Id_Raca=?", (id_raca,))
    linhagens = {r[1]: r[0] for r in cur.fetchall()}
    print(f"linhagens humanas no DB: {linhagens}")

    # Limpar tracos antigos do humano (raca + linhagens)
    cur.execute("DELETE FROM TB_TracoRacial WHERE Id_Raca=?", (id_raca,))
    print(f"[1] Apagados tracos antigos de humano")

    total = 0

    # 1) Traços da Raça Base
    sec_base = find_section_by_slug(data, "tracos-da-raca-base")
    if sec_base:
        traits = extract_h5_traits(sec_base["conteudo_html"])
        print(f"[2] Tracos da Raca Base: {len(traits)} traits")
        for t in traits:
            cur.execute(
                "INSERT INTO TB_TracoRacial (Id_Raca, Id_Linhagem, Id_Essencia, Nome, Descricao, NivelRequisito) "
                "VALUES (?, NULL, NULL, ?, ?, 1)",
                (id_raca, t["nome"][:150], t["descricao"]),
            )
            total += 1
            print(f"  + base: {t['nome']}")
    else:
        print("[2] WARN: Tracos da Raca Base nao encontrada")

    # 2) Linhagens (H4): match por slug-prefix do titulo
    for slug_lin, id_linhagem in linhagens.items():
        # ex: 'erthari-humanos-da-terra' -> prefix 'erthari'
        prefix = slug_lin.split("-")[0]
        sec = find_section_starts_with(data, prefix)
        if not sec:
            print(f"[3] WARN: section para linhagem {slug_lin} (prefix {prefix!r}) nao encontrada")
            continue
        traits = extract_h5_traits(sec["conteudo_html"])
        print(f"[3] Linhagem {sec['titulo']}: {len(traits)} traits")
        for t in traits:
            cur.execute(
                "INSERT INTO TB_TracoRacial (Id_Raca, Id_Linhagem, Id_Essencia, Nome, Descricao, NivelRequisito) "
                "VALUES (?, ?, NULL, ?, ?, 1)",
                (id_raca, id_linhagem, t["nome"][:150], t["descricao"]),
            )
            total += 1
            print(f"  + {sec['titulo']}: {t['nome']}")

    conn.commit()
    print(f"[4] Total inserido: {total}")
    conn.close()
    return 0


def populate_essencia(file_path: Path, slug_essencia: str = "essencia-infernal") -> int:
    """Para essencia, cada traço é um <h3> próprio (não <h5> como em raça base).
       Identifica H3 entre 'Poderes da Essencia' (intro) e 'Legado dos Circulos' (tabela)."""
    data = parse(file_path)
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    cur.execute("SELECT Id_Essencia FROM TB_Essencia WHERE Slug=?", (slug_essencia,))
    row = cur.fetchone()
    if not row:
        print(f"ERRO: TB_Essencia {slug_essencia} nao encontrada", file=sys.stderr)
        return 1
    id_essencia = row[0]

    cur.execute("DELETE FROM TB_TracoRacial WHERE Id_Essencia=? AND Id_EssLinhagem IS NULL",
                (id_essencia,))
    print(f"[1] Apagados tracos base antigos da essencia (preservando sub-linhagem)")

    # Procura H3 entre "Poderes da Essencia" (exclusivo) e o proximo H3 que seja
    # tabela de meta-info ("Legado dos Circulos", "Evolucao da Essencia")
    secoes = data["secoes"]
    start_idx = None
    end_idx = None
    for i, s in enumerate(secoes):
        if s["nivel"] == 3 and slug(s["titulo"]) == "poderes-da-essencia":
            start_idx = i + 1
        elif start_idx is not None and s["nivel"] == 3 and (
            "legado" in slug(s["titulo"]) or "evolucao" in slug(s["titulo"])
        ):
            end_idx = i
            break
    if start_idx is None:
        print("[2] WARN: nao encontrei 'Poderes da Essencia'. Secoes:")
        for s in secoes:
            print(f"   - H{s['nivel']} {s['titulo']}")
        conn.close()
        return 0
    if end_idx is None:
        end_idx = len(secoes)

    traits = []
    for s in secoes[start_idx:end_idx]:
        if s["nivel"] != 3:
            continue
        nome = s["titulo"].strip()
        if not nome or len(nome) > 120:
            continue
        descricao = WS.sub(" ", TAG.sub(" ", s["conteudo_html"])).strip()
        if descricao:
            traits.append({"nome": nome, "descricao": descricao[:3000]})

    print(f"[2] Tracos base da essencia ({slug_essencia}): {len(traits)} traits")
    total = 0
    for t in traits:
        cur.execute(
            "INSERT INTO TB_TracoRacial (Id_Raca, Id_Linhagem, Id_Essencia, Id_EssLinhagem, Nome, Descricao, NivelRequisito) "
            "VALUES (NULL, NULL, ?, NULL, ?, ?, 1)",
            (id_essencia, t["nome"][:150], t["descricao"]),
        )
        total += 1
        print(f"  + base essencia: {t['nome']}")

    conn.commit()
    print(f"[3] Total inserido: {total}")
    conn.close()
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    file_path = Path(sys.argv[1])
    fonte = sys.argv[2]
    if fonte == "humano":
        return populate_humano(file_path)
    elif fonte == "infernal":
        return populate_essencia(file_path, "essencia-infernal")
    else:
        print(f"fonte desconhecida: {fonte}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
