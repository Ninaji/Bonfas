"""
Inicializa o banco SQLite e popula com dados de raças 5e (SRD - domínio público).
Dados derivados da referência do D&D 5e SRD / 5e.tools (informações abertas).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "bonfas.db"
SCHEMA = Path(__file__).parent / "schema.sql"


def run_schema(conn: sqlite3.Connection) -> None:
    with open(SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


# ---------------------------------------------------------------------------
# Dados base (raças do SRD 5e)
# ---------------------------------------------------------------------------
RACAS = [
    {
        "nome": "Humano", "slug": "humano",
        "tagline": "Versáteis e ambiciosos, os filhos do curto fôlego.",
        "lore_pres": "Humanos são a raça mais adaptável e ambiciosa do multiverso, povoando praticamente todos os reinos.",
        "lore_rp": "Prosperam em missões curtas e grandes feitos. Buscam legado onde outras raças buscam permanência.",
        "lore_soc": "Formam reinos, impérios e repúblicas com rapidez. Culturalmente diversos entre regiões.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Variante", "slug": "humano-variante",
             "desc": "Ganha +1 em dois atributos, uma perícia e uma Talento inicial."},
            {"nome": "Padrão", "slug": "humano-padrao",
             "desc": "+1 em todos os atributos."},
        ],
        "tracos": [
            ("Idiomas", "Fala Comum e um idioma adicional.", 1),
            ("Deslocamento", "Deslocamento base de 9 metros.", 1),
        ],
    },
    {
        "nome": "Elfo", "slug": "elfo",
        "tagline": "Graciosos, longevos, ligados à magia ancestral.",
        "lore_pres": "Elfos são seres mágicos de graça sobrenatural, vivendo em florestas antigas e cidades atemporais.",
        "lore_rp": "Observadores pacientes; costumam considerar humanos apressados. Meditação substitui o sono.",
        "lore_soc": "Sociedades matriarcais ou meritocráticas, com longas tradições artísticas e arcanas.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Alto Elfo", "slug": "alto-elfo",
             "desc": "+1 Inteligência, aprende um truque de Mago."},
            {"nome": "Elfo da Floresta", "slug": "elfo-da-floresta",
             "desc": "+1 Sabedoria, deslocamento 10,5m, máscara da natureza."},
            {"nome": "Elfo Negro (Drow)", "slug": "drow",
             "desc": "+1 Carisma, visão no escuro aprimorada, magia drow."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Sentidos Aguçados", "Proficiência em Percepção.", 1),
            ("Ancestral Feérico", "Vantagem contra ser enfeitiçado; imune a sono mágico.", 1),
            ("Transe", "Medita 4h ao invés de dormir 8h.", 1),
        ],
    },
    {
        "nome": "Anão", "slug": "anao",
        "tagline": "Resilientes mestres da pedra e do aço.",
        "lore_pres": "Anões vivem em fortalezas-montanha, honrando clã e ancestrais.",
        "lore_rp": "Orgulhosos, diretos, rancorosos com inimigos tradicionais (goblinóides, gigantes).",
        "lore_soc": "Clãs matriarcais-patriarcais com guildas de forja, mineração e runa.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Anão das Colinas", "slug": "anao-das-colinas",
             "desc": "+1 Sabedoria, PV extras a cada nível."},
            {"nome": "Anão das Montanhas", "slug": "anao-das-montanhas",
             "desc": "+2 Força, proficiência em armaduras leves e médias."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Resiliência Anã", "Vantagem em testes contra veneno; resistência a veneno.", 1),
            ("Treinamento de Combate", "Proficiência em machados e martelos.", 1),
            ("Conhecimento de Pedra", "Perícia extra em História de trabalho em pedra.", 1),
        ],
    },
    {
        "nome": "Halfling", "slug": "halfling",
        "tagline": "Pequenos, sortudos e incansavelmente curiosos.",
        "lore_pres": "Halflings valorizam conforto, comunidade e boa comida — mas têm coragem surpreendente.",
        "lore_rp": "Calmos, simpáticos, resilientes ao medo.",
        "lore_soc": "Vilas rurais, famílias extensas, pouca hierarquia formal.",
        "permite_essencia": 0,
        "linhagens": [
            {"nome": "Pés-leves", "slug": "halfling-pes-leves",
             "desc": "+1 Carisma; pode se esconder atrás de criaturas maiores."},
            {"nome": "Robusto", "slug": "halfling-robusto",
             "desc": "+1 Constituição; vantagem adicional contra veneno."},
        ],
        "tracos": [
            ("Sortudo", "Re-rola 1 natural em d20 de ataque, teste ou resistência.", 1),
            ("Bravo", "Vantagem contra ser amedrontado.", 1),
            ("Agilidade Halfling", "Pode se mover por espaços de criaturas maiores.", 1),
        ],
    },
    {
        "nome": "Draconato", "slug": "draconato",
        "tagline": "Herdeiros do sopro dos dragões ancestrais.",
        "lore_pres": "Draconatos carregam sangue draconico, manifestando arma de sopro e resistência elemental.",
        "lore_rp": "Honrados, códigos de clã rígidos. Reverenciam feitos de armas.",
        "lore_soc": "Clãs guerreiros organizados por ancestral draconico.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Ancestral Vermelho", "slug": "draconato-vermelho",
             "desc": "Sopro de fogo em linha, resistência a fogo."},
            {"nome": "Ancestral Branco", "slug": "draconato-branco",
             "desc": "Sopro de frio em cone, resistência a frio."},
            {"nome": "Ancestral Negro", "slug": "draconato-negro",
             "desc": "Sopro de ácido em linha, resistência a ácido."},
        ],
        "tracos": [
            ("Arma de Sopro", "Uso único recuperado em descanso curto; dano escala com nível.", 1),
            ("Resistência Draconica", "Resistência ao tipo de dano do ancestral.", 1),
        ],
    },
    {
        "nome": "Gnomo", "slug": "gnomo",
        "tagline": "Engenhosos, curiosos, cheios de energia.",
        "lore_pres": "Gnomos são inventores natos, amantes de magia sutil e mecanismos engenhosos.",
        "lore_rp": "Entusiastas, faladores, raramente sérios. Veem a vida como experimento.",
        "lore_soc": "Comunidades isoladas em colinas ou subterrâneo; guildas artesãs.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Gnomo da Floresta", "slug": "gnomo-da-floresta",
             "desc": "+1 Destreza, truque mínima ilusão, falar com animais pequenos."},
            {"nome": "Gnomo das Rochas", "slug": "gnomo-das-rochas",
             "desc": "+1 Constituição, proficiência em ferramentas de artesão."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Esperteza Gnômica", "Vantagem em resistências de INT/SAB/CAR contra magia.", 1),
        ],
    },
    {
        "nome": "Meio-Elfo", "slug": "meio-elfo",
        "tagline": "Entre dois mundos, pertencente a nenhum.",
        "lore_pres": "Meio-elfos herdam graça élfica e ambição humana, frequentemente andarilhos.",
        "lore_rp": "Diplomatas naturais. Buscam identidade própria além das origens.",
        "lore_soc": "Raramente formam comunidades próprias; vivem em cidades humanas ou élficas.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Padrão", "slug": "meio-elfo-padrao",
             "desc": "+2 Carisma, +1 em dois atributos à escolha."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Ancestral Feérico", "Vantagem contra enfeitiçado; imune a sono mágico.", 1),
            ("Versatilidade em Perícias", "Proficiência em duas perícias à escolha.", 1),
        ],
    },
    {
        "nome": "Meio-Orc", "slug": "meio-orc",
        "tagline": "Força bruta temperada por resiliência humana.",
        "lore_pres": "Meio-orcs combinam o vigor orcuish com a adaptabilidade humana. Muitas vezes lutam contra estereótipos.",
        "lore_rp": "Intensos emocionalmente; valorizam lealdade e coragem.",
        "lore_soc": "Vivem em tribos orcas, cidades humanas ou como párias andarilhos.",
        "permite_essencia": 0,
        "linhagens": [
            {"nome": "Padrão", "slug": "meio-orc-padrao",
             "desc": "+2 Força, +1 Constituição."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Resistência Implacável", "Ao chegar a 0 PV, vai a 1 PV (1x por descanso longo).", 1),
            ("Ataques Selvagens", "Rola dado extra em crítico corpo a corpo.", 1),
        ],
    },
    {
        "nome": "Tiefling", "slug": "tiefling",
        "tagline": "Marcados pelo sangue infernal que não escolheram.",
        "lore_pres": "Tieflings carregam herança de infernais ancestrais — chifres, caudas, tons inumanos de pele.",
        "lore_rp": "Autossuficientes por necessidade; reagem ao preconceito com ironia ou desafio.",
        "lore_soc": "Raramente em comunidades próprias; marginais em cidades humanas.",
        "permite_essencia": 1,
        "linhagens": [
            {"nome": "Linhagem de Asmodeus", "slug": "tiefling-asmodeus",
             "desc": "+2 Carisma, +1 Inteligência; taumaturgia, repreensão infernal, escuridão."},
        ],
        "tracos": [
            ("Visão no Escuro", "Enxerga no escuro até 18 metros.", 1),
            ("Resistência Infernal", "Resistência a dano de fogo.", 1),
            ("Legado Infernal", "Truque taumaturgia; magias infernais em níveis superiores.", 1),
        ],
    },
]

# Essências (conceito próprio do universo — sem vínculo com uma raça específica)
ESSENCIAS = [
    {"nome": "Essência Arcana", "slug": "ess-arcana",
     "lore_pres": "Fluxo de Weave bruto impregnado na alma desde o nascimento.",
     "lore_rp": "Sente a vibração da magia em tudo; atraída por anomalias mágicas.",
     "lore_soc": "Rara — temida e cobiçada por academias arcanas."},
    {"nome": "Essência Divina", "slug": "ess-divina",
     "lore_pres": "Fragmento de poder celestial residente no portador.",
     "lore_rp": "Dividido entre vontade pessoal e propósito superior.",
     "lore_soc": "Reverenciada em ordens religiosas; associada a profecias."},
    {"nome": "Essência Primal", "slug": "ess-primal",
     "lore_pres": "Conexão espiritual com o mundo natural bruto.",
     "lore_rp": "Instintiva, ligada a lugares de poder silvestre.",
     "lore_soc": "Reconhecida por druidas e tribos da fronteira."},
    {"nome": "Essência Sombria", "slug": "ess-sombria",
     "lore_pres": "Vestígio de umbra penetrando a alma — sem implicar maldade.",
     "lore_rp": "Distante, observadora, com afinidade por locais crepusculares.",
     "lore_soc": "Vista com desconfiança, rotulada injustamente como corrupção."},
]


def seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Essências
    ess_ids = {}
    for e in ESSENCIAS:
        cur.execute(
            """INSERT INTO TB_Essencia (Nome, Slug, LorePresentation, LoreRoleplay, LoreSociety)
                   VALUES (?, ?, ?, ?, ?)""",
            (e["nome"], e["slug"], e["lore_pres"], e["lore_rp"], e["lore_soc"]),
        )
        ess_ids[e["slug"]] = cur.lastrowid

    # Raças + linhagens + traços
    for r in RACAS:
        cur.execute(
            """INSERT INTO TB_Raca
                   (Nome, Slug, Tagline, LorePresentation, LoreRoleplay, LoreSociety, PermiteEssencia)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (r["nome"], r["slug"], r["tagline"], r["lore_pres"],
             r["lore_rp"], r["lore_soc"], r["permite_essencia"]),
        )
        id_raca = cur.lastrowid

        lin_ids = []
        for l in r["linhagens"]:
            cur.execute(
                """INSERT INTO TB_Linhagem
                       (Id_Raca, Nome, Slug, Descricao, LorePresentation, LoreRoleplay, LoreSociety)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id_raca, l["nome"], l["slug"], l["desc"], None, None, None),
            )
            lin_ids.append(cur.lastrowid)

        for nome, desc, nivel in r["tracos"]:
            cur.execute(
                """INSERT INTO TB_TracoRacial
                       (Id_Raca, Id_Linhagem, Id_Essencia, Nome, Descricao, NivelRequisito)
                       VALUES (?, NULL, NULL, ?, ?, ?)""",
                (id_raca, nome, desc, nivel),
            )

    conn.commit()


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        run_schema(conn)
        seed(conn)
        count = conn.execute("SELECT COUNT(*) FROM TB_Raca").fetchone()[0]
        lin = conn.execute("SELECT COUNT(*) FROM TB_Linhagem").fetchone()[0]
        tr = conn.execute("SELECT COUNT(*) FROM TB_TracoRacial").fetchone()[0]
        ess = conn.execute("SELECT COUNT(*) FROM TB_Essencia").fetchone()[0]
        print(f"OK  raças={count}  linhagens={lin}  tracos={tr}  essencias={ess}")
        print(f"DB: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
