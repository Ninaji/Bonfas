# Sistema de Efeitos via Tags

> **Complementa [tags-e-cascata.md](tags-e-cascata.md).** Aquele documento
> trata de tags de **filtro** (decidir quem pode pegar uma opção do catálogo).
> Este documento trata de tags de **efeito** (descrever o que uma habilidade,
> traço ou talento *faz mecanicamente* na ficha do personagem). São conceitos
> ortogonais — cada `TagsJSON` carrega tags dos dois tipos misturadas.
>
> **🚨 Regra de portabilidade:** ver [regra-tags-universais.md](regra-tags-universais.md).
> Toda tag deve funcionar idêntico em qualquer card que a carregue (classe,
> subclasse, raça, traço, talento, ASI, sintético) — sem hardcode por fonte.

---

## 1. Motivação

Antes deste sistema, efeitos ficavam **implícitos na descrição em texto** das
habilidades/traços. Um Arcanismo +13 do Frosty era manualmente setado em
`TB_PersonagemPericia.Expertise=1` por alguém que leu a descrição de
"Conhecimentos Arcanos" e adivinhou. Isso quebrava se a hab fosse perdida
(rebuild, delevel) e duplicava esforço entre personagens com a mesma hab.

Com tags de efeito, a descrição vira **data**: `expertise:Arcanismo`. O
backend vê a hab ativa, deriva o efeito, e o frontend mostra. Sem cópia,
sem inferência por substring, sem estado órfão.

**Slogan:** descrição é prosa pra humano; tag é dado pra máquina.

---

## 2. Onde tags moram

Todas as tabelas de catálogo de efeitos têm coluna `TagsJSON TEXT NULL`:

| Tabela                  | O que guarda                             |
|-------------------------|------------------------------------------|
| `TB_ClasseHabilidade`   | habilidades de classe e subclasse        |
| `TB_TracoRacial`        | traços raciais e de essência (passivos)  |
| `TB_TalentoRacial`      | talentos de raça e essência (escolha)    |
| `TB_OpcaoJogo`          | catálogo geral (talentos de origem etc.) — usado por filtro de cascata, não por efeitos |
| `TB_Manobra`            | manobras de combate — tags são para filtro/grau |

**Convenção:** `TagsJSON` é uma string contendo um JSON-array de strings.
Vazio ou `NULL` = sem tags. Toda tag é do tipo `prefixo:valor` ou
`prefixo` standalone (raro).

---

## 3. Vocabulário canônico

### 3.1 Pickers (escolha N opções na hora de criar/editar o personagem)

Trigger uma UI de seleção. O `N` é o número de slots.

| Tag                     | Onde aplica       | Backend grava em                              |
|-------------------------|-------------------|-----------------------------------------------|
| `pick:pericia:N`        | `TB_TracoRacial`  | `TB_PersonagemEscolhaPericia(pid,origem,slot,id_pericia)` |
| `pick:idioma:N`         | `TB_TracoRacial`  | `TB_PersonagemIdioma` com `Origem='pick:<Traço>:<slot>'` |
| `pick:ferramenta:N`     | `TB_TracoRacial`  | mesma tabela `TB_PersonagemIdioma`, `Tipo='ferramenta'` |

Aplicados hoje:
- Habilidoso (Humano) → `pick:pericia:2`
- Poliglota (Humano) → `pick:idioma:2`
- Jeitinho Humano → `pick:ferramenta:2`

### 3.2 Perícias (efeito sobre `TB_PersonagemPericia`)

| Tag                       | Efeito                                                 |
|---------------------------|--------------------------------------------------------|
| `prof:<NomePericia>`      | personagem fica proficiente (`+BP`)                    |
| `expertise:<NomePericia>` | expertise (`+2×BP`); implica proficiência também       |

`<NomePericia>` é o nome humano-legível como aparece em `TB_PersonagemPericia.Nome` (case-insensitive). Ex.: `expertise:Arcanismo`.

Aplicados hoje:
- Conhecimentos Arcanos (Cav.Arcano Nv 10) → `expertise:Arcanismo`
- Táticas Arcanas (Cav.Arcano Nv 3) → `prof:Arcanismo`

