"""Cria TB_PersonagemClasse (multiclasse) e migra personagens existentes.

Modelo:
  - 1 personagem ↔ N classes (com nível e subclasse cada)
  - TB_PersonagemEscolha.Id_Classe/Id_Subclasse vira "primary" (Ordem=0)
  - Nivel total do personagem = SUM(Nivel) das classes
"""
import shutil, sqlite3, time

DB = 'bonfas.db'
ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Tabela
cur.execute("""
CREATE TABLE IF NOT EXISTS TB_PersonagemClasse (
    Id_PersonagemClasse INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Personagem INTEGER NOT NULL,
    Id_Classe     INTEGER NOT NULL,
    Id_Subclasse  INTEGER NULL,
    Nivel         INTEGER NOT NULL DEFAULT 1,
    Ordem         INTEGER NOT NULL DEFAULT 0,
    UNIQUE (Id_Personagem, Id_Classe),
    FOREIGN KEY (Id_Personagem) REFERENCES TB_Personagem(Id_Personagem) ON DELETE CASCADE
)
""")
print('TB_PersonagemClasse: criada (ou existe)')

# 2. Migra: pra cada TB_PersonagemEscolha com Id_Classe, cria entry primária
escolhas = cur.execute("""
    SELECT pe.Id_Personagem, pe.Id_Classe, pe.Id_Subclasse, pe.NivelMultiClasse,
           p.Nivel AS NivelTotal
    FROM TB_PersonagemEscolha pe
    JOIN TB_Personagem p ON p.Id_Personagem = pe.Id_Personagem
    WHERE pe.Id_Classe IS NOT NULL
""").fetchall()
for e in escolhas:
    pid = e['Id_Personagem']
    # Já existe entry?
    n = cur.execute(
        'SELECT COUNT(*) FROM TB_PersonagemClasse WHERE Id_Personagem=?', (pid,)
    ).fetchone()[0]
    if n > 0:
        print(f'  pid={pid}: já tem {n} classe(s) — skip migração')
        continue
    # NivelMultiClasse pode ser usado como "secundária", mas nesta migração
    # tratamos a única classe existente como primária com TB_Personagem.Nivel inteiro.
    nivel = e['NivelTotal'] or 1
    cur.execute(
        "INSERT INTO TB_PersonagemClasse (Id_Personagem, Id_Classe, Id_Subclasse, Nivel, Ordem) "
        "VALUES (?, ?, ?, ?, 0)",
        (pid, e['Id_Classe'], e['Id_Subclasse'], nivel),
    )
    print(f'  pid={pid}: Id_Classe={e["Id_Classe"]} Sub={e["Id_Subclasse"]} Nv={nivel} (primária)')

conn.commit()
print()
print('=== Estado pós-migração ===')
for r in cur.execute("""
    SELECT pc.Id_Personagem, p.Nome, c.Nome AS Classe, s.Nome AS Sub, pc.Nivel, pc.Ordem
    FROM TB_PersonagemClasse pc
    JOIN TB_Personagem p ON p.Id_Personagem=pc.Id_Personagem
    JOIN TB_Classe c ON c.Id_Classe=pc.Id_Classe
    LEFT JOIN TB_Subclasse s ON s.Id_Subclasse=pc.Id_Subclasse
    ORDER BY pc.Id_Personagem, pc.Ordem
""").fetchall():
    print(f"  pid={r['Id_Personagem']} ({r['Nome']}): {r['Classe']} {r['Nivel']}{' / ' + r['Sub'] if r['Sub'] else ''} (ordem {r['Ordem']})")

conn.close()
print('OK')
