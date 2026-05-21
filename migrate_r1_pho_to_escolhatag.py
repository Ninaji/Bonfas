"""R1 — Migra picks de TB_PersonagemHabilidadeOpcao (PHO) para TB_PersonagemEscolhaTag.

Parte do plano de remoção do código legado OpcaoTipoJSON+PHO. Esta fase é
PURAMENTE de dados — não deleta nada, idempotente, backup automático.

Operações:
  A) Pra cada hab com OpcaoTipoJSON, sintetizar `pick:<tipo>:<qtd>` em TagsJSON
     quando ainda não existe (preservando tags existentes). Skipa:
       - tipo "maestria-arma" (semântica diferente; virou `+manobras`).
       - tipo "save-prof" (já tem tag `save-prof-vontade` modelada na hab).
  B) Pra cada row PHO com SlotIndex + Texto, gerar entry equivalente em
     TB_PersonagemEscolhaTag. Origem=hab.Nome, Tipo derivado do SlotIndex via
     spec linear, Valor=Texto. Skip se já existe (PK composto cuida).
  C) Rows PHO sem SlotIndex (texto livre legado puro) ficam sem migrar —
     anotadas no log como dado órfão pra inspeção.

ROLLBACK: backup do DB em bonfas.db.bak.<ts>. Pra reverter, restaurar arquivo.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'

# Tipos que NÃO devem virar pick:* (têm modelagem diferente):
#   - maestria-arma → semântica de "valor somado", representada por `+manobras`
#   - save-prof     → já tem tag `save-prof-vontade` modelada
PULAR_TIPO_PICK = {"maestria-arma", "save-prof"}

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def _tags_existentes_strs(tags_json: str | None) -> set[str]:
    """Retorna set de strings canônicas das tags (string flat ou tag de objeto convertida)."""
    try:
        arr = json.loads(tags_json or "[]") or []
    except (json.JSONDecodeError, TypeError):
        return set()
    out = set()
    for t in arr:
        if isinstance(t, str):
            out.add(t)
        elif isinstance(t, dict) and isinstance(t.get("tag"), str):
            out.add(t["tag"])  # comparamos prefix
    return out


# =====================================================================
# A) Sintetizar pick:<tipo> em TagsJSON pra cada hab com OpcaoTipoJSON
# =====================================================================
print()
print("--- A) Sintetizar pick:* em TagsJSON pra habs com OpcaoTipoJSON ---")
habs = cur.execute(
    "SELECT Id_Habilidade, Nome, TagsJSON, OpcaoTipoJSON "
    "FROM TB_ClasseHabilidade WHERE OpcaoTipoJSON IS NOT NULL"
).fetchall()
n_synth = 0
for h in habs:
    try:
        spec = json.loads(h['OpcaoTipoJSON']) or []
    except (json.JSONDecodeError, TypeError):
        continue
    if not isinstance(spec, list):
        continue
    existing = _tags_existentes_strs(h['TagsJSON'])
    # Deteccao: existe alguma tag pick:<tipo> OU `<tipo>` standalone que cobre?
    cobertos: set[str] = set()
    for t in existing:
        m = t.split(":", 1)
        if m[0] == "pick" and ":" in t[5:]:
            # "pick:<tipo>:<N>" — extrai tipo
            parts = t.split(":")
            if len(parts) >= 2:
                cobertos.add(parts[1])
        # save-prof-vontade cobre tipo "save-prof"
        if t.startswith("save-prof-vontade"):
            cobertos.add("save-prof")

    novas_tags = []
    for s in spec:
        tipo = s.get("tipo")
        qtd = s.get("quantidade") or 1
        if not tipo or tipo in PULAR_TIPO_PICK:
            continue
        if tipo in cobertos:
            continue
        novas_tags.append(f"pick:{tipo}:{qtd}")

    if not novas_tags:
        continue
    # merge: preserva tags atuais + adiciona novas
    try:
        current = json.loads(h['TagsJSON'] or "[]") or []
    except (json.JSONDecodeError, TypeError):
        current = []
    merged = current + novas_tags
    new_json = json.dumps(merged, ensure_ascii=False)
    cur.execute(
        "UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
        (new_json, h['Id_Habilidade']),
    )
    n_synth += 1
    print(f"  hab {h['Id_Habilidade']:3} '{h['Nome']}': adicionou {novas_tags}")

print(f"Total habs com tag sintetizada: {n_synth}")


# =====================================================================
# B) Migrar rows PHO pra EscolhaTag
# =====================================================================
print()
print("--- B) Migrar rows TB_PersonagemHabilidadeOpcao -> TB_PersonagemEscolhaTag ---")
phos = cur.execute(
    "SELECT pho.Id_Personagem, pho.Id_Habilidade, pho.SlotIndex, pho.Texto, "
    "       pho.Id_Opcao, h.Nome AS HabNome, h.OpcaoTipoJSON "
    "FROM TB_PersonagemHabilidadeOpcao pho "
    "LEFT JOIN TB_ClasseHabilidade h ON h.Id_Habilidade = pho.Id_Habilidade "
    "ORDER BY pho.Id_Personagem, pho.Id_Habilidade, pho.SlotIndex"
).fetchall()
n_migrated = 0
n_orphan = 0
n_skipped = 0
for r in phos:
    pid = r['Id_Personagem']
    hid = r['Id_Habilidade']
    slot = r['SlotIndex']
    texto = (r['Texto'] or "").strip()
    hab_nome = r['HabNome']
    opcao_tipo_json = r['OpcaoTipoJSON']

    if not texto:
        n_skipped += 1
        continue
    if slot is None:
        # Texto livre legado puro — sem mapeamento de tipo possível.
        n_orphan += 1
        print(f"  [orfao]  pid={pid} hab={hid} '{hab_nome}' SlotIndex=NULL Texto='{texto[:40]}'")
        continue
    if not hab_nome or not opcao_tipo_json:
        n_orphan += 1
        print(f"  [orfao]  pid={pid} hab={hid} '{hab_nome}' sem OpcaoTipoJSON pra mapear tipo")
        continue

    # Mapeamento linear SlotIndex → tipo via spec
    try:
        spec = json.loads(opcao_tipo_json) or []
    except (json.JSONDecodeError, TypeError):
        n_orphan += 1
        continue
    cursor_idx = 0
    tipo_resolvido = None
    for s in spec:
        qtd = s.get("quantidade") or 1
        if cursor_idx <= slot < cursor_idx + qtd:
            tipo_resolvido = s.get("tipo")
            slot_local = slot - cursor_idx  # slot dentro do tipo
            break
        cursor_idx += qtd
    if not tipo_resolvido:
        n_orphan += 1
        continue
    if tipo_resolvido in PULAR_TIPO_PICK:
        # save-prof: sera tratado em R2 (vontade-tags); maestria-arma: nao migra (semantica diferente)
        n_skipped += 1
        continue

    # INSERT idempotente em TB_PersonagemEscolhaTag (PK = pid, origem, tipo, slot)
    cur.execute(
        "INSERT OR IGNORE INTO TB_PersonagemEscolhaTag "
        "(Id_Personagem, Origem, Tipo, SlotIndex, Valor) VALUES (?,?,?,?,?)",
        (pid, hab_nome, tipo_resolvido, slot_local, texto[:150]),
    )
    if cur.rowcount > 0:
        n_migrated += 1
        print(f"  [migrou] pid={pid} '{hab_nome}' tipo='{tipo_resolvido}' slot={slot_local} -> '{texto[:40]}'")

print(f"Migrados: {n_migrated}  |  Orfaos (sem mapeamento): {n_orphan}  |  Skipados: {n_skipped}")


# =====================================================================
# C) Save-prof-vontade: rows PHO com tipo save-prof viram entries em
#    TB_PersonagemEscolhaTag com Tipo='save-prof-vontade' (preparacao R2).
# =====================================================================
print()
print("--- C) save-prof-vontade: PHO -> EscolhaTag (preparando R2) ---")
n_vontade = 0
for r in phos:
    pid = r['Id_Personagem']
    hid = r['Id_Habilidade']
    slot = r['SlotIndex']
    texto = (r['Texto'] or "").strip()
    hab_nome = r['HabNome']
    opcao_tipo_json = r['OpcaoTipoJSON']

    if not texto or slot is None or not opcao_tipo_json:
        continue
    try:
        spec = json.loads(opcao_tipo_json) or []
    except (json.JSONDecodeError, TypeError):
        continue
    cursor_idx = 0
    tipo_resolvido = None
    for s in spec:
        qtd = s.get("quantidade") or 1
        if cursor_idx <= slot < cursor_idx + qtd:
            tipo_resolvido = s.get("tipo")
            break
        cursor_idx += qtd
    if tipo_resolvido != "save-prof":
        continue
    cur.execute(
        "INSERT OR IGNORE INTO TB_PersonagemEscolhaTag "
        "(Id_Personagem, Origem, Tipo, SlotIndex, Valor) VALUES (?,?,?,?,?)",
        (pid, hab_nome, "save-prof-vontade", 0, texto[:150]),
    )
    if cur.rowcount > 0:
        n_vontade += 1
        print(f"  [vontade] pid={pid} '{hab_nome}' -> '{texto[:40]}'")
print(f"Vontade-tags migrados: {n_vontade}")


conn.commit()
conn.close()
print()
print('OK — R1 concluida.')
