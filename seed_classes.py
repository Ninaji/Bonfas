"""
Seed mínimo das 13 classes conhecidas do Bonfire Tales / D&D 5e.
Insere apenas Nome/Slug/Tagline para que o DB tenha conteúdo enquanto
o scraping completo não é executado.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "bonfas.db"

CLASSES = [
    ("Artífice",     "artifice",     "Mestre das maravilhas mágicas engenhosas."),
    ("Bárbaro",      "barbaro",      "Guerreiro feral impulsionado por fúria primordial."),
    ("Bardo",        "bardo",        "Inspira, encanta e lança feitiços através da arte."),
    ("Clérigo",      "clerigo",      "Devoto canalizador do poder divino."),
    ("Druida",       "druida",       "Guardião da natureza e da forma selvagem."),
    ("Feiticeiro",   "feiticeiro",   "Magia inata correndo em seu sangue."),
    ("Guerreiro",    "guerreiro",    "Mestre das armas e táticas marciais."),
    ("Ladino",       "ladino",       "Especialista ágil em furtividade e precisão."),
    ("Mago",         "mago",         "Estudioso arcano que domina o Weave por estudo."),
    ("Monge",        "monge",        "Disciplina marcial que canaliza o ki interior."),
    ("Paladino",     "paladino",     "Juramento sagrado e poder marcial abençoado."),
    ("Patrulheiro",  "patrulheiro",  "Caçador das terras selvagens, vínculos primais."),
    ("Bruxo",        "bruxo",        "Pacto com entidade extraplanar concede poder."),
]


def main() -> None:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for nome, slug, tag in CLASSES:
        cur.execute(
            """INSERT INTO TB_Classe (Nome, Slug, Tagline)
                   VALUES (?, ?, ?)
                 ON CONFLICT(Slug) DO UPDATE SET
                       Nome=excluded.Nome, Tagline=excluded.Tagline""",
            (nome, slug, tag),
        )
    conn.commit()
    print(f"OK classes={cur.execute('SELECT COUNT(*) FROM TB_Classe').fetchone()[0]}")


if __name__ == "__main__":
    main()
