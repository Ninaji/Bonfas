"""Limpa Descricao da hab Conjuração do Caçador (id=116) — extraía lista de magias
colada como junk. Substituída pelo texto explicativo do sistema (espaços, preparação,
habilidade de conjuração, ritual, foco). A lista de magias é catálogo do servidor —
não vai no campo Descricao.
"""
import shutil
import sqlite3
import time

DB = "bonfas.db"
ID_HAB = 116  # Caçador Nv 1 Conjuração

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}")

# Texto extraído do caçador.extracted.html, seções:
# Espaços de Magia / Magias Preparadas / Habilidade de Conjuração / Ritual / Foco
DESCRICAO = (
    "Antes de cada caçada, eu escrevo. Não por gosto de poesia, mas por medo de não "
    "sobreviver. Anoto armadilhas, passos que denunciam emboscada, rituais antigos. "
    "O diário não é um livro: é um espelho do que enfrento.\n\n"
    "Espaços de Magia: a tabela O Caçador mostra quantos espaços de magia você possui "
    "para conjurar magias de nível 1+. Para conjurar, gaste um espaço do nível da magia "
    "ou superior. Recupera todos os espaços ao final de um Descanso Longo.\n\n"
    "Magias Preparadas: escolha um número de magias da lista de Caçador igual ao seu "
    "modificador de Inteligência ou Sabedoria + metade do seu nível de Caçador "
    "(arredondado para baixo, mínimo 1). As magias escolhidas devem ser de um nível "
    "para o qual você tenha espaços de magia. Preparar nova lista exige pelo menos "
    "1 minuto por nível de magia, em estudo e preparo dos componentes.\n\n"
    "Habilidade de Conjuração: Inteligência ou Sabedoria (sua escolha no nível 1) — "
    "a magia vem de estudo prático e conhecimento do oculto. CD de Resistência = "
    "8 + Bônus de Proficiência + Mod. INT/SAB. Ataque de Magia = Bônus de Proficiência "
    "+ Mod. INT/SAB.\n\n"
    "Ritual de Conjuração: você pode conjurar qualquer magia de Caçador como ritual "
    "se ela tiver o descritor Ritual e estiver preparada.\n\n"
    "Foco de Conjuração: pode usar um Foco Arcano (diário, orbe, componente específico) "
    "ou Ferramentas de Artesão (Suprimentos de Alquimista, Ferramentas de Ladrão) "
    "como foco para suas magias de Caçador."
)

conn = sqlite3.connect(DB)
cur = conn.cursor()

old = cur.execute("SELECT Descricao FROM TB_ClasseHabilidade WHERE Id_Habilidade=?", (ID_HAB,)).fetchone()
print(f"\nAntes ({len(old[0] or '')} chars):")
print(f"  {(old[0] or '')[:120]}...")

cur.execute("UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?", (DESCRICAO, ID_HAB))
conn.commit()

new = cur.execute("SELECT Descricao FROM TB_ClasseHabilidade WHERE Id_Habilidade=?", (ID_HAB,)).fetchone()
print(f"\nDepois ({len(new[0])} chars):")
print(f"  {new[0][:200]}...")
conn.close()
print("\nDONE.")
