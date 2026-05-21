"""Migration master: lê todos os JSONs em E:/Obsidian/_raw/parsed/ e faz UPSERT
idempotente em TB_Raca / TB_Linhagem / TB_Essencia / TB_EssenciaLinhagem / TB_TracoRacial.

Não toca raças/essências fora dos JSONs (Humano, Folken, Infernal ficam intactos).
Filtra TagsJSON contra whitelist canônica — tags inválidas vão pro Descricao só.
Heurística pós-processo adiciona prof:X quando descrição contém 'proficiência em X'.
"""
import json, re, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
PARSED = Path(r"E:\Obsidian\_raw\parsed")

# ---------- Whitelist de tags universais (regex) ----------
TAG_PATTERNS = [
    r"^\+atributo:(Forca|Destreza|Constituicao|Inteligencia|Sabedoria|Carisma)$",
    r"^resist:[\wÀ-ſ\-]+$",
    r"^imune:[\wÀ-ſ\-]+$",
    r"^cond-immune:[\wÀ-ſ\-]+$",
    r"^adv-cond:[\wÀ-ſ\-]+$",
    r"^velocidade:[\d\.\+]+m/[\d\+]+ft$",
    r"^visao-no-escuro:\d+m/\d+ft$",
    r"^\+idioma:[\wÀ-ſ\- ]+$",
    r"^prof:[\wÀ-ſ\- ]+$",
    r"^expertise:[\wÀ-ſ\- ]+$",
    r"^prof-arma:[\wÀ-ſ\- ]+$",
    r"^prof-armadura:[\wÀ-ſ\- ]+$",
    r"^pick:talento-origem:\d+$",
    r"^pick:pericia:[\wÀ-ſ\| ]+:\d+$",  # com filter alternativo via pipe
    r"^pick:pericia:\d+$",
]
TAG_WHITELIST = [re.compile(p) for p in TAG_PATTERNS]

# ---------- Normalização de tags (typos / acentos) ----------
TAG_FIX = {
    "resist:acido":           "resist:ácido",
    "resist:eletrico":        "resist:elétrico",
    "resist:trovao":          "resist:trovejante",
    "imune:envenenado":       "cond-immune:Envenenado",  # envenenado é condição, não tipo de dano
}

def normalize(tag: str) -> str:
    return TAG_FIX.get(tag, tag)

def is_valid(tag: str) -> bool:
    return any(p.match(tag) for p in TAG_WHITELIST)

# ---------- Heurística: detecta "proficiência em <Perícia>" no descricao e adiciona prof:X ----------
PERICIAS_PT = ["Acrobacia","Adestrar Animais","Arcanismo","Atletismo","Atuação","Enganação",
               "Furtividade","História","Intimidação","Intuição","Investigação","Lidar com Animais",
               "Medicina","Natureza","Percepção","Persuasão","Prestidigitação","Religião","Sobrevivência"]
PROF_RE = re.compile(r"proficiênc[ia]+\s+(?:n[ao]|em\s+a)?\s*(?:perícia\s+)?(" + "|".join(PERICIAS_PT) + r")", re.I)

def heuristic_prof(descricao: str, current_tags: list[str]) -> list[str]:
    extras = []
    for m in PROF_RE.finditer(descricao or ""):
        per = m.group(1).strip()
        # Normaliza primeira letra maiúscula (Atletismo, etc)
        per = per[0].upper() + per[1:]
        tag = f"prof:{per}"
        if tag not in current_tags and tag not in extras:
            extras.append(tag)
    return extras

# ---------- Filtro principal ----------
def clean_tags(raw: list[str], descricao: str = "") -> tuple[list[str], list[str]]:
    """Retorna (tags_aceitas, tags_rejeitadas)."""
    aceitas, rejeitadas = [], []
    for t in raw or []:
        n = normalize(t)
        if is_valid(n):
            if n not in aceitas:
                aceitas.append(n)
        else:
            rejeitadas.append(t)
    # Adiciona heurística prof:X
    for x in heuristic_prof(descricao, aceitas):
        if x not in aceitas:
            aceitas.append(x)
    return aceitas, rejeitadas

# ---------- DB helpers ----------
def upsert_raca(cur, j: dict) -> int:
    """Retorna Id_Raca."""
    slug = j["slug"]
    nome = j["nome"]
    tagline = j.get("tagline", "")[:250]
    lore = j.get("lore", {})
    tags_clean, _ = clean_tags(j.get("tags", []))
    row = cur.execute("SELECT Id_Raca FROM TB_Raca WHERE Slug=?", (slug,)).fetchone()
    if row:
        rid = row[0]
        cur.execute(
            "UPDATE TB_Raca SET Nome=?, Tagline=?, LorePresentation=?, LoreRoleplay=?, LoreSociety=?, "
            "TagsJSON=? WHERE Id_Raca=?",
            (nome, tagline, lore.get("presentation"), lore.get("roleplay"), lore.get("society"),
             json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None, rid),
        )
        return rid
    cur.execute(
        "INSERT INTO TB_Raca (Nome, Slug, Tagline, LorePresentation, LoreRoleplay, LoreSociety, "
        "PermiteEssencia, TagsJSON) VALUES (?,?,?,?,?,?,?,?)",
        (nome, slug, tagline, lore.get("presentation"), lore.get("roleplay"), lore.get("society"),
         1, json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None),
    )
    return cur.lastrowid

