"""Schema + catálogo + tag + progressão para Estilos de Ki (Monge Nv 2+).
Padrão idêntico a Inimigo Favorito / Segredos / Evolução Totêmica."""
import json, shutil, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ID_MONGE = 12

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

# Catálogo (extraído do raw)
ESTILOS = [
    ("agil",         "Estilo Ágil",         1,
     "Imediatamente após realizar a ação Atacar no seu turno, você pode gastar 1 Ponto de Ki para realizar dois Golpes Desarmados como uma Ação Bônus."),
    ("veloz",        "Estilo Veloz",        1,
     "Você flui como o vento. Defesa Rápida: ao usar Ação Bônus para Desengajar, gasta 1 Ki pra realizar também Desviar (Dodge). Passo do Vento: ao usar Ação para Disparada, gasta 1 Ki pra ganhar também Desengajar até o fim do turno."),
    ("rasteiro",     "Estilo Rasteiro",     1,
     "Quando acertar uma criatura com Golpe Desarmado, você pode forçar Save de Destreza. Em falha, o alvo fica Derrubado (Caído)."),
    ("impulso",      "Estilo de Impulso",   1,
     "Quando acertar Golpe Desarmado, força Save de Força. Em falha, empurra o alvo até 4,5 m (15 pés) pra longe de você."),
    ("habil",        "Estilo Hábil",        1,
     "Imediatamente após Atacar, gasta 1 Ki pra fazer um Golpe Desarmado como Ação Bônus. Se acertar, além do dano, alvo faz Save de Constituição; em falha, não pode Reagir até o fim do próximo turno dele."),
    ("debilitante",  "Estilo Debilitante",  1,
     "Quando acertar Golpe Desarmado, força Save de Destreza. Em falha, alvo sofre Desvantagem em todas jogadas de ataque até o fim do próximo turno dele."),
    ("fuga",         "Estilo de Fuga",      1,
     "Como Reação, quando uma criatura inimiga terminar o turno a até 3 m (10 pés) de você, você se move até metade do seu deslocamento. Esse movimento não provoca Ataques de Oportunidade."),
    ("constritor",   "Estilo Constritor",   2,
     "Quando acertar Golpe Desarmado, força Save de Destreza. Em falha, alvo fica Agarrado (Grappled) por você. Funciona apenas em criaturas até uma categoria de tamanho maior que a sua."),
    ("barreira",     "Estilo Barreira",     1,
     "Como Reação, quando você for alvo de um ataque feito por criatura que você atacou com Golpe Desarmado neste turno (ou último), recebe bônus na CA igual ao seu Bônus de Proficiência contra aquele atacante até o início do seu próximo turno."),
]

PROGRESSAO = [(2, "3"), (5, "4"), (11, "5"), (17, "6")]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_EstiloKi (
    Id_Estilo INTEGER PRIMARY KEY AUTOINCREMENT,
    Slug      VARCHAR(40) UNIQUE NOT NULL,
    Nome      VARCHAR(80) NOT NULL,
    CustoKi   INTEGER NOT NULL DEFAULT 1,
    Descricao TEXT
);
CREATE TABLE IF NOT EXISTS TB_PersonagemEstiloKi (
    Id            INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem INTEGER NOT NULL,
    Id_Estilo     INTEGER NOT NULL,
    Id_Habilidade INTEGER,
    SlotIndex     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (Id_Personagem, SlotIndex),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem),
    FOREIGN KEY (Id_Estilo) REFERENCES TB_EstiloKi(Id_Estilo)
);
""")
print("Schema OK")

ins = 0
for slug, nome, custo, desc in ESTILOS:
    if not cur.execute("SELECT 1 FROM TB_EstiloKi WHERE Slug=?", (slug,)).fetchone():
        cur.execute(
            "INSERT INTO TB_EstiloKi (Slug, Nome, CustoKi, Descricao) VALUES (?,?,?,?)",
            (slug, nome, custo, desc),
        )
        ins += 1
print(f"Catálogo: {ins} inseridos / {len(ESTILOS) - ins} existiam (total {len(ESTILOS)})")

# Tag gate na hab Ki Nv 2 do Monge
ki_id = cur.execute(
    "SELECT Id_Habilidade FROM TB_ClasseHabilidade WHERE Id_Classe=12 AND Nome='Ki' AND NivelAdquirido=2"
).fetchone()[0]
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
            ('["estilos-ki"]', ki_id))
print(f"Hab id={ki_id} 'Ki' Nv 2: TagsJSON=['estilos-ki']")

# Progressão TB_RecursoClasse
for nv, val in PROGRESSAO:
    if not cur.execute(
        "SELECT 1 FROM TB_RecursoClasse WHERE Id_Classe=? AND Id_Subclasse IS NULL AND Nome=? AND Nivel=?",
        (ID_MONGE, "Estilos de Ki", nv),
    ).fetchone():
        cur.execute(
            "INSERT INTO TB_RecursoClasse (Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor) VALUES (?,?,?,?,?,?)",
            (ID_MONGE, None, "Estilos de Ki", "estilos-ki", nv, val),
        )
print(f"TB_RecursoClasse: progressão Nv {[p[0] for p in PROGRESSAO]} = {[p[1] for p in PROGRESSAO]}")

conn.commit()
conn.close()
print("\nDONE.")
