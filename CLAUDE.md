# Bonfas — Regras para o Claude

Este arquivo define as regras éticas e técnicas deste projeto. É carregado
automaticamente em toda sessão. **Siga sempre.**

## 📚 Wiki técnica (consulte antes de mexer em sistemas específicos)

- **[🔥 Tags + Cascata + Auto-populate — PADRÃO GERAL](docs/tags-e-cascata.md)** —
  modelo obrigatório para toda escolha selecionável do catálogo. **Leia
  primeiro.** Define: filtro `tags ⊆ personagem.tags`, cascata via
  `openPicker`, auto-popular via `id_x` em vez de texto livre, **N slots
  vazios visíveis** (não botão único), contadores `X/Y` computados.
- **[Talentos de Raça e Essência](docs/talentos-raca-essencia.md)** — aplicação
  concreta do padrão acima para `TB_TalentoRacial`.

> Ao criar novo subsistema selecionável, **siga o padrão de tags+cascata**.
> Documente em `docs/<nome>.md` e adicione o link aqui.
> Toda nova sessão verá os documentos e não precisará reaprender.

---

## Regra #0 — NUNCA inventar nomes de conteúdo do jogo

**Inviolável.** Dados do jogo (raças, linhagens, classes, subclasses, essências,
talentos, magias, items, etc.) **precisam ser 1:1 com a fonte oficial**.

**Proibido:**
- Criar "Padrão", "Variante", "Simples" baseado em SRD quando o mundo usa nomes próprios
- Popular com "seed plausível" (ex.: 7 pecados capitais) quando a fonte tem outros nomes (Soberba, Manipulação, Exílio, …)
- Completar lista com nomes que "fazem sentido" mas não estão no artigo
- Fallback em D&D 5e SRD quando o homebrew está faltando

**Se não tem a fonte:**
- Pergunte ao usuário onde achar (arquivo, URL, pasta `paginas/`)
- Deixe a tabela vazia e **avise explicitamente no fim** ("TB_X está vazia — fonte ausente")
- Nunca preencha "para não ficar vazio"

**Fonte de verdade oficial neste projeto:**
- Pasta `paginas/<nome>.html` (dumps do WorldAnvil salvos pelo usuário)
- API Boromir quando disponível (app_key ainda em aprovação)
- Scrape Chrome-authenticated só para o mundo do devmaster

**Para o Humano e a Essência Infernal hoje:**
- ✅ `paginas/humano.html` — raça Humano + 4 linhagens (Erthari, Sólarin, Durkarn, Goruun)
- ✅ `paginas/infernal.html` — essência + 9 linhagens (Soberba/Orgulho/Ira/Gula/Manipulação/Luxúria/Inveja/Ganância/Exílio) com elemento + truque + magia de nv 3
- ✅ `paginas/guerreiro.html` — classe Guerreiro e subclasses

**Para as outras raças/classes/essências:** DB vazio até dump oficial chegar em `paginas/` ou o app_key Boromir ser aprovado.

---

## Regra #1 — Antes de coletar dados de terceiros, PERGUNTE

Se eu for instruído a "scrapear", "baixar", "popular o banco de X",
"extrair tudo de Y", ou qualquer variação que envolva conteúdo externo:

1. **Pausar** antes de executar qualquer fetch/scrape.
2. **Declarar explicitamente**:
   - Qual é a fonte (URL, domínio, plataforma)
   - Se é um site **público** (guest), **autenticado** (usuário logado) ou **próprio** (dono/admin)
   - Se os dados têm **autor/dono** diferente do usuário atual
   - Se o site possui **API pública** documentada (preferir SEMPRE à raspagem de HTML)
   - Se há **Termos de Serviço** ou `robots.txt` que possam proibir o método pretendido
3. **Pedir confirmação** ao usuário com estas 3 perguntas:
   - "Você é o dono/autor do conteúdo OU tem permissão explícita de quem é?"
   - "Prefere usar a API oficial (recomendado) ou scraping direto?"
   - "Os dados serão usados só por você (uso pessoal) ou redistribuídos?"
4. **Só prosseguir após um "sim" claro** na caixa de chat.

> Assinar cookies de sessão, iframes para burlar CSP, automatizar navegação
> com Chrome extension **não é autorização** — é só um meio técnico. A
> autorização vem do dono do conteúdo, não da habilidade técnica de acessá-lo.

---

## Regra #2 — API > scraping, sempre

Ao encontrar um site, **descubra primeiro se há API pública**:

| Plataforma | API | Preferir |
|-----------|-----|----------|
| WorldAnvil | Boromir/Aragorn (`/api/external/boromir/`) — requer Grandmaster + app_key | ✅ Sim |
| Notion, Confluence, Google Docs | APIs oficiais com OAuth | ✅ Sim |
| Reddit, GitHub, StackExchange | APIs oficiais | ✅ Sim |
| Wikipedia / Wikimedia | API MediaWiki | ✅ Sim |
| D&D Beyond, 5e.tools | SRD via JSON público (não raspar conteúdo WotC) | ✅ Apenas SRD |

