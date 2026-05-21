# Padrão: Tags + Cascata + Auto-populate

> **Regra geral do projeto Bonfas.** Sempre que houver uma opção selecionável
> de um catálogo oficial, o frontend NÃO deve pedir texto livre ao usuário.
> Deve mostrar uma cascata com os candidatos filtrados e auto-popular o
> campo quando o usuário escolher.

---

## 1. Quando aplicar este padrão

Qualquer escolha onde exista **catálogo oficial** (tabela de dados 1:1 com
o artigo WorldAnvil). Exemplos já implementados:

| Campo na ficha                | Catálogo        | Filtro                       |
|-------------------------------|-----------------|------------------------------|
| Raça                          | `TB_Raca`       | —                            |
| Linhagem racial               | `TB_Linhagem`   | `Id_Raca`                    |
| Essência                      | `TB_Essencia`   | `Raca.PermiteEssencia=1`     |
| Sub-linhagem da essência      | `TB_EssenciaLinhagem` | `Id_Essencia`          |
| Talentos de raça/essência     | `TB_TalentoRacial`    | `tags ⊆ personagem.tags` + tier |
| Manobras de combate           | `TB_Manobra`    | `Fonte=classe` + `Grau≤max`  |
| Classe / Subclasse            | `TB_Classe` / `TB_Subclasse` | `Id_Classe`     |
| Opções de habilidade de classe | `TB_OpcaoJogo` (filtra por `Tipo` declarado em `TB_ClasseHabilidade.OpcaoTipoJSON`) | `Id_Classe` ou `Id_Subclasse` via `TB_AcessoOpcao` |

