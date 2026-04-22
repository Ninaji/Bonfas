"""
Popula TB_Classe/Subclasse/RecursoClasse/ClasseHabilidade a partir do JSON
exportado do localStorage pelo extrator rodado na extensão Chrome.

Formato esperado (bonfas_classes.json):
[
  {
    "classe": "Bardo",
    "url": "https://...",
    "tagline": "...",
    "progressao": [ { "nivel": 1, "Proficiência": "+2", ... }, ... ],
    "habilidades_principais": [
       { "nome": "Inspiração Bárdica", "nivel": 1, "descricao": "..." },
       ...
    ],
    "subclasses": [
       { "nome": "Colégio do Conselho", "habilidades": [ {nome,nivel,descricao}, ... ] },
       ...
    ]
  },
  ...
]
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"
JSON_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "bonfas_classes.json"

# colunas da tabela de progressão que são contadas como "recurso nomeado"
# (as demais viram "valor"): tudo que não for nivel vira TB_RecursoClasse
STAT_COLS = ("Nível", "nivel")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "item"


def ingest() -> None:
    data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    total_classes = 0
    total_subs = 0
    total_recursos = 0
    total_habs = 0

    # nomes que caíram como None no extractor → mapeados pelo URL
    URL_FALLBACK = {
        "barbaro":     "Bárbaro",
        "guerreiro":   "Guerreiro",
        "ladino":      "Ladino",
        "artificer":   "Artífice",     # normaliza ao PT
        "bardo":       "Bardo",
        "cacador":     "Caçador",
        "clerigo":     "Clérigo",
        "druida":      "Druida",
        "feiticeiro":  "Feiticeiro",
        "mago":        "Mago",
        "mistico":     "Místico",
        "monge":       "Monge",
        "paladino":    "Paladino",
        "patrulheiro": "Patrulheiro",
    }

    for c in data:
        nome = c.get("classe")
        url = c.get("url") or ""
        if not nome:
            m = re.search(r"/a/([a-z0-9\-]+)-article", url)
            if m:
                nome = URL_FALLBACK.get(m.group(1), m.group(1).capitalize())
        # normaliza para PT quando o scrape trouxe variante EN
        if url:
            m = re.search(r"/a/([a-z0-9\-]+)-article", url)
            if m and m.group(1) in URL_FALLBACK:
                nome = URL_FALLBACK[m.group(1)]
        if not nome:
            continue
        cl_slug = slug(nome)
        cur.execute(
            """INSERT INTO TB_Classe (Nome, Slug, Tagline, SourceURL)
                   VALUES (?, ?, ?, ?)
                 ON CONFLICT(Slug) DO UPDATE SET
                       Nome=excluded.Nome, Tagline=excluded.Tagline,
                       SourceURL=excluded.SourceURL
               RETURNING Id_Classe""",
            (nome, cl_slug, (c.get("tagline") or "")[:255], c.get("url")),
        )
        id_classe = cur.fetchone()[0]
        total_classes += 1

        # recursos da tabela de progressão (todas as colunas != nivel)
        cur.execute("DELETE FROM TB_RecursoClasse WHERE Id_Classe=?", (id_classe,))
        for row in c.get("progressao", []):
            nivel = row.get("nivel") or 0
            for k, v in row.items():
                if k in STAT_COLS or not v or v in ("-", "—"):
                    continue
                cur.execute(
                    """INSERT INTO TB_RecursoClasse
                           (Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor)
                           VALUES (?, NULL, ?, ?, ?, ?)""",
                    (id_classe, k[:100], slug(k)[:100], nivel, str(v)[:50]),
                )
                total_recursos += 1

        # habilidades principais (Id_Subclasse IS NULL)
        cur.execute(
            "DELETE FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL",
            (id_classe,),
        )
        for h in c.get("habilidades_principais", []):
            cur.execute(
                """INSERT INTO TB_ClasseHabilidade
                       (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido)
                       VALUES (?, NULL, ?, ?, ?)""",
                (id_classe, (h.get("nome") or "?")[:150],
                 h.get("descricao") or "",
                 int(h.get("nivel") or 1)),
            )
            total_habs += 1

        # subclasses
        for sc in c.get("subclasses", []):
            sc_nome = sc.get("nome")
            if not sc_nome:
                continue
            sc_slug = slug(sc_nome)
            cur.execute(
                """INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, SourceURL)
                       VALUES (?, ?, ?, ?)
                     ON CONFLICT(Id_Classe, Slug) DO UPDATE SET
                           Nome=excluded.Nome, SourceURL=excluded.SourceURL
                   RETURNING Id_Subclasse""",
                (id_classe, sc_nome, sc_slug, c.get("url")),
            )
            id_sub = cur.fetchone()[0]
            total_subs += 1

            # habilidades da subclasse
            cur.execute(
                "DELETE FROM TB_ClasseHabilidade WHERE Id_Subclasse=?", (id_sub,),
            )
            for h in sc.get("habilidades", []):
                cur.execute(
                    """INSERT INTO TB_ClasseHabilidade
                           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido)
                           VALUES (?, ?, ?, ?, ?)""",
                    (id_classe, id_sub, (h.get("nome") or "?")[:150],
                     h.get("descricao") or "",
                     int(h.get("nivel") or 1)),
                )
                total_habs += 1

    conn.commit()
    conn.close()
    print(f"OK classes={total_classes}  subclasses={total_subs}  "
          f"recursos={total_recursos}  habilidades={total_habs}")


if __name__ == "__main__":
    ingest()