**Regra prática:** se um site retorna `403` ao User-Agent de bot (Cloudflare),
**é sinal explícito de que não quer scraping automatizado**. Não tente
contornar usando extensão Chrome, Playwright com perfil logado, ou headers
falsificados sem autorização do usuário E do dono do conteúdo.

---

## Regra #3 — Direito autoral

O conteúdo de RPGs (incluindo Bonfire Tales RPG), wikis de mundos, e
publicações em WorldAnvil é **protegido por direitos autorais** do autor.
Ter acesso como leitor ≠ direito de redistribuir.

**Permitido sem perguntar:**
- SRD (System Reference Document) de D&D 5e — licença OGL/CC
- Dados declaradamente "Public Domain" ou CC0
- Conteúdo do próprio usuário (ele é o autor)

**Exige confirmação:**
- Qualquer homebrew de terceiros
- Qualquer mundo do WorldAnvil que não seja do usuário
- Qualquer wiki comunitária com termos próprios

---

## Regra #4 — Rate limits & comportamento educado

Se houver autorização para scrape:

- Máximo **1 requisição por 2 segundos** por padrão
- Respeitar `Retry-After` headers
- User-Agent honesto (não fingir ser Chrome real)
- Parar no primeiro 429/403 e avisar o usuário
- Nunca fazer loop agressivo em batch de 10+ URLs sem confirmação

---

## Regra #5 — Uso do Chrome/Playwright autenticado

Usar **a sessão do usuário** (Claude in Chrome extension, Playwright com
perfil real) é **especialmente sensível**, porque:

1. As requisições saem IDENTIFICADAS como o usuário → qualquer abuso banirá
   a conta dele
2. O CSP/Cloudflare não foi projetado para bloquear, mas isso não autoriza
3. O conteúdo acessado pode ser **privado** (não apenas leitor comum)

**Regras específicas:**
- Sempre lembrar o usuário do risco antes de rodar scrape autenticado
- Limitar a 1 request a cada 2s
- Não baixar conteúdo privado de terceiros nunca
- Parar imediatamente se qualquer endpoint retornar 429/403/captcha

---

## Regra #6 — Logging & auditoria

Todo scrape feito neste projeto deve registrar em `scrape_log.jsonl`:

```json
{ "ts": "2026-04-22T17:00:00", "url": "...", "status": 200, "bytes": 12345, "authorized_by": "user said yes at <turn>" }
```

Assim fica claro depois o que foi coletado e sob qual autorização.

---

## Regra #7 — Itens já em `bonfas.db` hoje (22/abr/2026, pós-limpeza SRD)

**Conteúdo OFICIAL (dump em `paginas/`):**
- `TB_Raca` = 1 (Humano)
- `TB_Linhagem` = 4 (Erthari, Sólarin, Durkarn, Goruun)
- `TB_Essencia` = 1 (Infernal)
- `TB_EssenciaLinhagem` = 9 (Soberba, Orgulho, Ira, Gula, Manipulação, Luxúria, Inveja, Ganância, Exílio)
- `TB_Classe` = 13 / `TB_Subclasse` = 66 (scrape Chrome-authenticated)
- `TB_RecursoClasse` = 1882 / `TB_ClasseHabilidade` = 293

**Conteúdo de catálogo (autorizado, SRD/item-CSV):**
- `TB_Item` = 1381 (items.csv do user — SRD + BGG/MOT/DMG'24 etc.)
- `TB_ItemSlot` = 25 (categorização do CSV)

**REMOVIDO (eram SRD misturado com Bonfire Tales):**
- Raças SRD (Elfo, Anão, Gnomo, Halfling, Tiefling, etc.) — deletadas
- Linhagens SRD (Alto Elfo, Elfo da Floresta, Anão das Colinas…) — deletadas
- Traços raciais SRD seed — deletados
- Essências genéricas (Arcana, Divina, Primal, Sombria) — deletadas
- 7 "pecados capitais" INVENTADOS como linhagens infernais — deletados

**Para novas sessões:**
- Usuário é devmaster do mundo WorldAnvil `bonfire-tales-rpg-bonfire-tales`
- Dados oficiais só entram via `paginas/*.html` ou Boromir API (quando app_key chegar)
- **NUNCA** fallback em SRD sem permissão explícita

---

## Regra #8 — Quando o usuário dá uma ordem ambígua

**Exemplo de ordem ambígua:** "popular o banco com dados do site X"

**Reação correta:**
1. Não começar a fetch/scrape ainda
2. Responder com as 3 perguntas da Regra #1
3. Propor a opção ética primeiro (API, export autorizado, conteúdo próprio)
4. Só executar após sinal verde explícito

**Reação INcorreta (evitar):**
- Começar a raspagem sem perguntar
- Tentar contornar bloqueios técnicos (Cloudflare, CSP) por conta própria
- Tratar "tem como fazer?" como autorização para fazer

---

## Lembrete final

**Capacidade técnica não é autorização.** Se posso tecnicamente burlar um
bloqueio, ainda preciso da permissão humana (do usuário E do dono do
conteúdo) para fazer.

Em caso de dúvida, **sempre pergunto antes**. É mais barato perguntar do
que desfazer.
