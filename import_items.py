"""
Importa items.csv (download do usuário) para TB_Item + TB_ItemSlot.
Uso: python import_items.py [caminho-do-csv]
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).parent / "bonfas.db"
DEFAULT_CSV = Path(r"C:\Users\brian\Downloads\items.csv")

# ---------------------------------------------------------------------------
# Mapeamento Slot CSV -> categoria canônica + slot-ficha + bag-secao
# ---------------------------------------------------------------------------
SLOT_CATALOG = [
    # (codigo, nome, slotFicha, bagSecao, [aliases-csv (lower)])
    ("weapon",    "Armas",                None,     "armas",       ["weapon"]),
    ("shield",    "Escudos",              None,     "armas",       ["shield"]),
    ("armor",     "Armaduras",            "corpo",  "armaduras",   ["armor"]),
    ("ring",      "Anéis",                "aneis",  "aneis_bag",   ["ring"]),
    ("head",      "Cabeça",               "cabeca", "cabeca_bag",  ["head"]),
    ("neck",      "Pescoço",              "pescoco","pescoco_bag", ["neck"]),
    ("back",      "Costas",               "costas", "costas_bag",  ["back"]),
    ("face",      "Rosto",                "rosto",  "rosto_bag",   ["face"]),
    ("arms",      "Braços",               "bracos", "bracos_bag",  ["arms/wrist", "arms", "wrist"]),
    ("feet",      "Pés",                  "pes",    "pes_bag",     ["feet"]),
    ("waist",     "Cintura",              "cintura","cintura_bag", ["waist"]),
    ("torso",     "Torso",                "torso",  "torso_bag",   ["torso-not-armor", "torso"]),
    ("gloves",    "Luvas",                "maos",   "maos_bag",    ["wearing_in_hands"]),
    ("held",      "Empunhado",            None,      None,         ["holding_in_hands"]),
    ("wand",      "Varinhas",             None,     "varinhas",    ["wand"]),
    ("rod",       "Cajados/Bastões",      None,     "varinhas",    ["rod"]),
    ("potion",    "Poções",               None,     None,          ["potion"]),
    ("scroll",    "Pergaminhos",          None,     None,          ["scroll"]),
    ("ammunition","Munição",              None,     "municao",     ["ammunition"]),
    ("tattoo",    "Tatuagens",            None,     None,          ["tattoo"]),
    ("hovering",  "Flutuando",            None,     "flutuando",   ["hovering_near_you"]),
    ("vehicle",   "Veículos",             None,     "veiculos",    ["vehicle"]),
    ("building",  "Edificações",          None,     "edificacao",  ["building"]),
    ("accessory", "Acessórios",           None,     "acessorios",  ["accessory"]),
    ("misc",      "Outros",               None,     None,          []),   # fallback
]

# alias-lower -> codigo
ALIAS2CODE = {
    a.lower(): row[0]
    for row in SLOT_CATALOG
    for a in row[4]
}


def slug(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "item"




def ensure_slots(conn: sqlite3.Connection) -> dict[str, int]:
    cur = conn.cursor()
    code2id: dict[str, int] = {}
    for code, nome, slot_ficha, bag_sec, _aliases in SLOT_CATALOG:
        cur.execute(
            """INSERT INTO TB_ItemSlot (Codigo, Nome, SlotFicha, BagSecao)
                   VALUES (?, ?, ?, ?)
               ON CONFLICT(Codigo) DO UPDATE SET
                   Nome=excluded.Nome, SlotFicha=excluded.SlotFicha, BagSecao=excluded.BagSecao""",
            (code, nome, slot_ficha, bag_sec),
        )
    for row in cur.execute("SELECT Id_Slot, Codigo FROM TB_ItemSlot"):
        code2id[row[1]] = row[0]
    conn.commit()
    return code2id


def import_csv(conn: sqlite3.Connection, csv_path: Path) -> tuple[int, int]:
    code2id = ensure_slots(conn)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        # indexes by header name
        def col(name: str) -> int:
            return header.index(name)
        I_NAME   = col("Name")
        I_SLOT   = col("Slot")
        I_SRC    = col("Source")
        I_PAGE   = col("Page")
        I_TYPE   = col("Type")
        I_ATT    = col("Attunement")
        I_DMG    = col("Damage")
        I_PROP   = col("Properties")
        I_MAST   = col("Mastery")
        I_WEIGHT = col("Weight")
        I_VALUE  = col("Value")
        I_TEXT   = col("Text")
        I_NOMET  = col("Nome-traduzido")
        I_EFEITO = col("Efeito Traduzido")

        rows: list[tuple] = []
        seen: set[str] = set()
        ok = skipped = 0
        for row in reader:
            if not row or len(row) <= I_NAME:
                continue
            name = (row[I_NAME] or "").strip()
            if not name:
                skipped += 1
                continue
            raw_slot = (row[I_SLOT] or "").strip().lower()
            code = ALIAS2CODE.get(raw_slot, "misc")
            id_slot = code2id.get(code)

            sl = slug(name)
            # desambigua slugs repetidos
            base_sl, i = sl, 2
            while sl in seen:
                sl = f"{base_sl}-{i}"; i += 1
            seen.add(sl)

            def g(i: int) -> str | None:
                if i >= len(row): return None
                v = (row[i] or "").strip()
                return v or None

            rows.append((
                id_slot,
                name,
                g(I_NOMET),
                sl,
                g(I_SRC), g(I_PAGE), g(I_TYPE), g(I_ATT), g(I_DMG),
                g(I_PROP), g(I_MAST), g(I_WEIGHT), g(I_VALUE),
                g(I_TEXT), g(I_EFEITO),
            ))
            ok += 1

    cur = conn.cursor()
    cur.execute("DELETE FROM TB_Item")  # reimporta do zero
    cur.executemany(
        """INSERT INTO TB_Item
           (Id_Slot, Nome, NomeTraduzido, Slug, Source, Page, Tipo,
            Attunement, Damage, Properties, Mastery, Weight, Value,
            Texto, EfeitoTraduzido)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    return ok, skipped


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not csv_path.exists():
        sys.exit(f"CSV não encontrado: {csv_path}")
    if not DB_PATH.exists():
        sys.exit("bonfas.db não existe — rode `python init_db.py` primeiro.")

    conn = sqlite3.connect(DB_PATH)
    try:
        ok, skipped = import_csv(conn, csv_path)
        total = conn.execute("SELECT COUNT(*) FROM TB_Item").fetchone()[0]
        by_slot = conn.execute(
            """SELECT s.Codigo, s.Nome, COUNT(i.Id_Item)
                 FROM TB_ItemSlot s LEFT JOIN TB_Item i ON i.Id_Slot = s.Id_Slot
                 GROUP BY s.Id_Slot ORDER BY 3 DESC"""
        ).fetchall()
        print(f"OK  importados={ok}  skipped={skipped}  total={total}")
        for c, n, k in by_slot:
            print(f"   {c:12} {n:22} -> {k}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
