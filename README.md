# Bonfas

Backend + UI de criação automática de fichas de personagem para o RPG
**Bonfire Tales** (homebrew 5.5). Flask + SQLite + Vanilla JS, com
importação de conteúdo oficial a partir de dumps HTML do WorldAnvil.

![ficha preview](docs/preview.png)

---

## O que tem

- **Ficha interativa** (`/ficha/<id>`) com cascata de escolhas:
  raça → linhagem → essência → sub-linhagem, classe → subclasse → talentos,
  todos auto-populados do catálogo.
- **Cálculo automático** de HP, bônus de proficiência, testes de
  resistência, perícias e limites (manobras conhecidas, truques, etc.) —
  tudo baseado na progressão oficial da classe.
- **Padrão universal** de tags + cascata + auto-populate aplicado em
  todos os subsistemas selecionáveis. Ver
  [`docs/tags-e-cascata.md`](docs/tags-e-cascata.md).
- **Parsers** que lêem dumps HTML do WorldAnvil (salvos em `paginas/`) e
  populam o DB 1:1 com o conteúdo oficial — nunca inventa nomes.
- **Widget de equipamento** (`/`) com silhueta + linhas conectoras para
  todos os slots do corpo, autocomplete do catálogo de items.

## Stack

- **Python 3** + Flask (backend, `app.py`)
- **SQLite** (um arquivo, `bonfas.db`)
- **Vanilla JS + CSS** (frontend sem bundler, `static/`)
- Opcional: Playwright para scraping alternativo

## Como rodar

```bash
pip install -r requirements.txt
python init_db.py                           # cria bonfas.db com schema base
python import_items.py C:/caminho/items.csv # popula catálogo de items (CSV do usuário)
python seed_classes.py                      # seed mínimo de 13 classes
# coloque dumps HTML oficiais em paginas/
python seed_humano_infernal.py              # raça Humano + essência Infernal
python parse_classe_v2.py paginas/guerreiro.html guerreiro
python parse_manobras.py paginas/guerreiro.html guerreiro
python parse_talentos.py paginas/humano.html humano
python parse_talentos.py paginas/infernal.html infernal

python app.py                               # http://127.0.0.1:5000/ficha/1
```

## Estrutura do projeto

```
bonfas/
├── app.py                       # Flask backend (endpoints REST + páginas)
├── schema.sql                   # DDL principal (raças, classes, items, personagem)
├── init_db.py                   # cria bonfas.db a partir de schema.sql
├── build_classes_db.py          # gera cópia minimalista só com 6 tabelas
│                                 de classes (arquitetura do ER oficial)
├── parse_artigo.py              # parser genérico de view-source
├── parse_classe_v2.py           # parser de classe com classificação por
│                                 nomes universais + keywords de subclasse
├── parse_talentos.py            # parser de talentos raciais/essenciais
├── parse_manobras.py            # parser de manobras (catálogo TB_Manobra)
├── seed_*.py                    # seeds pontuais
├── wa_client.py                 # cliente READ-ONLY Boromir API do WorldAnvil
├── scrape_playwright.py         # fallback via Playwright
├── static/
│   ├── ficha.js / ficha.css     # renderizador da ficha interativa
│   ├── equipment.js / .css      # widget de equipamento
│   ├── Aventureiro.png
│   └── ...
├── templates/
│   ├── ficha.html
│   └── index.html               # demo do widget de equipamento
├── docs/                        # wiki técnica interna
│   ├── tags-e-cascata.md
│   └── talentos-raca-essencia.md
├── paginas/                     # (gitignored) dumps HTML oficiais
└── CLAUDE.md                    # regras e padrão obrigatório
```

## Arquitetura do DB

### Tabelas principais

- **Catálogo 5e-SRD de items:** `TB_Item`, `TB_ItemSlot`
- **Raças / Essências:** `TB_Raca`, `TB_Linhagem`, `TB_Essencia`,
  `TB_EssenciaLinhagem`, `TB_TracoRacial`
- **Classes:** `TB_Classe`, `TB_Subclasse`, `TB_RecursoClasse`,
  `TB_ClasseHabilidade`, `TB_OpcaoJogo`, `TB_AcessoOpcao`
- **Talentos raciais:** `TB_TalentoRacial`
- **Manobras de combate (catálogo):** `TB_Manobra`
- **Personagem:** `TB_Personagem`, `TB_PersonagemEscolha`,
  `TB_PersonagemAtributo`, `TB_PersonagemTalento`,
  `TB_PersonagemHabilidadeOpcao`, `TB_PersonagemTecnica`,
  `TB_PersonagemInventarioItem`, `TB_PersonagemMagia`,
  `TB_PersonagemPericia`, `TB_PersonagemIdioma`,
  `TB_PersonagemResistencia`, `TB_PersonagemPersonalidade`,
  `TB_EquipamentoPersonagem`

### O modelo canônico de "opções selecionáveis"

Seguindo o ER de classes:

| Tabela | Descrição |
|---|---|
| `TB_Classe` | Info da classe base |
| `TB_Subclasse` | Subclasse (Id_Classe FK) |
| `TB_RecursoClasse` | Valores da tabela de progressão (dado de combate, bônus de prof, slots de magia, truques — coisas não calculadas por fórmula) |
| `TB_ClasseHabilidade` | Features que o personagem adquire ao nível X (Surto de Ação, Ataque Extra) |
| `TB_OpcaoJogo` | **Habilidades opcionais selecionáveis** (manobras, eldritch invocations, segredos de caçador) |
| `TB_AcessoOpcao` | Diz quais classes/subclasses têm acesso a cada opção |

Esse modelo é preservado em uma cópia minimalista
`bonfas_classes.db` (gerada por `build_classes_db.py`).

## Regras de conteúdo

**Regra #0 (ver [CLAUDE.md](CLAUDE.md)):** nunca inventar nomes de conteúdo
do jogo. Tudo vem 1:1 de:

1. Dumps HTML oficiais em `paginas/*.html` (gitignored — copyright do mundo)
2. No futuro: API Boromir do WorldAnvil (requer Application Key)

O SRD D&D 5e é fonte autorizada para items (licença OGL/CC).

## Padrão "Tags + Cascata + Auto-populate"

Toda escolha selecionável do catálogo segue este padrão (ver
[`docs/tags-e-cascata.md`](docs/tags-e-cascata.md)):

- **Filtro**: `talento.tags ⊆ personagem.tags` (nunca intersecção)
- **UI**: `N slots vazios clicáveis` (não botão único `+`)
- **Backend**: recebe `id_x` e auto-popula nome/descrição do catálogo
- **Contador**: `X/Y` calculado da tabela de progressão

## Segredos e dados sensíveis

- `.env.txt` (ignorado): token da API do WorldAnvil
- `paginas/*.html` (ignorado): conteúdo do WorldAnvil
- `bonfas.db` (ignorado): contém o conteúdo populado — regenerável dos
  scripts de seed/parse

## Licença

Código fonte: MIT (ver [LICENSE](LICENSE)).
Conteúdo do jogo Bonfire Tales: copyright do criador do mundo.