def upsert_linhagem(cur, raca_id: int, sl: dict) -> int:
    slug = sl["slug"]
    tags_clean, _ = clean_tags(sl.get("tags", []))
    row = cur.execute(
        "SELECT Id_Linhagem FROM TB_Linhagem WHERE Slug=? AND Id_Raca=?",
        (slug, raca_id),
    ).fetchone()
    if row:
        lid = row[0]
        cur.execute(
            "UPDATE TB_Linhagem SET Nome=?, Descricao=?, TagsJSON=? WHERE Id_Linhagem=?",
            (sl["nome"], sl.get("descricao"),
             json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None, lid),
        )
        return lid
    cur.execute(
        "INSERT INTO TB_Linhagem (Id_Raca, Nome, Slug, Descricao, TagsJSON) VALUES (?,?,?,?,?)",
        (raca_id, sl["nome"], slug, sl.get("descricao"),
         json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None),
    )
    return cur.lastrowid

def upsert_essencia(cur, j: dict) -> int:
    slug = j["slug"]
    nome = j["nome"]
    lore = j.get("lore", {})
    tags_clean, _ = clean_tags(j.get("tags", []))
    row = cur.execute("SELECT Id_Essencia FROM TB_Essencia WHERE Slug=?", (slug,)).fetchone()
    if row:
        eid = row[0]
        cur.execute(
            "UPDATE TB_Essencia SET Nome=?, LorePresentation=?, LoreRoleplay=?, LoreSociety=?, TagsJSON=? "
            "WHERE Id_Essencia=?",
            (nome, lore.get("presentation"), lore.get("roleplay"), lore.get("society"),
             json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None, eid),
        )
        return eid
    cur.execute(
        "INSERT INTO TB_Essencia (Nome, Slug, LorePresentation, LoreRoleplay, LoreSociety, TagsJSON) "
        "VALUES (?,?,?,?,?,?)",
        (nome, slug, lore.get("presentation"), lore.get("roleplay"), lore.get("society"),
         json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None),
    )
    return cur.lastrowid

def upsert_ess_lin(cur, ess_id: int, sl: dict) -> int:
    slug = sl["slug"]
    tags_clean, _ = clean_tags(sl.get("tags", []))
    row = cur.execute(
        "SELECT Id_EssLinhagem FROM TB_EssenciaLinhagem WHERE Slug=? AND Id_Essencia=?",
        (slug, ess_id),
    ).fetchone()
    if row:
        sid = row[0]
        cur.execute(
            "UPDATE TB_EssenciaLinhagem SET Nome=?, Descricao=?, TagsJSON=? WHERE Id_EssLinhagem=?",
            (sl["nome"], sl.get("descricao"),
             json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None, sid),
        )
        return sid
    cur.execute(
        "INSERT INTO TB_EssenciaLinhagem (Id_Essencia, Nome, Slug, Descricao, TagsJSON) VALUES (?,?,?,?,?)",
        (ess_id, sl["nome"], slug, sl.get("descricao"),
         json.dumps(tags_clean, ensure_ascii=False) if tags_clean else None),
    )
    return cur.lastrowid

def replace_tracos(cur, where_clause: str, where_args: tuple, tracos: list[dict],
                   raca_id=None, lin_id=None, ess_id=None, esslin_id=None) -> tuple[int, list[str]]:
    """Apaga traços antigos via where_clause + INSERT novos. Retorna (count, rejeitadas)."""
    cur.execute(f"DELETE FROM TB_TracoRacial WHERE {where_clause}", where_args)
    rejeitadas_total = []
    inseridos = 0
    for tr in tracos or []:
        tags_aceitas, tags_rej = clean_tags(tr.get("tags_sugeridas", []), tr.get("descricao", ""))
        rejeitadas_total.extend(f"{tr['nome']}::{x}" for x in tags_rej)
        cur.execute(
            "INSERT INTO TB_TracoRacial (Id_Raca, Id_Linhagem, Id_Essencia, Id_EssLinhagem, "
            "Nome, Descricao, NivelRequisito, TagsJSON) VALUES (?,?,?,?,?,?,?,?)",
            (raca_id, lin_id, ess_id, esslin_id,
             tr["nome"], tr.get("descricao"), 1,
             json.dumps(tags_aceitas, ensure_ascii=False) if tags_aceitas else None),
        )
        inseridos += 1
    return inseridos, rejeitadas_total

