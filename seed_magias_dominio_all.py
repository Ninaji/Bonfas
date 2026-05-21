"""Popula MagiaExpandidaJSON em TODAS as subclasses do Paladino e Clérigo,
parseando paginas/paladino.txt (markdown table) e paginas/clerigo.txt (text).

Convenção de tier→nivel_da_magia:
  PALADINO (5 tiers, 2 spells cada): 3°→1, 5°→2, 9°→3, 13°→4, 17°→5
  CLÉRIGO (4 tiers, 4/2/2/2 spells):
    3°: 4 spells → primeiros 2 são lvl 1, últimos 2 lvl 2
    5°: 2 spells lvl 3
    7°: 2 spells lvl 4
    9°: 2 spells lvl 5

A regra Bonfire (`para as duas classes somado`) usa nivel_personagem_min
contra nivel_total. Como o user pediu pra REMOVER o lock, deixo
nivel_personagem_min=1 (ignorado pela UI).

Idempotente: re-roda sempre o mesmo resultado.
"""
import json
import re
import shutil
import sqlite3
import time
from pathlib import Path

DB = 'bonfas.db'
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def split_spell_token(s: str) -> tuple[str, str | None]:
    """'Raio Guiador (Guiding Bolt)' → ('Raio Guiador', 'Guiding Bolt').
    'Escudo da Fé' → ('Escudo da Fé', None)."""
    s = s.strip()
    m = re.match(r'^(.+?)\s*\((.+?)\)\s*$', s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, None


# ============================================================
# PALADINO — paladino.txt usa markdown table
# ============================================================
PAL_TIER_TO_LVL = {3: 1, 5: 2, 9: 3, 13: 4, 17: 5}
# Para Paladino, cada tier corresponde a um único spell level
PAL_LVL_TO_TIER = {v: k for k, v in PAL_TIER_TO_LVL.items()}


def parse_paladino_subclass_blocks(text: str) -> dict[str, list[dict]]:
    """Iterativo line-based — encontra '**Magias de Domínio (Nome):**' e
    coleta as rows do markdown table até linha vazia ou outro header."""
    lines = text.splitlines()
    result: dict[str, list[dict]] = {}
    sub_re = re.compile(r'\*\*Magias de Domínio \(([^)]+)\):?\*\*')
    row_re = re.compile(r'^\|\s*(\d+)º\s*\|\s*(.+?)\s*\|\s*$')
    i = 0
    while i < len(lines):
        m = sub_re.search(lines[i])
        if not m:
            i += 1
            continue
        nome = m.group(1).strip()
        magias = []
        # Procura table rows nas próximas 30 linhas
        for j in range(i+1, min(i+30, len(lines))):
            ln = lines[j].rstrip()
            if ln.startswith('---') or ln.startswith('Nome:') or ln.startswith('**'):
                break
            mr = row_re.match(ln)
            if not mr:
                continue
            tier = int(mr.group(1))
            spell_lvl = PAL_TIER_TO_LVL.get(tier)
            if spell_lvl is None:
                continue
            for token in mr.group(2).split(','):
                pt, en = split_spell_token(token)
                if not pt:
                    continue
                magias.append({
                    "nome": pt,
                    "nome_ingles": en,
                    "fonte_lista": str(spell_lvl),
                    "auto_preparada": True,
                    "nivel_personagem_min": 1,
                    "tier_unlock": tier,  # nivel da CLASSE em que ficou disponível
                })
        if magias:
            result[nome] = magias
        i += 1
    return result


# ============================================================
# CLÉRIGO — clerigo.txt extraído de HTML, formato livre
# ============================================================
CLE_TIER_LVL_MAP = {
    3: [1, 1, 2, 2],   # 4 spells: primeiros 2 lvl 1, últimos 2 lvl 2
    5: [3, 3],
    7: [4, 4],
    9: [5, 5],
}


def parse_clerigo_subclass_blocks(text: str) -> dict[str, list[dict]]:
    """Detecta seções 'Magias de Domínio' e associa à subclasse anterior
    pelo header (linha sozinha tipo ' Caos', ' Guerra', etc.)."""
    lines = text.splitlines()
    # Find subclass headers (single word PT, after small whitespace)
    sub_re = re.compile(r'^\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)\s*$')
    md_pat = re.compile(r'^\s*Magias de Domínio\s*$')
    result: dict[str, list[dict]] = {}
    last_sub = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        # Detecta header de subclasse
        m_sub = sub_re.match(ln)
        if m_sub and m_sub.group(1) in (
            'Arcano', 'Caos', 'Escuridão', 'Guerra', 'Luz', 'Morte',
            'Natureza', 'Ordem', 'Paz', 'Tempestade', 'Trapaça', 'Vida',
        ):
            last_sub = m_sub.group(1)
            i += 1
            continue
        # Detecta "Magias de Domínio" header
        if md_pat.match(ln) and last_sub:
            # Pula linhas em branco e "Nível de ClérigoMagias"
            j = i + 1
            magias = []
            while j < len(lines) and j - i < 15:
                row = lines[j].strip()
                if not row or row.startswith('Nível de'):
                    j += 1
                    continue
                m_tier = re.match(r'^(\d+)º\s*(.+)$', row)
                if m_tier:
                    tier = int(m_tier.group(1))
                    spell_text = m_tier.group(2)
                    lvl_map = CLE_TIER_LVL_MAP.get(tier, [])
                    tokens = [t for t in spell_text.split(',') if t.strip()]
                    for idx, token in enumerate(tokens):
                        pt, en = split_spell_token(token)
                        if not pt:
                            continue
                        spell_lvl = lvl_map[idx] if idx < len(lvl_map) else lvl_map[-1] if lvl_map else 1
                        magias.append({
                            "nome": pt,
                            "nome_ingles": en,
                            "fonte_lista": str(spell_lvl),
                            "auto_preparada": True,
                            "nivel_personagem_min": 1,
                            "tier_unlock": tier,  # nivel do Clérigo em que ficou disponível
                        })
                else:
                    break  # fim do bloco
                j += 1
            if magias:
                result[last_sub] = magias
            i = j
            continue
        i += 1
    return result


# ============================================================
# Aplica
# ============================================================
pal_text = Path('paginas/paladino.txt').read_text(encoding='utf-8')
cle_text = Path('paginas/clerigo.txt').read_text(encoding='utf-8')

pal_data = parse_paladino_subclass_blocks(pal_text)
cle_data = parse_clerigo_subclass_blocks(cle_text)

print(f'\n=== Paladino: {len(pal_data)} subclasses parseadas ===')
for nome, mags in pal_data.items():
    print(f'  {nome}: {len(mags)} magias')

print(f'\n=== Clérigo: {len(cle_data)} subclasses parseadas ===')
for nome, mags in cle_data.items():
    print(f'  {nome}: {len(mags)} magias')


# Helper: encontra Id_Subclasse pelo nome (tolerante a variações)
def find_sub(id_classe: int, nome_parsed: str) -> int | None:
    # Paladino: nomes diretos (Conquista, Coroa, Devoção, ...)
    # Clérigo: nomes com prefixo "Domínio da/do X"
    # Tenta exact, depois LIKE
    r = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Nome=?",
        (id_classe, nome_parsed),
    ).fetchone()
    if r:
        return r['Id_Subclasse']
    r = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Nome LIKE ?",
        (id_classe, f'%{nome_parsed}%'),
    ).fetchone()
    return r['Id_Subclasse'] if r else None


