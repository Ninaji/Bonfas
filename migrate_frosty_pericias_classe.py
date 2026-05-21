"""Migra perícias de classe do Frosty pra TB_PersonagemEscolhaPericia.

Antes: Atletismo + Percepção marcadas direto em TB_PersonagemPericia.Proficiente=1
       (anti-padrão § sistema-de-efeitos-via-tags.md — efeito derivado em tabela base).
Depois: registradas em TB_PersonagemEscolhaPericia(Origem='Guerreiro', slot 0/1).

História + Religião continuam como Proficiente=1 direto (origem: Background Arqueólogo;
sem migração agora — Background-as-tag é stretch goal futuro).

Idempotente: skip se já existem entries com origem 'Guerreiro'.
"""
import shutil
import sqlite3
import time

DB = 'bonfas.db'
PID = 2

ts = time.strftime('%Y%m%d-%H%M%S')
shutil.copy(DB, f'{DB}.bak.{ts}')
print(f'Backup: {DB}.bak.{ts}')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Já existem escolhas com origem Guerreiro?
ja = cur.execute(
    "SELECT COUNT(*) AS n FROM TB_PersonagemEscolhaPericia "
    "WHERE Id_Personagem=? AND Origem='Guerreiro'", (PID,),
).fetchone()['n']
if ja > 0:
    print(f'Frosty já tem {ja} escolhas Guerreiro — skip.')
else:
    # Pegar Id_Pericia de Atletismo e Percepção
    perics = {}
    for r in cur.execute(
        "SELECT Id_Pericia, Nome FROM TB_PersonagemPericia "
        "WHERE Id_Personagem=? AND Nome IN ('Atletismo', 'Percepção')",
        (PID,),
    ).fetchall():
        perics[r['Nome']] = r['Id_Pericia']
    if 'Atletismo' not in perics or 'Percepção' not in perics:
        raise SystemExit(f'Não achei Atletismo/Percepção: {perics}')
    cur.execute(
        "INSERT INTO TB_PersonagemEscolhaPericia "
        "(Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo) VALUES (?,?,?,?,?)",
        (PID, 'Guerreiro', 0, perics['Atletismo'], 'proficiencia'),
    )
    cur.execute(
        "INSERT INTO TB_PersonagemEscolhaPericia "
        "(Id_Personagem, Origem, SlotIndex, Id_Pericia, Tipo) VALUES (?,?,?,?,?)",
        (PID, 'Guerreiro', 1, perics['Percepção'], 'proficiencia'),
    )
    cur.execute(
        "UPDATE TB_PersonagemPericia SET Proficiente=0 "
        "WHERE Id_Personagem=? AND Id_Pericia IN (?,?)",
        (PID, perics['Atletismo'], perics['Percepção']),
    )
    print(f'  Atletismo (id {perics["Atletismo"]}): movida para escolha Guerreiro slot 0')
    print(f'  Percepção (id {perics["Percepção"]}): movida para escolha Guerreiro slot 1')

conn.commit()
conn.close()
print('OK')