### 3.3 Testes de Resistência

| Tag                       | Efeito                                                 |
|---------------------------|--------------------------------------------------------|
| `save-prof:<Atributo>`    | atributo entra em `state.saves_proficientes`           |

`<Atributo>` aceita nome longo PT-BR (`Forca`, `Constituicao`, `Inteligencia`...).

Aplicados hoje:
- Conhecimentos Arcanos → `save-prof:Inteligencia`

### 3.4 Resistências, Imunidades, Vulnerabilidades de **dano**

| Tag                       | Efeito                                                 |
|---------------------------|--------------------------------------------------------|
| `resist:<Elemento>`       | resistência (dano metade)                              |
| `immune:<Elemento>`       | imunidade (sem dano)                                   |
| `vuln:<Elemento>`         | vulnerabilidade (dano dobro)                           |

**`<Elemento>` validado contra `ELEMENTOS_CANONICOS`** em `app.py` (frozenset
de 13 valores oficiais 5.5e BR). Tag fora da lista é ignorada com log.

```
Ácido, Concussão, Cortante, Energia, Fogo, Frio, Necrótico,
Perfurante, Psíquico, Radiante, Raio, Trovejante, Veneno
```

Aplicados:
- Sangue da Umbra e Fogo → `resist:Necrótico`
- Resiliência da Pedra → `resist:Veneno`
- *Auto-derivado*: `Linhagem.Elemento` (ex.: Orgulho → resist Fogo) é injetado pelo backend sem precisar de tag literal.

### 3.5 Imunidade / vantagem em **condição** (≠ dano)

⚠️ **Veneno (dano) ≠ Envenenado (condição).** Não confundir.

| Tag                              | Efeito                                          |
|----------------------------------|-------------------------------------------------|
| `cond-immune:<Condição>`         | condição não pode ser aplicada                  |
| `adv-cond:<Condição>`            | vantagem em save pra evitar/encerrar a condição |

**`<Condição>` validado contra `CONDICOES_CANONICAS`** (frozenset de 15
valores oficiais 5.5e BR):

```
Agarrado, Amedrontado, Atordoado, Caído, Cego, Enfeitiçado,
Envenenado, Exaustão, Incapacitado, Inconsciente, Invisível,
Paralisado, Petrificado, Restringido, Surdo
```

Aplicados:
- Resiliência da Pedra → `adv-cond:Envenenado` (combo com `resist:Veneno`)
- Instinto Humano → `adv-cond:Exaustão`
- Ancestralidade Feérica → `adv-cond:Enfeitiçado`

**Não modelar imunidades muito específicas** (ex.: "imune a magia de sono")
como tag — fica como prosa na descrição. O sistema canoniza só o
vocabulário oficial 5.5e.

### 3.6 Movimentos

| Tag                          | Efeito                                              |
|------------------------------|-----------------------------------------------------|
| `andar:<Xft>`                | override do andar base (raro)                       |
| `voar:<Xft>` / `voar:eq`     | velocidade de voo (`eq` = igual ao andar)           |
| `nadar:<Xft>` / `nadar:eq`   | velocidade de natação                               |
| `cavar:<Xft>` / `cavar:eq`   | velocidade de cavar                                 |

`X` é número inteiro de pés. `:eq` resolve dinamicamente para o valor de
`andar` no momento da serialização — se andar mudar (talento, item),
`voar:eq` segue junto.

Backend devolve `state.movimentos = { andar: {ft, m, origem}, voar: {…}, ... }`.
A coluna `TB_Personagem.Velocidade` (texto livre tipo `"9 m / 30 ft"`) é
parseada pra extrair o `andar` base — apenas o valor em pés conta.

Aplicados:
- Asas da Condenação → `voar:eq`

### 3.7 Tags categoriais (standalone, sem `:`)

| Tag           | Significado                                      |
|---------------|--------------------------------------------------|
| `conjurador`  | hab CONCEDE Conjuração ou Magia de Pacto base   |
| `infernal`    | tag descritiva pré-existente; não tem efeito derivado hoje |

