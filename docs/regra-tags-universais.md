# Regra de Tags Universais

> **Regra do projeto Bonfas.** Toda tag — perícia, idioma, ferramenta,
> resistência, imunidade, condição, save, movimento, PV, picker — DEVE
> funcionar exatamente igual em qualquer card que a carregue, independente
> da origem (classe, subclasse, raça, linhagem, essência, traço, talento de
> raça, talento de origem, talento de classe Nv 4+, ou card sintético).
>
> **Tag é dado portável.** Se uma tag tem mecânica num card, ela tem a
> mesma mecânica em qualquer outro card. O sistema não pode ter "tag X só
> funciona em traço racial" ou "tag Y só em hab de classe".

Complementa [`sistema-de-efeitos-via-tags.md`](sistema-de-efeitos-via-tags.md)
(vocabulário) e [`tags-e-cascata.md`](tags-e-cascata.md) (filtros de
catálogo). Este doc trata de **portabilidade**.

---

## 1. Por que esta regra existe

Antes da regra, mecânicas idênticas viviam em handlers separados por
fonte. Por exemplo:

- `pv-por-nivel:2` só era lido em **slots de talento de origem** — então
  o mesmo efeito num talento de classe (Tough+ pegado num ASI) não
  contava.
- `pick:pericia:N` só era processado em `TB_TracoRacial` — então não
  podia ser colado num hab de classe ou num card sintético da primeira
  classe.
- `save-prof-vontade:` iterava habs e talentos, mas não traços — uma
  trait racial com a mesma cascade não funcionava.

Consequência: cada tag nova exigia 4-5 cópias de lógica espalhadas. A
qualquer adição surgiam inconsistências (tag funciona aqui, não funciona
ali). A regra resolve isso.

---

## 2. O que torna uma tag "universal"

Uma tag é universal quando satisfaz as 4 propriedades:

1. **Identificação por prefixo**, não por contexto. O parser olha
   `prefix:value` ou `prefix` standalone. Não importa de onde a tag veio.

2. **Origem viaja com a tag.** Cada efeito derivado carrega o nome do
   item-fonte (`Origem`). Frontend usa pra tooltip/debug. O motor não
   diferencia "tag de hab" vs "tag de traço" — só sabe `(tag, origem)`.

3. **Aggregator iteração ampla.** O backend faz `_agg_tags_from(items)`
   sobre **todas** as fontes que carregam `TagsJSON`, não sobre uma só.
   Adicionar uma fonte nova é 1 linha (mais um `_agg_tags_from(...)`).

4. **Frontend agnóstico de fonte.** Helpers como
   `renderPickSlotsFromTags(tagsJSON, origem, filterList?)` operam em
   `(tag, origem)` — não inspecionam tipo de objeto. Qualquer card pode
   chamar.

---

## 3. Fontes (qualquer uma pode carregar qualquer tag)

| Fonte                         | Tabela                  | Coluna     | Exemplo                              |
|-------------------------------|-------------------------|------------|--------------------------------------|
| Classe (linha-mãe)            | `TB_Classe`             | `TagsJSON` | (vazio até preencher via /debug/classes) |
| Subclasse (linha-mãe)         | `TB_Subclasse`          | `TagsJSON` | (vazio até preencher via /debug/classes) |
| Hab de classe (Nv 1+)         | `TB_ClasseHabilidade`   | `TagsJSON` | Conhecimentos Arcanos                |
| Hab de subclasse (Nv 3+)      | `TB_ClasseHabilidade`   | `TagsJSON` | Olhar Honesto                        |
| Raça (linha-mãe)              | `TB_Raca`               | `TagsJSON` | (vazio até preencher via /debug/racas) |
| Linhagem racial (linha-mãe)   | `TB_Linhagem`           | `TagsJSON` | (vazio até preencher via /debug/racas) |
| Essência (linha-mãe)          | `TB_Essencia`           | `TagsJSON` | (vazio até preencher via /debug/essencias) |
| Sub-linhagem da essência (linha-mãe) | `TB_EssenciaLinhagem` | `TagsJSON` | (vazio até preencher via /debug/essencias) |
| Traço de raça base            | `TB_TracoRacial`        | `TagsJSON` | Habilidoso                           |
| Traço de linhagem racial      | `TB_TracoRacial`        | `TagsJSON` | Determinação Comum                   |
| Traço de essência base        | `TB_TracoRacial`        | `TagsJSON` | Sangue da Umbra e Fogo               |
| Traço de sub-linhagem da essência | `TB_TracoRacial`    | `TagsJSON` | Linhagem Orgulho                     |
| Talento de raça/essência (tier) | `TB_TalentoRacial`    | `TagsJSON` | Vontade de Ferro                     |
| Talento de classe Nv 4+ (ASI) | `TB_PersonagemTalento`  | `TagsJSON` | Resilient (Constitution)             |
| Talento de origem             | `TB_OpcaoJogo` Tipo='talento-origem' | `TagsJSON` | Robusto (`pv-por-nivel:2`) |
| Item (linha-mãe, **não consumida pelo agregador hoje**) | `TB_Item` | `TagsJSON` | reservado pra tela debug futura de itens |
| Card sintético da primeira classe | virtual (gerado em `personagem_full`) | (sintético) | "Proficiências de Classe" com `pick:pericia:N` |
| Card sintético de equipamento     | virtual                 | (sem tag — só lista) | "Equipamento Inicial"  |
| Background (futuro)           | a definir               | a definir  | a definir                            |

