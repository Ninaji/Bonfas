"""Adiciona catálogo Kensei aos Estilos de Ki.
Schema: TB_EstiloKi ganha coluna Catalogo (default 'ki').
9 estilos Kensei inseridos com Catalogo='kensei'.
Tag flat 'kensei-estilos' na hab Nv 3 'Estilos Kensei' (sub Kensei 133)."""
import json, shutil, sqlite3, sys, time
sys.stdout.reconfigure(encoding="utf-8")

DB = "bonfas.db"
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

KENSEI = [
    ("kensei-kirisaki",       "Kirisaki",       1,
     "Ação Bônus. Após Atacar, gaste 1 Ki + Ação Bônus pra fazer 2 ataques com Armas Kensei. +1 Ki: troca de arma Kensei entre os ataques."),
    ("kensei-enbu",           "Enbu",           1,
     "Ação Bônus. Realize Disparada/Desengajar/Desviar como Ação Bônus; +1 Ki pra incluir uma 2ª dessas ações na mesma Ação Bônus."),
    ("kensei-takitsubo",      "Takitsubo",      1,
     "Ao acertar (corpo). Quando acerta Golpe Desarmado ou ataque com arma Kensei, alvo faz Save de Destreza; em falha, Derrubado."),
    ("kensei-nobori-ten",     "Nobori Ten",     1,
     "Ao acertar (corpo). Quando acerta Golpe Desarmado ou ataque com arma Kensei, alvo faz Save de Força; em falha, empurrado 4,5m (15 ft)."),
    ("kensei-sogi",           "Sōgi",           1,
     "Ação Bônus (após Atacar). Faça 1 Golpe Desarmado ou ataque com arma Kensei; se acertar, Save de Constituição: em falha, alvo não pode Reagir até o fim do próximo turno dele."),
    ("kensei-hebigiri",       "Hebigiri",       1,
     "Ao acertar. Quando acerta Golpe Desarmado ou ataque com arma Kensei, alvo faz Save de Destreza; em falha, Desvantagem em todas jogadas de ataque até o fim do próximo turno dele."),
    ("kensei-tengu-kaze",     "Tengu Kaze",     1,
     "Reação. 1 Ki: criatura inimiga termina turno a até 3m (10 ft) — você move metade do deslocamento sem provocar ataques de oportunidade. 2 Ki: aciona quando inimigo erra ataque contra você dentro de 3m."),
    ("kensei-kudaki",         "Kudaki",         2,
     "Ao acertar (corpo). Escolha: Quebra em Laço (Save DES; falha = Agarrado, alvo até 1 categoria de tamanho maior) OU Desarme Kensei (Save DES; falha = derruba 1 arma/objeto aos pés)."),
    ("kensei-maroi-no-uneri", "Maroi no Uneri", 1,
     "Reação. Quando atacado por criatura que você atacou no último turno, segurando arma Kensei corpo: ganha bônus na CA = BP contra essa criatura até início do próximo turno."),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1) Schema: add coluna Catalogo se não existe
cols = [r[1] for r in cur.execute("PRAGMA table_info('TB_EstiloKi')")]
if "Catalogo" not in cols:
    cur.execute("ALTER TABLE TB_EstiloKi ADD COLUMN Catalogo VARCHAR(20) DEFAULT 'ki'")
    print("Coluna Catalogo adicionada (default 'ki')")
else:
    print("Coluna Catalogo já existia")

# Garante que estilos atuais ficam como 'ki'
cur.execute("UPDATE TB_EstiloKi SET Catalogo='ki' WHERE Catalogo IS NULL")
n_ki = cur.execute("SELECT COUNT(*) FROM TB_EstiloKi WHERE Catalogo='ki'").fetchone()[0]
print(f"Estilos atuais como 'ki': {n_ki}")

# 2) Insere Kensei
ins = 0
for slug, nome, custo, desc in KENSEI:
    if not cur.execute("SELECT 1 FROM TB_EstiloKi WHERE Slug=?", (slug,)).fetchone():
        cur.execute(
            "INSERT INTO TB_EstiloKi (Slug, Nome, CustoKi, Descricao, Catalogo) VALUES (?,?,?,?,'kensei')",
            (slug, nome, custo, desc),
        )
        ins += 1
print(f"\nKensei: {ins} inseridos / {len(KENSEI) - ins} existiam (total {len(KENSEI)})")

# 3) Tag flat 'kensei-estilos' na hab "Estilos Kensei" sub Kensei (133) Nv 3
hab = cur.execute(
    "SELECT Id_Habilidade FROM TB_ClasseHabilidade "
    "WHERE Id_Classe=12 AND Id_Subclasse=133 AND Nome='Estilos Kensei' AND NivelAdquirido=3"
).fetchone()
if hab:
    cur.execute("UPDATE TB_ClasseHabilidade SET TagsJSON=? WHERE Id_Habilidade=?",
                ('["kensei-estilos"]', hab[0]))
    print(f"Hab id={hab[0]} 'Estilos Kensei' sub Kensei: TagsJSON=['kensei-estilos']")
else:
    print("AVISO: hab 'Estilos Kensei' sub Kensei Nv 3 não encontrada")

conn.commit()
print("\n=== STATS ===")
for cat in ("ki", "kensei"):
    n = cur.execute("SELECT COUNT(*) FROM TB_EstiloKi WHERE Catalogo=?", (cat,)).fetchone()[0]
    print(f"  Catalogo='{cat}': {n} estilos")
conn.close()
print("\nDONE.")
