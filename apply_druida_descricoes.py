"""Aplica as descrições limpas escritas à mão (druida_descricoes.py) sobre as
63 features de Druida no DB, substituindo o texto poluído do parser-regex.

Backup automático. Reporta qualquer feature sem descrição manual mapeada.
"""
from __future__ import annotations
import sqlite3, shutil, sys, time
from druida_descricoes import DESCRICOES, chave_para

sys.stdout.reconfigure(encoding="utf-8")
DB = "bonfas.db"
ID_DRUIDA = 6

ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

conn = sqlite3.connect(DB)
cur = conn.cursor()

rows = cur.execute(
    "SELECT Id_Habilidade, Id_Subclasse, Nome, NivelAdquirido, length(Descricao) "
    "FROM TB_ClasseHabilidade WHERE Id_Classe=? "
    "ORDER BY Id_Subclasse IS NULL DESC, Id_Subclasse, NivelAdquirido, Nome",
    (ID_DRUIDA,),
).fetchall()

print(f"=== Aplicando descrições limpas para {len(rows)} features ===\n")
ok, missing = 0, []
for r in rows:
    hab_id, sub_id, nome, nivel, old_len = r
    key = chave_para(sub_id, nome)
    desc = DESCRICOES.get(key)
    if desc is None:
        missing.append((hab_id, sub_id, nome, nivel))
        continue
    cur.execute("UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?",
                (desc, hab_id))
    sub_lbl = f"sub={sub_id}" if sub_id else "classe"
    print(f"  [ok] id={hab_id:<4} {sub_lbl:<8} Nv{nivel:>2} {nome:<42} {old_len} -> {len(desc)}")
    ok += 1

if missing:
    print(f"\n[!] {len(missing)} features SEM descrição manual mapeada:")
    for m in missing:
        print(f"     id={m[0]} sub={m[1]} Nv{m[3]} {m[2]}")
else:
    print(f"\nTodas as {ok} features atualizadas.")

conn.commit()
conn.close()
print("\nDONE.")
