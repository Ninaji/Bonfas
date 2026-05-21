# Habilidades com Escolha (A/B/C) — Wiki

> **Escopo:** quando uma habilidade de classe ou subclasse oferece escolhas
> embutidas tipo "A, B ou C" (ex.: Estilo de Luta, perícia do Cortesão
> Desonrado, ASI ou Talento), aplicar o padrão
> [Tags + Cascata + Auto-populate](tags-e-cascata.md) em vez de input
> de texto livre.

---

## 1. Conceito

Algumas `TB_ClasseHabilidade` têm `TemEscolha=1` porque a descrição obriga o
jogador a escolher. Antes desta feature, o frontend caía num modal de texto
livre — anti-padrão (Regra #0 do `CLAUDE.md` proíbe inventar nomes).

Agora cada habilidade pode declarar **estruturalmente** quais Tipos de
opção oferece e quantas escolhas em cada. O frontend renderiza N slots
clicáveis (mesmo padrão N-slots de Talentos de Raça/Essência) e abre um
picker que lista opções do `TB_OpcaoJogo` filtradas por classe/subclasse
do personagem.

---

## 2. Schema

### 2.1 `TB_ClasseHabilidade.OpcaoTipoJSON` (TEXT NULL)

Lista JSON de sub-escolhas. Cada entrada tem `tipo` (string) e `quantidade`
(int):

```json
[
  { "tipo": "estilo-de-luta", "quantidade": 1 },
  { "tipo": "maestria-arma",  "quantidade": 3 }
]
```

NULL = a habilidade não tem catálogo backed → cai no caminho legado de
texto livre via `openHabModal`.

### 2.2 `TB_PersonagemHabilidadeOpcao` (escolhas do personagem)

```sql
Id              INTEGER PK
Id_Personagem   INTEGER NOT NULL
Id_Habilidade   INTEGER NOT NULL
Texto           TEXT     NOT NULL  -- nome (auto-populado do catalogo) ou texto livre
Id_Opcao        INTEGER  NULL      -- FK TB_OpcaoJogo (path catálogo)
SlotIndex       INTEGER  NULL      -- posição linear dentro do JSON spec da hab
```

- Catalog pick: `Id_Opcao` populado, `SlotIndex` populado, `Texto =
  TB_OpcaoJogo.Nome` (auto-populado pelo backend).
- Texto livre com slot: `Id_Opcao=NULL`, `SlotIndex` populado (fallback
  para catálogo vazio).
- Texto livre legado: ambos `NULL` (rows pré-migração).

Indexes em `(Id_Opcao)` e `(Id_Personagem, Id_Habilidade, SlotIndex)`.

### 2.3 SlotIndex linear

Para uma habilidade com `OpcaoTipoJSON = [{tipo:A,qtd:1},{tipo:B,qtd:3}]`:

| SlotIndex | Tipo correspondente |
|-----------|---------------------|
| 0         | A (1º) |
| 1         | B (1º) |
| 2         | B (2º) |
| 3         | B (3º) |

O frontend mantém esse mapping (parseando `OpcaoTipoJSON`) para saber
qual tipo passar no picker.

---

## 3. Endpoints

### 3.1 `GET /api/personagens/<pid>/habilidade-opcoes-disponiveis/<hid>`

Retorna o catálogo filtrado para esta habilidade do personagem:

```json
{
  "habilidade":      { "Id_Habilidade": 533, "Nome": "Cortesão Desonrado", "OpcaoTipoJSON": "[...]", "TemEscolha": 1 },
  "tags_personagem": ["humano", "infernal", "orgulho"],
  "slots_atuais":    [{ "SlotIndex": 0, "Id_Opcao": 22, "Texto": "Historia", "OpcaoNome": "Historia", "OpcaoTipo": "pericia-cortesao", "OpcaoDesc": "..." }],
  "opcao_tipos": [
    {
      "tipo": "pericia-cortesao",
      "quantidade": 1,
      "opcoes": [{ "Id_Opcao": 22, "Nome": "Historia", ... }, ...],
      "catalogo_vazio": false
    }
  ]
}
```

Filtro: `TB_OpcaoJogo o JOIN TB_AcessoOpcao a ON a.Id_Opcao = o.Id_Opcao
WHERE o.Tipo = ? AND (a.Id_Classe = personagem.classe OR a.Id_Subclasse =
personagem.subclasse)`. Tags do personagem são retornadas para uso futuro
de filtro fino (Não usadas no v1 — `TB_OpcaoJogo` não tem `TagsJSON`).

### 3.2 `PUT /api/personagens/<pid>/habilidade-opcao/<hid>`

Aceita 3 formatos:

```json
// catálogo (preferido)
{ "id_opcao": 22, "slot_index": 0 }

// texto livre num slot (fallback de catálogo vazio)
{ "texto": "Defesa", "slot_index": 0 }

// texto livre legado (sem slot — habilidade sem OpcaoTipoJSON)
{ "texto": "valor qualquer" }
```

### 3.3 `DELETE /api/personagens/<pid>/habilidade-opcao/<hid>/<slot>`

Remove a escolha do slot especificado.

---

## 4. UI

`fmtHab` (em `static/ficha.js`) detecta `h.OpcaoTipoJSON`. Quando truthy:

- Renderiza `<div class="hab-slots-row">` com N `<div class="tier-slot
  hab-slot empty|filled">` slots.
- Pin no topo da habilidade vira `slotsPreenchidos/total` em vez de ✓/⚙.
- Click em slot vazio → `pickHabOpcao(habId, slotIndex, tipo)` →
  `openPicker(...)`.
- Click em slot preenchido → confirm + DELETE.

Quando o catálogo daquele Tipo está vazio (`catalogo_vazio: true`), o
picker oferece fallback de texto livre via `prompt()` com aviso explícito
sobre Regra #0.

CSS: classes `.tier-slot` reusadas; modificadores `.hab-slot` e
`.hab-slots-row` adicionados (visual mais compacto, borda esquerda
diferenciando do bloco de talentos de raça).

---

## 5. Como classificar uma habilidade nova

1. Identificar o ID em `TB_ClasseHabilidade` da habilidade.
2. Ler `paginas/<classe>.html` (ou `paginas/<classe>.extracted.html`
   pra versão limpa) na linha da habilidade.
3. Decidir Tipos:
   - Lista exaustiva no artigo? → Tipo novo, popular `TB_OpcaoJogo`.
   - Lista com "como"/"tais como"/"exemplo"? → Tipo novo, **deixar
     vazio** + fallback texto livre.
   - Aponta pra outra seção do artigo? → criar Tipo, deixar vazio,
     planejar parser próprio.
4. UPDATE `TB_ClasseHabilidade SET OpcaoTipoJSON='[{...}]' WHERE
   Id_Habilidade=?`.
5. Se for popular o catálogo: INSERT em `TB_OpcaoJogo` (Tipo, Nome 1:1
   da fonte) + INSERT em `TB_AcessoOpcao` (linkar à classe ou
   subclasse).
6. Testar `GET /api/personagens/<test>/habilidade-opcoes-disponiveis/<hid>`.

---

## 6. Tipos conhecidos hoje

| Tipo                | Quantidade canonica | Catálogo populado? | Fonte exaustiva? |
|---------------------|---------------------|--------------------|------------------|
| `manobra`           | varia (TB_Manobra é pré-existente) | sim (21 entradas) | sim |
| `pericia-cortesao`  | 1                   | sim (4: Historia, Intuicao, Performance, Persuasao) | sim (linha 1653 de `paginas/guerreiro.extracted.html`) |
| `estilo-de-luta`    | 1                   | **sim (10 entradas — PHB 2024 base)** | exceção autorizada à Regra #0 em 2026-05-03 — Bonfire Tales não oficializou lista; usado PHB 2024 marcado em `Descricao`. Substituir quando homebrew oficializar. |
| `maestria-arma`     | 3 (varia por nível) | **não** | fonte aponta pra todas armas (Simples ou Marciais) — pode ser populado de TB_Item |
| `asi-ou-talento`    | 1                   | **não** | requer 2 sub-pickers (atributo OU talento) — modelo composto pendente |

---

## 7. Habilidades classificadas hoje (Guerreiro Id_Classe=8)

| Id  | Nome                              | OpcaoTipoJSON |
|-----|-----------------------------------|---------------|
| 515 | Disciplina Marcial                | `[{"tipo":"estilo-de-luta","quantidade":1},{"tipo":"maestria-arma","quantidade":3}]` |
| 533 | Cortesão Desonrado (sub Ronin=39) | `[{"tipo":"pericia-cortesao","quantidade":1}]` |
| 536 | Incremento de Atributo ou Talento | `[{"tipo":"asi-ou-talento","quantidade":1}]` |

Habilidades adicionais com `TemEscolha=1` (não classificadas, ainda em
texto livre legado) para as outras subclasses do Guerreiro: ver query
abaixo.

```sql
SELECT Id_Habilidade, Nome, NivelAdquirido, Id_Subclasse, OpcaoTipoJSON
  FROM TB_ClasseHabilidade
 WHERE Id_Classe=8 AND TemEscolha=1
 ORDER BY NivelAdquirido, Id_Subclasse;
```

---

## 8. Não está coberto (out of scope desta v1)

- Tags filter `talento.tags ⊆ personagem.tags` em `TB_OpcaoJogo` —
  precisa adicionar coluna `TagsJSON`.
- Catálogos `estilo-de-luta`, `maestria-arma`, `talento-geral` —
  aguardam fonte oficial (Regra #0).
- Tipos compostos (`asi-ou-talento` como bifurcação) — picker simples
  só lista opções do Tipo; bifurcação real exige modal especial.
- Aplicar mesma feature em `TB_PersonagemTecnica` (manobras de
  combate) — atualmente em path separado via `openHabModal` modo
  "lista". Unificação é stretch goal.

---

## 9. Migração

Script: `migrate_opcoes_v2.py` (idempotente).
- ALTER columns
- UPDATE `OpcaoTipoJSON` para 3 habilidades
- INSERT 4 perícias do Cortesão Desonrado em `TB_OpcaoJogo` + acesso
  Subclasse=39 em `TB_AcessoOpcao`
