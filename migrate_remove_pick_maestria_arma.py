"""Remove a tag `pick:maestria-arma` de TagsJSON em qualquer hab.

Razão: "Maestria de Armas" no Bonfire Tales NÃO é um pick (não é "escolha 6
armas"). É um valor que cresce com nível e SOMA ao limite de Técnicas/Manobras
do personagem. Modelar como `pick:*` foi engano de domínio.

Tags afetadas (3 habs do Guerreiro com a tag errada hoje):
  - 515 Disciplina Marcial (originalmente populada por migrate_disciplina_marcial_tags.py)
  - 516 Retomar Fôlego (populada via /debug pelo user)
  - 517 Fundamentos de Batalha (populada via /debug pelo user)

Mantém `pick:estilo-de-luta` em cada uma (essa modelagem está correta — escolha
de 1 estilo dentre catálogo TB_OpcaoJogo Tipo='estilo-de-luta').

Idempotente — varre todas as habs e remove a tag onde existir, sem assumir IDs.

A tag correta para "valor somado em manobras" é tema de próxima iteração — pode
ser `manobras-bonus:N` (string com n_por_nivel) ou outra sintaxe. Sem decisão
ainda; coluna TagsJSON fica conservadora.
"""
import json
import shutil
import sqlite3
import time

DB = 'bonfas.db'

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def _is_pick_maestria(tag):
    """Detecta string ou objeto com tag pick:maestria-arma:..."""
    if isinstance(tag, str):
        return tag.startswith("pick:maestria-arma")
    if isinstance(tag, dict):
        t = tag.get("tag")
        return isinstance(t, str) and t.startswith("pick:maestria-arma")
    return False


afetadas = 0
removidas_total = 0

# Varre QUALQUER tabela que carrega TagsJSON. Hoje as 3 habs alvo estão em
# TB_ClasseHabilidade, mas o filtro genérico cobre futuras inserções erradas.
for tbl, pk in [
    ('TB_ClasseHabilidade', 'Id_Habilidade'),
    ('TB_TalentoRacial',    'Id_TalentoRacial'),
    ('TB_TracoRacial',      'Id_Traco'),
    ('TB_OpcaoJogo',        'Id_Opcao'),
    ('TB_Classe',           'Id_Classe'),
    ('TB_Subclasse',        'Id_Subclasse'),
    ('TB_Raca',             'Id_Raca'),
    ('TB_Linhagem',         'Id_Linhagem'),
    ('TB_Essencia',         'Id_Essencia'),
    ('TB_EssenciaLinhagem', 'Id_EssLinhagem'),
    ('TB_Item',             'Id_Item'),
]:
    rows = cur.execute(
        f"SELECT {pk} AS pk, Nome, TagsJSON FROM {tbl} WHERE TagsJSON IS NOT NULL"
    ).fetchall()
    for r in rows:
        try:
            tags = json.loads(r['TagsJSON']) or []
        except (json.JSONDecodeError, TypeError):
            continue
        novo = [t for t in tags if not _is_pick_maestria(t)]
        if len(novo) == len(tags):
            continue
        afetadas += 1
        removidas_total += (len(tags) - len(novo))
        novo_json = json.dumps(novo, ensure_ascii=False) if novo else None
        cur.execute(
            f"UPDATE {tbl} SET TagsJSON=? WHERE {pk}=?",
            (novo_json, r['pk']),
        )
        print(f"  {tbl} pk={r['pk']} '{r['Nome']}': removidas {len(tags)-len(novo)} tag(s) pick:maestria-arma")

conn.commit()
conn.close()
print(f'OK — {afetadas} row(s) atualizada(s), {removidas_total} tag(s) removida(s) total.')