> **Coluna `TagsJSON` adicionada em `TB_Raca`, `TB_Linhagem`, `TB_Classe`, `TB_Subclasse`, `TB_Essencia`, `TB_EssenciaLinhagem`, `TB_Item`** via `migrate_tags_universal.py` (Mai/2026). Conteúdo começa NULL — preenche pela página de debug `/debug/<entidade>`. Item NÃO entra no agregador `_agg_tags_from` ainda; coluna está pronta para a tela debug específica de itens (futuro).

**Convenção de override.** Onde há sobreposição entre catálogo e instância
do personagem (ex.: `TB_TalentoRacial` vs `TB_PersonagemTalento`), a
instância precede via `COALESCE(pt.TagsJSON, tr.TagsJSON)`. Permite
override por personagem sem mexer no catálogo.

---

## 4. Catálogo de tags (matriz de portabilidade)

Todas as tags abaixo funcionam **idêntico** em qualquer fonte da §3.

### 4.0 Forma de uma tag

`TagsJSON` é um array JSON. Cada entrada pode ser:

- **String** — forma canônica original: `"pick:pericia:2"`, `"expertise:Arcanismo"`, `"resist:Fogo"`. Continua válida em 100% dos casos.
- **Objeto** — extensão pra carregar metadata estruturada sem inflar o nome da tag. Campos suportados:
  - `tag` (obrigatório) — prefixo da tag, ex: `"pick:pericia"`, `"resist"`, `"pick:maestria-arma"`. Sem o `:N` no fim quando há `n_por_nivel`.
  - `filter` (opcional) — whitelist de candidatos pra `pick:*`. Convertido em sufixo `=A|B|C` na string final.
  - `n_por_nivel` (opcional) — mapeia `{nivel_minimo: N}`. Resolve no agregador contra **nível da classe** quando a tag vem de hab/sub/classe (multiclasse-aware) ou nível total caso contrário. Pega o maior nível ≤ atual, retorna o N correspondente, concatena como `:N` na tag final. Se nenhum nível bater (char abaixo do mínimo), tag é descartada.

Exemplos:
```jsonc
// String simples — forma canônica
"resist:Fogo"

// Objeto com whitelist
{ "tag": "pick:pericia:1", "filter": ["Atletismo", "Furtividade", "Investigação"] }

// Objeto com progressão por nível (caso Maestria de Armas Guerreiro)
{ "tag": "pick:maestria-arma", "n_por_nivel": {"1": 3, "4": 4, "10": 5, "16": 6} }

// Objeto com progressão + whitelist (combinável)
{ "tag": "pick:pericia",       "n_por_nivel": {"1": 1, "10": 2}, "filter": ["Atletismo", "História"] }
```

**Resolução de `n_por_nivel`:**
- O agregador recebe `nivel_efetivo` por item: `NivelClasse` (vindo do SELECT da hab/classe/sub do char) ou `nivel_pers` (total) como fallback.
- Multiclasse: cada hab carrega o nível DAQUELA classe (Guerreiro 10/Mago 5 → Disciplina Marcial resolve com 10, não 15).
- Tag final propagada continua sendo string (`pick:maestria-arma:5`) — todos os parsers ascendentes continuam funcionando sem mudança.

Use a forma objeto quando precisar de `filter` ou `n_por_nivel`. Caso contrário, prefira string — é mais compacta.

### 4.1 Pickers

