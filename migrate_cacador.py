"""Popular catálogo da classe Caçador + sub Exterminadores de Monstros.

Mínimo necessário pra fichas de Caçador funcionarem:
  - TB_Classe.SavesJSON: Destreza/Inteligencia (corrigido — estava For/Des)
  - ArmorProfJSON, WeaponProfJSON, SkillsJSON, ToolProfJSON populados
  - Sub "Ordem dos Exterminadores de Monstros" inserida (linkada a Russ posteriormente)

Habs Nv 3+ e outras subclasses ficam pendentes — popular sob demanda.
Idempotente. Backup automático.
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

ID_CLASSE_CACADOR = 4

# 1. Corrigir/popular TB_Classe Caçador
saves = json.dumps(["Destreza", "Inteligencia"], ensure_ascii=False)
armor = json.dumps(["Armadura Leve", "Armadura Média", "Escudos"], ensure_ascii=False)
weapons = json.dumps(["Armas Simples", "Armas Marciais"], ensure_ascii=False)
tools = json.dumps([], ensure_ascii=False)
# Choose 3 das opções listadas no CSV
skills = json.dumps({
    "choose": 3,
    "from": ["Atletismo", "Acrobacia", "Arcanismo", "História", "Intuição",
             "Investigação", "Religião", "Sobrevivência"],
}, ensure_ascii=False)

cur.execute(
    """UPDATE TB_Classe SET SavesJSON=?, ArmorProfJSON=?, WeaponProfJSON=?,
                            ToolProfJSON=?, SkillsJSON=?
       WHERE Id_Classe=?""",
    (saves, armor, weapons, tools, skills, ID_CLASSE_CACADOR),
)
print(f"TB_Classe Caçador: SavesJSON+ArmorProfJSON+WeaponProfJSON+SkillsJSON atualizados")

# 2. Sub-classe Ordem dos Exterminadores de Monstros
slug_sub = "ordem-exterminadores-monstros"
existing = cur.execute(
    "SELECT Id_Subclasse FROM TB_Subclasse WHERE Id_Classe=? AND Slug=?",
    (ID_CLASSE_CACADOR, slug_sub),
).fetchone()
if existing:
    id_sub_em = existing['Id_Subclasse']
    print(f"Sub Exterminadores já existe (id={id_sub_em})")
else:
    cur.execute(
        """INSERT INTO TB_Subclasse (Id_Classe, Nome, Slug, Tagline)
           VALUES (?,?,?,?)""",
        (ID_CLASSE_CACADOR, "Ordem dos Exterminadores de Monstros",
         slug_sub, "Caçadores especializados em criaturas de outros planos."),
    )
    id_sub_em = cur.lastrowid
    print(f"Sub Exterminadores inserida (id={id_sub_em})")

conn.commit()
conn.close()
print('OK')
