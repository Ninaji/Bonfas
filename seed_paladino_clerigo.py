"""Seed: Paladino + Clérigo habilidades, idempotente.

PALADINO (Id_Classe=13):
  - Formato: paginas/paladino.txt com blocos [HABILIDADES]
  - Campo `Subclasse:` vazio = base | slug = subclasse (juramento-da-X)
  - Slug→Nome: mapeado abaixo. Subclasses faltantes são criadas.

CLÉRIGO (Id_Classe=5):
  - Formato: paginas/clerigo.txt extraído de HTML
  - Subclasses sinalizadas por "Domínio da X" header
  - Habs Nv X: Y depois desse header pertencem àquela subclasse

Idempotente: limpa habs "lixo" do run anterior antes de re-inserir.
"""
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


# ============================================================
# 0. Limpa habs lixo do seed anterior em Paladino que ficaram com
# Id_Subclasse=NULL mas pertencem a subclasse. Reseed do zero todas.
# ============================================================
print('Limpando habs Paladino + Clérigo que serão re-inseridas...')
n = cur.execute("DELETE FROM TB_ClasseHabilidade WHERE Id_Classe IN (5, 13)").rowcount
print(f'  removed {n} rows (vão ser re-inseridas)')


# ============================================================
# 1. PALADINO — parse paladino.txt
# ============================================================
PALADINO_SUB_SLUG_NOME = {
    'juramento-da-conquista':  'Conquista',
    'juramento-da-coroa':      'Coroa',
    'juramento-da-devocao':    'Devoção',
    'juramento-da-gloria':     'Glória',
    'juramento-da-morte':      'Morte',
    'juramento-da-redencao':   'Redenção',
    'juramento-da-vinganca':   'Vingança',
    'juramento-dos-vigilantes':'Vigilantes',
    'juramento-primordial':    'Primordial',
}


def _strip_magias_dominio(desc: str) -> str:
    """Remove a seção 'Magias de Domínio' do texto da descrição.
    Os spells são capturados no `seed_magias_dominio_all.py` em formato estruturado
    (TB_Subclasse.MagiaExpandidaJSON) — UI renderiza tabela própria.
    """
    if not desc:
        return desc
    # Paladino: bloco markdown "**Magias de Domínio (X):**" + tabela até EOF da hab
    desc = re.sub(r'\n\s*\*\*Magias de Domínio[\s\S]*$', '', desc)
    # Clérigo: linha "Magias de Domínio" + tier text até EOF
    desc = re.sub(r'\n\s*Magias de Domínio\s*\n[\s\S]*$', '', desc)
    return desc.strip()


def parse_paladino_txt(path: Path) -> list[dict]:
    text = path.read_text(encoding='utf-8')
    if '[HABILIDADES]' not in text:
        return []
    text = text.split('[HABILIDADES]', 1)[1]
    blocks = [b.strip() for b in text.split('\n---') if b.strip()]
    habs = []
    for b in blocks:
        m_nome = re.search(r'^Nome:\s*([^\r\n]+)$', b, re.M)
        m_niv  = re.search(r'^Nivel:\s*(\d+)\s*$',  b, re.M)
        # Sub: linha "Subclasse:" com value após \s+ — se line for só "Subclasse:" o group fica None
        m_sub  = re.search(r'^Subclasse:[ \t]+(\S[^\r\n]*?)\s*$', b, re.M)
        m_desc = re.search(r'^Descrição:\s*\n([\s\S]+)', b, re.M)
        if not (m_nome and m_niv):
            continue
        nome = m_nome.group(1).strip()
        nivel = int(m_niv.group(1))
        sub_slug = (m_sub.group(1).strip() if m_sub else None)
        # filtra valores não-slugs (ex.: 'nao', 'sim') que escaparam
        if sub_slug and not sub_slug.startswith('juramento-'):
            sub_slug = None
        desc = (m_desc.group(1).strip() if m_desc else "")
        desc = _strip_magias_dominio(desc)
        habs.append({
            'nome': nome, 'nivel': nivel,
            'sub_slug': sub_slug,
            'descricao': desc,
        })
    return habs


paladino_habs = parse_paladino_txt(Path('paginas/paladino.txt'))
print(f'\n=== Paladino: {len(paladino_habs)} habs parseadas ===')

# Cria subclasses faltantes pra Paladino (Glória/Redenção/Vingança/Vigilantes não existem)
def upsert_subclasse(id_classe: int, nome: str, slug: str | None = None) -> int:
    r = cur.execute(
        "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Nome=?",
        (id_classe, nome),
    ).fetchone()
    if r:
        return r['Id_Subclasse']
    s = slug or re.sub(r'[^a-z0-9]+', '-', nome.lower()).strip('-')
    cur.execute(
        "INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug) VALUES (?, ?, ?)",
        (id_classe, nome, s),
    )
    print(f'  + Subclasse criada: ({id_classe}) {nome} → Id={cur.lastrowid}')
    return cur.lastrowid


paladino_sub_ids: dict[str, int] = {}
for slug, nome in PALADINO_SUB_SLUG_NOME.items():
    paladino_sub_ids[slug] = upsert_subclasse(13, nome, slug.replace('juramento-da-', '').replace('juramento-', ''))