Geram N slots clicáveis no card. Click → modal → grava em
`TB_PersonagemEscolhaPericia` ou `TB_PersonagemIdioma` com `Origem` =
nome do card.

| Tag                     | Catálogo de pick                                          |
|-------------------------|-----------------------------------------------------------|
| `pick:pericia:N`        | 18 perícias padrão (`TB_PersonagemPericia`)               |
| `pick:idioma:N`         | `IDIOMA_CATALOG` no frontend                              |
| `pick:ferramenta:N`     | `FERRAMENTA_CATALOG` no frontend                          |
| `pick:talento-origem:N` | `TB_OpcaoJogo Tipo='talento-origem'`                      |

**Filtro opcional:** `data-filter-list="A|B|C"` no slot HTML restringe
aos nomes listados. Usado pela primeira classe (lista `SkillsJSON.from`).
Sem filtro = qualquer item do catálogo não-prof.

**Helper único:** `renderPickSlotsFromTags(tagsJSON, origem, filterList?)`
em `static/ficha.js`. Qualquer card que tenha `pick:*` no `TagsJSON`
ganha os slots passando esse helper.

### 4.2 Perícias

| Tag                       | Efeito                                              |
|---------------------------|-----------------------------------------------------|
| `prof:<NomePericia>`      | proficiência (`+BP`)                                |
| `expertise:<NomePericia>` | expertise (`+2×BP`); implica proficiência           |

### 4.3 Saves

| Tag                          | Efeito                                           |
|------------------------------|--------------------------------------------------|
| `save-prof:<Atributo>`       | atributo entra em `state.saves_proficientes`     |
| `save-prof-vontade:<def>\|<alts>` | cascade: se char já tem `<def>` → picker em `<alts>`; senão → auto-aplica `<def>` |

### 4.4 Resistências de dano

Validado contra `ELEMENTOS_CANONICOS` (frozenset 5.5e BR — 13 valores).

| Tag                 | Efeito                                                 |
|---------------------|--------------------------------------------------------|
| `resist:<Elemento>` | resistência (dano metade)                              |
| `immune:<Elemento>` | imunidade (sem dano)                                   |
| `vuln:<Elemento>`   | vulnerabilidade (dano dobro)                           |

### 4.5 Condições

Validado contra `CONDICOES_CANONICAS` (15 valores 5.5e BR).

⚠️ Veneno (dano) ≠ Envenenado (condição). Use `resist:Veneno` para o
primeiro, `cond-immune:Envenenado` para o segundo.

| Tag                       | Efeito                                                 |
|---------------------------|--------------------------------------------------------|
| `cond-immune:<Condição>`  | condição não pode ser aplicada                         |
| `adv-cond:<Condição>`     | vantagem em save pra evitar/encerrar a condição        |

### 4.6 Movimentos

| Tag                       | Efeito                                              |
|---------------------------|-----------------------------------------------------|
| `andar:<Xft>`             | override do andar base (raro)                       |
| `voar:<Xft>` / `voar:eq`  | velocidade de voo (`eq` = igual ao andar)           |
| `nadar:<Xft>` / `nadar:eq`| velocidade de natação                               |
| `cavar:<Xft>` / `cavar:eq`| velocidade de cavar                                 |

### 4.7 Pontos de Vida

| Tag                  | Efeito                                                  |
|----------------------|---------------------------------------------------------|
| `pv-por-nivel:N`     | +N PV por nível total do personagem (caso especial pré-prefixo) |

Hoje processado para qualquer fonte (universal). Tag-legado mantida sem prefixo `+` por compatibilidade — semanticamente equivalente a `+pv:N×nivel`.

### 4.8 Tags acumuladoras (prefixo `+`) — princípio universal

Tags com prefixo `+` são **acumuladores numéricos**. Múltiplas fontes da mesma chave **somam** — princípio universal: "se hab tem `+1 X` e raça tem `+1 X`, char ganha 2X".

| Tag                       | Efeito                                                   |
|---------------------------|----------------------------------------------------------|
| `+<chave>:N`              | Soma N ao acumulador `<chave>` (qualquer chave)          |
| `+<chave>` com `n_por_nivel` | Igual, mas N resolvido por nível antes de somar       |

Exemplos:
```jsonc
// Forma string flat
"+manobras:2"
"+ca:1"

// Forma objeto com progressão por nível
{"tag": "+manobras", "n_por_nivel": {"1": 3, "4": 4, "10": 5, "16": 6}}
```

