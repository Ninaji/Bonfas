"""Descrições limpas de todas as 76 features de Bardo, escritas à mão a partir
do dump oficial (paginas/bardo.html). Substituem o output do parser que tinha
resíduos de scraper (`id="spoiler-..."`, `class="..."`, etc).

Chave: nome canônico (classe) OU 'slug:Nome' (subclasse).
  Prefixos de colégio: conselho, conspiracao, criacao, danca, espiritos,
  fascinio, laminas, skald.

Convenção (mesma do druida_descricoes.py):
  - Aspas duplas: 1 sentença de flavor
  - "Efeito:" introduz mecânicas
  - Sub-mecânicas com nome em prosa
  - Sem HTML, sem markdown, sem regex magic
"""

DESCRICOES = {

    # ======================================================================
    # CLASSE — 14 descrições únicas (cobrem 20 entradas; ASI e Característica
    # de Colégio repetem por nível)
    # ======================================================================
    "Conjuração de Magias":
        '"Minha magia é dirigir atenção: um símbolo no bolso, uma história curta, '
        'um traço de giz no chão." Efeito: você remodela a realidade em harmonia '
        'com sua música. Truques: conhece 2 truques da lista de Bardo (sugestões: '
        'Luzes Dançantes, Zombaria Viciosa); aprende truques adicionais nos níveis '
        '4 e 10; ao ganhar nível pode trocar 1 truque. Preparação: prepara magias '
        'de Bardo de 1º+ conforme a coluna "Magias Preparadas" (começa com 4). '
        'Espaços de Magia: conforme a tabela do Bardo; recupera todos em Descanso '
        'Longo. Troca de Magias: ao ganhar nível, pode trocar 1 magia preparada '
        'por outra da lista. Atributo de Conjuração: Carisma. Foco: pode usar um '
        'Instrumento Musical como foco. CD = 8 + bônus prof. + mod. Carisma; '
        'Ataque de Magia = bônus prof. + mod. Carisma.',

    "Inspiração Bárdica":
        '"Presença é linguagem. Eu só ajusto a cena para que a pessoa reencontre '
        'a própria coragem." Efeito: você inspira outras criaturas. Conceder '
        '(Ação Bônus): escolhe 1 criatura (não você) a até 18 m que possa ver ou '
        'ouvir você; ela ganha 1 Dado de Inspiração (começa d6). Só pode ter 1 '
        'dado por vez. Usar: dentro de 60 min, ao falhar em Teste de Habilidade, '
        'Jogada de Ataque ou TR, a criatura rola o Dado e soma ao teste (pode '
        'virar a falha em sucesso); o dado é gasto após rolado. Usos por descanso '
        '= mod. Carisma (mín 1); recupera todos em Descanso Longo. Aprimoramentos: '
        'o dado vira d8 no Nv 5, d10 no Nv 10, d12 no Nv 15.',

    "Especialização":
        '"Perícia é leitura fina: do ambiente, das pessoas, do tempo." Efeito: '
        'escolha 2 perícias nas quais já tenha proficiência — seu bônus de '
        'proficiência é dobrado em testes com elas. No 9º nível você escolhe '
        'mais 2 perícias para o mesmo benefício (ver Especialização Aprimorada).',

    "Pau Pra Toda Obra":
        '"Quando falta o recurso perfeito, entra o improviso competente." Efeito: '
        'você pode adicionar metade do seu bônus de proficiência (arred. baixo) '
        'a qualquer teste de habilidade que ainda não inclua o bônus de '
        'proficiência.',

    "Colégio de Bardo":
        '"Todo artista escolhe sua gramática: dança, espada, valor, conhecimento, '
        'criação, espíritos, conspiração." Efeito: no 3º nível escolha um Colégio '
        'de Bardo (Conselho, Conspiração, Criação, Dança, Espíritos, Fascínio, '
        'Lâminas ou Skald). Concede características no 3º nível e novamente nos '
        'níveis 6, 14 e 18.',

    "Incremento de Atributo ou Talento":
        '"A ferramenta principal sou eu. Lapidar corpo, mente e instinto amplia '
        'o alcance de qualquer performance." Efeito: ao alcançar os níveis 4, 8, '
        '12, 16 e 19, escolha: Aumento de Atributo (+2 num atributo, ou +1 em '
        'dois diferentes; máximo 20); ou Talento (cujos pré-requisitos você '
        'atenda).',

    "Fonte de Inspiração":
        '"Entre atos, respiro e rearranjo a cena. A centelha volta." Efeito: '
        'Recuperação Aprimorada — recupera todos os usos de Inspiração Bárdica '
        'ao terminar Descanso Curto ou Longo. Conversão Mágica — pode gastar um '
        'Espaço de Magia de qualquer nível (sem ação) para recuperar 1 uso de '
        'Inspiração Bárdica imediatamente.',

    "Característica de Colégio":
        '"Cada ato revela truques que só a linguagem escolhida permite." '
        'Efeito: você ganha a característica do seu Colégio de Bardo '
        'correspondente a este nível, conforme o Colégio escolhido no 3º nível.',

    "Contra-Canto":
        '"Eu quebro o clima: um contragesto, uma palavra no timing certo — e a '
        'mente volta para si." Efeito (Reação): se você ou uma criatura a até '
        '9 m falhar em um TR contra efeito que aplicaria Enfeitiçado ou '
        'Amedrontado, você força essa criatura a refazer o TR com Vantagem '
        'contra a mesma CD; o novo resultado vale.',

    "Especialização (Aprimorada)":
        '"Dominar é enxergar onde todos olham e notar o que ninguém percebe." '
        'Efeito: no 9º nível, escolha mais 2 perícias nas quais já seja '
        'proficiente — passa a adicionar o dobro do bônus de proficiência em '
        'testes com elas.',

    "Segredos Mágicos":
        '"Coleciono técnicas de outros palcos — templo, floresta, biblioteca." '
        'Efeito: a partir do 10º nível (e sempre que Magias Preparadas '
        'aumentar), você pode escolher novas magias preparadas das listas de '
        'Bardo, Clérigo, Druida e Mago. Elas contam como magias de Bardo e usam '
        'Carisma como atributo. Substituições ao subir de nível também podem vir '
        'dessas listas.',

    "Dado de Inspiração (d12)":
        '"Quando a minha presença ocupa a sala, até o cético respira diferente." '
        'Efeito: no 15º nível, seu Dado de Inspiração se torna um d12.',

    "Inspiração Superior":
        '"No abrir das cortinas, entro já com reservas." Efeito: sempre que '
        'rolar Iniciativa e tiver menos de 2 usos de Inspiração Bárdica '
        'restantes, você recupera usos até ter 2.',

    "Palavras da Criação":
        '"Duas sentenças primais: uma que chama de volta, outra que encerra." '
        'Efeito: no 20º nível, você tem sempre preparadas Palavra de Poder: '
        'Cura e Palavra de Poder: Matar (contam como Bardo, não contam no '
        'limite). Dueto de Poder: ao conjurar qualquer uma delas, pode escolher '
        'um segundo alvo a até 3 m do primeiro; o efeito se aplica a ambos.',

    # ======================================================================
    # COLÉGIO DO CONSELHO (sid 6) — 6 features
    # ======================================================================
    "conselho:Conselho Bárdico":
        '"Se a dúvida é grande, eu começo pelo fato que ninguém ousa negar." '
        'Efeito: sempre que fizer um teste de Inteligência para recordar '
        'informação, ou um teste de Carisma para convencer uma criatura, você '
        'pode substituir o d20 pelo seu nível de Bardo (antes de saber o '
        'resultado). Ganha proficiência em Enganação, História e Persuasão.',

    "conselho:Lógica Cortante":
        '"Uma vírgula muda o tempo; um adjetivo, a coragem; um silêncio, a '
        'sentença." Efeito (Reação): quando uma criatura (não você) a até 18 m '
        'que possa ouvir e entender você fizer uma jogada de ataque, TR ou '
        'teste de habilidade, você gasta 1 uso de Inspiração Bárdica e rola seu '
        'Dado de Inspiração, aplicando o resultado à rolagem dela: somar (para '
        'reforçar) ou subtrair (para enfraquecer). Decida antes de saber o '
        'resultado. Não concede nem consome o Dado de Inspiração que a criatura '
        'já tenha — é modificação direta da rolagem dela.',

    "conselho:Conselho Potente":
        '"Quando meu empurrão não resolve, eu guardo o empurrão para a hora '
        'certa." Efeito: se você usar sua Reação de Lógica Cortante e, ainda '
        'assim, a criatura errar o ataque, falhar no teste de habilidade ou no '
        'TR, o uso de Inspiração Bárdica não é gasto.',

    "conselho:Descobertas Mágicas":
        '"Um bom argumento cita fontes; um argumento excelente as domina." '
        'Efeito: escolha 2 magias das listas de Clérigo, Druida e/ou Mago '
        '(truque ou magia para a qual tenha espaços conforme a tabela de '
        'Bardo). Sempre as tem preparadas. Em Descanso Longo pode substituir '
        '1 delas por outra que atenda aos mesmos requisitos.',

    "conselho:Perícia Inigualável":
        '"Se a tese escorrega, eu reenuncio — e mostro por que nunca foi sobre '
        'sorte." Efeito: quando você fizer um teste de habilidade e falhar, '
        'pode gastar 1 uso de Inspiração Bárdica, rolar seu Dado de Inspiração '
        'e somar ao d20 (pode virar a falha em sucesso). Se ainda assim falhar, '
        'o uso não é gasto.',

    "conselho:Palavras Contagiantes":
        '"Convencer não termina no convencido — propaga-se como palmas bem '
        'marcadas." Efeito (Reação): quando uma criatura a até 18 m adicionar '
        'um dos seus Dados de Inspiração a um ataque/teste/TR e tiver sucesso, '
        'ou quando uma criatura sob Palavras Cortantes falhar, você pode '
        'encorajar ou desmoralizar uma criatura diferente (não você) que possa '
        'ouvi-lo a até 18 m — concedendo 1 Dado de Inspiração Bárdica ou '
        'aplicando Palavras Cortantes de novo, sem gastar usos. Usos por '
        'descanso = mod. Carisma (mín 1); recupera em Descanso Longo.',

    # ======================================================================
    # COLÉGIO DA CONSPIRAÇÃO (sid 7) — 7 features
    # ======================================================================
    "conspiracao:Influência Astuta":
        '"Nem todo recado precisa atravessar a sala." Efeito: ganha '
        'proficiência em Enganação e em 2 ferramentas à escolha entre Kit de '
        'Disfarces, Kit de Falsificação, Kit de Venenos ou Ferramentas de '
        'Ladrão. Ao conjurar uma magia de Bardo com componente verbal que '
        'tenha apenas 1 alvo a até 3 m, pode escolher que só o alvo ouça o '
        'componente verbal.',

    "conspiracao:Assalto Psíquico":
        '"A lâmina distrai, a frase decide." Efeito: ao acertar uma criatura '
        'com ataque com arma, pode gastar 1 Dado de Inspiração Bárdica para '
        'causar dano psíquico adicional igual a 2 rolagens do Dado de '
        'Inspiração. Escala: +3 rolagens no Nv 6; +4 no Nv 14; +5 no Nv 18.',

    "conspiracao:Sementes do Terror":
        '"Um minuto basta. Eu organizo a sala como um palco." Efeito: se '
        'conversar com uma criatura que possa ouvir e entender você por ao '
        'menos 1 minuto, pode gastar 1 Dado de Inspiração Bárdica para forçá-la '
        'a um TR de Sabedoria contra sua CD de Magia. Falha: por 1 hora ela '
        'fica Amedrontada de uma criatura (à sua escolha) que ambos possam ver '
        'e a trata como inimiga. Termina cedo se o alvo amedrontado ou aliados '
        'dele forem atacados por você/aliados. O alvo não percebe a '
        'manipulação, qualquer que seja o resultado.',

    "conspiracao:Golpe Sorrateiro":
        '"Treinei para que meu segundo gesto valha mais que o primeiro." '
        'Efeito: 1 vez por turno, ao acertar uma criatura com ataque com arma, '
        'causa dano adicional igual a 1 rolagem do seu Dado de Inspiração (não '
        'gasta o dado). Escala: 2 rolagens no Nv 14; 3 no Nv 18.',

    "conspiracao:Visagem Roubada":
        '"Rostos são figurinos que contam histórias antes da fala." Efeito: '
        'quando um humanoide que você possa ver morrer a até 9 m, pode usar '
        'Reação para capturar a Visagem dele. Como Ação, consome a Visagem '
        'para se transformar nele como era em vida, ganhando lembranças '
        'superficiais e info que ele compartilharia com conhecido casual. Dura '
        '1 hora (encerra como Ação). Criatura desconfiada percebe com TR de '
        'Sabedoria (Intuição) oposto ao seu Carisma (Enganação). Só 1 Visagem '
        'por vez; capturar outra perde a anterior.',

    "conspiracao:Manipulação Sinistra":
        '"Não peço obediência; ofereço discrição." Efeito: pode usar Sementes '
        'do Terror como Ação. Em falha do TR do alvo, em vez do efeito normal, '
        'pode plantar a crença de que você conhece o segredo mais sombrio '
        'dele: o alvo fica Enfeitiçado por você indefinidamente (até você ou '
        'aliados agirem com hostilidade contra ele). Enfeitiçado assim, ele o '
        'ajuda secretamente o melhor que puder, exceto lutar diretamente ou '
        'arriscar a própria vida. Só 1 criatura assim por vez; enfeitiçar '
        'outra encerra na anterior.',

    "conspiracao:Angústia Mental":
        '"Posso encerrar o medo num único golpe — ponto final limpo." Efeito: '
        'quando usar Assalto Psíquico, o alvo faz TR de Sabedoria contra sua '
        'CD de Magia ou fica Amedrontado de você até o fim do seu próximo '
        'turno. Além disso, ao acertar com ataque com arma uma criatura '
        'Amedrontada de você, pode encerrar a condição nela para transformar '
        'esse ataque em Acerto Crítico automático.',

    # ======================================================================
    # COLÉGIO DA CRIAÇÃO (sid 8) — 6 features
    # ======================================================================
    "criacao:Fragmento da Canção":
        '"Um pequeno símbolo orbita quem você inspira." Efeito: sempre que '
        'conceder Inspiração Bárdica, cria um Fragmento da Canção (nota, '
        'estrela, flor, runa) que orbita até 1,5 m do alvo. Intangível, '
        'invulnerável, dura até o alvo gastar o Dado de Inspiração. Ao usar o '
        'dado, aplique e o fragmento se desfaz: Teste de Habilidade — rola o '
        'Dado de Inspiração 2x e escolhe o melhor. Jogada de Ataque — após '
        'aplicar o dado, o fragmento estoura: alvo atingido e cada criatura à '
        'sua escolha a até 1,5 m fazem TR de Constituição contra sua CD; falha '
        'sofre dano trovejante igual ao resultado do Dado, sucesso nada. Teste '
        'de Resistência — após aplicar o dado, o alvo recebe PV temporários '
        'iguais ao resultado do Dado + mod. Carisma (mín 1).',

    "criacao:Obra da Criação":
        '"Você risca o contorno no ar e a matéria lembra seu formato." Efeito '
        '(Ação): cria um objeto inanimado não mágico que caiba na sua mão (ou '
        'em espaço desocupado a até 3 m). Visivelmente mágico; PV = nível de '
        'Bardo; CA = seu valor de Carisma; dura 1 hora (some a 0 PV, se você '
        'morrer, ou se criar outro). Valor ≤ 20 × nível de Bardo PO; você deve '
        'ser familiar com o objeto (se a fabricação exige perícia, precisa de '
        'proficiência nas ferramentas). Escala por slot: sem slot = tamanho da '
        'mão; 1º = Minúsculo; 2º = Pequeno; 3º = Médio; 4º = Grande; 5º = '
        'Enorme. Uso: 1/Descanso Longo (sem usos, gasta espaço de 2º+ para '
        'reusar). Só 1 Obra ativa por vez (muda no Nv 14, ver Crescendo '
        'Criativo). Pode substituir componentes não consumíveis, mas não '
        'consumíveis.',

    "criacao:Língua Ancestral":
        '"Toda porta tem um idioma secreto." Efeito (Ação): infunde sua fala '
        'com a Canção da Criação. Por 1 hora, qualquer criatura a até 18 m que '
        'possa ouvi-lo o entende como se você falasse o idioma nativo dela (a '
        'criatura deve falar ao menos 1 idioma). Usos: 1/Descanso Longo (sem '
        'usos, gasta espaço de 2º+ para reusar).',

    "criacao:Dança da Criação":
        '"Você chama e o objeto se endireita como colega de ofício recém-'
        'desperto." Efeito (Ação): no 6º nível, anima um item não mágico '
        'Grande ou menor que possa ver a até 9 m. Usa a ficha do Item Dançante '
        '(usa o seu bônus de proficiência). Amigável a você e companheiros, '
        'obedece a seus comandos. Animado até 0 PV ou até você morrer. '
        '1/Descanso Longo (ou gasta espaço de 3º+ para reusar). Só 1 item '
        'animado por vez (animar novo torna o anterior inanimado). Item '
        'Dançante: constructo Médio ou menor, CA 16 (armadura natural), PV '
        '10 + 5 × seu nível, deslocamento 9 m, planar 9 m.',

    "criacao:Crescendo Criativo":
        '"A bancada vira coro de utilidades sem ruído." Efeito: ao usar Obra '
        'da Criação, pode criar até mod. Carisma objetos (mín 2) de uma vez; '
        'excedendo, escolhe quais criações anteriores somem. Apenas 1 objeto '
        'pode ter o maior tamanho; os demais Pequenos ou Minúsculos. Remove o '
        'limite de valor em PO (restrição de componentes consumíveis '
        'permanece). Ao gastar espaço de magia com Obra da Criação, a criação '
        'dura 24 horas (em vez de 1).',

    "criacao:Canção Verdadeira":
        '"O rascunho decide morar no mundo." Efeito: Obra perene — ao usar '
        'Obra da Criação gastando espaço de magia, o objeto é permanente (até '
        'destruído). Orquestra da Matéria — pode manter até 2 Itens Dançantes '
        '(o 2º exige espaço de 3º+); animar um 3º torna um anterior inanimado. '
        'Comando em coro — 1×/turno, ao conjurar magia de Bardo ou conceder '
        'Inspiração Bárdica, ordena que um Item Dançante faça a Ação Ajudar '
        'sem custo de ação. Despertar a matéria — aprende despertar e pode '
        'conjurá-la sem componente material (depois precisa 1 Descanso Longo '
        'para repetir); se lançada num Item Dançante seu, ele se comunica '
        'telepaticamente nos seus idiomas.',

    # ======================================================================
    # COLÉGIO DA DANÇA (sid 9) — 8 features
    # ======================================================================
    "danca:Cena é Corpo":
        '"Seu carisma não sai da boca — sai do eixo." Efeito: ganha '
        'proficiência em Atuação; se já for proficiente, ganha Especialização '
        '(dobro do bônus de proficiência) nela. Ao fazer teste de Carisma '
        '(Atuação) dançando, pode substituir o d20 pelo seu nível de Bardo '
        '(antes de saber o resultado).',

    "danca:Defesa Desarmada & Golpe de Palco":
        '"Guarda é desenho e passo é escudo." Efeito: Defesa Desarmada — sem '
        'armadura nem escudo, CA base = 10 + mod. Destreza + mod. Carisma. '
        'Golpe de Palco — pode usar Destreza em vez de Força nas jogadas de '
        'ataque dos Golpes Desarmados; ao causar dano com Golpe Desarmado, '
        'pode causar concussão = 1 rolagem do Dado de Inspiração Bárdica + '
        'mod. Destreza (em vez do dano normal); essa rolagem não gasta o Dado.',

    "danca:Dança em Cena":
        '"Você liga o palco dentro do combate: passos apagam oportunidades." '
        'Efeito (Ação Bônus): gasta 1 uso de Inspiração Bárdica para iniciar '
        'uma apresentação de Dança, que dura 1 minuto e termina se você ficar '
        'Incapacitado. A Dança concede: você deve se mover ao menos 1,5 m em '
        'cada turno para mantê-la ativa (senão termina ao fim do turno); seu '
        'deslocamento não provoca Ataques de Oportunidade; Vantagem em TR de '
        'Destreza. Sempre que usar um Estilo de Dança gastando Inspiração '
        'Bárdica, pode conceder 1 Inspiração Bárdica a uma criatura à escolha '
        'a até 18 m que possa ver ou ouvir você, sem gastar outro uso. '
        '— Estilos de Dança: você aprende 1 Estilo de Ki da classe Monge que '
        'vira um Estilo de Dança para você. Regra de custo: "gaste 1 ponto de '
        'Ki" lê-se como "gaste 1 uso de Inspiração Bárdica". Aprende outro '
        'Estilo nos níveis 6, 14 e 18 (escolha no campo Estilos de Dança).',

    "danca:Estilo de Fuga":
        '"Você abre uma fresta de tempo e espaço." Efeito: você aprende o '
        'Estilo de Fuga (não conta para o total de Estilos que conhece). Ao '
        'usar o Estilo de Fuga, escolha uma criatura a até 9 m: ela pode usar '
        'a Reação para mover-se até metade do deslocamento em qualquer direção '
        'sem provocar Ataques de Oportunidade.',

    "danca:Inspiração em Movimento":
        '"Sua palavra abre um corredor invisível." Efeito: sempre que uma '
        'criatura usar seu Dado de Inspiração (em ataque, teste ou TR), ela '
        'pode se mover até 4,5 m sem provocar Ataques de Oportunidade após '
        'resolver a jogada.',

    "danca:Evasão Coreografada":
        '"Explosões obedecem a quem manda no tempo." Efeito: quando um efeito '
        'exigir TR de Destreza para sofrer metade do dano, você sofre 0 em '
        'sucesso e metade em falha. Se uma ou mais criaturas a até 1,5 m de '
        'você fizerem o mesmo teste, pode compartilhar este benefício com elas '
        'para aquele teste. Não funciona se você estiver Incapacitado.',

    "danca:Magia em Passo":
        '"Feitiço entra na batida e a técnica vem junto." Efeito: quando você '
        'conjurar uma magia com uma Ação, pode ativar 1 Estilo de Dança de '
        'Ação Bônus que normalmente exigiria "ao acertar um ataque '
        'desarmado".',

    "danca:Cortesia da Plateia":
        '"Por um instante, o mundo paga a entrada." Efeito: uma vez por '
        'combate, você pode usar 1 Estilo de Dança sem gastar um uso de '
        'Inspiração Bárdica.',

    # ======================================================================
    # COLÉGIO DOS ESPÍRITOS (sid 10) — 7 features
    # ======================================================================
    "espiritos:Foco Espiritual":
        '"Velas, vidro, osso e tinta — cada peça é uma porta." Efeito: pode '
        'usar como Foco de Conjuração para magias de Bardo: vela, bola de '
        'cristal, caveira, quadro espiritual ou baralho de tarô. Além disso, '
        'onde uma feature pedir instrumento musical, esses itens também '
        'contam.',

    "espiritos:Sussurros de Orientação":
        '"O espírito não grita; ajeita um grau a bússola." Efeito: aprende o '
        'truque Orientação (não conta no limite de truques); para você o '
        'alcance dele é 18 m ao conjurar.',

    "espiritos:Arcanos do Véu":
        '"Não adivinho o futuro — eu o coleciono de antemão." Efeito (Ação '
        'Bônus, segurando o Foco Espiritual): gasta 1 uso de Inspiração '
        'Bárdica para Comprar — role 2× d12 nos Arcanos e escolha 1; fica '
        'preparado por até 10 min (comprar de novo encerra o anterior; só 1 '
        'preparado por vez). Jogar (Ação Bônus): escolha criatura a até 9 m '
        '(inclusive você) e aplique o Arcano; alternativamente conjure uma '
        'magia vinculada à carta (mesmo que use Ação) com essa Ação Bônus. '
        'TR usam sua CD de Magia; dano/cura usam seu Dado de Inspiração. '
        'Arcanos (d12): 1) O Louco — Salto de Fé (alvo teleporta 9 m de '
        'Reação; até Carisma criaturas a 9 m imitam). 2) O Mago — Manifestação '
        '(ataque CaC mágico; 2× Dado de Inspiração de força + mod. Carisma). '
        '3) A Sacerdotisa — Intuição (10 min, +1 dado em testes INT/SAB/CAR). '
        '4) A Imperatriz — Abundância (PV temp = 1× Dado + nível Bardo; +3 m '
        'desloc. e +1 CA enquanto durar). 5) O Imperador — Bastião (1 min, +2 '
        'CA contra 1º ataque/rodada, Vantagem vs. empurrão/derrubar). 6) O '
        'Eremita — Vulto (invisível até fim do próximo turno ou até acertar; '
        'se acertar, +1× Dado necrótico e alvo Amedrontado). 7) A Justiça — '
        'Golpe Equivalente (criaturas escolhidas a 9 m: TR Força, falha 3× '
        'Dado trovejante + Derrubada, sucesso metade). 8) A Roda — Virada de '
        'Sorte (Vantagem na próxima jogada; se falhar, rola de novo 1×). '
        '9) O Carro — Investida (Correr ou Desengajar; sem provocar '
        'oportunidade até fim do turno). 10) A Temperança — Restauro (2× Dado '
        '+ Carisma PV e remove 1 condição: cego/surdo/paralisado/petrificado/'
        'envenenado). 11) O Diabo — Tentação (TR Sabedoria; falha 2× Dado '
        'psíquico + Incapacitado, sucesso metade). 12) A Torre — Ruptura (cone '
        '9 m do alvo; TR Destreza, falha 4× Dado fogo, sucesso metade; '
        'concentrações fazem TR Constituição vs. CD ou perdem). Segredo do '
        'Véu: ao comprar cartas por rolagem, só você e o Mestre sabem o '
        'resultado antes da ativação; se outro jogador souber, a carta não '
        'produz efeito (recursos não reembolsados).',

    "espiritos:Sessão de Tarô":
        '"Três velas, cartas viradas, respirações presas." Efeito (ritual de '
        '1 hora em Descanso Curto/Longo, com o Foco Espiritual): para cada '
        'participante disposto (inclusive você), role 1× d12 nos Arcanos e '
        'associe 1 carta virada para baixo a essa criatura (só você e o '
        'Mestre conhecem). Até o próximo Descanso Longo, cada participante '
        'gasta a própria Ação Bônus para virar e jogar a carta (1 uso); '
        'cálculos usam seu Dado/CD/mod. Carisma; origem é você, área/alcance a '
        'partir de quem jogou. Magia emprestada: você "aprende" 1 magia de '
        'Adivinhação ou Necromancia de qualquer classe com nível ≤ nº de '
        'participantes e ≤ nível que pode conjurar (conta como Bardo, fora da '
        'lista, até o próximo Descanso Longo). Frequência: 1/Descanso Longo.',

    "espiritos:Foco Espiritual Aprimorado":
        '"Quando a mesa acredita, até a magia simples pesa mais." Efeito: '
        'sempre que conjurar uma magia de Bardo que cause dano ou cure usando '
        'seu Foco Espiritual, adiciona 1 rolagem do seu Dado de Inspiração '
        'Bárdica a uma rolagem de dano ou de cura dessa magia.',

    "espiritos:Conexão Mística":
        '"Corte de três: uma carta para o risco, outra para o desejo, outra '
        'para o acerto." Efeito: ao usar Arcanos do Véu para comprar cartas, '
        'role 3× d12 e escolha 1; se dois resultados forem iguais, pode '
        'ignorar ambos e escolher qualquer Arcano da lista. Afinamento do '
        'foco: ao aplicar o bônus de Foco Espiritual Aprimorado, pode rolar o '
        'Dado de Inspiração 2× e ficar com o maior.',

    "espiritos:Arcano Maior":
        '"Algumas cartas não se compram — se declaram." Efeito: ao rolar '
        'Iniciativa, prepara 1 Arcano à escolha sem gastar Inspiração (pronto '
        'por até 10 min). 1×/Descanso Longo: no seu turno pode jogar 2 Arcanos '
        'diferentes na mesma Ação Bônus.',

    # ======================================================================
    # COLÉGIO DO FASCÍNIO (sid 11) — 8 features
    # ======================================================================
    "fascinio:Dom de Palco":
        '"Se houver plateia, já existe uma luz me esperando." Efeito: ganha '
        'proficiência em Atuação; se já for proficiente, ganha Especialização '
        '(dobro do bônus de proficiência) nessa perícia.',

    "fascinio:Manto Deslumbrante":
        '"Visto brilho como quem veste um verbo." Efeito (Ação Bônus): gasta '
        '1 uso de Inspiração Bárdica e rola o Dado de Inspiração; escolha até '
        'mod. Carisma criaturas (mín 1) que possam ver você a até 9 m — cada '
        'uma recebe PV temporários iguais ao resultado e pode se mover até o '
        'próprio deslocamento sem provocar Ataques de Oportunidade '
        'imediatamente.',

    "fascinio:Presença Hipnótica":
        '"Dê-me um minuto. O resto a plateia resolve sozinha." Efeito: após '
        'se apresentar por ao menos 1 minuto, como Ação gasta 1 uso de '
        'Inspiração Bárdica para forçar criaturas à escolha que ouviram a '
        'apresentação e estejam a até 27 m a fazer TR de Sabedoria contra sua '
        'CD de Magia. Falha: enfeitiçada por você por 1 hora (ou até você/'
        'aliados agirem hostil contra qualquer membro da audiência); idolatra '
        'você e faz o que pedir, exceto arriscar a vida ou lutar por você. '
        'Sucesso: fica inconsciente da tentativa de encanto.',

    "fascinio:Abertura de Palco":
        '"O combate começa no seu compasso." Efeito (Reação ao rolar '
        'Iniciativa): gasta 1 uso de Inspiração Bárdica para iniciar '
        'imediatamente sua Dança em Cena. Além disso, você e criaturas à '
        'escolha a até 9 m que possam ouvir você rolam seu Dado de Inspiração '
        'Bárdica e somam o resultado à própria jogada de iniciativa.',

    "fascinio:Encanto Reflexo":
        '"Se vierem com ferro, que a mão escorregue de admiração." Efeito '
        '(Reação): quando uma criatura que possa ver você acertar um ataque '
        'contra você, gasta 1 uso de Inspiração Bárdica, rola o Dado de '
        'Inspiração e soma à sua CA contra aquele ataque (pode fazê-lo '
        'errar). Com o Manto Deslumbrante ativo, usa sem gastar Inspiração '
        '(ainda consome a Reação).',

    "fascinio:Visagem de Outro Mundo":
        '"O Manto deixa de ser lampejo e vira estado de cena." Efeito: ao '
        'usar o Manto Deslumbrante, ele pode durar até 1 minuto (termina se '
        'ficar Incapacitado ou encerrar como Ação Bônus). Enquanto ativo, em '
        'cada turno pode usar Ação Bônus escolhendo criatura que possa ver/'
        'ouvir você a até 9 m: Encanto Sutil — conjura charm person ou command '
        'sem espaço (charm person assim dura só enquanto o Manto, máx 1 min); '
        'ou Brilho que Protege — alvo recebe PV temporários iguais a 1 rolagem '
        'do Dado de Inspiração e pode se mover até o deslocamento sem provocar '
        'oportunidade.',

    "fascinio:Manto de Proteção":
        '"Onde eu lidero, ninguém perde a cabeça — perde o medo." Efeito: '
        'enquanto o Manto Deslumbrante estiver ativo, você e criaturas à '
        'escolha a até 9 m que possam ver/ouvir você ganham: Vantagem em TR '
        'para resistir e encerrar Enfeitiçado, Amedrontado, Paralisado e '
        'Atordoado; e veem através de ilusões de nível ≤ mod. Carisma (mín 1). '
        'Além disso, ao rolar Iniciativa sem estar surpreendido nem '
        'incapacitado, pode usar Reação gastando 1 uso de Inspiração Bárdica '
        'para ativar o Manto Deslumbrante imediatamente.',

    "fascinio:Presença Majestosa":
        '"Há vontades que parecem rocha — até serem vistas de perto." Efeito: '
        'sempre que conjurar uma magia de Encantamento contra criatura que '
        'possa ver você a até 9 m, pode gastar 1 uso de Inspiração Bárdica '
        'para impor Desvantagem no TR dela. Com o Manto Deslumbrante ativo, '
        'usa sem gastar Inspiração Bárdica.',

    # ======================================================================
    # COLÉGIO DAS LÂMINAS (sid 12) — 6 features
    # ======================================================================
    "laminas:Duelista Elegante":
        '"A mão que segura a lâmina também segura o olhar de quem assiste." '
        'Efeito: ganha proficiência com Armas Marciais; ganha 1 Maestria com '
        'Arma (pode alterar ao fim de Descanso Longo); pode usar uma arma '
        'Simples ou Marcial como Foco de Conjuração; ganha proficiência em '
        'Atuação. Ao fazer teste de Carisma (Atuação), pode fazer Destreza '
        '(Atuação) se a apresentação incorporar uma arma cortante com a qual '
        'seja proficiente.',

    "laminas:Estilo de Luta":
        '"Escolha sua gramática: guarda fechada, cortes curtos." Efeito: '
        'escolha 1 Estilo de Luta (pode trocar ao subir nível em Bardo): '
        'Defesa — com armadura, +1 CA; Duelo — com arma corpo a corpo numa '
        'mão e nenhuma outra arma, +2 no dano; Combate com Duas Armas — soma '
        'mod. de habilidade ao dano do ataque secundário; Arma Pesada — ao '
        'rolar 1 ou 2 num dado de dano de arma corpo a corpo de duas mãos, '
        'pode rolar de novo (usa o novo).',

    "laminas:Floreios de Lâmina":
        '"Velocidade é silêncio estudado." Efeito: ao fazer a Ação de Ataque, '
        'sua velocidade +3 m até o fim do turno. Se um ataque com arma dessa '
        'ação acertar, pode gastar 1 uso de Inspiração Bárdica para aplicar 1 '
        'floreio (só 1 por turno): Defensivo — soma o Dado de Inspiração ao '
        'dano e à sua CA até o início do próximo turno; Móvel — soma o Dado ao '
        'dano e empurra o alvo até 5× o resultado em pés, depois Reação para '
        'mover até a velocidade a 1,5 m do alvo sem provocar oportunidade '
        'dele; Cortante — soma o Dado ao dano e causa o mesmo valor a outra '
        'criatura à escolha a até 1,5 m de você.',

    "laminas:Segundo Ataque Mágico":
        '"Entre um corte e outro, um gesto que redesenha a cena." Efeito: ao '
        'fazer a Ação de Ataque, ataca duas vezes em vez de uma. Pode '
        'substituir um dos ataques por um truque de Bardo (conjuração: Ação) '
        'que conheça e que não tenha vindo de Segredos Mágicos (Nv 10).',

    "laminas:Ritmo Infindável":
        '"Quando o corpo sabe a coreografia, a lâmina dança sozinha." Efeito: '
        'sempre que usar um Floreio de Lâmina, pode optar por rolar 1d6 e usar '
        'esse resultado em vez de gastar um uso de Inspiração Bárdica (decide '
        'após acertar o ataque, antes de aplicar os efeitos do floreio).',

    "laminas:Represália Letal":
        '"Se tocar no meu compasso, recebe a resposta no mesmo tempo." Efeito '
        '(Reação): quando uma criatura que possa ver você o acertar com '
        'ataque corpo a corpo, faz 1 ataque corpo a corpo contra ela com '
        'Vantagem. Ao usar um Floreio de Lâmina durante sua ação, pode Correr '
        'ou Desengajar como Ação Bônus neste turno. Além disso, aprende 2 '
        'Técnicas de Combate do Guerreiro à escolha; onde elas pedirem o dado '
        'de recurso, usa seu Dado de Inspiração Bárdica.',

    # ======================================================================
    # COLÉGIO SKALD (sid 13) — 8 features
    # ======================================================================
    "skald:Forja do Skald":
        '"Se a saga pede aço, eu aprendi a caligrafar com lâminas." Efeito: '
        'ganha proficiência com todas as armas marciais, escudos e armaduras '
        'pesadas; pode usar arma ou escudo como foco de conjuração. Vigor de '
        'Skald: seu PV máximo aumenta em 3 imediatamente e +1 a cada novo '
        'nível de Bardo.',

    "skald:Estrofe de Batalha":
        '"Um verso bem posto vira guarda, vira ponta — vira chance." Efeito: '
        'uma criatura que possua um Dado de Inspiração Bárdica seu pode gastá-'
        'lo para: Defesa (Reação, ao ser atingida por ataque — rola o Dado e '
        'soma à própria CA contra aquele ataque); ou Ofensa (logo após '
        'acertar uma jogada de ataque — rola o Dado e soma ao dano do '
        'ataque).',

    "skald:Verso Afiado":
        '"Se o corte falha por um sopro, eu costuro o sopro ao corte." '
        'Efeito: quando fizer uma jogada de ataque com arma e errar, pode '
        'gastar 1 uso de Inspiração Bárdica, rolar o Dado de Inspiração e '
        'somar à jogada de ataque (pode virar erro em acerto). Sem ação; '
        'decida após ver que errou, antes do Mestre seguir adiante.',

    "skald:Brado de Investida":
        '"Eu digo \'agora\', e os pés entendem \'primeiro\'." Efeito (Reação '
        'ao rolar Iniciativa): gasta 1 uso de Inspiração Bárdica; criaturas à '
        'escolha que possam ouvir você a até 9 m somam o resultado de 1 '
        'rolagem do seu Dado de Inspiração às próprias jogadas de iniciativa.',

    "skald:Segundo Ataque (Mágico)":
        '"Entre duas batidas, cabe um truque bem empunhado." Efeito: ao fazer '
        'a Ação de Ataque, ataca duas vezes em vez de uma. Pode substituir 1 '
        'desses ataques por um truque de Bardo que conheça (aprendido '
        'naturalmente, não via Segredos Mágicos Nv 10).',

    "skald:Hidromel do Valor":
        '"Eu não empresto só números — empresto fôlego." Efeito: quando '
        'adicionar um Dado de Inspiração Bárdica seu a um ataque/teste/TR de '
        'outra criatura, também concede a ela PV temporários iguais ao mod. '
        'Carisma (mín 1). Enquanto mantiver esses PV, o deslocamento dela '
        'aumenta em 3 m.',

    "skald:Runas no Aço":
        '"Refrão arcano, riposta de ferro." Efeito: após conjurar uma magia '
        'com tempo de conjuração Ação no seu turno, pode fazer 1 ataque com '
        'arma como Ação Bônus.',

    "skald:Coro das Sagas":
        '"Se a guerra começa, começamos juntos — cada voz com seu verso." '
        'Efeito: ao usar Brado de Investida, pode conceder a cada criatura '
        'aliada até 1 Dado de Inspiração Bárdica no início do combate '
        '(funcionam como Inspiração Bárdica normal sua). Pode reusar gastando '
        '1 Dado de Inspiração Bárdica como Reação quando vir uma criatura cair '
        'a 0 PV a até 9 m de você — reescolhendo as criaturas que recebem os '
        'Dados.',
}


# Mapping (id_subclasse → prefixo) — mesmo padrão do druida_descricoes
SUBCLASSE_PREFIXES = {
    6:  "conselho",
    7:  "conspiracao",
    8:  "criacao",
    9:  "danca",
    10: "espiritos",
    11: "fascinio",
    12: "laminas",
    13: "skald",
}


def chave_para(sub_id, nome):
    if sub_id is None:
        return nome
    return f"{SUBCLASSE_PREFIXES[sub_id]}:{nome}"


if __name__ == "__main__":
    print(f"Total descrições: {len(DESCRICOES)}")
    for k, v in DESCRICOES.items():
        print(f"  {k:<40} ({len(v)} chars)")
