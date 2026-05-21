"""Schema + catálogo + tag + progressão para Evolução Totêmica
(sub Ordem da Aliança Selvagem do Caçador, Nv 3+)."""
import shutil, sqlite3, time, json

DB = "bonfas.db"
ID_HAB = 126           # Caçador sub Aliança Selvagem Nv 3 — Evolução Totêmica
ID_SUB_ALIANCA = 21
ID_CACADOR = 4

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

CARACS = [
    # Tier 'menor' — todas Nv 3+
    ("menor", "Audição e Olfato Aguçados", "audicao-olfato-agucados",
     "O espírito tem Vantagem em testes de Sabedoria (Percepção) que dependam de audição ou olfato."),
    ("menor", "Camuflagem", "camuflagem",
     "O espírito tem Vantagem em testes de Destreza (Furtividade) enquanto estiver em terreno natural ou sob condições de Penumbra e Escuridão."),
    ("menor", "Escalada Aracnídea", "escalada-aracnidea",
     "O espírito ganha deslocamento de Escalada igual ao seu deslocamento de caminhada. Pode escalar superfícies difíceis, incluindo tetos, sem precisar fazer testes de Habilidade."),
    ("menor", "Prender a Respiração", "prender-respiracao",
     "O espírito pode prender a respiração por 1 hora."),
    ("menor", "Resistência Elemental", "resistencia-elemental",
     "Escolha um tipo de dano: Ácido, Elétrico, Fogo, Frio ou Trovão. O espírito ganha Resistência ao tipo escolhido. Pode ser selecionada múltiplas vezes, escolhendo um tipo diferente a cada vez."),
    ("menor", "Táticas de Matilha", "taticas-matilha",
     "O espírito tem Vantagem nas jogadas de ataque contra uma criatura se você ou outro aliado estiver a até 1,5 m da criatura e não estiver Incapacitado."),
    # Tier 'maior' — Nv 6+
    ("maior", "Alcance Estendido", "alcance-estendido",
     "O alcance dos ataques corpo a corpo do espírito aumenta em 1,5 m."),
    ("maior", "Ecolocalização", "ecolocalizacao",
     "O espírito ganha Visão às Cegas com alcance de 9 m. Perde esse benefício se estiver Surdo."),
    ("maior", "Forma Aumentada", "forma-aumentada",
     "O tamanho do espírito torna-se Grande. Ganha Vantagem em testes de Força para empurrar, agarrar ou escapar de um agarrão."),
    ("maior", "Investida", "investida",
     "Se o espírito se mover ao menos 6 m em linha reta em direção a um alvo e acertá-lo com um ataque corpo a corpo no mesmo turno, o alvo sofre 1d8 de dano extra. Se for criatura, deve fazer Save de Força contra sua CD de Segredos; em falha fica Caído."),
    ("maior", "Robustez Espiritual", "robustez-espiritual",
     "O máximo de PV do espírito aumenta em (2 × Nível de Caçador). Bônus retroativo, escala com nível."),
    ("maior", "Sopro Elemental", "sopro-elemental",
     "Quando comandar o espírito a atacar, pode substituir o ataque por um sopro em Cone de 9 m. Save de DES contra CD de Segredos: dano = (mod INT/SAB) Dados de Caçador (mín 1). Tipo: Ácido/Elétrico/Fogo/Frio/Trovão. Recarrega após Descanso Curto/Longo."),
]

PROGRESSAO = [(3, "1"), (6, "2"), (10, "3"), (14, "4"), (18, "5")]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS TB_EvolucaoTotemica (
    Id_Evolucao INTEGER PRIMARY KEY AUTOINCREMENT,
    Tier        VARCHAR(10) NOT NULL,
    Nome        VARCHAR(100) NOT NULL,
    Slug        VARCHAR(100) UNIQUE NOT NULL,
    Descricao   TEXT
);
CREATE TABLE IF NOT EXISTS TB_PersonagemEvolucaoTotemica (
    Id              INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem   INTEGER NOT NULL,
    Id_Evolucao     INTEGER NOT NULL,
    Id_Habilidade   INTEGER,
    Variante        VARCHAR(40),  -- ex.: tipo de dano em Resistência Elemental
    SlotIndex       INTEGER NOT NULL DEFAULT 0,
    UNIQUE (Id_Personagem, SlotIndex),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem),
    FOREIGN KEY (Id_Evolucao) REFERENCES TB_EvolucaoTotemica(Id_Evolucao)
);
""")
print("Schema OK")

# 2) Catálogo (idempotente por slug)
ins = 0
for tier, nome, slug, desc in CARACS:
    if not cur.execute("SELECT 1 FROM TB_EvolucaoTotemica WHERE Slug=?", (slug,)).fetchone():
        cur.execute("INSERT INTO TB_EvolucaoTotemica (Tier, Nome, Slug, Descricao) VALUES (?,?,?,?)",
                    (tier, nome, slug, desc))
        ins += 1
print(f"Catálogo: {ins} inseridos / {len(CARACS) - ins} já existiam (total {len(CARACS)})")

# 3) Tag gate
cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
            ('["evolucao-totemica"]', ID_HAB))
print(f"Hab id={ID_HAB}: TagsJSON=['evolucao-totemica']")

# 4) Progressão em TB_RecursoClasse
for nv, val in PROGRESSAO:
    if not cur.execute(
        "SELECT 1 FROM TB_RecursoClasse WHERE Id_Classe=? AND Id_Subclasse=? AND Nome=? AND Nivel=?",
        (ID_CACADOR, ID_SUB_ALIANCA, "Evolução Totêmica", nv),
    ).fetchone():
        cur.execute(
            "INSERT INTO TB_RecursoClasse (Id_Classe, Id_Subclasse, Nome, Slug, Nivel, Valor) VALUES (?,?,?,?,?,?)",
            (ID_CACADOR, ID_SUB_ALIANCA, "Evolução Totêmica", "evolucao-totemica", nv, val),
        )
print("TB_RecursoClasse: progressão Nv 3/6/10/14/18 = 1/2/3/4/5")

conn.commit()
conn.close()
print("\nDONE.")
