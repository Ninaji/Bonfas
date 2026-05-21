# Bonfas

Backend + UI de criação automática de fichas de personagem para o RPG
**Bonfire Tales** (homebrew D&D 5.5). Flask + SQLite + Vanilla JS.

O banco já vem **populado e versionado** (`bonfas.db`) — basta clonar,
instalar as dependências e rodar para ver todas as 13 classes, subclasses,
magias, equipamentos e personagens de exemplo.

---

## O que tem

- **Ficha interativa** (`/ficha/<id>`) com cascata de escolhas:
  raça → linhagem → essência → sub-linhagem, classe → subclasse → talentos,
  todos auto-populados do catálogo.
- **13 classes completas** (Nv 1–20) com subclasses, features e descrições
  limpas: Guerreiro, Mago, Feiticeiro, Ladino, Druida, Bardo, Bárbaro,
  Artífice, Clérigo, Paladino, Monge, Místico, Caçador.
- **Cálculo automático** de PV, bônus de proficiência, testes de
  resistência, perícias, slots de magia e limites (manobras, truques,
  infusões, estilos, etc.) — baseado na progressão oficial de cada classe.
- **Substrate de tags universal**: toda escolha selecionável é dirigida por
  tags (`pick:<tipo>:N`, `+<chave>:N`, flat gates), sem código hardcoded por
  classe. Campos especiais (Surto Selvagem do Druida, Estilos de Dança do
  Bardo, Infusões do Artífice) reusam o mesmo motor. Ver
  [`docs/tags-e-cascata.md`](docs/tags-e-cascata.md).
- **Widget de equipamento** (`/`) com silhueta + linhas conectoras para os
  slots do corpo e autocomplete do catálogo de items (1381 itens SRD).
- **Personagens de exemplo**: Frosty (Guerreiro), Arthus (Druida), Kenji
  (Bárbaro), Lynn (Artífice), Sam (Monge), Russ (Caçador), Haruhime
  (Místico), Katherine (Paladino), Lyra (Bardo).

## Stack

- **Python 3** + Flask (backend, `app.py`)
- **SQLite** (um arquivo, `bonfas.db` — já incluído no repo)
- **Vanilla JS + CSS** (frontend sem bundler, `static/`)

## Como rodar

```bash
git clone https://github.com/Ninaji/Bonfas.git
cd Bonfas
pip install -r requirements.txt
python app.py            # usa o bonfas.db que já vem no repo
# abre http://127.0.0.1:5000  (lista de fichas em /, ficha em /ficha/<id>)
```

Não é preciso popular nada: o `bonfas.db` já contém todo o conteúdo.
Para recriar o schema do zero (DB vazio), use `python init_db.py`.

> **Deploy:** o app é Flask (servidor), então **não roda em GitHub Pages**
> (que só serve arquivos estáticos). Para hospedar com edição compartilhada,
> use um serviço que roda Python (Render, Railway, Fly.io, PythonAnywhere, VPS).

## Estrutura do projeto

```
Bonfas/
├── app.py                # Flask backend (endpoints REST + páginas)
├── bonfas.db             # SQLite POPULADO (fonte de verdade do runtime)
├── requirements.txt      # Flask + Flask-Cors
├── init_db.py            # cria um bonfas.db vazio a partir do schema
├── schema.sql            # DDL principal
├── static/
│   ├── ficha.js / .css   # renderizador da ficha interativa
│   ├── equipment.js/.css # widget de equipamento
│   ├── debug.js / .css    # painel de debug
│   └── *.png / *.svg      # assets
├── templates/
│   ├── index.html         # home / lista de fichas
│   ├── ficha.html
│   └── debug.html
├── docs/                 # wiki técnica interna
│   ├── tags-e-cascata.md
│   ├── sistema-de-efeitos-via-tags.md
│   └── ...
└── CLAUDE.md             # regras de conteúdo e padrões obrigatórios
```

### Pipeline de população (não versionado)

Os scripts de ETL que constroem o `bonfas.db` ficam **fora do repo**
(gitignored) e vivem apenas localmente — o resultado canônico é o próprio
`bonfas.db` versionado. O padrão por classe é:

- `parse_<classe>_full.py` — lê o dump HTML do WorldAnvil e gera JSONs
  (meta, features, subs)
- `migrate_<classe>_full.py` — wipe + reinsert no DB, aplica tags
- `<classe>_descricoes.py` + `apply_<classe>_descricoes.py` — descrições
  limpas escritas à mão (substituem o output cru do parser)
- `seed_<personagem>.py` — cria personagens de exemplo

## Padrão "Tags + Cascata + Auto-populate"

Toda escolha selecionável segue este padrão (ver
[`docs/tags-e-cascata.md`](docs/tags-e-cascata.md)):

- **Filtro**: `opcao.tags ⊆ personagem.tags`
- **UI**: N slots vazios clicáveis (não botão único `+`)
- **Backend**: recebe a escolha e auto-popula nome/descrição do catálogo
- **Contador**: `X/Y` calculado da progressão (via `n_por_nivel`)

Famílias de tag: `pick:<tipo>:N` (slots), `+<chave>:N` (acumulador),
`<flat>` (gate). Princípio: **tag > código hardcoded** — a progressão vive
na tag, não em tabelas/ifs por classe.

## Regras de conteúdo

**Regra #0 (ver [CLAUDE.md](CLAUDE.md)):** nunca inventar nomes de conteúdo
do jogo. Tudo vem 1:1 de dumps HTML oficiais do WorldAnvil (mantidos
localmente, fora do repo por copyright). O SRD D&D 5e é fonte autorizada
para items (licença OGL/CC).

## Licença

Código fonte: MIT (ver [LICENSE](LICENSE)).
Conteúdo do jogo Bonfire Tales: copyright do criador do mundo.