# ============================================================
# 2. CLÉRIGO — parse clerigo.txt
# ============================================================
CLERIGO_SUB_PREFIXO = {  # nome capturado → nome canônico no DB
    'Arcano':     'Domínio Arcano',
    'Caos':       'Domínio do Caos',
    'Escuridão':  'Domínio da Escuridão',
    'Guerra':     'Domínio da Guerra',
    'Luz':        'Domínio da Luz',
    'Morte':      'Domínio da Morte',
    'Natureza':   'Domínio da Natureza',
    'Ordem':      'Domínio da Ordem',
    'Paz':        'Domínio da Paz',
    'Tempestade': 'Domínio da Tempestade',
    'Trapaça':    'Domínio da Trapaça',
    'Vida':       'Domínio da Vida',
}
# 'Caos: O Riso de Khaelor' é variante do Caos — ignora subheader
CLERIGO_SUBHEADER_IGNORE = {'Caos: O Riso de Khaelor'}

# Habs BASE do Clérigo — atribuídas como base mesmo se vierem após um header de Domínio
# (PHB 2024 organiza o doc com base intercalada com subclass features depois das listas).
CLERIGO_HABS_BASE = {
    'Conjuração',
    'Ordem Sagrada',
    'Ritos Sacros',
    'Canalizar Divindade',
    'Domínio Divino',
    'Aumento no Valor de Habilidade',
    'Aprimoramento de Atributo',  # variação de nome
    'Autoridade Sagrada',
    'Característica de Domínio Divino',
    'Golpes Abençoados',
    'Intervenção Divina',
    'Incremento no Valor de Habilidade',
    'Golpes Abençoados Aprimorados',
    'Intervenção Divina Maior',
    'Intervenção Divina Suprema',
    'Intervenção Suprema do Domínio',
    'Característica de Subclasse',  # marker de Nv 17 base ("ganha característica da sua subclasse")
}


def parse_clerigo_txt(path: Path) -> list[dict]:
    lines = path.read_text(encoding='utf-8').splitlines()
    # Match "Domínio Arcano" OU "Domínio da/do/dos X"
    sub_re = re.compile(r'^\s*Dom[íi]nio (?:(?:da|do|dos) )?(.+?)\s*$', re.I)
    hab_re = re.compile(r'^\s*N[íi]vel\s+(\d+):\s*(.+?)\s*$', re.I)
    sub_at: list[tuple[int, str]] = []
    hab_at: list[tuple[int, int, str]] = []
    for i, ln in enumerate(lines):
        m = sub_re.match(ln)
        if m:
            nome = m.group(1).strip()
            if nome not in CLERIGO_SUBHEADER_IGNORE:
                sub_at.append((i, nome))
            continue
        m2 = hab_re.match(ln)
        if m2:
            hab_at.append((i, int(m2.group(1)), m2.group(2).strip()))
    habs = []
    cuts = sorted([i for i, _ in sub_at] + [i for i, _, _ in hab_at] + [len(lines)])
    for li, nivel, nome in hab_at:
        # Override: nome em CLERIGO_HABS_BASE → base, ignora subclass header anterior
        if nome.strip() in CLERIGO_HABS_BASE:
            sub_nome = None
        else:
            sub_nome = None
            for s_li, s_n in sub_at:
                if s_li < li:
                    sub_nome = s_n
                else:
                    break
        next_cut = next(c for c in cuts if c > li)
        desc_lines = lines[li+1:next_cut]
        desc = '\n'.join(l.strip() for l in desc_lines).strip()
        desc = re.sub(r'\n{3,}', '\n\n', desc)
        desc = _strip_magias_dominio(desc)
        habs.append({
            'nome': nome, 'nivel': nivel,
            'sub_nome': sub_nome,
            'descricao': desc,
        })
    return habs


clerigo_habs = parse_clerigo_txt(Path('paginas/clerigo.txt'))
print(f'\n=== Clérigo: {len(clerigo_habs)} habs parseadas ===')

# Subclasses do Clérigo
clerigo_sub_ids: dict[str, int] = {}
for parsed_nome, canonico in CLERIGO_SUB_PREFIXO.items():
    clerigo_sub_ids[parsed_nome] = upsert_subclasse(5, canonico)


# ============================================================
# 3. INSERT habs (já está limpo, então é só insert)
# ============================================================
def insert_hab(id_classe: int, id_subclasse: int | None, nome: str,
               nivel: int, descricao: str, origem: str) -> int:
    cur.execute(
        "INSERT INTO TB_ClasseHabilidade (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem) "
        "VALUES (?, ?, ?, ?, ?, 0, ?)",
        (id_classe, id_subclasse, nome, descricao, nivel, origem),
    )
    return cur.lastrowid


print('\n=== INSERT habs Paladino ===')
pal_b, pal_s = 0, 0
for h in paladino_habs:
    sub_id = paladino_sub_ids.get(h['sub_slug']) if h['sub_slug'] else None
    origem = 'subclasse' if sub_id else 'base'
    insert_hab(13, sub_id, h['nome'], h['nivel'], h['descricao'], origem)
    if sub_id: pal_s += 1
    else: pal_b += 1
print(f'  Paladino: {pal_b} base + {pal_s} subclasse = {pal_b + pal_s}')

print('\n=== INSERT habs Clérigo ===')
cle_b, cle_s = 0, 0
for h in clerigo_habs:
    sub_id = clerigo_sub_ids.get(h['sub_nome']) if h['sub_nome'] else None
    origem = 'subclasse' if sub_id else 'base'
    insert_hab(5, sub_id, h['nome'], h['nivel'], h['descricao'], origem)
    if sub_id: cle_s += 1
    else: cle_b += 1
print(f'  Clérigo: {cle_b} base + {cle_s} subclasse = {cle_b + cle_s}')

conn.commit()
conn.close()
print('\nOK')