**Resultado no payload `/full`:**
- `state.bonus_acumulados`: `{"<chave>": <total_somado>, ...}`
- `state.bonus_fontes`: `{"<chave>": [{"nome": "<origem>", "valor": <N>}, ...]}` (rastreabilidade)

**Aplicação atual:** `state.bonus_acumulados.manobras` adiciona slots ao final de `state.manobras_slots` (slots com `from_bonus: true`). Outras chaves ficam disponíveis no payload mas ainda não têm consumidor automático — UI pode usar conforme precisar.

**Distinção crítica:**
- `pick:X:N` → escolha de N coisas de catálogo X. **N = quantidade de slots**, não acumula.
- `+X:N` → soma N ao contador X. **Cada fonte soma**, sem limite.
- `prof:X` → binário (tem ou não tem). Múltiplas fontes redundantes.

**Sem catálogo de chaves canônicas** — qualquer string serve. Convencione nomes consistentes entre habs/raças/talentos.

### 4.8 Categoriais (standalone, sem `:`)

| Tag           | Significado                                      |
|---------------|--------------------------------------------------|
| `conjurador`  | hab CONCEDE Conjuração ou Magia de Pacto base   |
| `infernal`    | descritivo, sem efeito derivado hoje            |

---

## 5. Como adicionar uma tag nova respeitando a regra

Checklist de 6 passos. Se algum não for atendido, a tag VIOLA a regra
universal — reabra o desenho.

1. **Defina o prefixo e o vocabulário.** Documente em `§4` deste arquivo
   (ou em `sistema-de-efeitos-via-tags.md`). Se tem vocabulário canônico
   (ex.: lista de elementos), adicione constante em `app.py`.

2. **Implemente o parser no aggregator central.** `app.py:personagem_full()`
   tem 3 chamadas `_agg_tags_from(...)` que cobrem habs+sub+traços+talentos.
   Seu parser DEVE consumir `tag_origem` (lista de `(tag, origem)`) — não
   olhar a fonte específica. Isso garante portabilidade.

3. **Sem branches por tipo de fonte.** Se você se pegar escrevendo
   `if origem_table == "TB_ClasseHabilidade"` ou
   `for hab in habs_cls`, **pare**. Use `tag_origem` agregado.

4. **Frontend — helper genérico.** Se a tag tem efeito visual (badge,
   slot, widget), implemente UM helper que aceita `(tagsJSON, origem,
   ...)`. Não duplique em fmtTraco, fmtHab e renderXCard. Se já existe
   um helper genérico (`renderPickSlotsFromTags`, `renderTagBadges`),
   estenda-o em vez de criar novo.

5. **Teste em 3 fontes diferentes.** Coloque a tag em (a) um hab, (b)
   um traço racial, (c) um talento. Verifique que o efeito é idêntico
   nas três. Se não for, há um leak de contexto.

6. **Atualize a matriz §4 e o `sistema-de-efeitos-via-tags.md`.**
   Documentação é parte da feature.

---

## 6. Anti-padrões (violam a regra)

### 6.1 Iterar uma fonte específica

```python
# ❌ ERRADO — só processa em habs
for h in habs_cls:
    if "pv-por-nivel" in h.get("TagsJSON", ""):
        ...

# ✅ CERTO — iterar tag_origem agregado
for t, origem in tag_origem:
    if t.startswith("pv-por-nivel:"):
        ...
```

### 6.2 Tag que carrega contexto da fonte

```python
# ❌ ERRADO — embute "isso é de classe"
"prof-classe:Atletismo"
"prof-raca:Atletismo"

# ✅ CERTO — efeito puro, origem vem do agregador
"prof:Atletismo"  # mesmo em qualquer card; backend sabe a origem via tag_origem
```

### 6.3 Helper de UI que checa tipo de objeto

```js
// ❌ ERRADO
if (item.Id_Habilidade) renderForHab(item);
else if (item.Id_Traco) renderForTraco(item);

// ✅ CERTO
renderPickSlotsFromTags(item.TagsJSON, item.Nome, opts);
```

### 6.4 Persistir efeito derivado

Já coberto em [`sistema-de-efeitos-via-tags.md`§10](sistema-de-efeitos-via-tags.md):
não setar `TB_PersonagemPericia.Proficiente=1` direto quando a prof vem
de tag — perder a fonte deixa o estado órfão.

### 6.5 "Esta tag só faz sentido em X"