Usadas pra documentar categoria. Aparecem como badge informacional na UI;
não afetam state derivado. Aplicado por regex em `migrate_hab_tags.py` em
toda hab "Conjuração" / "Conjuração de Magias" / "Magia de Pacto".

---

## 4. Pipeline backend

```
┌─────────────────┐    ┌──────────────┐    ┌───────────────────┐
│ TagsJSON em hab │ ── │ aggregator   │ ── │ state.X derivado  │
│ + traço + tal   │    │ (personagem_ │    │ - pericias        │
│ + auto_efeitos  │    │  full)       │    │ - saves_prof      │
│ + manuais (BD)  │    │              │    │ - resistencias    │
└─────────────────┘    └──────────────┘    │ - condicoes       │
                                           │ - movimentos      │
                                           │ - escolhas_pericia│
                                           │ - escolhas_idioma │
                                           └───────────────────┘
```

Localizado em `app.py:personagem_full()`. Os passos:

1. Carrega `habs_cls`, `habs_sub`, `tracos`, `talentos_full` (filtrados por nível/raça/lin/ess).
2. `_agg_tags_from(items)` — varre `TagsJSON` de cada um, popula `tag_origem: list[(tag, origem_nome)]`.
3. Para cada categoria de tag:
   - Filtra `tag_origem` pelo prefixo
   - Valida valor contra lista canônica (quando aplicável)
   - Aplica em `state.<X>` ou retorna lista derivada
4. Inclui no `jsonify` final.

**Origem viaja com o efeito.** Cada item derivado carrega `Origem` (nome
do traço/hab que produziu a tag). O frontend usa pra tooltip/debug.

---

## 5. Pipeline frontend (`static/ficha.js`)

### 5.1 Badges ao lado do nome

`renderTagBadges(tagsJSON)` é chamado em `fmtHab` e `fmtTraco`. Mapeamentos:

- `TAG_LABEL` — prefixos `prefixo:valor` → `{label, cls}`
- `TAG_LABEL_STANDALONE` — tags sem `:` (categoriais) → `{label, cls}`

CSS: `.tag-badge` base + variante `.tag-<algo>` (`.tag-pick`, `.tag-prof`,
`.tag-exp`, `.tag-save`, `.tag-resist`, `.tag-immune`, `.tag-vuln`,
`.tag-conjurador`, `.tag-move`).

Hover no badge mostra a tag literal (debug).

### 5.2 Slots de picker (`pick:*:N`)

Em `fmtTraco`: detecta `pick:(pericia|idioma|ferramenta):N` via regex e
chama `renderPickSlots(t, kind, n)` que produz N slots com a UI padrão
`tier-slot empty/filled` + `× remove`.

Click vazio → `openPicker()` filtrando candidatos.
Click `×` → `DELETE /api/personagens/<pid>/escolhas-(pericia|idioma)/<origem>/<slot>` → re-render.

### 5.3 Widget de movimentos

Substituiu `ca-circle` de VEL. Container `.vel-box` mostra 4 linhas
(`andar`, `voar`, `nadar`, `cavar`) com ícone+nome à esquerda e
`Xft / Xm` à direita. Linhas sem movimento mostram `—` cinza.

### 5.4 Caixas de resistência

5 caixas em vez de 3 (separadas por dano vs condição):
- Resistências (dano)
- Imunidades (dano)
- Vulnerabilidades
- Imune a Condição
- Vantagem vs. Condição

Cada item carrega tooltip da `Origem`.

---

## 6. Endpoints novos desta família

| Método | Rota                                                      | Função                       |
|--------|-----------------------------------------------------------|------------------------------|
| POST   | `/api/personagens/<pid>/escolhas-pericia`                 | upsert pick de perícia       |
| DELETE | `/api/personagens/<pid>/escolhas-pericia/<origem>/<slot>` | esvazia slot                 |
| POST   | `/api/personagens/<pid>/escolhas-idioma`                  | upsert pick (idioma/ferr.)   |
| DELETE | `/api/personagens/<pid>/escolhas-idioma/<origem>/<slot>`  | esvazia slot                 |
| PUT    | `/api/personagens/<pid>/pericias/<peric_id>`              | toggle prof/expertise BASE (não pickup) |

