# Talentos de Raça e Essência — Wiki

> **Escopo:** sistema de talentos de progressão racial/essencial do Bonfire Tales RPG
> conforme implementado em `bonfas.db` + `static/ficha.js` + `app.py`.
>
> **Fonte oficial:** seções **"Evolução Racial"** (em artigos de raça) e
> **"Evolução da Essência"** (em artigos de essência) do WorldAnvil.

---

## 1. Conceito

Todo personagem ganha **5 slots de talento progressivo** nos níveis **1, 5, 9,
13 e 17**. Cada slot comporta **um único talento** que pode vir de:

- **Raça** (ex.: Humano, Anão, Elfo…)
- **Essência** (ex.: Infernal, Celestial, Bestial…) — se a raça permite
  `PermiteEssencia=1` e o personagem escolheu ser **Essenciata**

Os dois **compartilham** os mesmos 5 slots — o jogador decide tier a tier se
aquela escolha vem da raça ou da essência.

Além destes 5, a **classe** fornece slots separados (ASI/Talento) nos seus
próprios níveis — ver [seção 6](#6-talentos-de-classe-asi).

### 1.1 Tags = pré-requisito

Cada talento tem uma lista de **tags** (ex.: `["humano"]`, `["infernal"]`,
`["humano","erthari"]`). O personagem herda tags de:

| Origem              | Tag gerada       |
|---------------------|------------------|
| Raça                | slug da raça (`humano`)                       |
| Linhagem racial     | primeira palavra do slug (`erthari`)          |
| Essência            | slug sem prefixo (`infernal`)                 |
| Linhagem da essência (pecado) | slug direto (`orgulho`)             |

**Regra de visibilidade:** um talento aparece no modal se
`talento.tags ⊆ personagem.tags`. Ou seja, **todas** as tags do talento
precisam estar no personagem.

#### Exemplo: Frosty (Humano + Infernal + Orgulho)

- Tags do personagem: `{humano, infernal, orgulho}`
- Talento "Tatuagens Arcanas" (tags `[humano]`): ✅ visível
- Talento "Aprendiz Prático" (tags `[humano, erthari]`): ❌ **não**, falta `erthari`
- Talento "Aspecto Bestial" (tags `[infernal]`): ✅ visível
- Talento hipotético "Orgulho Intacto" (tags `[infernal, orgulho]`): ✅ visível

---

## 2. Essenciata e o cascade de escolhas

Quando a raça tem `PermiteEssencia=1`, a **listagem de linhagens** da raça
inclui uma opção virtual chamada **"Essenciata"**:

```
/api/racas/humano/linhagens  →  [Erthari, Sólarin, Durkarn, Goruun, ★ Essenciata]
```

Clicar em **Essenciata** NÃO salva uma linhagem racial — abre um picker de
**Essência**. Escolhida a essência, abre outro picker de **sub-linhagem**
(pecado infernal, lar celestial, tipo dracônico, etc.).

Fluxo do cascade na UI (`ficha.js:pickRaca`):

```
clique Raça → lista 9 raças
 └─ clique Humano → PATCH Id_Raca + abre linhagens humanas
     └─ clique Essenciata → abre pick de essência
         └─ clique Infernal → PATCH Id_Essencia + abre sub-linhagens
             └─ clique Orgulho → PATCH Id_EssLinhagem ✔ FIM
```

---

## 3. Auto-efeitos da sub-linhagem da essência

Cada linhagem de essência (tabela `TB_EssenciaLinhagem`) tem três colunas
estruturadas extraídas da tabela **"Legado dos Círculos"**:

| Coluna        | Ex. (Orgulho) | O que faz |
|---------------|---------------|-----------|
| `Elemento`    | Fogo          | Resistência a esse tipo de dano |
| `TruqueNome`  | Raio de Fogo [Fire Bolt] | Truque inato (sempre disponível) |
| `MagiaN3Nome` | Golpe Incandescente [Searing Smite] | Magia de 1º nível · 1×/descanso longo · **desbloqueia no nível 3+** |

Esses efeitos são retornados pelo backend em `/api/personagens/<id>/full`
sob a chave `auto_efeitos`:

```json
{
  "auto_efeitos": {
    "origem": "Linhagem Orgulho (Essência Infernal)",
    "resistencia": "Fogo",
    "truque": "Raio de Fogo [Fire Bolt]",
    "magia_n3": "Golpe Incandescente [Searing Smite]"
  }
}
```

No frontend aparecem:

- **Resistências:** badge ★ `Fogo` (linha com borda vermelha)
- **Magias (se conjurador):** injetadas na grid nos níveis 0 e 1
- **Magias Inatas (se NÃO conjurador):** bloco independente com os 2 efeitos

---

## 4. 5 slots × 2 fontes = picker misto

A coluna **"Talentos de Raça / Essência"** tem 5 rows (Nv 1, 5, 9, 13, 17).
Cada row é um slot independente:

| Estado visual | Class CSS          | Comportamento |
|---------------|--------------------|---------------|
| `empty`       | ativo, tracejado   | Modal abre, vê talentos do tier disponíveis |
| `filled`      | azul + nome        | Click pede confirmação de remover |
| `locked`      | 🔒 + cinza         | Ainda clicável — **modo planejamento** |
| `locked filled` | cinza itálico + "(planejado)" | Já escolhido, aguarda nível subir |

Endpoint do modal:

```
GET /api/personagens/<id>/talentos-raciais-disponiveis
→ { tags_personagem: [...], nivel: N, talentos: [...] }
```

Retorna **todos** os talentos cujas tags são subconjunto das do personagem.
O filtro por tier é feito no cliente (`NivelMinimo === tier_clicado`).

Ao escolher:

```
POST /api/personagens/<id>/talentos-raciais
     { id_talento: <int>, categoria: 'raca'|'essencia' }
```

Servidor **garante 1 slot por tier por categoria** — deleta anterior antes
de inserir. Como Raça e Essência compartilham visualmente o slot, se o user
escolher essência Nv 1 por cima de uma raça Nv 1 já escolhida, o front
envia a categoria correta mas o anterior precisa ser removido manualmente
(feature futura).

---

## 5. Adicionando novos talentos ao catálogo

### 5.1 Via HTML salvo (caminho oficial)

Salve a página do WorldAnvil em `paginas/<slug>.html` e rode:

```bash
python parse_talentos.py paginas/humano.html     humano
python parse_talentos.py paginas/infernal.html   infernal
```

O parser procura a seção "Evolução Racial" ou "Evolução da Essência" e
extrai cada `<h5>Nome</h5> + <b>Pré-requisito:</b> ... + <b>Efeito:</b> ...`.

O fonte-tag (segundo argumento) define a tag base injetada + subtags vindas
de "(Erthari, Goruun)" parsing automático.

### 5.2 Nunca inventar talentos

**Regra #0 do [CLAUDE.md](../CLAUDE.md):** conteúdo do jogo é 1:1 com a
fonte oficial. Se a essência Infernal oficial tem 9 linhagens (Soberba,
Orgulho, Ira, Gula, Manipulação, Luxúria, Inveja, Ganância, Exílio), não
popular "os 7 pecados capitais" (Preguiça não existe no Bonfire Tales).

---

## 6. Talentos de Classe (ASI)

Além dos 5 slots raça/essência, cada classe tem slots próprios nos níveis
de ASI/Talento. Definidos em `TB_Classe.ASINiveisJSON`:

| Classe       | Níveis de ASI/Talento                  |
|--------------|----------------------------------------|
| Guerreiro    | **4, 6, 8, 12, 14, 16, 19** (7 slots — bônus Fighter D&D 5.5) |
| Todas as outras | 4, 8, 12, 16, 19 (5 slots padrão)   |

Na UI, o título da coluna mostra a classe: "Talentos de Classe (Guerreiro)".
Os slots da classe usam texto livre (por ora) — no futuro poderão abrir
modal de "Talentos Gerais" quando houver catálogo populado via
`TB_OpcaoJogo` (que hoje está vazio).

---

## 7. Schema — tabelas relacionadas

```
TB_Raca
  ├─ PermiteEssencia (bit)
  └─ 0..N TB_Linhagem

TB_Essencia
  └─ 0..N TB_EssenciaLinhagem
       ├─ Elemento     (auto-resist)
       ├─ TruqueNome   (auto-truque)
       └─ MagiaN3Nome  (auto-magia nv 3+)

TB_TalentoRacial  (catálogo)
  ├─ TagsJSON         → ["humano"] | ["infernal","orgulho"] etc.
  ├─ NivelMinimo      → 1 | 5 | 9 | 13 | 17
  ├─ PreReqTexto      → texto literal do artigo
  ├─ Descricao        → efeito completo
  └─ Fonte            → slug da fonte (humano, infernal, ...)

TB_PersonagemEscolha
  ├─ Id_Raca / Id_Linhagem / Id_Essencia / Id_EssLinhagem

TB_PersonagemTalento   (escolhas do personagem)
  ├─ Categoria: 'raca' | 'essencia' | 'classe' | 'geral' | 'extra'
  ├─ Nivel     (tier do slot: 1/5/9/13/17 OU ASI 4/6/8/…)
  ├─ Id_TalentoRacial  (FK opcional para rastrear origem)
  └─ Nome/Detalhes     (fallback pra texto livre em classe)
```

---

## 8. Endpoints resumo

| Método | Rota | Finalidade |
|--------|------|-----------|
| GET    | `/api/racas/<slug>/linhagens` | Linhagens (+ Essenciata virtual) |
| GET    | `/api/essencias/<slug>/linhagens` | Sub-linhagens da essência |
| GET    | `/api/personagens/<id>/talentos-raciais-disponiveis` | Filtra por tags |
| POST   | `/api/personagens/<id>/talentos-raciais` | Adiciona talento do catálogo |
| POST   | `/api/personagens/<id>/talento-manual` | Texto livre (classe/extra) |
| DELETE | `/api/personagens/<id>/talentos/<tid>` | Remove slot |
| GET    | `/api/personagens/<id>/full` | Tudo + `auto_efeitos` calculado |

---

## 9. Referências de código

- Seed oficial: [`seed_humano_infernal.py`](../seed_humano_infernal.py)
- Parser de talentos: [`parse_talentos.py`](../parse_talentos.py)
- Backend: [`app.py`](../app.py) (seções `talentos-raciais-*` e `auto_efeitos`)
- UI: [`static/ficha.js`](../static/ficha.js) (`tierSlot`, `pickTalentoRacEss`, `pickTalentoTier`)
- Schema: [`schema.sql`](../schema.sql) + `ALTER` feitos inline

---

## 10. Checklist ao adicionar nova raça ou essência

1. Salvar HTML oficial em `paginas/<slug>.html`
2. Criar seed com `INSERT INTO TB_Raca` (ou `TB_Essencia`) + linhagens
3. Se for essência com "Legado dos Círculos": popular colunas `Elemento`,
   `TruqueNome`, `MagiaN3Nome` em `TB_EssenciaLinhagem`
4. Rodar `python parse_talentos.py paginas/<slug>.html <fonte>` para
   extrair talentos
5. Testar no frontend: escolher raça+linhagem e validar que:
   - Tags geradas estão corretas
   - Talentos do catálogo aparecem no picker
   - Auto-efeitos (se essência) aparecem em Resistências e Magias