Se você acha que uma tag só faria sentido em raça (ex.: "Habilidoso só é
de Humano"), **a tag não é a unidade certa**. A *tag em si* só descreve
o efeito (`pick:pericia:2`). O *fato de ser do Humano* é dado da fonte
(`TB_TracoRacial.Id_Raca`). Não junte. Outras raças podem ter
`pick:pericia:2` no futuro com semântica idêntica.

---

## 7. Status atual da implementação (auditoria)

| Tag                  | Universal? | Notas                                                                   |
|----------------------|:----------:|-------------------------------------------------------------------------|
| `pick:pericia:N`     |     ✅     | Helper unificado (`renderPickSlotsFromTags`). 4 fontes hoje.            |
| `pick:idioma:N`      |     ✅     | Mesmo helper.                                                           |
| `pick:ferramenta:N`  |     ✅     | Mesmo helper.                                                           |
| `pick:talento-origem:N` | ⚠️ parcial | Tag emitida em traço racial; picker chama rota dedicada (`pickTalentoOrigem`) em vez de passar pelo helper genérico. |
| `prof:<P>`           |     ✅     | `_agg_tags_from` consome 4 fontes (habs+sub, traços, talentos, talentos-de-origem). |
| `expertise:<P>`      |     ✅     | Idem.                                                                   |
| `save-prof:<A>`      |     ✅     | Idem.                                                                   |
| `save-prof-vontade:` |     ✅     | `_processa_vontade_tags` itera habs+talentos+traços. Auto-default funciona em todos; pick em traço fica sem storage por enquanto (fallback: slot vazio). |
| `resist/immune/vuln` |     ✅     | Validado contra `ELEMENTOS_CANONICOS`.                                  |
| `cond-immune/adv-cond` |   ✅     | Validado contra `CONDICOES_CANONICAS`.                                  |
| `andar/voar/nadar/cavar:N` | ✅   | Aggregator consome todas fontes.                                        |
| `pv-por-nivel:N`     |     ✅     | Lê de `tag_origem` agregado universal — qualquer fonte (hab, traço, talento, ASI, talento-de-origem) contribui. |
| `conjurador` (categorial) | ✅   | Badge informativo.                                                      |

**Pendências pra fechar a regra:**

- [x] ~~`pv-por-nivel:N` deve ler de `tag_origem` agregado~~ — ✅ resolvido. Talentos-de-origem entram no `_agg_tags_from`; o handler agora itera `tag_origem`.
- [x] ~~`save-prof-vontade:` precisa adicionar traços ao loop~~ — ✅ resolvido. Loop adicional `for trc in tracos:`. Auto-default funciona; o branch de pick em traço fica sem storage até definirmos um mecanismo (TB_PersonagemEscolhaTag genérico ou similar) — slot fica vazio na UI nesse caso.
- [ ] `pick:talento-origem:N` está hoje em traço racial via tag, mas
      o picker usa rota dedicada (`/escolhas` PATCH). Unificar via
      `renderPickSlotsFromTags` exigiria rota genérica de pick para
      qualquer "tipo" — refactor maior, adiado.
- [ ] **(novo)** Storage de pick em traço para `save-prof-vontade:`. Hoje
      auto-default cobre o caso comum; quando char já tem o save default,
      traço fica sem efeito (não pode picar). Solução: criar
      `TB_PersonagemEscolhaTag(pid, Origem, SlotIndex, Valor, Tipo)`
      genérica e ajustar `_processa_vontade_tags` para ler dela quando
      `kind == "traco"`.

---

## 8. Onde olhar no código

| Tema                              | Arquivo / função                                            |
|-----------------------------------|-------------------------------------------------------------|
| Aggregator central                | `app.py: personagem_full()` (busca por `_agg_tags_from`)    |
| Helpers de tag por categoria      | mesmo arquivo, blocos sequenciais após o aggregator         |
| Helper UI de pickers              | `static/ficha.js: renderPickSlotsFromTags()`                |
| Helper UI de badges               | `static/ficha.js: renderTagBadges()`                        |
| Click handler dos slots           | `static/ficha.js: querySelectorAll("[data-pick-slot]")`     |
| Validações de vocabulário canônico | `app.py: ELEMENTOS_CANONICOS`, `CONDICOES_CANONICAS`       |

---

*v1 — Mai/2026. Estabelece a regra de portabilidade para todas as tags
do projeto. Atualizar §7 conforme as pendências forem resolvidas.*
