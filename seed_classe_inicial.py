"""Seed: ArmorProfJSON, WeaponProfJSON, ToolProfJSON, EquipamentoInicialJSON pra Pal/Cler/Guerreiro.

Fonte: PHB 2024 + 5e.tools, com naming do Bonfire Tales (PT-BR).
Idempotente — sempre sobrescreve as 4 colunas pra cada classe.

Equipamento estruturado como lista de dicts:
  {"qtd": 1, "nome": "Cota de Malha", "tipo": "armor", "valor": "75 gp"}
ou:
  {"opcao": [
      [{"qtd":1,"nome":"X"}],
      [{"qtd":1,"nome":"Y"}],
  ], "rotulo": "(a) X ou (b) Y"}
"""
import json
import sqlite3

DB = 'bonfas.db'

CLASSES = {
    13: {  # Paladino
        'armor':   ['Armadura Leve', 'Armadura Média', 'Armadura Pesada', 'Escudos'],
        'weapons': ['Armas Simples', 'Armas Marciais'],
        'tools':   [],
        'equipamento': [
            {'qtd': 1, 'nome': 'Cota de Malha',     'tipo': 'armor',  'valor': '75 gp'},
            {'qtd': 1, 'nome': 'Escudo',            'tipo': 'armor',  'valor': '10 gp'},
            {'qtd': 1, 'nome': 'Espada Longa',      'tipo': 'weapon', 'valor': '15 gp'},
            {'qtd': 6, 'nome': 'Azagaia',           'tipo': 'weapon', 'valor': '5 sp ea'},
            {'qtd': 1, 'nome': 'Símbolo Sagrado',   'tipo': 'gear',   'valor': '5 gp'},
            {'qtd': 1, 'nome': 'Pacote de Sacerdote', 'tipo': 'pack', 'valor': '19 gp'},
            {'qtd': 1, 'nome': 'Bolsa com 9 PO',    'tipo': 'gold',   'valor': '9 gp'},
        ],
    },
    5: {   # Clérigo
        'armor':   ['Armadura Leve', 'Armadura Média', 'Escudos'],
        'weapons': ['Armas Simples'],
        'tools':   [],
        'equipamento': [
            {'qtd': 1, 'nome': 'Camisa de Malha',   'tipo': 'armor',  'valor': '50 gp'},
            {'qtd': 1, 'nome': 'Escudo',            'tipo': 'armor',  'valor': '10 gp'},
            {'qtd': 1, 'nome': 'Maça',              'tipo': 'weapon', 'valor': '5 gp'},
            {'qtd': 1, 'nome': 'Símbolo Sagrado',   'tipo': 'gear',   'valor': '5 gp'},
            {'qtd': 1, 'nome': 'Pacote de Sacerdote', 'tipo': 'pack', 'valor': '19 gp'},
            {'qtd': 1, 'nome': 'Bolsa com 7 PO',    'tipo': 'gold',   'valor': '7 gp'},
        ],
    },
    8: {   # Guerreiro
        'armor':   ['Armadura Leve', 'Armadura Média', 'Armadura Pesada', 'Escudos'],
        'weapons': ['Armas Simples', 'Armas Marciais'],
        'tools':   [],
        'equipamento': [
            {'qtd': 1, 'nome': 'Cota de Malha',     'tipo': 'armor',  'valor': '75 gp'},
            {'qtd': 1, 'nome': 'Espada Larga',      'tipo': 'weapon', 'valor': '50 gp'},
            {'qtd': 8, 'nome': 'Azagaia',           'tipo': 'weapon', 'valor': '5 sp ea'},
            {'qtd': 1, 'nome': 'Pacote do Aventureiro', 'tipo': 'pack', 'valor': '12 gp'},
            {'qtd': 1, 'nome': 'Bolsa com 4 PO',    'tipo': 'gold',   'valor': '4 gp'},
        ],
    },
}


def main() -> None:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for cid, data in CLASSES.items():
        cur.execute(
            "UPDATE TB_Classe SET ArmorProfJSON=?, WeaponProfJSON=?, ToolProfJSON=?, EquipamentoInicialJSON=? "
            "WHERE Id_Classe=?",
            (
                json.dumps(data['armor'], ensure_ascii=False),
                json.dumps(data['weapons'], ensure_ascii=False),
                json.dumps(data['tools'], ensure_ascii=False),
                json.dumps(data['equipamento'], ensure_ascii=False),
                cid,
            ),
        )
        nome = cur.execute("SELECT Nome FROM TB_Classe WHERE Id_Classe=?", (cid,)).fetchone()[0]
        print(f'  {nome} (Id={cid}) atualizado: {len(data["armor"])} armor, {len(data["weapons"])} weapon, {len(data["tools"])} tool, {len(data["equipamento"])} equip')
    conn.commit()
    conn.close()
    print('OK')


if __name__ == '__main__':
    main()