POST `/escolhas-idioma` é **upsert smart**: se o nome já existe em
`TB_PersonagemIdioma` com qualquer origem, move pra `pick:<Traço>:<slot>`
em vez de duplicar.

---

## 7. Migrations (idempotentes)

- `migrate_traco_tags.py` — tags em `TB_TracoRacial` (Habilidoso, Poliglota, Jeitinho, Sangue da Umbra e Fogo, etc.)
- `migrate_hab_tags.py` — tags em `TB_ClasseHabilidade` (Conhecimentos Arcanos, Táticas Arcanas, Conjuração via regex)
- `migrate_talento_tags.py` — tags em `TB_TalentoRacial` (Asas da Condenação)
- `migrate_escolha_pericia.py` — cria `TB_PersonagemEscolhaPericia` + migra Frosty

Todos fazem backup `bonfas.db.bak.<ts>` antes de qualquer ALTER/INSERT.
Helper `_merge_tags()` em `migrate_hab_tags.py` preserva tags existentes
em vez de sobrescrever.

---

## 8. Como adicionar nova hab/traço com efeito

1. Edite `migrate_hab_tags.py` (ou `migrate_traco_tags.py`/`migrate_talento_tags.py`)
2. Adicione entrada no `TAGS_BY_NOME` (match exato) ou `TAGS_BY_NOME_PATTERN` (regex)
3. Rode `python migrate_*.py` — backup automático, idempotente
4. Recarregue a ficha — efeito aplica imediatamente (Flask debug auto-reload)

Exemplo:
```python
TAGS_BY_NOME = {
    'Improvisador Sagaz': ['pick:pericia:1'],   # talento Erthari Nv 5+
    'Vontade de Ferro':   ['save-prof:Sabedoria'],  # talento Humano Nv 9+
    'Camuflagem Anfíbia': ['nadar:eq', 'resist:Frio'],
}
```

---

## 9. Como adicionar novo prefixo de tag

1. Decidir: tag derivada (afeta state) ou só categorial (badge informativo)?
2. Se derivada:
   - `app.py`: parser do prefixo no aggregator (`personagem_full`)
   - Nova chave no payload (`state.<algo>`)
   - Frontend: consumir essa chave no widget apropriado
3. Adicionar entrada em `TAG_LABEL` (prefixo:valor) ou `TAG_LABEL_STANDALONE` (sem `:`)
4. CSS: `.tag-<nome>` com cor distinta
5. Documentar aqui no §3

Se for elemento/condição/etc. com vocabulário canônico, atualizar a
constante apropriada em `app.py` (ex.: `ELEMENTOS_CANONICOS`).

---

## 10. Anti-padrões

- **Não persistir efeito derivado em tabela base.** Ex.: NÃO setar
  `TB_PersonagemPericia.Proficiente=1` direto quando a prof vem de hab.
  Use a tag e deixe o backend derivar — caso contrário, perder a hab
  deixa estado órfão.

- **Não usar substring matching no frontend pra inferir efeito.** Se
  precisa saber se personagem tem voo, leia `state.movimentos.voar`,
  não `if /asas/i.test(talento.Nome)`.

- **Não inventar valores de elemento/condição.** Use só os canônicos.
  Para homebrew novo, adicionar à constante em `app.py` primeiro.

- **Não confundir tags de filtro (`tags ⊆ personagem.tags` no
  [tags-e-cascata.md](tags-e-cascata.md)) com tags de efeito (este
  documento).** Estão na mesma `TagsJSON` mas servem propósitos
  diferentes — o backend trata cada uma na sua etapa.

---

*Versão 1 — implementado durante refactor da ficha do Frosty (Mai/2026).
Frosty é o personagem-canônico de teste deste sistema (Humano + Essência
Infernal Orgulho, Cavaleiro Arcano Nv 16).*
