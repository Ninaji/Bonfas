# Plano — popular raças e essências do Bonfire

## Estado do DB hoje

| Item | Status | Fonte _raw |
|---|---|---|
| Humano (raça)         | ✅ 18 traços, 4 sublinhagens | (já populado) |
| Folken (raça)         | ✅ 18 traços, 5 sublinhagens | folken.html |
| Anão (raça)           | ⚠ placeholder, 0 traços, 0 sublinhagens | anao.extracted.html |
| Elfo (raça)           | ⚠ placeholder, 0 traços, 0 sublinhagens | elfo.extracted.html |
| Orc (raça)            | ⚠ placeholder, 0 traços, 0 sublinhagens | orc.extracted.html |
| Essência Infernal     | ✅ 9 sublinhagens (pecados), só 2 traços base | (interno) |
| Essência Bestial      | ⚠ 5 sublinhagens, 0 traços base, 0 traços sub | bestial.extracted.html |
| Essência Celestial    | ❌ não existe ainda | celestial.extracted.html |
| Essência Dracônica    | ❌ não existe ainda | draconico.extracted.html |
| Essência Elemental    | ❌ não existe ainda | elemental.extracted.html + fogo/terra/agua/ar |
| Essência Vampírica    | ❌ não existe ainda | vampiro.extracted.html |

## Estrutura observada nos HTMLs

### Raças (anão / elfo / orc)
- H2 "{Nome}" — header
- H2 "Divergência Ancestral"
- H3 "Interpretando um {X}" → lore roleplay
- H3 "Sociedade e Cultura" → lore society
- H3 "Traços da Raça Base" → traços base (TB_TracoRacial com Id_Raca)
- H3 "Opção A: Linhagens X" → header de sublinhagens
- H3/H4 por sublinhagem (Montanha/Profundezas; Sylvanar/Aetherin/...; Branco/Cinza/Negro/Vermelho/Verde) → TB_Linhagem + TB_TracoRacial com Id_Linhagem
- H3 "Opção B: Essências" → link externo (não popular aqui)
- H3 "Evolução Racial" → texto descritivo

### Essências (bestial / celestial / dracônica / vampiro)
- H2 "Essência {X}"
- H3 "Vivendo como um {Y}" → lore roleplay
- H3 "Sociedade e Origem" → lore society
- H3 "Poderes da Essência" → header
- H3 — N traços base (cada um vira TB_TracoRacial com Id_Essencia)
- H3 "Evolução da Essência" + sub-headers (campeão/corrompido/flagelado etc) → TB_EssenciaLinhagem + TB_TracoRacial com Id_EssLinhagem

### Essência Elemental (especial)
- elemental.extracted.html é índice com link pra 4 essências:
- fogo.extracted.html / terra / agua / ar — cada um é uma sublinhagem da Essência Elemental
- 1 essência mãe + 4 sublinhagens

## Convenção de tags (resumo pra parsers)

Tags universais já em uso no projeto:
- `+atributo:Forca` / `+atributo:Destreza` / etc — somador
- `resist:fogo` / `resist:radiante` / `resist:necrótico`
- `imune:doente` / `imune:sono`
- `cond-immune:Amedrontado` / `cond-immune:Enfeitiçado`
- `adv-cond:Amedrontado` (vantagem em saves contra)
- `velocidade:9m/30ft`
- `visao-no-escuro:18m/60ft`
- `+idioma:Anão` / `+idioma:Élfico` / etc
- `prof:Percepção` / `expertise:Furtividade`
- `prof-arma:Machado de Guerra` / `prof-armadura:Pesada`
- `pick:talento-origem:1` (reusa slot universal)

Não inventar tags novas. Se uma feature não cabe, deixa só no Descricao.

## Tabelas do DB (schema)

```sql
TB_Raca           (Id_Raca, Nome, Slug, Tagline, LorePresentation, LoreRoleplay, LoreSociety, PermiteEssencia, TagsJSON)
TB_Linhagem       (Id_Linhagem, Id_Raca, Nome, Slug, LorePresentation, LoreRoleplay, LoreSociety, Descricao, TagsJSON)
TB_Essencia       (Id_Essencia, Nome, Slug, LorePresentation, LoreRoleplay, LoreSociety, TagsJSON)
TB_EssenciaLinhagem (Id_EssLinhagem, Id_Essencia, Nome, Slug, Descricao, TagsJSON)
TB_TracoRacial    (Id_Traco, Id_Raca, Id_Linhagem, Id_Essencia, Id_EssLinhagem, Nome, Descricao, NivelRequisito, TagsJSON)
                   -- exatamente 1 das 4 FKs preenchida
```

## Estratégia de execução

### Fase A — paralelo (8 sub-agents)
Cada agent gera **APENAS um JSON estruturado** em `E:\Obsidian\_raw\parsed\<slug>.json`. Não toca DB.

Schema JSON unificado:
```json
{
  "tipo": "raca" | "essencia",
  "slug": "anao",
  "nome": "Anão",
  "tagline": "...",
  "lore": {"presentation": "...", "roleplay": "...", "society": "..."},
  "tags": [],
  "tracos_base": [
    {"nome": "...", "descricao": "...", "tags_sugeridas": ["..."]}
  ],
  "sublinhagens": [
    {"slug": "montanha", "nome": "Linhagem da Montanha",
     "descricao": "...", "tags": [],
     "tracos": [
       {"nome": "...", "descricao": "...", "tags_sugeridas": ["..."]}
     ]
    }
  ]
}
```

Distribuição de agents:
1. **Anão** ← `_raw/anao.extracted.html` — raça + 2 sublinhagens (Montanha, Profundezas)
2. **Elfo** ← `_raw/elfo.extracted.html` — raça + 5 sublinhagens (Sylvanar, Aetherin, Noctelar, Lunareth, Solariin)
3. **Orc** ← `_raw/orc.extracted.html` — raça + 5 sublinhagens (Branco, Cinza, Negro, Vermelho, Verde)
4. **Bestial** ← `_raw/bestial.extracted.html` — essência + 5 sub já existentes (Predadores/Vigilantes/Ágeis/Ancestrais/Kitsune)
5. **Celestial** ← `_raw/celestial.extracted.html` — essência + 3 sub (Campeão, Corrompido, Flagelado)
6. **Dracônica** ← `_raw/draconico.extracted.html` — essência + sub (verificar quais)
7. **Elemental** ← `_raw/elemental + fogo + terra + agua + ar.extracted.html` — essência mãe + 4 sub
8. **Vampírica** ← `_raw/vampiro.extracted.html` — essência + sub (verificar)

### Fase B — sequencial (eu)
- Migration master `migrate_racas_essencias_master.py` lê todos os JSONs em `_raw/parsed/` e faz INSERT/UPDATE idempotente por slug.
- Tags são processadas conservadoramente: só aplica `tags_sugeridas` se forem da convenção universal conhecida; resto vai pro Descricao.
- Smoke test final: SELECT count agrupado por origem, comparação com expected.
- Log único no Obsidian: 1 entrada com summary das 8 raças/essências populadas.
