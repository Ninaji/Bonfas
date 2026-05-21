"""Popula TODAS as features de Caçador (classe Nv 3-20 + 6 subs Nv 6/10/14/18).

Lê descrições do parser (cacador_full.json) e usa mapeamento explícito:
  - Features de classe (Id_Subclasse=NULL): tudo que não é Nv-3-flavor-de-sub e nem feature
    listada como específica de uma ordem (Nv 6/10/14/18 mapeadas).
  - Features de subclasse: mapeamento abaixo, derivado de leitura textual de cada hab.

ASIs (Nv 4, 8, 12, 16, 19) entram como TemEscolha=1, Origem='classe' (padrão Guerreiro).
"Característica de Ordem" headers (Nv 6/10/14/18) viram TemEscolha=1 Origem='subclasse'
no Id_Subclasse=NULL — é o pick:caracteristica-ordem que o jogador faz a cada nível-marco.

Idempotente por (Id_Classe, Id_Subclasse, Nome, NivelAdquirido).
"""
import json
import shutil
import sqlite3
import time
from pathlib import Path

DB = "bonfas.db"
ID_CACADOR = 4

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

FEATS = json.loads(Path("cacador_full.json").read_text(encoding="utf-8"))
# Lookup: (nivel, nome) -> descricao
desc_by = {(f["nivel"], f["nome"]): f["descricao"] for f in FEATS}


# Mapeamento de subclasse: (nivel, nome) -> Id_Subclasse
# Derivado de leitura textual das features Nv 6/10/14/18.
SUB_MAP = {
    # Nv 6 — uma feature por ordem
    (6, "Elo de Caça Rúnica"):     21,   # Aliança Selvagem (vínculo com espírito)
    (6, "Ruptura Rúnica"):         125,  # Viajantes (símbolo trava fuga)
    (6, "Ruptura de Selo"):        124,  # Exterminadores (dobra impacto extraplanar)
    (6, "Instinto Coletivo"):      126,  # Enxame
    (6, "Manto das Sombras"):      127,  # Sombras
    (6, "Supressão Alquímica"):    128,  # Mutantes
    # Nv 10
    (10, "Cerco de Presas Rituais"): 21,   # Aliança ("Seu espírito aprende a lidar")
    (10, "Eco Purgante"):            124,  # Exterminadores (cadeia de impacto)
    (10, "Salto de Travessia"):      125,  # Viajantes ("Runas de Travessia")
    (10, "Enxame Expansivo"):        126,  # Enxame
    (10, "Golpe Cirúrgico"):         127,  # Sombras ("a partir das sombras")
    (10, "Percepção Predatória"):    128,  # Mutantes ("após tanta mutação")
    # Nv 14 — Enxame tem 2 (Colmeia + Voo Simbiótico)
    (14, "Reflexo Instintivo"):      21,   # Aliança ("Espírito Primordial ganha")
    (14, "Última Palavra"):          124,  # Exterminadores ("determinação")
    (14, "Véu Desfeito"):            125,  # Viajantes ("selo, fenda, existir de lado")
    (14, "Colmeia Instintiva"):      126,  # Enxame
    (14, "Voo Simbiótico"):          126,  # Enxame (segunda opção)
    (14, "Contra-Ataque Sombrio"):   127,  # Sombras
    (14, "Transfusão Mutagênica"):   128,  # Mutantes
    # Nv 18 — Segredos
    (18, "Segredo: Chamado da Presa Imortal"): 21,   # Aliança ("ele volta")
    (18, "Segredo: Cilada Final"):              124,  # Exterminadores (disparo + runa)
    (18, "Segredo: Caminho Final"):             125,  # Viajantes ("portais, fendas")
    (18, "Segredo: Ninho Devorador"):           126,  # Enxame
    (18, "Segredo: Névoa Sepulcral"):           127,  # Sombras
    (18, "Segredo: Sangue Venenoso"):           128,  # Mutantes
}


