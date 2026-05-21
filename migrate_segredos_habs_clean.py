"""Reescreve as 3 habs Nv 1 'Segredos de Caçador: <Linha>' (ids 120/121/122) para
exibirem APENAS flavor + efeito geral da linha. A lista de segredos individuais
fica na section dedicada de Segredos (não duplica)."""
import shutil
import sqlite3
import time

DB = "bonfas.db"
ts = time.strftime("%Y%m%d-%H%M%S")
shutil.copy(DB, f"{DB}.bak.{ts}")
print(f"Backup: {DB}.bak.{ts}\n")

DESCS = {
    120: (  # Alquimia e Poções
        "\"Minha alquimia não tem rótulo, prazo de validade ou gosto bom. "
        "Misturo veneno com cura, pólvora com erva e fecho o frasco antes que "
        "exploda. Não ofereço meus frascos a ninguém por um motivo simples: o "
        "que cura meu corpo calejado provavelmente mataria um homem comum antes "
        "de chegar ao estômago.\"\n\n"
        "Efeito geral:\n\n"
        "Reagentes Instáveis. Ao escolher um Segredo da linha Alquimia e "
        "Poções, você aprende a preparar os componentes base para aquela "
        "fórmula (pastas, óleos voláteis, misturas de pós). Ao final de cada "
        "Descanso Longo, você renova seu estoque de reagentes. Enquanto tiver "
        "ao menos 1 Ponto de Segredo, você é considerado como tendo os "
        "materiais necessários para criar e ativar instantaneamente qualquer "
        "poção ou bomba que conheça.\n\n"
        "Toxicidade Exclusiva. Devido à natureza instável e tóxica dos seus "
        "preparos, eles se tornam inertes ou venenosos segundos após saírem "
        "da sua mão. Se você entregar uma dessas poções a outra criatura para "
        "que ela a use depois, a mistura se degrada em uma gosma inútil no "
        "final do seu turno. Apenas você sabe a dosagem e o momento exato de "
        "ativação (misturar, agitar ou adicionar o catalisador) para que o "
        "efeito ocorra."
    ),
    121: (  # Armadilhas e Emboscadas
        "Nem toda armadilha é madeira, ferro e corda. Às vezes é só saber "
        "onde o outro vai pisar. Aprendi a montar laços em silêncio, esconder "
        "gatilhos no caminho certo e transformar sucata em ameaça. O truque "
        "não é ter a ferramenta perfeita — é ter a ferramenta boa o bastante, "
        "pronta na hora certa.\n\n"
        "Efeito geral:\n\n"
        "Ferramentas de caça. Ao escolher um Segredo da linha Armadilhas e "
        "Emboscadas, você aprende também a preparar a ferramenta de caça "
        "associada a ele (uma rede reforçada, um arpão de tração, carga de "
        "estilhaços, ganchos, etc.). Ao final de cada Descanso Longo, você "
        "pode preparar essas ferramentas. Enquanto tiver ao menos 1 Ponto "
        "de Segredo, você é considerado como tendo à disposição uma versão "
        "funcional de cada ferramenta ligada aos Segredos de Armadilhas e "
        "Emboscadas que conhece. Se uma dessas ferramentas for perdida, "
        "danificada ou consumida, ela é reposta automaticamente ao final do "
        "próximo Descanso Longo."
    ),
    122: (  # Conhecimentos Ancestrais
        "\"Esses sinais não estão escritos em pergaminhos nem são ensinados "
        "em academias de magia. São gatilhos mentais, cicatrizes abertas na "
        "memória e gestos que doem as juntas. Um mago precisa de palavras e "
        "varinhas; eu só preciso de um segundo de foco e da vontade de ver "
        "a coisa feita. Não posso te ensinar o sinal, porque ele não é algo "
        "que eu sei — é algo que eu sou.\"\n\n"
        "Efeito geral:\n\n"
        "Mnemónica Oculta. Ao escolher um Segredo da linha Conhecimentos "
        "Ancestrais, você grava o padrão mental e somático daquele sinal "
        "(Signum) em sua memória muscular e psique. Ao final de cada Descanso "
        "Longo, você medita para realinhar esses conhecimentos. Enquanto "
        "tiver ao menos 1 Ponto de Segredo, você é capaz de canalizar a "
        "energia necessária para manifestar qualquer Sinal que conheça.\n\n"
        "Canalização Pessoal. Os Sinais não são magias externas, mas "
        "projeções da sua própria força vital e foco. Eles não podem ser "
        "escritos em pergaminhos de magia, ensinados a outros personagens "
        "ou armazenados em itens mágicos (como anéis de armazenar magia). "
        "O efeito emana diretamente de você e exige sua presença consciente "
        "para existir."
    ),
}

conn = sqlite3.connect(DB)
cur = conn.cursor()
for hid, desc in DESCS.items():
    old = cur.execute("SELECT Nome, Descricao FROM TB_ClasseHabilidade WHERE Id_Habilidade=?", (hid,)).fetchone()
    cur.execute("UPDATE TB_ClasseHabilidade SET Descricao=? WHERE Id_Habilidade=?", (desc, hid))
    print(f"id={hid} {old[0]}")
    print(f"  antes ({len(old[1] or '')} chars): {(old[1] or '')[:90]}...")
    print(f"  depois ({len(desc)} chars): {desc[:90]}...")
    print()
conn.commit()
conn.close()
print("DONE.")