**Proibido:** `prompt()` ou `<input type="text">` para conteúdo que tem
catálogo. Isso permitiria o usuário inventar nomes que não existem, violando
a [Regra #0](../CLAUDE.md) (nunca inventar nomes).

**Permitido como fallback:** texto livre **apenas** para campos sem
catálogo ainda populado (ex.: "Talentos de Classe" enquanto não temos
`TB_OpcaoJogo`) ou texto realmente livre (nome do personagem,
personalidade, inventário improvisado).

---

## 2. Estrutura do catálogo

Todo catálogo que precisa ser filtrado por pré-requisitos segue esta
convenção:

```sql
CREATE TABLE TB_Catalogo_X (
    Id_X        INTEGER PK,
    Nome        VARCHAR NOT NULL,
    Slug        VARCHAR UNIQUE,
    TagsJSON    TEXT NOT NULL,       -- ["humano"], ["guerreiro","1grau"], ...
    NivelMinimo INTEGER,             -- se progressivo
    PreReqTexto VARCHAR,             -- literal do artigo, para exibição
    Descricao   TEXT NOT NULL,       -- conteúdo oficial 1:1
    Fonte       VARCHAR,             -- slug do arquivo origem
    ...
);
```

### Regras das tags

- **Tudo em lowercase** com `slug()` (sem acentos, hífens entre palavras)
- **Grupos conhecidos:**
  - Raça/essência: `humano`, `erthari`, `infernal`, `orgulho`, `ira`, ...
  - Classe: `guerreiro`, `mago`, `bardo`, ...
  - Grau/tier: `1grau`, `2grau`, `3grau`, `4grau`
  - Nível de acesso: `nv5`, `nv9`, ... (se precisar filtrar por nível exato)
  - Pré-req de atributo: `for13`, `dex15` (quando o talento exige isso)
- **Uma tag = uma exigência.** A lógica de filtro no endpoint é
  **`talento.tags ⊆ personagem.tags`**, nunca intersecção. Se o talento
  diz "humano E erthari", o personagem precisa ter **ambas**.

### Tags do personagem

Computadas no endpoint de disponibilidade. Exemplo p/ Frosty:

```js
tags_personagem = {
  "humano",      // da raça
  "infernal",    // da essência (slug sem "essencia-")
  "orgulho",     // da sub-linhagem da essência
  // (sem linhagem humana — ela é Essenciata)
}
```

---

## 3. Cascata na UI

### 3.1 Modal de cascata reutilizável

`openPicker({ title, options, onPick, renderOption })` em
[`ficha.js`](../static/ficha.js). Aceita:

- `title` — texto do header
- `options` — array do backend
- `renderOption(o)` — template HTML da linha (nome + tags + descrição curta)
- `onPick(o)` — callback ao clicar. Deve:
  1. Fazer POST/PUT ao backend com **id** do item escolhido (não o nome)
  2. Chamar `load()` para re-renderizar

### 3.2 Encadeamento automático (cascade)

Se a escolha de A desbloqueia B (ex.: Raça → Linhagem → Essência → Sub-linhagem),
o `onPick` de A deve **automaticamente abrir o picker de B** via
`setTimeout(() => pickB(...), 120)` depois do `await load()`.

### 3.3 Slots clicáveis (padrão N slots vazios)

**Padrão preferido para seções com limite X/Y:** render **N slots fixos**
(um para cada posição do limite) — igual "Talentos de Raça/Essência"
(5 slots por tier) e agora "Técnicas/Manobras" do Guerreiro (N = valor da
tabela de progressão).

```js
// ficha.js — estrutura canônica
Array.from({ length: limite }).map((_, i) => {
  const t = lista[i];
  if (t) return `<div class="tier-slot filled" data-pick-slot data-tid="${t.Id}">...</div>`;
  return `<div class="tier-slot empty" data-pick-slot><i>... — clique para escolher</i></div>`;
}).join("");
```

**Handler único:**
```js
root.querySelectorAll("[data-pick-slot]").forEach(slot => {
  slot.addEventListener("click", async () => {
    if (slot.dataset.tid) {            // preenchido → remover (com confirm)
      if (!confirm("Remover?")) return;
      await fetch(`/api/.../${slot.dataset.tid}`, { method: "DELETE" });
    } else {                            // vazio → abrir cascata
      openCascadePicker();
    }
    await load();
  });
});
```

**CSS compartilhado** (`tier-slot.empty|filled|locked` em `ficha.css`):
- `empty` — tracejado, cursor pointer, hover amarelo
- `filled` — azul marinho, nome em bold, click confirma remover
- `locked` — 🔒 cinza, clicável em modo planejamento (opcional)

**NÃO usar:**
- Botão único `+ Adicionar` (omite quantos faltam, confuso)
- Lista flat sem limite visível
- `+` pequeno no canto do header

**Benefício visual:** o usuário vê imediatamente quantos slots tem disponíveis
e quais estão preenchidos.

Exemplos ativos:
- Talentos de Raça/Essência: 5 slots × tiers (1, 5, 9, 13, 17)
- Talentos de Classe: N slots (ex.: 7 para Guerreiro em níveis ASI)
- Técnicas/Manobras: N slots = valor computado da progressão

---

## 4. Auto-popular em vez de texto livre

Ao clicar no item do picker, o backend puxa os campos canônicos do
catálogo e insere **o texto oficial**:

```js
// ERRADO — pede texto livre
const v = prompt("Nome da manobra:");
await fetch(..., body: JSON.stringify({ nome: v }));

// CERTO — envia o ID; backend busca o texto
await fetch(..., body: JSON.stringify({ id_manobra: m.Id_Manobra }));
// backend:
//   SELECT Nome, Descricao FROM TB_Manobra WHERE Id_Manobra = ?
//   INSERT INTO TB_PersonagemTecnica (Nome, Descricao, Id_Manobra) VALUES ...
```

Vantagens:
1. Nome preservado 1:1 da fonte
2. Descrição completa aparece automaticamente na ficha
3. Se o catálogo for atualizado (errata), basta re-migrar sem tocar nas
   fichas dos personagens
4. `Id_Manobra` (FK) permite filtros/queries futuras (ex.: "quantos
   jogadores escolheram Ataque de Finta?")

---

## 5. Limites calculados (X/Y)

Valores numéricos da tabela de progressão (ex.: "Manobras Conhecidas",
"Magias Preparadas", "Truques") são expostos em `state.limites.<chave>`
pelo endpoint `/api/personagens/<id>/full`. A UI usa para:

- Mostrar `N/M` no header da seção
- Esconder o botão "+ Adicionar" quando `N >= M`
- Alertar se `N > M` (overflow visual com cor)

Mapeamento em [`app.py`](../app.py) (função `personagem_full`):

```python
for col_nome, chave in [
    ("Manobras Conhecidas", "manobras"),
    ("Magias Preparadas",   "magias_preparadas"),
    ("Truques",             "truques"),
    ...
]:
```

Pega **o maior nível ≤ personagem.Nivel** da coluna. Ex.: Guerreiro nv 16 →
valor da linha `Nivel=16` da coluna `Manobras Conhecidas` = "7".

---

## 6. Checklist ao adicionar novo catálogo

1. **Schema** com `TagsJSON` + `Fonte` + `Slug UNIQUE`
2. **Parser** que lê `paginas/<origem>.html` e popula (1:1, sem inventar nomes)
3. **Endpoint `disponiveis`** que:
   - Calcula tags do personagem
   - Filtra `talento.tags ⊆ personagem.tags`
   - Considera nível/grau máximo
   - Remove já-escolhidos via `ja_escolhida: true`
4. **FK opcional** `Id_X` na tabela de escolhas do personagem
5. **Endpoint POST** que aceita `{ id_x }` e auto-popula nome/desc do catálogo
6. **UI** com `openPicker`, botão central visível quando couber, contador
   X/Y quando a classe definir limite
7. **Documentar** em `docs/<sistema>.md` (ver [talentos-raca-essencia.md](talentos-raca-essencia.md))

---

## 7. Anti-padrões (não fazer)

| ❌ Anti-padrão                            | ✅ Padrão correto                          |
|------------------------------------------|--------------------------------------------|
| `prompt("Nome da manobra:")`             | Modal cascata com `TB_Manobra`             |
| Botão `+` genérico no header             | **N slots vazios clicáveis** (padrão N-slots) |
| Botão único "+ Adicionar"                | Renderizar todos os slots do limite ao mesmo tempo |
| Contador manual `(3 escolhidas)`         | `{atuais}/{limite}` calculado automaticamente |
| `<input>` pra "fighting style"           | Picker com opções oficiais                  |
| Popular "variante plausível" no DB       | Deixar vazio + parsear HTML oficial         |
| Filtro `tags ∩ talento.tags != ∅`        | `talento.tags ⊆ personagem.tags`           |