# Features que viram CLASSE (Id_Subclasse=NULL). Todas as demais Nv 3+ que não são
# os Nv-3-flavor das subclasses (já populadas) e que não estão em SUB_MAP.
# Classifico aqui o que insiro como classe nova:
CLASSE_FEATS = [
    # nivel, nome, tem_escolha, origem
    (3,  "Ordem de Caçador",                    1, "classe"),     # pick:subclasse
    (4,  "Incremento de Atributo ou Talento",   1, "classe"),     # ASI
    (5,  "Segundo Ataque",                      0, "classe"),     # = Ataque Extra
    (5,  "Território de Caça",                  0, "classe"),
    (6,  "Característica de Ordem",             1, "subclasse"),  # pick caractr. ordem Nv 6
    (7,  "Caçador Implacável",                  0, "classe"),
    (8,  "Incremento de Atributo ou Talento",   1, "classe"),
    (9,  "Instinto Afiado",                     0, "classe"),
    (10, "Característica de Ordem",             1, "subclasse"),
    (11, "Predador Astuto",                     0, "classe"),
    (12, "Incremento de Atributo ou Talento",   1, "classe"),
    (13, "Passos Invisíveis",                   0, "classe"),
    (14, "Característica de Ordem",             1, "subclasse"),
    (15, "Vontade Inabalável",                  0, "classe"),
    (16, "Incremento de Atributo ou Talento",   1, "classe"),
    (17, "Instinto Predatório",                 0, "classe"),
    (18, "Característica de Ordem",             1, "subclasse"),
    (19, "Incremento de Atributo ou Talento",   1, "classe"),
    (20, "Domínio da Caçada",                   0, "classe"),
]


def upsert_hab(cur, id_subclasse, nome, nivel, tem_escolha, origem) -> str:
    desc = desc_by.get((nivel, nome))
    if desc is None:
        return f"NO-DESC ({nivel},{nome})"
    # idempotência
    if id_subclasse is None:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND NivelAdquirido=?",
            (ID_CACADOR, nome, nivel),
        ).fetchone()
    else:
        row = cur.execute(
            "SELECT Id_Habilidade FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND NivelAdquirido=?",
            (ID_CACADOR, id_subclasse, nome, nivel),
        ).fetchone()
    if row:
        return "skip"
    cur.execute(
        """INSERT INTO TB_ClasseHabilidade
           (Id_Classe, Id_Subclasse, Nome, Descricao, NivelAdquirido, TemEscolha, Origem, TagsJSON)
           VALUES (?,?,?,?,?,?,?,NULL)""",
        (ID_CACADOR, id_subclasse, nome, desc, nivel, tem_escolha, origem),
    )
    return "ins"


conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Classe (Id_Subclasse=NULL)
print("=== CLASSE (Id_Subclasse=NULL) ===")
for nivel, nome, tem_esc, origem in CLASSE_FEATS:
    res = upsert_hab(cur, None, nome, nivel, tem_esc, origem)
    print(f"  Nv{nivel:>2} esc={tem_esc} orig={origem:<10}  {nome:<40} [{res}]")

# 2) Subclasses (mapeamento explícito)
print("\n=== SUBCLASSES ===")
sub_nomes = {
    21: "Aliança Selvagem", 124: "Exterminadores", 125: "Viajantes",
    126: "Enxame", 127: "Sombras", 128: "Mutantes",
}
# Agrupar por sub para print mais legível
by_sub: dict[int, list] = {}
for (nivel, nome), sid in SUB_MAP.items():
    by_sub.setdefault(sid, []).append((nivel, nome))
for sid in sorted(by_sub):
    print(f"\n  Sub {sid} {sub_nomes.get(sid, '?')}:")
    for nivel, nome in sorted(by_sub[sid]):
        res = upsert_hab(cur, sid, nome, nivel, 0, "subclasse")
        print(f"    Nv{nivel:>2}  {nome:<40} [{res}]")

conn.commit()

# 3) Stats finais
print("\n=== STATS FINAIS ===")
total_class = cur.execute(
    "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse IS NULL", (ID_CACADOR,)
).fetchone()[0]
print(f"  Habs CLASSE Caçador: {total_class}")
for sid, sname in sub_nomes.items():
    n = cur.execute(
        "SELECT COUNT(*) FROM TB_ClasseHabilidade WHERE Id_Classe=? AND Id_Subclasse=?", (ID_CACADOR, sid)
    ).fetchone()[0]
    print(f"  Sub {sid} ({sname}): {n} habs")

conn.close()
print("\nDONE.")
