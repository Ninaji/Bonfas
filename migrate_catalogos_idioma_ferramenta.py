"""Popula TB_OpcaoJogo com catálogos de Idioma e Ferramenta (D&D 5.5e BR + Bonfire).
Substitui os arrays hardcoded em ficha.js — agora é fonte única no DB."""
import shutil, sqlite3, time

DB = "bonfas.db"
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

IDIOMAS = [
    # exclui "Comum" — default automático, não pickável
    "Anão", "Drácônico", "Élfico", "Gigante", "Goblin", "Halfling",
    "Infernal", "Orc", "Profundo", "Silvestre", "Sub-Comum",
    "Celestial", "Ínferi", "Aquático", "Druídico", "Cant Ladino",
    "Ônceros",
]

FERRAMENTAS = [
    # Kits de artesão (PHB 2024)
    "Kit de Alquimista", "Kit de Caligrafista", "Kit de Carpinteiro",
    "Kit de Cartógrafo", "Kit de Cervejaria", "Kit de Cobrador",
    "Kit de Couro", "Kit de Cozinheiro", "Kit de Disfarce",
    "Kit de Envenenador", "Kit de Falsificador", "Kit de Ferreiro",
    "Kit de Herbalismo", "Kit de Joalheiro", "Kit de Ladrão",
    "Kit de Marceneiro", "Kit de Navegação", "Kit de Olaria",
    "Kit de Pedreiro", "Kit de Pintor", "Kit de Tecelão",
    "Kit de Vidreiro", "Kit de Vinicultor",
    # Instrumentos musicais
    "Alaúde", "Cítara", "Flauta", "Flauta de Pã", "Gaita-de-foles",
    "Lira", "Tambor", "Viola", "Trompa", "Pan-flauta",
    # Jogos
    "Conjunto de Dados", "Conjunto de Cartas", "Conjunto de Xadrez",
    # Veículos
    "Veículos Terrestres", "Veículos Aquáticos", "Veículos Aéreos",
]


def slugify(s: str) -> str:
    repl = {"á":"a","à":"a","â":"a","ã":"a","ä":"a","é":"e","è":"e","ê":"e","ë":"e",
            "í":"i","ì":"i","î":"i","ï":"i","ó":"o","ò":"o","ô":"o","õ":"o","ö":"o",
            "ú":"u","ù":"u","û":"u","ü":"u","ç":"c"}
    out = s.lower()
    for k,v in repl.items(): out = out.replace(k, v)
    import re
    return re.sub(r"[^a-z0-9]+", "-", out).strip("-")


conn = sqlite3.connect(DB)
cur = conn.cursor()


def upsert_opcao(tipo: str, nome: str) -> str:
    slug = slugify(nome)
    if cur.execute("SELECT 1 FROM TB_OpcaoJogo WHERE Tipo=? AND Slug=?", (tipo, slug)).fetchone():
        return "skip"
    cur.execute(
        "INSERT INTO TB_OpcaoJogo (Tipo, Nome, Slug, Descricao, TagsJSON) VALUES (?,?,?,NULL,NULL)",
        (tipo, nome, slug),
    )
    return "ins"


for nome in IDIOMAS:
    res = upsert_opcao("idioma", nome)
    print(f"  idioma  [{res}]  {nome}")

print()
for nome in FERRAMENTAS:
    res = upsert_opcao("ferramenta", nome)
    print(f"  ferr    [{res}]  {nome}")

conn.commit()
print("\n=== STATS ===")
for tipo in ("idioma", "ferramenta"):
    n = cur.execute("SELECT COUNT(*) FROM TB_OpcaoJogo WHERE Tipo=?", (tipo,)).fetchone()[0]
    print(f"  Tipo='{tipo}': {n} entries")
conn.close()
print("\nDONE.")
