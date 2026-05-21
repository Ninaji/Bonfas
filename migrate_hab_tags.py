"""Adiciona TagsJSON em TB_ClasseHabilidade e popula tags pra habs conhecidas.

Tags suportadas (string convention — sem enum):
  - prof:<NomePericia>                 → +BP em testes da perícia
  - expertise:<NomePericia>            → +2*BP em testes da perícia
  - save-prof:<Atributo>               → proficiente em teste de resistência
  - resist:<Elemento> | immune:<Elemento> | vuln:<Elemento>  (canônicos 5.5e)
  - cond-immune:<Condição> | adv-cond:<Condição>             (canônicos 5.5e)
  - conjurador                         → categorial: hab CONCEDE Conjuração/Pacto base

Idempotente — pode rodar repetidas vezes.
"""
import json
import re
import shutil
import sqlite3
import time

DB = 'bonfas.db'

# 1. Backup
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 2. ALTER (idempotente: só adiciona se não existir)
cols = [r['name'] for r in cur.execute('PRAGMA table_info(TB_ClasseHabilidade)').fetchall()]
if 'TagsJSON' in cols:
    print('TagsJSON já existe, skip ALTER')
else:
    cur.execute('ALTER TABLE TB_ClasseHabilidade ADD COLUMN TagsJSON TEXT NULL')
    print('TagsJSON adicionada')

# 3. Map Nome→TagsJSON (apenas habs identificadas manualmente)
TAGS_BY_NOME = {
    'Conhecimentos Arcanos': ['expertise:Arcanismo', 'save-prof:Inteligencia'],
    'Táticas Arcanas':       ['prof:Arcanismo'],
    # Adicionar outras conforme identificadas. Padrão: ler descrição com essas keywords:
    #   "recebe proficiência em <Pericia>"                       → prof:<Pericia>
    #   "Aptidão em <X>" / "dobrando seu bônus de proficiência"  → expertise:<X>
    #   "proficiência em testes de resistência de <Atributo>"    → save-prof:<Atributo>
    # Tags categoriais (standalone, sem valor):
    #   "conjurador" — hab que CONCEDE Conjuração ou Magia de Pacto base
    # Aplicado abaixo a TODA hab "Conjuração" e "Conjuração de Magias" (full + 1/3 casters).
}

# Tags por padrão de Nome (regex case-insensitive). Aplicado depois de TAGS_BY_NOME.
TAGS_BY_NOME_PATTERN = [
    # qualquer hab cujo Nome bate "Conjuração" exato OU "Conjuração de Magias" OU "Magia de Pacto"
    # ganha tag categorial 'conjurador'
    (r'^(Conjuração|Conjuração de Magias|Magia de Pacto)$', ['conjurador']),
]

def _merge_tags(raw_existing: str | None, novas: list[str]) -> str:
    """Faz merge mantendo unique e ordem (existentes primeiro, depois novas)."""
    existing = []
    if raw_existing:
        try:
            loaded = json.loads(raw_existing)
            if isinstance(loaded, list):
                existing = [t for t in loaded if isinstance(t, str)]
        except (json.JSONDecodeError, TypeError):
            existing = []
    seen = set()
    out = []
    for t in existing + novas:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return json.dumps(out, ensure_ascii=False)


aplicados = 0
# Aplica TAGS_BY_NOME (match exato)
for nome, tags in TAGS_BY_NOME.items():
    rows = cur.execute(
        'SELECT Id_Habilidade, TagsJSON FROM TB_ClasseHabilidade WHERE Nome=?',
        (nome,),
    ).fetchall()
    for r in rows:
        merged = _merge_tags(r['TagsJSON'], tags)
        cur.execute(
            'UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?',
            (merged, r['Id_Habilidade']),
        )
        aplicados += 1
        print(f'  [exato]   "{nome}" id={r["Id_Habilidade"]}: tags = {merged}')

# Aplica TAGS_BY_NOME_PATTERN (regex). Faz merge — não sobrescreve.
for pattern, tags in TAGS_BY_NOME_PATTERN:
    regex = re.compile(pattern, re.IGNORECASE)
    rows = cur.execute(
        'SELECT Id_Habilidade, Nome, TagsJSON FROM TB_ClasseHabilidade'
    ).fetchall()
    for r in rows:
        if not regex.search(r['Nome'] or ''):
            continue
        merged = _merge_tags(r['TagsJSON'], tags)
        if merged == (r['TagsJSON'] or ''):
            continue  # nada novo
        cur.execute(
            'UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?',
            (merged, r['Id_Habilidade']),
        )
        aplicados += 1
        print(f'  [pattern] "{r["Nome"]}" id={r["Id_Habilidade"]}: tags = {merged}')

conn.commit()
print(f'Total aplicado: {aplicados} habilidade(s)')
conn.close()
print('OK')