print('\n=== Aplicando UPDATE em TB_Subclasse ===')
total_p, total_c = 0, 0
for nome, mags in pal_data.items():
    sub_id = find_sub(13, nome)
    if not sub_id:
        print(f'  ⚠ Paladino "{nome}" — subclasse não encontrada no DB')
        continue
    cur.execute(
        "UPDATE TB_Subclasse SET MagiaExpandidaJSON=? WHERE Id_Subclasse=?",
        (json.dumps(mags, ensure_ascii=False), sub_id),
    )
    print(f'  Paladino "{nome}" (Id {sub_id}): {len(mags)} magias')
    total_p += len(mags)

for nome, mags in cle_data.items():
    sub_id = find_sub(5, nome)
    if not sub_id:
        print(f'  ⚠ Clérigo "{nome}" — subclasse não encontrada no DB')
        continue
    cur.execute(
        "UPDATE TB_Subclasse SET MagiaExpandidaJSON=? WHERE Id_Subclasse=?",
        (json.dumps(mags, ensure_ascii=False), sub_id),
    )
    print(f'  Clérigo "{nome}" (Id {sub_id}): {len(mags)} magias')
    total_c += len(mags)

conn.commit()
conn.close()
print(f'\nTotal: {total_p} magias Paladino + {total_c} Clérigo = {total_p+total_c}')
print('OK')
