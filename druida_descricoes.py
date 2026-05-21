"""Descrições limpas de todas as 63 features de Druida, escritas à mão a partir
do dump oficial (paginas/druida.html). Substituem o output do parser regex que
tinha resíduos de scraper (`<span`, `href="..."`, etc).

Chave: (Id_Subclasse_ou_None, Nome_canonico). Valor: texto plano único.

Convenção:
  - Aspas duplas para 1 sentença de flavor inicial
  - "Efeito:" introduz mecânicas
  - Sub-mecânicas com nome em prosa: "Reservatório Primal:", "Recuperação:"
  - Sem HTML, sem markdown, sem regex magic
  - Tabelas em prosa: "Nv X = valor; Nv Y = valor"
"""

# Tabela de descrições. Chave = nome canônico da feature.
# Para classe: usa-se a chave direta (Id_Subclasse IS NULL).
# Para subclasse: usa-se prefixo SLUG: ex "esporos:Magias do Círculo".
DESCRICOES = {

    # ======================================================================
    # CLASSE — 12 features únicas (algumas cobrem múltiplos níveis)
    # ======================================================================
    "Conjuração Druídica":
        '"Entre folhas e bruma, aprendi primeiro a ouvir e, ouvindo, a falar na '
        'língua que a seiva entende." Efeito: você canaliza a essência sagrada do '
        'mundo natural para conjurar magias de cura, proteção e fúria elemental. '
        'Truques: no 1º nível conhece 2 truques da lista de Druida (mais em níveis '
        'altos conforme a tabela). Preparando Magias: para conjurar de 1º círculo+ '
        'gasta espaço; recupera todos em Descanso Longo. Ao final de cada Descanso '
        'Longo prepara magias de Druida em número igual a nível de Druida + mod. '
        'de Sabedoria (mínimo 1), entre círculos para os quais possui espaços. '
        'Ritual: pode conjurar como ritual qualquer magia de Druida preparada com '
        'a marca Ritual (não gasta espaço, +10 min de conjuração). Foco: pode usar '
        'um Foco Druídico como foco de conjuração. Habilidade de Conjuração: '
        'Sabedoria. CD de Resistência = 8 + bônus prof. + mod. Sabedoria. '
        'Modificador de Ataque Mágico = bônus prof. + mod. Sabedoria.',

    "Vínculo Natural":
        '"Não peço que a mata me obedeça, eu a escuto." Efeito: sua conexão com a '
        'natureza permeia olhar, voz e respiração. Fala das Bestas: você está '
        'permanentemente sob o efeito de falar com animais (sem gastar espaço, '
        'sem concentração, sem componentes). Empatia Selvagem: Vantagem em testes '
        'de Carisma (Lidar com Animais) e Sabedoria (Lidar com Animais). '
        'Conhecimento Natural: em testes de Inteligência (Natureza), adiciona seu '
        'mod. de Sabedoria ao resultado (mínimo +1), somando ao mod. de '
        'Inteligência e bônus de proficiência normalmente.',

    "Ordem Primal":
        '"Nem toda raiz cresce na mesma direção. Eu apenas reconheço qual delas me '
        'reconheceu primeiro." Efeito: no 2º nível, escolha uma Ordem Primal. '
        'Xamã: aprende 2 truques adicionais da lista de Mago (contam como Druida, '
        'Sabedoria é sua habilidade de conjuração para eles); em testes de '
        'Inteligência (Arcanismo) ou Inteligência (Religião), adiciona seu mod. de '
        'Sabedoria ao resultado (mínimo +1). Guardião: ganha proficiência em armas '
        'marciais e armaduras médias.',

    "Surto Selvagem":
        '"A seiva antiga corre por atalhos que não cabem nos grimórios." Efeito: '
        'no 2º nível você acessa uma reserva de energia primordial chamada Surto '
        'Selvagem. Reservatório: usos conforme a tabela do Druida (2 no 2º nível). '
        'Recuperação: 1 uso em Descanso Curto; todos em Descanso Longo. Como ação '
        'bônus pode gastar 1 uso para recuperar 1 espaço de 1º círculo, ou gastar '
        '1 espaço de 1º círculo+ para recuperar 1 uso. '
        'Opções (escolha uma a cada uso, gasta 1 uso de Surto Selvagem): '
        '1) Forma Selvagem; 2) Rito dos Antigos; 3) Erupção Elemental; 4) Elo '
        'Primal; 5) Crescimento Virente. '
        '— Opção 1: Forma Selvagem (Ação Bônus): transforma-se em uma de suas '
        'Formas Conhecidas por nº de horas = metade do nível de Druida (arred. '
        'baixo). PV temp. = 2 × nível de Druida. Usa Força/Destreza/Constituição '
        'da besta (mantém Int/Sab/Car), mantém proficiências (usa a maior). Não '
        'pode conjurar magias (mantém Concentração). Equipamento se funde ao '
        'corpo. Formas Conhecidas — Evolução: Nv 2 = 4 formas, ND 1/4, sem voo; '
        'Nv 4 = 6 formas, ND 1/2, sem voo; Nv 8 = 8 formas, ND 1, voo permitido. '
        'Substitui 1 forma por outra em cada Descanso Longo. '
        '— Opção 2: Rito dos Antigos (Ação): conjura uma magia de Druida '
        'preparada com a tag Ritual, sem gastar espaço e sem os 10 min extras '
        'de ritual. '
        '— Opção 3: Erupção Elemental (Ação): cria coluna cilíndrica de 1,5 m '
        'raio × 9 m altura em ponto a até 9 m. Terreno difícil até o início do '
        'seu próximo turno. Escolha Ar (trovejante), Terra (concussão), Ígneo '
        '(fogo) ou Água (frio). Cada criatura na área faz TR Destreza vs. sua CD '
        'de magia; falha sofre 2d6 + nível de Druida do tipo escolhido, sucesso '
        'metade. Colunas adicionais: Nv 9 = 2 colunas; Nv 17 = 3 colunas '
        '(pontos distintos). '
        '— Opção 4: Elo Primal (Ação): aprende encontrar familiar (não conta no '
        'limite preparado) e pode conjurá-la sem espaço/componentes. Familiar é '
        'Besta ou Planta, tamanho Miúdo ou Pequeno. ND máximo do Familiar: Nv 2 '
        '= 0, Nv 4 = 1/8, Nv 8 = 1/4, Nv 12 = 1/2, Nv 16 = 1. '
        '— Opção 5: Crescimento Virente (Ação): aura de vegetação densa raio 3 m '
        'centrada em você, dura 1 min ou até ficar Incapacitado. Área é terreno '
        'difícil para criaturas hostis. Alcance expandido: Nv 9 = 6 m; '
        'Nv 17 = 9 m.',

    "Círculo Druídico":
        '"O círculo é a forma perfeita da natureza." Efeito: no 3º nível vincula-se '
        'a um Círculo Druídico (Esporos, Estrelas, Lua, Marés, Pastor Elemental, '
        'Sonhos ou Terra). Recebe as características de 3º nível do Círculo '
        'escolhido e características adicionais nos níveis 6, 10 e 18 de Druida.',

    "Aprimoramento de Atributo ou Talento":
        '"A seiva sobe com o passar das estações." Efeito: ao alcançar o 4º nível, '
        'e novamente nos níveis 8, 12, 16 e 19, escolha: Aumento de Atributo '
        '(+2 num atributo, ou +1 em dois atributos diferentes; máximo 20); ou '
        'Talento (escolha um talento cujos pré-requisitos você atenda).',

    "Intuição Selvagem":
        '"Aprendi a ler o que não se mostra: o silêncio entre dois coaxos, a pressa '
        'de um rastro fresco." Efeito: no 5º nível ganha proficiência em duas '
        'perícias à sua escolha entre Intuição, Sobrevivência, Medicina, Natureza '
        'ou Percepção. Especialização Instintiva: se já for proficiente em uma '
        'dessas perícias, em vez disso adquire Especialização (dobro do bônus de '
        'proficiência em testes daquela perícia).',

    "Característica de Círculo":
        '"Minha conexão com o ciclo escolhido se aprofunda. A magia deixa de ser '
        'esforço e passa a ser reflexo." Efeito: você recebe a característica do '
        'seu Círculo Druídico correspondente a este nível, conforme o Círculo '
        'escolhido no 3º nível.',

    "Fúria Elemental":
        '"A natureza fala em línguas antigas: gelo que conserva, brasa que devora, '
        'trovão que afasta." Efeito: no 7º nível escolha uma das opções (pode '
        'alterar ao fim de um Descanso Longo). '
        'Feitiçaria Potente: sempre que conjurar um truque de Druida que cause '
        'dano, ou quando uma criatura sofrer dano de um efeito do seu Surto '
        'Selvagem, adiciona seu mod. de Sabedoria a uma rolagem de dano desse '
        'efeito. Você escolhe se o dano adicional é do tipo original ou Elétrico, '
        'Fogo, Gélido ou Trovejante. Restrições: aplica em apenas 1 alvo por '
        'conjuração; só afeta truques da lista de Druida; dano extra não é '
        'multiplicado em crítico. '
        'Golpe Primal: uma vez por turno, ao acertar com arma ou ataque de besta '
        'enquanto em Forma Selvagem, causa 1d8 de dano adicional (aumenta para '
        '2d8 no 14º nível). Tipo: Elétrico, Fogo, Gélido ou Trovejante (escolhe a '
        'cada acerto). Restrições: só uma vez por turno; ataque deve ser parte da '
        'Ação ou Ação Bônus (não Reação).',

    "Guardião da Terra":
        '"Antes de erguer muralhas, a floresta aprende a atrasar passos." Efeito: '
        'no 9º nível você manipula terreno e magia para controlar o campo. '
        'Vigilância da Mata: sempre que uma criatura hostil estiver dentro de área '
        'criada por uma magia sua (que afete terreno) ou pelo seu Surto Selvagem, '
        'e essa criatura fizer um teste de resistência, você pode usar Reação '
        'para impor Desvantagem nele. Não se aplica ao TR inicial contra a magia '
        'ou Surto que criou a área (só aos subsequentes, enquanto permanecer na '
        'área). Sussurro pelas Raízes: pode conjurar truques de Druida tendo como '
        'alvo criaturas dentro dessas áreas, mesmo sem linha de visão direta ou '
        'além do alcance normal do truque (o feitiço ainda precisa de alvo válido '
        'e segue as demais regras; a terra serve de conduto).',

    "Alma da Natureza":
        '"Quando o mundo me atravessa, não encontra arestas, encontra seiva." '
        'Efeito: no 14º nível, sua fisiologia foi moldada de forma permanente '
        'pela magia primal. Sangue Inócuo: imune a dano de Veneno, à condição '
        'Envenenado e a doenças. Seiva Lenta: para cada 10 anos passados, '
        'envelhece apenas 1 ano. Metamorfose Infinda: pode usar Forma Selvagem '
        'para se transformar em feras de ND 1 ou inferior sem gastar usos de '
        'Surto Selvagem (não recebe PV temporários nessa modalidade; demais '
        'regras de Forma Selvagem continuam).',

    "Arquidruida":
        '"Há um ponto em que a mata deixa de ser cenário e vira pulso." Efeito: '
        'no 20º nível, você se torna uma manifestação do ciclo natural. '
        'Forma Selvagem Ilimitada: pode usar Forma Selvagem à vontade, sem gastar '
        'usos de Surto Selvagem (ainda gasta Ação Bônus). '
        'Magia Primal: enquanto estiver com ao menos 1 PV, não pode ser '
        'amaldiçoado, atordoado, paralisado, petrificado ou enfeitiçado por '
        'efeitos mágicos. '
        'Sopro do Mundo: ao terminar um Descanso Curto, recupera 1 espaço de '
        'magia gasto de cada círculo de 1º a 5º. '
        'Sintonia Total: sempre tem preparadas conjurar animais, despertar, '
        'cura ferimentos em massa e tempestade dos elementos.',

    # ======================================================================
    # CÍRCULO DOS ESPOROS (sid 22) — 7 features
    # ======================================================================
    "esporos:Magias do Círculo":
        '"Minha magia brota do fim para alimentar o começo." Efeito: você tem '
        'sempre preparadas as Magias do Círculo dos Esporos (não contam no limite '
        'de magias preparadas, contam como Druida). Lista: Nv 3 (1º círc.) '
        'Infligir Ferimentos, Dívida do Diabo; Nv 3 (2º) Repouso Tranquilo, '
        'Armadura da Morte; Nv 5 (3º) Animar Mortos, Conceder Maldição; Nv 7 (4º) '
        'Definhar, Sifão Sacrificial; Nv 9 (5º) Névoa Mortal, Contágio.',

    "esporos:Hospedeiro Fúngico":
        '"Carrego uma colônia veterana sob a pele, esporos pacientes que aprendem '
        'a cuspir frio." Efeito: seu corpo é hospedeiro permanente de esporos '
        'simbióticos. Esporos Mortais: aprende o truque Toque Arrepiante (conta '
        'como Druida, não conta no limite). Necrose Ancestral: uma vez por turno, '
        'ao causar dano com magia de Druida ou arma, adiciona 1d8 de dano '
        'necrótico ao dano causado. Colônia Simbiótica: uma vez por turno, ao '
        'causar dano necrótico, ganha PV temporários iguais à metade do dano '
        'necrótico (arred. baixo); não funciona contra Construtos ou Mortos-Vivos.',

    "esporos:Guardião Fúngico":
        '"Eu e a colônia respiramos juntos." Efeito: você pode despertar seus '
        'esporos em uma forma de combate reforçada. Fusão Micelial (Ação Bônus): '
        'gasta 1 uso de Surto Selvagem para assumir a forma de Guardião Fúngico '
        'por 10 min (ou até ficar Incapacitado, ou encerrar com Ação Bônus). '
        'Carapaça de Micélio: ao se transformar, recebe PV temporários iguais a '
        '3 × nível de Druida. Enquanto nessa forma, PV temp. ganhos por Colônia '
        'Simbiótica se acumulam até o teto de 3 × nível de Druida (excesso é '
        'perdido). Miasma de Esporos: ar em raio 3 m enche-se de esporos tóxicos. '
        'No início ou final do turno de cada criatura viva (não Construto/Morto-'
        'Vivo, à sua escolha) dentro da área, ela faz TR Constituição vs. sua CD '
        'de magia; falha sofre dano necrótico, sucesso nada. A área conta como '
        'criada pelo seu Surto Selvagem. Dano do Miasma: Nv 3 = 1d8; Nv 6 = 2d8; '
        'Nv 10 = 3d8; Nv 18 = 4d8.',

    "esporos:Soldado Fúngico":
        '"Nem todo corpo termina. Alguns viram jardim." Efeito: você usa matéria '
        'orgânica como vetor disciplinado para seus esporos. Rito de Invocação: '
        'aprende Invocar Morto-Vivo (sempre preparada, conta como Druida, não '
        'conta no limite). Atalho do Cadáver: se houver cadáver de criatura viva '
        '(não Construto/Morto-Vivo) a até 3 m, morto há no máximo 1 hora, pode '
        'conjurar Invocar Morto-Vivo como Ação Bônus; nesse uso, a criatura '
        'invocada assume a forma Pútrida; pode gastar 1 uso de Surto Selvagem '
        'para dispensar o componente material (mantém verbais/somáticos). '
        'Concentração da Colônia: enquanto em forma de Guardião Fúngico, se o '
        'espaço usado em Invocar Morto-Vivo tiver círculo ≤ ⌊nível_Druida/3⌋, '
        'pode transferir a Concentração para a colônia (não precisa fazer TR; '
        'se a forma terminar, retoma a Concentração sem ação ou a magia acaba). '
        'Unhas Apodrecidas: o ataque Rotting Claw da criatura invocada causa '
        'dano necrótico em vez de cortante. Simbiose à Distância: uma vez por '
        'turno, quando a criatura invocada causar dano necrótico, esse dano '
        'conta como causado por você para Colônia Simbiótica.',

    "esporos:Esporos Virulentos":
        '"Quanto mais velho o micélio, mais fina a lâmina do seu perfume." '
        'Efeito: sua nuvem de esporos se torna mais vasta. Miasma Expandido: '
        'enquanto em forma de Guardião Fúngico, o raio do Miasma de Esporos '
        'aumenta para 4,5 m. Emanação do Soldado: enquanto tiver criatura '
        'invocada por Invocar Morto-Vivo, ela emana um Miasma de Esporos próprio '
        'em raio 1,5 m, usando sua CD, com mesmo tipo e quantidade de dano que '
        'seu Miasma atual e mesmas regras, exceto: a criatura invocada não ganha '
        'PV temporários por essa área (você permanece como fonte do efeito).',

    "esporos:Assimilação Elemental":
        '"Esporos aprendem rápido. Absorvem, decompõem, devolvem em outra forma." '
        'Efeito: você mistura energia necrótica com poder elemental. Sintonia '
        'Necrótica: ao usar Fúria Elemental, adiciona dano necrótico às opções '
        'de tipo. Se escolheu Feitiçaria Potente, ao adicionar seu mod. de '
        'Sabedoria ao dano de truque de Druida ou efeito de Surto Selvagem, pode '
        'escolher que o dano adicional seja necrótico. Se escolheu Golpe Primal, '
        'ao causar o dano extra dessa feature, pode escolher que esse dano '
        'adicional seja necrótico. O tipo é declarado ao aplicar.',

    "esporos:Colônia Anciã":
        '"A colônia já não mora em mim, nós somos a mesma casa." Efeito: sua '
        'simbiose atinge profundidade celular. Sustento do Micélio: ao ativar '
        'Colônia Simbiótica, se seus PV atuais estiverem abaixo da metade do '
        'máximo, primeiro recupera PV até exatamente metade do máximo; o valor '
        'remanescente de PV temporários é aplicado normalmente. Acima da metade, '
        'Colônia Simbiótica funciona como de costume. Solo Entranhado: qualquer '
        'área do seu Miasma de Esporos (de Guardião Fúngico ou de criatura '
        'invocada por Invocar Morto-Vivo) é terreno difícil para criaturas à sua '
        'escolha enquanto estiverem dentro dela. No início de cada turno seu, '
        'você reescolhe quais criaturas são afetadas (persiste até o seu próximo '
        'turno); não escolhidas se movem normalmente.',

    # ======================================================================
    # CÍRCULO DAS ESTRELAS (sid 23) — 6 features
    # ======================================================================
    "estrelas:Magias do Círculo":
        '"O céu me entrega um alfabeto de luz. Eu apenas aprendo quais letras '
        'precisam ser ditas primeiro." Efeito: sempre tem preparadas as Magias '
        'do Círculo das Estrelas (não contam no limite, contam como Druida). '
        'Lista: Nv 3 truque Orientação; Nv 3 (1º) Raio Guiado, Clarão do Fogo '
        'Estelar; Nv 3 (2º) Raio Lunar, Ventos de Verão; Nv 5 (3º) Colheita do '
        'Brilho Lunar, Clarividência; Nv 7 (4º) Radiância Enjoativa, Sumidouro '
        'Gravitacional; Nv 9 (5º) Muralha de Luz, Alvorada; Nv 13 (7º) Coroa de '
        'Estrelas.',

    "estrelas:Mapa Estelar":
        '"Na palma da mão, carrego um atlas do firmamento." Efeito: você cria um '
        'Mapa Estelar (placa de pedra perfurada, disco de vidro gravado, '
        'pergaminho de constelações ou similar), que funciona como foco de '
        'conjuração para suas magias de Druida. Se for perdido ou destruído, '
        'pode criar um novo com ritual de 8 horas em Descanso Longo (sem custo). '
        'Sinal de Luar: enquanto segurando o Mapa, pode conjurar Raio Guiado sem '
        'gastar espaço; usos por dia iguais ao seu mod. de Sabedoria (mínimo 1), '
        'recuperando todos em Descanso Longo.',

    "estrelas:Forma Estelar":
        '"Traço minha própria constelação no corpo: juntas que brilham como '
        'estrelas, tendões alinhados em prata." Efeito: você pode assumir uma '
        'forma luminosa infundida pelo poder das constelações. Ascensão da '
        'Constelação (Ação Bônus): gasta 1 uso de Surto Selvagem; emite luz '
        'plena em raio 3 m + fraca por mais 3 m; dura 10 minutos (termina se '
        'dispensar, ficar Incapacitado ou usar novamente). Escolha da '
        'Constelação ao ativar: Arqueiro, Cálice ou Dragão; no início de cada '
        'turno, pode trocar. Arqueiro: ao ativar e como Ação Bônus em cada turno, '
        'faz um ataque mágico à distância contra criatura a até 18 m; acerto = '
        '1d8 + mod. Sabedoria de dano radiante (usa seu Mod. de Ataque Mágico). '
        'Cálice: ao conjurar magia com espaço que cure PV, você ou uma criatura '
        'a até 9 m recupera 1d8 + mod. Sabedoria PV adicionais. Dragão: em '
        'testes de Inteligência, Sabedoria ou TR de Constituição para manter '
        'Concentração, trata resultado de 9 ou menos como 10 antes de '
        'modificadores.',

    "estrelas:Presságio Cósmico":
        '"O céu deixa bilhetes na margem da noite." Efeito: você canaliza '
        'favorecimento ou desventura do cosmos. Ao terminar um Descanso Longo, '
        'role 1d6: par = Fortuna; ímpar = Infortúnio (vale até próximo Descanso '
        'Longo). Enquanto o presságio estiver ativo, pode usar Reação quando '
        'criatura que possa ver a até 9 m fizer jogada de ataque, TR ou teste '
        'de habilidade — Fortuna soma 1d6 ao resultado dela, Infortúnio subtrai '
        '1d6. Declarar antes do Mestre anunciar sucesso/falha. Usos por descanso '
        '= mod. Sabedoria (mín 1); recupera todos em Descanso Longo.',

    "estrelas:Constelações Cintilantes":
        '"As linhas de prata se adensam." Efeito: sua Forma Estelar ganha '
        'potência. Brilho Aumentado: Arqueiro passa a causar 3d8 + mod. '
        'Sabedoria radiante; Cálice passa a curar 3d8 + mod. Sabedoria PV '
        'adicionais. Voo do Dragão: com a constelação Dragão ativa, ganha '
        'deslocamento de voo = deslocamento de caminhada (pode flutuar sem se '
        'mover). Céu Mutável: uma vez por turno, pode trocar a constelação '
        'ativa em qualquer momento do turno (ainda em Forma Estelar).',

    "estrelas:Corona Borealis":
        '"A coroa não é metal, é constelação trançada em volta do pensamento." '
        'Efeito: você funde Forma Estelar com Coroa de Estrelas. Fusão Estelar: '
        'em seu turno, se estiver em Forma Estelar com Coroa de Estrelas ativa, '
        'sem usar ação você funde os dois efeitos: duração da Forma Estelar passa '
        'a ser igual à restante da Coroa (máximo 1 hora); ganha Resistência a '
        'concussão, perfurante e cortante; pode usar as cargas de Coroa de '
        'Estrelas durante a fusão. Benefícios Coroados (cada constelação ganha '
        'um benefício adicional ao gastar 1 carga de Coroa): Arqueiro Coroado '
        '(Chuva Lunar) — em vez de 1 ataque, escolhe N criaturas a até 18 m (N '
        '= mod. Sabedoria, mín 1) e faz 1 ataque mágico contra cada com o dano '
        'do Arqueiro. Cálice Coroado (Astrolábio da Vida) — não rola ataque; '
        'escolhe criatura a até 36 m que recupera PV iguais ao dano radiante da '
        'carga em acerto normal. Dragão Coroado (Raio Estelar) — como Ação, '
        'libera linha de 30 m × 1,5 m; cada criatura na linha faz TR Destreza '
        'vs. sua CD; falha sofre o dano radiante da carga, sucesso metade. Usos '
        'da Fusão: 2 por Descanso Longo.',

    # ======================================================================
    # CÍRCULO DA LUA (sid 24) — 5 features
    # ======================================================================
    "lua:Magias do Círculo":
        '"O brilho da lua revela o que o sol dispersa." Efeito: sempre tem '
        'preparadas as Magias do Círculo da Lua (não contam no limite). Pode '
        'conjurá-las mesmo em Forma Selvagem (ignora a restrição usual de não '
        'conjurar nessa forma; demais regras se aplicam). Lista: Nv 3 truques '
        'Fagulha Estelar, Selvageria Primeva; Nv 3 (1º) Curar Ferimentos, Lâmina '
        'Faminta; Nv 3 (2º) Raio Lunar, Passo Nebuloso; Nv 5 (3º) Conjurar '
        'Animais, Colheita do Brilho Lunar; Nv 7 (4º) Fonte de Luz Lunar, '
        'Chamado do Selvagem; Nv 9 (5º) Cura em Massa, Manto Lunar de Alustriel.',

    "lua:Formas Lunares":
        '"A lua não tem uma só face." Efeito: sua Forma Selvagem é modificada '
        'pela magia lunar. ND Máximo: o ND máximo da besta que pode assumir é '
        '⌈nível_Druida/3⌉ (Nv 3 = 1, Nv 6 = 2, Nv 9 = 3, Nv 12 = 4, Nv 15 = 5, '
        'Nv 18 = 6, Nv 20 = 7). Armadura da Lua: em Forma Selvagem, sua CA passa '
        'a ser 13 + mod. Sabedoria se for maior que a CA natural da besta. '
        'Vigor Lunar: ao entrar em Forma Selvagem, ganha PV temporários iguais '
        'a 4 × nível de Druida. Eclipses Lunares: ao entrar em Forma Selvagem, '
        'se sintonizado com um Item Lunar ou sob lua cheia visível, pode '
        'declarar canalização — Vigor Lunar passa a 5 × nível de Druida. '
        'Aspecto Lunar (escolha ao entrar; dura enquanto na forma): '
        'Lua Cheia (predador ofensivo) — ao usar Ação de Ataque com arma natural, '
        'pode usar Ação Bônus para segundo ataque com arma natural diferente '
        '(garra+mordida); usos por descanso curto = mod. Sabedoria (mín 1). '
        'Lua Nova (caçador furtivo) — pode usar Ação Bônus para Disparada, '
        'Desengajar ou Esconder. Lua Crescente (defensor) — quando acerta '
        'criatura com ataque natural em Forma Selvagem ou com magia do Círculo '
        'da Lua, ela tem Desvantagem em todas as jogadas de ataque até o início '
        'do seu próximo turno, exceto contra você.',

    "lua:Maré de Caça":
        '"A lua afina tendões como afina marés." Efeito: você molda o combate '
        'como uma perseguição ritual. Instinto Predatório: em Forma Selvagem, '
        'uma vez por turno, ao acertar com ataque de arma natural, pode forçar '
        'TR de Força ou Destreza (sua escolha) vs. sua CD; falha aplica um '
        'efeito: Derrubar (Prostrada), Empurrar (3 m em linha reta) ou Travar '
        '(deslocamento 0 até início do seu próximo turno). Ataques Guiados pela '
        'Lua: em Forma Selvagem, pode usar seu mod. de Sabedoria no lugar de '
        'Força ou Destreza para jogadas de ataque e dano dos ataques naturais.',

    "lua:Forma Selvagem Anciã":
        '"Os ritos antigos engrossam meu couro." Efeito: em Forma Selvagem, '
        'Resistência a dano de concussão, perfurante e cortante. Surto de '
        'Instinto: ao rolar Iniciativa sem nenhum uso de Surto Selvagem '
        'restante, recupera 1 uso.',

    "lua:Avatar da Lua":
        '"Minha forma original é lembrança. Minha carne é rito." Efeito: você '
        'se torna um avatar do ciclo lunar. Conjuração Instintiva: pode '
        'conjurar magias de Druida normalmente em Forma Selvagem, desde que '
        'não exijam componentes materiais ou que esses não sejam consumidos. '
        'Seu corpo transformado conta como foco de conjuração; pode executar '
        'componentes verbais e somáticos em qualquer Forma Selvagem. '
        'Metamorfose Fluida: em Forma Selvagem, como Ação Bônus, pode trocar '
        'para outra besta que conheça mantendo todos os efeitos ativos '
        '(Concentração, Aspecto Lunar atual, PV e PV temp., marcas e condições '
        'aplicadas); o ND deve respeitar seu limite. Eclipse das Três Luas: uma '
        'vez por Descanso Longo, ao entrar em Forma Selvagem pode invocar este '
        'modo — recebe simultaneamente os benefícios de Lua Cheia, Lua Nova e '
        'Lua Crescente, e ganha PV temporários iguais a 7 × nível de Druida em '
        'vez do valor normal de Vigor Lunar; dura enquanto a forma durar.',

    # ======================================================================
    # CÍRCULO DAS MARÉS (sid 25) — 6 features
    # ======================================================================
    "mares:Magias das Marés":
        '"Carrego comigo o ofício da água." Efeito: sempre tem preparadas as '
        'Magias das Marés (não contam no limite, contam como Druida). Lista: '
        'Nv 3 truque Raio de Gelo; Nv 3 (1º) Onda Trovejante, Névoa '
        'Obscurecente; Nv 3 (2º) Rajada de Vento, Estrondo; Nv 5 (3º) '
        'Relâmpago, Respirar na Água; Nv 7 (4º) Controlar Água, Tempestade de '
        'Gelo; Nv 9 (5º) Conjurar Elemental, Imobilizar Monstro.',

    "mares:Discípulo das Águas":
        '"Aprendi a ouvir o que a água diz: cede, contorna, retorna." Efeito: '
        'Pulmões de Maré — ganha deslocamento de nado igual ao de caminhada e '
        'pode respirar tanto ar quanto água. Truque da Corrente: aprende o '
        'truque Moldar Água (não conta no limite de truques e não pode ser '
        'substituído ao subir de nível).',

    "mares:Surto Selvagem: Aura de Maré":
        '"Ergo a mão e a umidade se adensa." Efeito (Ação Bônus): gasta 1 uso '
        'de Surto Selvagem para emanar aura aquosa em raio 4,5 m centrada em '
        'você; dura 1 min, move-se com você, termina se ficar Incapacitado ou '
        'encerrar voluntariamente (Ação Bônus). Conta como uso de Surto '
        'Selvagem para todos os fins. Maré de Retorno: criaturas à sua escolha '
        'dentro da aura tratam-na como terreno difícil, salvo se tiverem '
        'deslocamento de nado. Fluxo Natural: aliados escolhidos ignoram '
        'terreno difícil dentro da aura; uma vez por turno, ao se mover dentro, '
        'um aliado escolhido pode se deslocar 1,5 m adicional sem provocar '
        'oportunidade. Restauração de Maré: ao conjurar magia que recupera PV, '
        'adiciona mod. Sabedoria aos PV recuperados por cada alvo (mín +1); '
        'além disso, ao conjurar magia com espaço que cure qualquer criatura, '
        'cada criatura à sua escolha dentro da aura também recupera PV iguais '
        'ao seu nível de Druida.',

    "mares:Ressaca":
        '"Sob a superfície, a água guarda um puxão que só cede para quem sabe '
        'boiar." Efeito: enquanto sua Aura de Maré estiver ativa, quando '
        'criatura hostil dentro da aura se mover voluntariamente, pode usar '
        'Reação para forçar TR de Força vs. sua CD. Falha: escolhe Corrente '
        'Direcionada (empurra para espaço desocupado dentro da aura) ou '
        'Expulsão pela Maré (empurra 3 m para fora da aura medidos da borda). '
        'Sucesso: deslocamento da criatura reduzido em 3 m até o fim daquele '
        'movimento. Criaturas com deslocamento de nado têm Desvantagem nesse '
        'TR. Dilúvio Focal: ao alvejar criatura dentro da Aura de Maré com uma '
        'das suas Magias das Marés, ela tem Desvantagem no TR inicial.',

    "mares:Águas da Vida":
        '"Onde a maré me cerca, cada respiração vira goles de descanso. Eu '
        'reparto isso com os meus." Efeito: ao ativar Surto Selvagem: Aura de '
        'Maré, você e cada aliado à sua escolha dentro da aura no momento da '
        'ativação ganham PV temporários iguais ao seu nível de Druida + mod. '
        'de Sabedoria. PV temp. não gastos são perdidos quando a aura termina.',

    "mares:Mestre das Ondas":
        '"Já não ergo a água. Eu caminho com ela." Efeito: Maré à Vontade — '
        'pode conjurar Controlar Água à vontade sem gastar espaço (ainda exige '
        'Concentração). Maré Ampla: o raio da sua Aura de Maré aumenta para 9 '
        'm. Tsunami Instantâneo: uma vez por Descanso Longo, se estiver em '
        'corpo d\'água grande o suficiente (lago, rio largo, mar, oceano), '
        'pode conjurar Tsunami como Ação (sem espaço, sem componentes '
        'materiais); ponto de origem em qualquer ponto a até 90 m sobre/dentro '
        'do corpo d\'água; ainda exige Concentração.',

    # ======================================================================
    # CÍRCULO DO PASTOR ELEMENTAL (sid 26) — 5 features
    # ======================================================================
    "pastor:Vínculo Elemental do Pastor":
        '"Medito onde a seiva encontra o vento." Efeito: você estabelece '
        'conexão profunda com planos elementais. Sintonização Elemental: ao '
        'terminar Descanso Longo, gasta 1 hora em ritos para se sintonizar '
        'com Água, Ar, Fogo ou Terra (define magias do círculo e tipo do seu '
        'Familiar Primal até nova sintonização). Magias do Elemento (sempre '
        'preparadas, contam como Druida, fora do limite): '
        'Água — Nv 3 truque Moldar Água; Nv 3 (1º) Névoa Obscurecente; Nv 3 '
        '(2º) Nublar; Nv 5 (3º) Tempestade de Granizo; Nv 7 (4º) Controlar a '
        'Água; Nv 9 (5º) Cone de Frio. '
        'Ar — Nv 3 truque Lufada; Nv 3 (1º) Onda Trovejante; Nv 3 (2º) Rajada '
        'de Vento; Nv 5 (3º) Muralha de Vento; Nv 7 (4º) Invisibilidade Maior; '
        'Nv 9 (5º) Aparência. '
        'Fogo — Nv 3 truque Controlar Chamas; Nv 3 (1º) Mãos Flamejantes; Nv 3 '
        '(2º) Raio Ardente; Nv 5 (3º) Bola de Fogo; Nv 7 (4º) Escudo de Fogo; '
        'Nv 9 (5º) Coluna de Chamas. '
        'Terra — Nv 3 truque Moldar Terra; Nv 3 (1º) Santuário; Nv 3 (2º) '
        'Agarrão Terreno de Maximilian; Nv 5 (3º) Mesclar-se às Rochas; Nv 7 '
        '(4º) Moldar Rochas; Nv 9 (5º) Muralha de Pedra. '
        'Lista Universal do Pastor (sempre preparada, qualquer sintonização): '
        'Nv 3 (1º) Bênção; Nv 3 (2º) Invocar Fera; Nv 5 (3º) Sinal da '
        'Esperança; Nv 7 (4º) Invocar Elemental; Nv 9 (5º) Invocar Dragão.',

    "pastor:Familiar Primal":
        '"A fera pequena não é arma, é sentinela." Efeito: ao usar Surto '
        'Selvagem: Elo Primal, pode invocar um Familiar Primal em vez do '
        'familiar normal. É um Elemental cuja aparência reflete sua '
        'Sintonização Elemental atual (usa ficha do elemento sintonizado). '
        'Age no seu turno, imediatamente após você. Obedece a comandos verbais '
        'seus, sem exigir ação; sem comandos, realiza Esquivar. Vínculo '
        'telepático em raio 30 m. Pode usar Ação para ver e ouvir pelos '
        'sentidos dele até o início do seu próximo turno. Se reduzido a 0 PV, '
        'desaparece; pode invocá-lo novamente com Elo Primal. Ficha-base: '
        'Pequeno elemental; CA 11 + Bônus de Proficiência (armadura natural); '
        'PV 20 + 5 × nível de Druida; deslocamento 9 m, nado 9 m.',

    "pastor:Exaltação Elemental":
        '"Com um estalo de rito, meu companheiro deixa de ser centelha e vira '
        'tocha." Efeito (Ação Bônus): gasta 1 uso de Surto Selvagem para fazer '
        'seu Familiar Primal entrar em Exaltação Elemental; o familiar pode '
        'estar em qualquer ponto a até 9 m. Duração: 1 min (ou até 0 PV do '
        'familiar, ou até você ficar Incapacitado). Efeitos: tamanho do '
        'familiar = Médio; Força +2; PV temporários = 2 × nível de Druida. '
        'Aura Explosiva: ao entrar em Exaltação, onda de choque em aura 3 m; '
        'criaturas à sua escolha na área fazem TR Destreza vs. sua CD; falha '
        'sofre N d6 do tipo do elemento (N = mod. Sabedoria, mín 1d6); sucesso '
        'metade. Socorro dos Espíritos: no início de cada turno do familiar '
        'exaltado, criaturas dos tipos Besta, Dragão, Elemental, Fada ou Planta '
        'à sua escolha dentro da aura recuperam PV iguais ao mod. Sabedoria '
        '(mín 1).',

    "pastor:Exaltação Maior do Familiar":
        '"Quando o laço cresce, o espírito cresce com ele." Efeito: Tamanho e '
        'Força — ao entrar em Exaltação Elemental, pode escolher que o familiar '
        'fique Grande; nesse caso, bônus total de Força é +6 (substitui o +2). '
        'Aura Ampliada: durante Exaltação, raio da aura passa a 9 m. Reações '
        'Elementais (uma por rodada): '
        'Fogo (Cremação Tutelar): quando criatura Grande ou menor morre na '
        'aura, o corpo é incinerado; familiar recupera N d6 PV (N = mod. '
        'Sabedoria, mín 1d6); em seguida, escolhe criatura na aura para '
        'recuperar essa quantidade ou sofrer essa quantidade como dano de fogo. '
        'Água (Maré Redentora): aliado na aura sofreria dano — reduz o dano em '
        'N d6 (N = mod. Sabedoria, mín 1d6); pode deslocar a criatura 1,5 m '
        'para espaço desocupado sem provocar oportunidade; se o dano for fogo, '
        'ela ganha Resistência a fogo até o início do próximo turno do '
        'familiar. Ar (Rajada Desviadora): aliado na aura é alvo de ataque à '
        'distância — recebe meia cobertura (+2 CA contra esse ataque); em '
        'seguida pode se mover 3 m sem provocar oportunidade; se o ataque '
        'errar, atacante sofre N d6 elétrico ou trovejante (N = mod. '
        'Sabedoria; tipo à sua escolha a cada uso). Terra (Prisão da Terra): '
        'inimigo na aura tenta se mover voluntariamente — TR Força vs. sua CD; '
        'falha deslocamento 0 nesse movimento; sucesso deslocamento reduzido '
        'em 3 m.',

    "pastor:Reduto Elemental, Vigília dos Quatro":
        '"Quando meu passo vacila, o mundo me devolve em quatro vozes." Efeito '
        '(gatilho): quando reduzido a 0 PV mas não morrer instantaneamente, '
        'pode ativar Reduto Elemental (uso por Descanso Longo). Casulo '
        'Elemental: você entra em estase até o início do seu próximo turno — '
        'deslocamento 0, Paralisado, imune a dano, não pode ser alvo de '
        'efeitos ou magias; dano pendente nesse intervalo é ignorado. Chamado '
        'dos Guardiões: 4 Feras Elementais em Exaltação Elemental surgem em '
        'espaços desocupados a até 6 m de você; você escolhe o elemento de '
        'cada; agem imediatamente após surgir, em sequência (sua ordem). Cada '
        'usa ficha do seu Familiar Primal com Exaltação Elemental (com ajustes '
        'de tamanho e aura). Permanecem até o início do seu próximo turno. '
        'Restauração: ao terminar o efeito, você recupera PV iguais à soma da '
        'metade dos PV restantes de cada Fera Elemental invocada (arred. '
        'baixo).',

    # ======================================================================
    # CÍRCULO DOS SONHOS (sid 148) — 9 features
    # ======================================================================
    "sonhos:Magia dos Sonhos":
        '"Nem toda magia cresce em terra e água. Algumas florescem no intervalo '
        'entre um suspiro e o sono." Efeito: sempre tem preparadas as Magias '
        'do Círculo dos Sonhos (não contam no limite, contam como Druida). '
        'Lista: Nv 3 (1º) Luz de Fadas, Adormecer; Nv 3 (2º) Auxílio, '
        'Invisibilidade; Nv 7 (3º) Medo, Convocar Fada; Nv 9 (4º) Confusão, '
        'Assassino Fantasmagórico; Nv 13 (5º) Sonho, Vidência.',

    "sonhos:Sussurro Onírico":
        '"Há curas que são ervas e há curas que são lembranças." Efeito: você '
        'recebe um reservatório de Dados de Sonho. Reservatório: N d6 (N = '
        'nível de Druida). Recuperação: recupera todos os Dados de Sonho em '
        'Descanso Longo. Uso (Ação Bônus): escolhe criatura a até 18 m, gasta '
        'até mod. Sabedoria Dados de Sonho do reservatório (mín 1), rola, '
        'escolhe um efeito: Bálsamo do Sonhar — alvo recupera PV iguais ao '
        'total rolado. Sussurro do Pesadelo — alvo sofre dano psíquico igual '
        'ao total rolado e faz TR Sabedoria vs. sua CD; falha tem Desvantagem '
        'no próximo TR de Sabedoria até o fim do seu próximo turno.',

    "sonhos:Telepatia Onírica":
        '"Falar é lento demais para certas verdades." Efeito (Ação Bônus): '
        'escolhe criatura a até 9 m; você e ela podem se comunicar '
        'telepaticamente enquanto estiverem a uma distância (em milhas) ≤ mod. '
        'Sabedoria (mín 1 milha). Para se entenderem, cada um deve usar '
        'mentalmente um idioma que o outro conheça. Duração: N minutos (N = '
        'nível de Druida); termina antes se você formar elo com outra criatura.',

    "sonhos:Mensageiro dos Sonhos":
        '"Quando alguém dorme, a mente baixa suas muralhas, mas não as '
        'derruba." Efeito: quando você formar conexão com Telepatia Onírica e '
        'a criatura alvo estiver dormindo (natural ou por magia), a conexão se '
        'estende ao sonho dela. Enquanto durar, você pode enviar mensagens, '
        'imagens e sensações dentro do sonho como se falasse diretamente com a '
        'mente dela. A criatura percebe sua presença como parte do sonho; você '
        'pode se apresentar como você mesmo ou como figura simbólica. A '
        'criatura não desperta automaticamente por causa dessa comunicação.',

    "sonhos:Refúgio Onírico":
        '"Aprendi que descanso não é ausência de perigo, é um tipo de '
        'proteção." Efeito: durante Descanso Curto ou Longo, ritual de 10 min '
        'invoca os poderes do Plano Onírico. Escolha ponto a até 9 m; esfera '
        'invisível de raio 9 m centrada nele (cobertura total ainda bloqueia '
        'linha de efeito). Enquanto dentro, você e aliados escolhidos: +5 em '
        'testes de Destreza (Furtividade) e Sabedoria (Percepção); invisíveis '
        'para quem está fora; imunes a magias/efeitos de adivinhação de fora; '
        'luz de chamas dentro (tochas, fogueiras) não visível do lado de fora. '
        'Esfera se desfaz no fim do descanso ou se você se afastar mais de 9 m '
        'do ponto central. Só um Refúgio Onírico ativo por vez.',

    "sonhos:Surto Selvagem, Véu do Crepúsculo":
        '"Em combate, não há tempo para construir um lar." Efeito (Ação): '
        'gasta 1 uso de Surto Selvagem para criar esfera onírica em ponto a '
        'até 18 m; raio inicial 3 m (Nv 6); 6 m (Nv 10); 9 m (Nv 18). Dura 1 '
        'min, sem Concentração, termina se dispensar (sem ação) ou criar novo '
        'Véu. Ao criar e no início de cada turno seu, você escolhe quais '
        'criaturas são afetadas. Hostis escolhidas: Desvantagem em ataques '
        'contra alvos dentro da esfera. Aliadas escolhidas: Vantagem em '
        'ataques contra alvos dentro da esfera. Terreno: dentro da esfera é '
        'terreno difícil apenas para criaturas que você escolher. Mover o Véu: '
        'pode usar Ação Bônus para movê-lo até 3 m. Só um Véu do Crepúsculo '
        'ativo por vez.',

    "sonhos:Caminhos Escondidos":
        '"Sei onde as mentes se dobram." Efeito (Ação Bônus): escolhe criatura '
        'disposta a até 9 m; ela se teleporta para espaço desocupado que ela '
        'possa ver a até 18 m da posição atual dela. Usos por descanso = mod. '
        'Sabedoria (mín 1), recupera todos em Descanso Longo. Limiar Guiado: '
        'quando usar Caminhos Escondidos em criatura dentro de área criada por '
        'você (Véu do Crepúsculo, Refúgio Onírico ou área de magia de Druida '
        'sua), pode fazer o teletransporte ser para outro ponto dentro dessa '
        'área (em vez do alcance normal); não gasta um uso de Caminhos '
        'Escondidos nesse caso.',

    "sonhos:Refúgio Onírico Aprimorado":
        '"Chega um ponto em que uma bolha de silêncio não basta." Efeito: ao '
        'criar Refúgio Onírico, pode optar por transformá-lo em espaço '
        'semelhante a Mansão Magnífica de Mordenkainen. Porta e Morada: em '
        'vez de esfera invisível, conjura porta cintilante a até 18 m; leva a '
        'morada extradimensional ligada ao Plano Onírico, projetada por você, '
        'comportando até 50 cubos contíguos de 3 m. Ambiente limpo, seguro, '
        'confortável, responde sutilmente ao seu humor. Servos semi-'
        'transparentes atendem (não causam dano). Você e criaturas designadas '
        'entram e saem pela porta. Termina no fim do descanso ou se você se '
        'afastar mais de 9 m da porta. Mente Protegida e Fortaleza Mental: '
        'enquanto durar, criaturas em descanso ali ficam sob Mente Blindada '
        'durante todo o descanso; ao terminar, ficam sob Fortaleza do '
        'Intelecto até o início do próximo descanso.',

    "sonhos:Sonho Lúcido":
        '"Não sou mais um visitante do Plano Onírico." Efeito: quando usar '
        'Sussurro Onírico e gastar 5 ou mais Dados de Sonho em um único uso, '
        'aplique conforme a opção. Bálsamo do Sonhar Aprimorado: após a cura '
        'normal, alvo recebe também Restauração Menor (sem componentes/sem '
        'espaço). Sussurro do Pesadelo Aprimorado: se o alvo falhar no TR de '
        'Sabedoria, fica Paralisado até o fim do próximo turno dele. Sonho '
        'Dentro do Véu: sempre que usar Sussurro Onírico em alvo dentro do seu '
        'Véu do Crepúsculo ativo — Sussurro do Pesadelo é feito com '
        'Desvantagem no TR; Bálsamo do Sonhar cura o valor máximo de cada '
        'dado gasto (6 PV por d6 em vez de rolar).',

    # ======================================================================
    # CÍRCULO DA TERRA (sid 149) — 7 features
    # ======================================================================
    "terra:Acólito da Natureza":
        '"Sei onde o barro cede, onde a raiz firma, onde a areia engana." '
        'Efeito: você ignora terreno difícil imposto por ambientes naturais '
        '(neve profunda, pântanos, selvas densas, cascalho solto, dunas, gelo '
        'irregular, vegetação emaranhada). Não evita terreno difícil criado '
        'por magia ou construções artificiais, salvo se a magia ou habilidade '
        'descrever explicitamente como natural.',

    "terra:Regeneração Natural":
        '"A terra não desperdiça." Efeito: ao terminar Descanso Curto, quando '
        'você recuperaria usos de Surto Selvagem, pode abdicar de recuperar 1 '
        'uso de Surto Selvagem; em troca, recupera 1 espaço de magia gasto de '
        'um círculo à sua escolha, até no máximo seu mod. de Sabedoria (mín '
        '1º círculo). Ex.: mod. Sab. +3 permite recuperar espaço de até 3º '
        'círculo ao custo de 1 uso de Surto Selvagem que recuperaria.',

    "terra:Magias do Terreno":
        '"Cada lugar tem uma oração própria." Efeito: ritual de 1 hora em '
        'meditação (pode ser parte de Descanso Curto/Longo) para se '
        'sintonizar com o Terreno em que está. Tipos: Costa, Deserto, '
        'Floresta, Campina, Montanha, Pântano, Tundra ou Subterrâneo. '
        'Enquanto sintonizado, sempre tem preparadas as magias do Terreno '
        'escolhido (não contam no limite, contam como Druida). Pode mudar '
        'fazendo o ritual novamente. '
        'Costa: Nv 3 truque Moldar Água; Nv 3 (1º) Névoa Obscurecente; Nv 3 '
        '(2º) Passo Nebuloso; Nv 5 (3º) Onda de Maré; Nv 7 (4º) Esfera '
        'Aquosa; Nv 9 (5º) Redemoinho. '
        'Deserto: Nv 3 truque Controlar Chamas; Nv 3 (1º) Imagem Silenciosa; '
        'Nv 3 (2º) Demônio de Poeira; Nv 5 (3º) Muralha de Areia; Nv 7 (4º) '
        'Terreno Alucinatório; Nv 9 (5º) Redemoinho. '
        'Floresta: Nv 3 truque Chicote de Espinhos; Nv 3 (1º) Emaranhar; Nv 3 '
        '(2º) Pele de Casca; Nv 5 (3º) Videira Apreensora; Nv 7 (4º) Muralha '
        'de Espinhos; Nv 9 (5º) Passo Arbóreo. '
        'Campina: Nv 3 truque Selvageria Primal; Nv 3 (1º) Passos Longos; Nv '
        '3 (2º) Passar sem Rastro; Nv 5 (3º) Aceleração; Nv 7 (4º) Liberdade '
        'de Movimento; Nv 9 (5º) Passo Longínquo. '
        'Montanha: Nv 3 truque Moldar Terra; Nv 3 (1º) Tremor de Terra; Nv 3 '
        '(2º) Crescimento de Espinhos; Nv 5 (3º) Invocar Relâmpagos; Nv 7 '
        '(4º) Pilares de Terra; Nv 9 (5º) Muralha de Pedra. '
        'Pântano: Nv 3 truque Infestação; Nv 3 (1º) Gordura; Nv 3 (2º) '
        'Escalada de Aranha; Nv 5 (3º) Nuvem Fétida; Nv 7 (4º) Inseto '
        'Gigante; Nv 9 (5º) Praga de Insetos. '
        'Tundra: Nv 3 truque Mordida Gélida; Nv 3 (1º) Faca de Gelo; Nv 3 '
        '(2º) Imobilizar Pessoa; Nv 5 (3º) Lentidão; Nv 7 (4º) Tempestade '
        'de Gelo; Nv 9 (5º) Cone de Frio. '
        'Subterrâneo: Nv 3 truque Spray Venenoso; Nv 3 (1º) Sono; Nv 3 (2º) '
        'Cegueira ou Surdez; Nv 5 (3º) Inimigos por Toda Parte; Nv 7 (4º) '
        'Moldar Rochas; Nv 9 (5º) Passagem pela Parede.',

    "terra:Surto Selvagem, Crescimento Exuberante":
        '"Digo uma palavra antiga e o chão lembra que sabe crescer." Efeito '
        '(Ação): gasta 1 uso de Surto Selvagem; escolhe cubo 4,5 m de lado a '
        'até 9 m, com ao menos um lado apoiado em superfície sólida. Cada '
        'criatura na área faz TR Destreza vs. sua CD; falha sofre 3d6 cortante '
        'mágico, sucesso metade. Conta como uso de Surto Selvagem para todos '
        'os fins. Terreno Difícil Persistente: após a explosão, a área se '
        'enche de vegetação densa e espinhos, ficando como terreno difícil '
        'por até 1 hora (ou até ser destruída por efeito adequado, ou até '
        'usar Crescimento Exuberante novamente). Criatura que se mover '
        'voluntariamente dentro sofre 1d6 cortante mágico a cada 1,5 m '
        'percorrido (no máximo uma vez por turno).',

    "terra:Crescimento Primevo":
        '"O mato me reconhece e abre caminho." Efeito: aprimora Surto '
        'Selvagem: Crescimento Exuberante. Aliados Isentos: ao criar a área, '
        'designa qualquer número de criaturas visíveis como aliadas; elas '
        'ignoram o terreno difícil e não sofrem o dano por mover-se dentro. '
        'Cobertura Natural: aliados designados ganham meia cobertura dentro '
        'da área (+2 CA, +2 em TR de Destreza). Aprimoramento de Dano: o dano '
        'inicial passa a Nv 3 = 3d6; Nv 6 = 4d6; Nv 10 = 6d6; Nv 18 = 9d6.',

    "terra:Amparo Natural":
        '"A terra ergue o ombro por mim." Efeito (Reação): ao sofrer dano de '
        'ácido, frio, fogo, elétrico, veneno ou trovejante, gasta 1 uso de '
        'Surto Selvagem para ganhar Resistência a esse tipo de dano. A '
        'resistência se aplica ao dano que desencadeou a reação e dura até '
        'você usar Amparo Natural de novo (escolhendo outro tipo) ou até '
        'terminar um Descanso Longo.',

    "terra:Mago Ancestral":
        '"Agora meu passo conhece dois sotaques de chão." Efeito: Dupla '
        'Sintonização — pode permanecer sintonizado a dois Terrenos ao mesmo '
        'tempo, mantendo ambas as listas de Magias do Terreno sempre '
        'preparadas. Ao realizar o ritual de Magias do Terreno, pode '
        'substituir uma ou ambas as sintonizações; pode escolher qualquer '
        'tipo de Terreno da tabela. Memória da Terra: ao se sintonizar com '
        'um Terreno usando o ritual, ao final você conjura Comunhão com a '
        'Natureza sem gastar espaço.',
}


# Mapping: (id_subclasse_or_None, nome) → chave em DESCRICOES
# Para classe: nome direto. Para subclasse: prefixo slug.
SUBCLASSE_PREFIXES = {
    22:  "esporos",
    23:  "estrelas",
    24:  "lua",
    25:  "mares",
    26:  "pastor",
    148: "sonhos",
    149: "terra",
}


def chave_para(sub_id: int | None, nome: str) -> str:
    """Resolve a chave em DESCRICOES para um par (sub, nome)."""
    if sub_id is None:
        return nome
    prefix = SUBCLASSE_PREFIXES[sub_id]
    return f"{prefix}:{nome}"


if __name__ == "__main__":
    print(f"Total descrições: {len(DESCRICOES)}")
    for k, v in DESCRICOES.items():
        print(f"  {k:<55} ({len(v)} chars)")
