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

## Referência de Tags

Tags ficam em `TagsJSON` (uma lista) das tabelas `TB_ClasseHabilidade`,
`TB_OpcaoJogo`, `TB_TracoRacial`, `TB_TalentoRacial`, `TB_Classe`. Podem ser
**string** (`"conjurador"`) ou **objeto** com progressão
(`{"tag":"pick:metamagia","n_por_nivel":{"3":2,"10":3}}`).

### 1. Filtro — quais opções aparecem para o personagem

Regra: uma opção só aparece se `opcao.tags ⊆ personagem.tags`.

| Tag | Para que serve |
|---|---|
| `humano`, `infernal`, `erthari`, `folken`… | slug de raça/linhagem/essência — talento/traço só some pra quem tem aquele slug |
| `nv1`, `nv4` | nível mínimo (talento de Nv 4 só aparece a partir do Nv 4) |
| `for13`,`dex13`,`con13`,`int13`,`sab13`,`car13` | pré-requisito de atributo ≥ 13 |

### 2. `pick:<tipo>:N` — abre N slots de escolha (vira um campo na ficha)

Cada `pick` soma N slots; múltiplas tags do mesmo tipo acumulam. A forma
objeto com `n_por_nivel` resolve N pela progressão do nível.

| Tag | Campo / o que escolhe |
|---|---|
| `pick:pericia:N` | N perícias para **proficiência** |
| `pick:expertise:N` | N perícias para **especialização** (dobra o bônus de prof.) |
| `pick:idioma:N` / `pick:ferramenta:N` | idiomas / ferramentas (catálogo + digitar) |
| `pick:talento-geral:N` | talentos gerais |
| `pick:talento-origem:N` | talentos de origem (ex.: Raízes Profundas dá +1) |
| `pick:texto:N` | escolha finita/livre (com `filter` e `descricoes` opcionais) |
| `pick:estilo-de-luta:N` | Estilos de Luta (Guerreiro/Paladino) |
| `pick:estilo-danca:N` | **Estilos de Dança** (Bardo da Dança — pool de Estilos de Ki do Monge; custo lido como Inspiração Bárdica) |
| `pick:metamagia:N` | **Metamagias** (Feiticeiro) |
| `pick:infusao-artificer:N` | **Infusões** (Artífice) — cada slot recebe infusão do catálogo (filtrada por nível) ou **Replicar Item Mágico** |
| `pick:manifestacao-mistica:N` | Manifestações Místicas (Místico) |
| `pick:ordem-sagrada:N` | Ordens Sagradas (Paladino/Clérigo) |
| `pick:doutrina-marcial:N` | Doutrinas Marciais |
| `pick:pericia-cortesao:N` | Perícias de Cortesão |
| `pick:alianca-selvagem-companheiro:N` | Companheiro de Aliança Selvagem (Caçador) |

### 3. `+<chave>:N` — acumulador (soma um contador)

| Tag | Efeito |
|---|---|
| `+maestrias-arma:N` | soma N ao nº de Maestrias de Arma (Ladino/Bárbaro via `n_por_nivel`) |

### 4. Gates flat (presença = liga a seção/efeito)

| Tag | Liga |
|---|---|
| `conjurador` | painel de **Magias** (todo conjurador) |
| `surto-selvagem` | campo **Surto Selvagem** (Druida); `druida-lua` muda o CR para ⌈nível/3⌉ |
| `pontos-feiticaria` | painel de **Pontos de Feitiçaria** (Feiticeiro) |
| `estilos-ki` / `kensei-estilos` | **Estilos de Ki / Kensei** (Monge) |
| `segredos-misticos` / `feiticaria-mistica` | **Segredos Místicos** (Místico) |
| `tecnica-furtividade` | pool de **Técnicas de Furtividade** (Ladino) |
| `segredos`, `inimigo-favorito`, `evolucao-totemica` | seções do **Caçador** |
| `asi-feature` | **esconde** a feature de Aumento/Incremento de Atributo dos blocos (já está nos slots de talento) |
| `oculta-hab` | **esconde** a feature dos blocos (ex.: catálogos redundantes) |

### 5. Proficiências, defesas e efeitos diretos

| Tag | Efeito |
|---|---|
| `prof:<Perícia>` / `expertise:<Perícia>` | proficiência / especialização naquela perícia |
| `save-prof:<Atributo>` | proficiência no teste de resistência |
| `save-prof-vontade:<default>\|<alt1>,<alt2>` | save com escolha entre alternativas |
| `prof-arma:<X>` / `prof-armadura:<X>` / `prof-ferramenta:<X>` | proficiências de equipamento |
| `resist:<Elemento>` / `imune:<X>` / `cond-immune:<Cond>` | resistência / imunidade |
| `adv-cond:<Cond>` | Vantagem em saves contra a condição |
| `visao-no-escuro:<dist>` | sentido (ex.: `visao-no-escuro:36m/120ft`) |
| `escalar:eq` / `nadar:eq` / `voar:eq` | deslocamento igual ao de caminhada |
| `velocidade:+X` / `pv-por-nivel:N` / `unarmored-defense:<Atr>` | bônus diretos |
| `metamagia:<slug>` | **auto-concede** uma metamagia "sempre preparada" (ex.: Origem Divina) |
| `gate:<x>` | pré-requisito que outra opção exige presente |

### Como adicionar uma tag nova

O motor é genérico — na maioria dos casos é **só dado, sem mexer em código**:

1. **Slot novo (`pick:`)**: ponha a tag na `TagsJSON` da feature/talento.
   Ex.: `{"tag":"pick:meu-tipo","n_por_nivel":{"3":1,"10":2}}`. Se o catálogo
   de opções vive em `TB_OpcaoJogo` (Tipo=`meu-tipo`), o picker genérico já
   funciona via `/api/opcoes?tipo=meu-tipo`.
2. **Catálogo fora de `TB_OpcaoJogo`** (ex.: reuso de outra tabela): exponha
   uma lista no `/full` (`<tipo>_catalogo`) e adicione um branch no handler
   de pick em `static/ficha.js` (modelo: `estilo-danca`, `infusao-artificer`).
3. **Seção dedicada (campo próprio)**: renderize a seção no `ficha.js` quando
   a tag flat estiver em `aggregated_tags` (modelo: Surto Selvagem,
   Metamagias). Adicione o `<tipo>` aos `skipKinds` para não renderizar inline.
4. **Efeito direto** (prof/resist/save…): o backend (`_agg_tags_from` em
   `app.py`) já interpreta os prefixos conhecidos — basta usar o prefixo certo.
5. **Esconder uma feature**: marque-a com `asi-feature` ou `oculta-hab`.

Detalhes em [`docs/tags-e-cascata.md`](docs/tags-e-cascata.md),
[`docs/sistema-de-efeitos-via-tags.md`](docs/sistema-de-efeitos-via-tags.md)
e [`docs/regra-tags-universais.md`](docs/regra-tags-universais.md).

## Regras de conteúdo

**Regra #0 (ver [CLAUDE.md](CLAUDE.md)):** nunca inventar nomes de conteúdo
do jogo. Tudo vem 1:1 de dumps HTML oficiais do WorldAnvil (mantidos
localmente, fora do repo por copyright). O SRD D&D 5e é fonte autorizada
para items (licença OGL/CC).

## Licença

Código fonte: MIT (ver [LICENSE](LICENSE)).
Conteúdo do jogo Bonfire Tales: copyright do criador do mundo.