# ---------- Main ----------
def main():
    ts = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(DB, f"{DB}.bak.{ts}")
    print(f"Backup: {DB}.bak.{ts}\n")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rejeitadas_global: dict[str, list[str]] = {}
    stats: list[dict] = []

    arquivos = sorted(PARSED.glob("*.json"))
    for f in arquivos:
        j = json.loads(f.read_text(encoding="utf-8"))
        slug = j["slug"]; nome = j["nome"]; tipo = j["tipo"]
        rejs = []
        print(f"--- {slug} ({nome}) tipo={tipo} ---")

        if tipo == "raca":
            rid = upsert_raca(cur, j)
            n_base, rej_b = replace_tracos(
                cur, "Id_Raca=? AND Id_Linhagem IS NULL", (rid,),
                j.get("tracos_base", []), raca_id=rid,
            )
            rejs.extend(rej_b)
            n_lin = 0; n_lin_t = 0
            for sl in j.get("sublinhagens", []) or []:
                lid = upsert_linhagem(cur, rid, sl)
                n_lin += 1
                cnt, rej = replace_tracos(
                    cur, "Id_Linhagem=?", (lid,),
                    sl.get("tracos", []), raca_id=None, lin_id=lid,
                )
                n_lin_t += cnt
                rejs.extend(rej)
            print(f"   Id_Raca={rid}  base={n_base}  sublinhagens={n_lin}  traços-sub={n_lin_t}")
            stats.append({"slug": slug, "tipo": "raca", "id": rid, "base": n_base,
                          "sub": n_lin, "sub_t": n_lin_t, "rejeitadas": len(rejs)})

        elif tipo == "essencia":
            eid = upsert_essencia(cur, j)
            n_base, rej_b = replace_tracos(
                cur, "Id_Essencia=? AND Id_EssLinhagem IS NULL", (eid,),
                j.get("tracos_base", []), ess_id=eid,
            )
            rejs.extend(rej_b)
            n_sub = 0; n_sub_t = 0
            for sl in j.get("sublinhagens", []) or []:
                sid = upsert_ess_lin(cur, eid, sl)
                n_sub += 1
                cnt, rej = replace_tracos(
                    cur, "Id_EssLinhagem=?", (sid,),
                    sl.get("tracos", []), ess_id=None, esslin_id=sid,
                )
                n_sub_t += cnt
                rejs.extend(rej)
            print(f"   Id_Essencia={eid}  base={n_base}  sublinhagens={n_sub}  traços-sub={n_sub_t}")
            stats.append({"slug": slug, "tipo": "essencia", "id": eid, "base": n_base,
                          "sub": n_sub, "sub_t": n_sub_t, "rejeitadas": len(rejs)})

        if rejs:
            rejeitadas_global[slug] = rejs

    conn.commit()

    # Smoke test final
    print("\n=== Smoke test ===")
    print("Raças:")
    for r in cur.execute("SELECT Id_Raca, Nome FROM TB_Raca ORDER BY Id_Raca"):
        n_base = cur.execute(
            "SELECT COUNT(*) FROM TB_TracoRacial WHERE Id_Raca=? AND Id_Linhagem IS NULL", (r[0],)
        ).fetchone()[0]
        n_lin = cur.execute(
            "SELECT COUNT(*) FROM TB_Linhagem WHERE Id_Raca=?", (r[0],)
        ).fetchone()[0]
        print(f"  id={r[0]}  {r[1]:<20}  traços_base={n_base}  linhagens={n_lin}")

    print("Essências:")
    for r in cur.execute("SELECT Id_Essencia, Nome FROM TB_Essencia ORDER BY Id_Essencia"):
        n_base = cur.execute(
            "SELECT COUNT(*) FROM TB_TracoRacial WHERE Id_Essencia=? AND Id_EssLinhagem IS NULL", (r[0],)
        ).fetchone()[0]
        n_sub = cur.execute(
            "SELECT COUNT(*) FROM TB_EssenciaLinhagem WHERE Id_Essencia=?", (r[0],)
        ).fetchone()[0]
        print(f"  id={r[0]}  {r[1]:<25}  traços_base={n_base}  sub-linhagens={n_sub}")

    if rejeitadas_global:
        print("\n=== Tags rejeitadas (não casaram com whitelist canônica) ===")
        for slug, rejs in rejeitadas_global.items():
            print(f"  {slug}:")
            for r in rejs:
                print(f"    - {r}")

    conn.close()
    print("\nDONE.")

if __name__ == "__main__":
    main()
