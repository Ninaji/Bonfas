"""Descrições limpas das 62 features de Artífice (paginas/artificer.html).
Chave: nome canônico (classe) OU 'slug:Nome' (subclasse). Mesmo padrão dos
demais <classe>_descricoes.py.
"""

DESCRICOES = {
    # ===== CLASSE (12 únicas, cobrem 19 entradas) =====
    "Conjuração de Magias":
        '"Meus feitiços não nascem do nada: cada um é uma máquina que montei." '
        'Efeito: você canaliza magia através de ferramentas. Foco: usa '
        'Ferramentas de Ladrão, de Funileiro ou de Artesão com proficiência '
        'como foco (precisa em mãos; conta como componente material). Truques: '
        '2 no 1º nível da lista de Artífice (mais nos níveis 10 e 14); pode '
        'trocar 1 ao terminar Descanso Longo. Espaços de Magia: conforme a '
        'tabela; recupera todos em Descanso Longo. Magias Preparadas: prepara '
        'magias de Artífice de 1º+ conforme a coluna da tabela (começa com 2); '
        'pode alterar em cada Descanso Longo. Habilidade de Conjuração: '
        'Inteligência. CD = 8 + bônus prof. + mod. Inteligência; Ataque Mágico '
        '= bônus prof. + mod. Inteligência.',

    "Engenhoca Mágica":
        '"Não é gesto arcano misterioso — é conhecer cada parafuso da realidade '
        'e saber qual apertar." Efeito: com ferramentas de ladrão ou de '
        'artesão em mãos, pode conjurar Consertar (truque) e, como rituais, '
        'Detectar Magia e Identificar (ferramentas substituem componentes). '
        'Além disso, como Ação, toca um objeto Minúsculo não mágico e concede '
        '1 propriedade: luz (plena 1,5 m + fraca 1,5 m); mensagem gravada (até '
        '6 s, audível a 3 m ao toque); odor/som contínuo (perceptível a 3 m); '
        'ou efeito visual estático (imagem/até 25 palavras/formas). Dura '
        'indefinidamente (encerra como Ação). Máximo de objetos simultâneos = '
        'mod. Inteligência (mín 1); exceder encerra o mais antigo.',

    "Infusões":
        '"Eu não transformo o objeto; liberto o potencial que já está lá." '
        'Efeito: no 2º nível você imbui objetos com magia, criando itens '
        'temporários. Conhece um número de Infusões conforme a tabela '
        '(Infusões Conhecidas: Nv 2=4, 6=5, 10=6, 14=7, 18=8) e mantém até '
        'esse número de itens infundidos ativos (Itens Infundidos: Nv 2=2, '
        '6=3, 10=4, 14=5, 18=6). Limite de potência: nenhum item concede bônus '
        'cumulativo > +3 (CA, acerto, dano, etc.), nem mais de +3 dados extras. '
        'Imbuir: ao fim de um Descanso Longo, toca um objeto não mágico (ou '
        'item mágico dentro do limite) com ferramentas de artesão e aplica 1 '
        'Infusão conhecida; se exigir sintonização, conta como uma única '
        'sintonização. Cada Infusão fica em 1 objeto, cada objeto tem 1 '
        'Infusão. Persistem indefinidamente; somem se você morrer (após mod. '
        'Inteligência dias), substituir, ou transferir. Em Descanso Longo pode '
        'gastar 1 h para trocar uma Infusão conhecida por outra (respeitando '
        'pré-requisitos). [O campo "Infusões de Artificer" abaixo lista o '
        'catálogo e permite escolher cada infusão ou Replicar Item Mágico.]',

    "Replicar Item Mágico":
        '"Todo item mágico é um projeto que alguém já resolveu antes de mim." '
        'Efeito: pode usar suas Infusões para replicar itens mágicos '
        'estudados. Em Descanso Longo, gasta 1 h examinando um item mágico que '
        'esteja tocando; ao final, substitui uma Infusão conhecida pelo '
        'conhecimento dele e passa a poder imbuir um objeto com as '
        'propriedades desse item (seguindo as regras das Infusões). Não pode '
        'replicar consumíveis de uso único (pergaminhos, poções). Raridade '
        'permitida: Comum no 2º nível; Incomum no 6º; Raro no 14º. (No campo '
        'de Infusões, escolha "Replicar Item Mágico" e selecione o item da '
        'página de equipamentos — ele ocupa 1 slot de Infusão.)',

    "Especialização":
        '"Eu decido em que direção quero quebrar as regras primeiro." Efeito: '
        'no 3º nível escolhe uma Especialização (Alquimista, Armadurista, '
        'Aprimorado, Engenheiro de Construto, Ferreiro de Batalha ou '
        'Magiduelista). Cada uma tem Magias da Especialização (sempre '
        'preparadas, contam como Artífice mas não no limite) e concede '
        'características no 3º nível e novamente nos níveis 5, 10 e 15.',

    "Percepção do Artífice":
        '"Um item mágico é só mais uma interface mal projetada." Efeito: no 3º '
        'nível pode se sintonizar e usar qualquer item mágico, ignorando '
        'requisitos de alinhamento, classe, raça ou conjuração. Pode também '
        'usar a CD de resistência das suas magias de Artífice no lugar da CD '
        'normal exigida por um item mágico.',

    "Recarga Arcana":
        '"Nenhuma fonte de energia deveria ficar parada." Efeito: no 3º nível, '
        'durante um Descanso Curto, recupera espaços de magia gastos cujo nível '
        'combinado seja igual ao seu mod. de Inteligência (1×, depois precisa '
        'de Descanso Longo). Como Ação Bônus, pode tocar um item mágico (que '
        'criou via Replicar Item Mágico e que use cargas) a 1,5 m, gastar 1 '
        'espaço de magia de 1º+ e recarregar cargas iguais ao nível do espaço.',

    "Aumento de Atributo":
        '"Engrenagens melhores exigem mãos mais firmes, mente mais afiada." '
        'Efeito: nos níveis 4, 8, 12, 16 e 19, aumente um atributo em +2 ou '
        'dois atributos em +1 cada (máximo 20).',

    "Lampejo de Gênio":
        '"O mundo inteiro parece um mecanismo e eu enxergo a peça fora do '
        'lugar." Efeito (Reação): no 6º nível, quando você ou criatura que '
        'possa ouvi-lo a até 9 m fizer um teste de atributo ou de '
        'resistência, adiciona seu mod. de Inteligência à rolagem. Usos = mod. '
        'Inteligência (mín 1); recupera em Descanso Longo.',

    "Artesão Exímio":
        '"Ferramentas comuns nas minhas mãos fazem protocolos arcanos '
        'obedecerem." Efeito: no 7º nível, adiciona o dobro do bônus de '
        'proficiência a testes com ferramentas em que seja proficiente. Além '
        'disso, sua Especialização passa a poder infundir itens mágicos com '
        'suas Infusões (sem exceder +3 numérico).',

    "Maestria em Itens Mágicos":
        '"Cada item é uma linha de comando, e eu rodo vários sistemas ao mesmo '
        'tempo." Efeito: no 9º nível pode se sintonizar com até 4 itens '
        'mágicos simultâneos (5 no 14º nível, 6 no 18º).',

    "Magnum Opus":
        '"Minhas obras-primas são extensões da minha própria vontade." Efeito: '
        'no 20º nível, recebe +1 em todos os testes de resistência por cada '
        'item mágico sintonizado. Além disso, se for reduzido a 0 PV mas não '
        'morrer instantaneamente, pode encerrar a sintonização com 1 item ou '
        'Infusão para, em vez disso, ficar com 20 PV.',

    # ===== ALQUIMISTA (sub 1) =====
    "alquimista:Ferramentas do Ofício":
        '"Antes da Trama, eu aprendi a mexer com vidros, fogo e coisas que '
        'ninguém colocaria no mesmo recipiente." Efeito: proficiência com '
        'Suprimentos de Alquimista (se já tiver, escolhe outras ferramentas de '
        'artesão).',
    "alquimista:Magias de Alquimista":
        '"Algumas fórmulas precisam ser lançadas direto na realidade." Efeito: '
        'sempre tem preparadas (contam como Artífice, fora do limite, não '
        'substituíveis): Nv 3 healing word, inflict wounds; Nv 5 acid arrow, '
        'flaming sphere; Nv 9 gaseous form, mass healing word; Nv 13 blight, '
        'death ward; Nv 17 cloudkill, reincarnate.',
    "alquimista:Elixires Alquímicos":
        '"Meus elixires são meu jeito de estar em todos os lugares ao mesmo '
        'tempo." Efeito: você ganha Infusões de Elixir — nos níveis 3, 5, 9, '
        '13 e 17, suas Infusões Conhecidas aumentam +1, escolhidas da lista de '
        'Infusões de Elixir. Criar (Descanso Longo, 1 h, Suprimentos de '
        'Alquimista): 1 frasco de cada Elixir que conhece (sem gastar espaço), '
        'no nível mais baixo; viáveis até o próximo Descanso Longo. Síntese '
        'Rápida (Ação Bônus): gasta espaço do nível indicado para criar 1 '
        'frasco e usá-lo na mesma ação. Só 1 Elixir ativo de cada tipo. O '
        'efeito é tratado como magia conjurada por você (usa sua CD/Ataque '
        'Mágico). Usar (Ação): Beber (recebe a magia; se exigir Concentração, '
        'o Elixir sustenta sem concentrar; 1 Elixir de ingestão por vez); '
        'Administrar (a aliado inconsciente/voluntário a 1,5 m); Arremessar '
        '(a até 9 m, só efeitos ofensivos/de área; se exigir Concentração, '
        'dura 2 rodadas sem concentrar).',
    "alquimista:Poções Potentes":
        '"Eu só preciso descobrir quanto é quase demais." Efeito: sempre que '
        'um Elixir seu ou magia de Artífice sua causar dano de ácido, fogo, '
        'necrótico ou veneno, ou curar PV, adiciona seu mod. de Inteligência '
        '(mín +1) a uma rolagem de dano ou cura.',
    "alquimista:Reagentes Restauradores":
        '"Cura, foco, resistência — tudo depende do aditivo certo." Efeito: '
        'sempre que uma criatura beber voluntariamente um Elixir seu, recebe '
        'PV temporários iguais ao seu nível de Artífice. Além disso, aprende '
        'restauração menor e pode conjurá-la como ritual (não conta no limite '
        'de magias preparadas).',
    "alquimista:Mestre Alquimista":
        '"Meu corpo aprendeu a tratar veneno como mais um tempero." Efeito: '
        'imune a efeitos de Elixires que você criou (salvo se quiser ser '
        'afetado). Resistência a ácido e veneno; imune à condição Envenenado. '
        'Caldeirão Conjurado: conjura Caldeirão Borbulhante de Tasha sem '
        'espaço/preparação/componentes (foco = Suprimentos de Alquimista), 1/'
        'Descanso Longo. Administração Rápida: usa um Elixir como Ação Bônus e '
        'pode gastar um espaço para criar um Elixir conhecido na mesma Ação '
        'Bônus.',

    # ===== ARMADURISTA (sub 3) =====
    "armadurista:Ferramentas do Ofício":
        '"Eu posso desmontar uma armadura até o último rebite e reconstruí-la." '
        'Efeito: proficiência com armaduras pesadas e ferramentas de ferreiro '
        '(se já tiver as ferramentas, escolhe outras de artesão).',
    "armadurista:Magias do Armadurista":
        '"Minha armadura é um circuito de feitiços pré-carregados." Efeito: '
        'sempre preparadas (Artífice, fora do limite, não substituíveis): Nv 3 '
        'Escudo, Onda Trovejante; Nv 5 Imagem Espelhada, Detonar; Nv 9 Raio '
        'Relâmpago, Passo Trovejante; Nv 13 Escudo de Fogo, Esfera de '
        'Tempestade; Nv 17 Onda Destrutiva, Muralha de Força.',
    "armadurista:Armadura Arcana":
        '"Se vou confiar minha vida a um metal, ele tem que conhecer minha '
        'magia." Efeito: em Descanso Longo, 1 h com ferramentas de ferreiro '
        'transforma uma armadura vestida em sua Armadura Arcana (só 1 por '
        'vez). Enquanto vestida: ignora requisito de Força; veste/remove como '
        'Ação; não pode ser removida contra sua vontade; serve de foco de '
        'conjuração; elmo abre/fecha como Ação Bônus. Estrutura Integrada: 5 '
        'módulos (Elmo, Peitoral, Botas, 2 Manoplas) podem integrar itens '
        'mágicos compatíveis (mantêm propriedades, contam no limite de '
        'sintonização, podem receber Infusões).',
    "armadurista:Configuração de Combate":
        '"A diferença está em como eu ajusto os parâmetros." Efeito: ao fim de '
        'um Descanso Longo escolha o modo. Modo Infiltrador: Vantagem em '
        'Percepção e Investigação (Elmo); Ação Bônus para Correr/Desengajar/'
        'Esconder (Peitoral); voo = caminhada no turno, deve pousar ao fim '
        '(Botas). Modo Colosso: Vantagem em Intimidação e contra Amedrontado '
        '(Elmo); Ação Bônus para PV temporários = nível Artífice + mod. Int '
        '(Peitoral), usos = mod. Int por Descanso Longo; Vantagem contra '
        'derrubar/mover (Botas).',
    "armadurista:Manoplas de Energia":
        '"Se a armadura é o corpo, as manoplas são os punhos." Efeito: a '
        'Armadura Arcana inclui 2 Manoplas de Energia (sempre empunhadas; cada '
        'uma é um item separado para Infusões, integra itens de mãos/luvas). '
        'Contam como 2 armas corpo a corpo; pode usar mod. Inteligência no '
        'lugar de Força/Destreza nos ataques/dano. Dano de Energia (force): '
        'Nv 3 1d6, Nv 5 1d8, Nv 11 1d10, Nv 17 1d12. Modo Infiltrador: armas '
        'simples Leves, maestrias Corte (Nick) e Vexar (Vex). Modo Colosso: '
        'armas marciais Pesadas, maestrias Minar (Sap) e Debilitar (Weaken).',
    "armadurista:Ataque Extra Mágico":
        '"Não faz sentido escolher entre aço e feitiço." Efeito: no 5º nível, '
        'ataca duas vezes na Ação de Ataque; pode substituir um desses ataques '
        'por um truque de Artífice (conjuração 1 Ação).',
    "armadurista:Reconfiguração Tática":
        '"Alguns ajustes e a armadura vira um muro ambulante." Efeito: no 10º '
        'nível, pode alterar o modo da Armadura Arcana gastando 10 minutos com '
        'ferramentas de ferreiro.',
    "armadurista:Sistema Modular Avançado":
        '"Minha armadura nunca está terminada." Efeito: no 10º nível, aprende '
        '2 Infusões adicionais (aplicadas à Armadura Arcana). Modo '
        'Infiltrador: voo totalmente estável (não precisa pousar). Modo '
        'Colosso: ao entrar em Sangrando, PV temporários = nível Artífice + '
        'mod. Int (1×/Descanso Curto); pode usar o Reforço Energético em '
        'aliado a 9 m via Ação Bônus.',
    "armadurista:Núcleo Arcano Sintonizado":
        '"O núcleo muda antes mesmo de eu decidir." Efeito: no 15º nível, '
        'muda o modo da Armadura Arcana como Ação Bônus, usos = mod. Int '
        '(recupera em Descanso Longo). Cada módulo pode receber até 2 Infusões '
        'simultâneas; aplicar Infusão numa Manopla afeta ambas, mas consome um '
        'espaço de infusão em cada (2 no total).',

    # ===== APRIMORADO (sub 4) =====
    "aprimorado:Ferramentas do Ofício":
        '"Para refazer um corpo, você precisa entender a carne e o metal." '
        'Efeito: proficiência com ferramentas de coureiro e de ferreiro (se já '
        'tiver, escolhe outras de artesão).',
    "aprimorado:Magias do Aprimorado":
        '"Cada feitiço passa a ser uma atualização de sistema." Efeito: sempre '
        'preparadas (Artífice, fora do limite): Nv 3 Absorver Elementos, Golpe '
        'Trovejante; Nv 5 Alterar-se, Escalada de Aranha; Nv 9 Golpe Cegante, '
        'Aceleração; Nv 13 Liberdade de Movimentação, Invisibilidade Maior; '
        'Nv 17 Golpe de Banimento, Potencializar Perícia.',
    "aprimorado:Físico Modular":
        '"Meu corpo deixou de ser um limite e virou um conjunto de slots." '
        'Efeito: seu corpo conta como itens para Infusões — Cabeça, Tronco, '
        'Braços, Pernas (cada parte recebe 1 Infusão). Sem armadura, CA = 10 + '
        'mod. Destreza + mod. Inteligência (pode usar escudo; Infusões no '
        'tronco contam pra CA). Infusões Conhecidas +1 (aplicada a uma parte '
        'do corpo), e +1 de novo nos níveis 5, 10 e 15 (também em partes do '
        'corpo).',
    "aprimorado:Armas Integradas":
        '"Eu não carrego armas. Eu as encaixo onde havia limitações '
        'anatômicas." Efeito: pode infundir/integrar qualquer arma sem Duas '
        'Mãos nos braços (cada braço conta como manopla e arma; duas armas em '
        'braços diferentes permitem Combate com Duas Armas). Ação Bônus '
        'retrai/estende a arma. Mantém integradas infundidas = bônus de '
        'proficiência, com Maestria de Arma em cada. Integradas: dano base '
        'vira 1d10, ganham Acuidade, perdem Versátil; Arremessáveis funcionam '
        '(separam ao arremessar). Troca a arma ativa no início do turno ou ao '
        'atacar (sem ação).',
    "aprimorado:Ataque Extra Mágico":
        '"Não faz sentido desperdiçar o momento com um único golpe." Efeito: '
        'no 5º nível, ataca duas vezes na Ação de Ataque; pode substituir um '
        'desses ataques por um truque de Artífice (conjuração 1 Ação).',
    "aprimorado:Integração Otimizada":
        '"Cada peça é uma atualização. Meu corpo é um overclock constante." '
        'Efeito: no 10º nível, para cada parte do corpo (incl. Armas '
        'Integradas) portando Infusão: +1 em testes de Força/Destreza/'
        'Constituição (máx +6) e +1,5 m de deslocamento (máx +9 m). Dano base '
        'das Armas Integradas sobe para 2d10.',
    "aprimorado:Mestre Aprimorado":
        '"Comecei a projetar algo que não obedece mais às mesmas regras." '
        'Efeito: no 15º nível, é Humanoide e Construto; não precisa comer/'
        'dormir/respirar e não envelhece (Descanso Longo = 4 h de manutenção '
        'em semitranse); resistência a contundente, perfurante e cortante.',

    # ===== ENGENHEIRO DE CONSTRUTO (sub 5) =====
    "engenheiro:Magias do Engenheiro de Construto":
        '"Posso pré-carregar as soluções na minha lista de feitiços." Efeito: '
        'sempre preparadas (Artífice, fora do limite): Nv 3 Mísseis Mágicos, '
        'Escudo Arcano; Nv 5 Bafo de Dragão, Vínculo Protetor; Nv 9 Aura de '
        'Vitalidade, Pequena Cabana de Leomond; Nv 13 Metamorfose, Escudo de '
        'Fogo; Nv 17 Círculo de Teletransporte, Passo Distante.',
    "engenheiro:Defensor de Aço":
        '"Eu construí o meu, pra ter certeza de que ele nunca esquece quem '
        'proteger." Efeito: no 3º nível ganha um Defensor de Aço (amigável, '
        'obedece a comandos; você define aparência e nº de pernas). Consertar '
        'cura 2d6 nele; se morto há até 1 h, revive como Ação (a 1,5 m, '
        'gastando espaço de 1º+; volta com PV cheios após 1 min). Em Descanso '
        'Longo cria um novo (com ferramentas de funileiro; o anterior some). '
        'Ficha: Médio constructo, CA 13 (armadura natural), PV 20 + 10 × '
        '(nível − 3), deslocamento 12 m.',
    "engenheiro:Reparos Rápidos":
        '"Faíscas e rachaduras são lembrete de manutenção preventiva." '
        'Efeito: no 3º nível, suas magias de cura afetam o Defensor mesmo '
        'sendo construto; como Ação, repara 2d6 + mod. Inteligência PV nele, '
        'usos = bônus de proficiência (recupera em Descanso Longo).',
    "engenheiro:Ataque Reativo":
        '"O mínimo que posso fazer é garantir que se arrependa na mesma fração '
        'de segundo." Efeito: no 5º nível, quando o Defensor usa Defletir '
        'Ataque e o ataque erra, ele faz um ataque contra o atacante como '
        'parte da mesma reação.',
    "engenheiro:Defensor Aprimorado":
        '"Ele é laboratório móvel, guindaste, batedor e muralha no mesmo '
        'chassi." Efeito: no 5º nível, em Descanso Longo (com ferramentas de '
        'funileiro) escolhe 1 aprimoramento para o Defensor: Radar de '
        'Localização (Vantagem em Percepção; Sobrecarga: sente criaturas em '
        '1,6 km); Sonar (visão às cegas 9 m; Sobrecarga: visão verdadeira 9 m, '
        'ver pelos olhos dele); Mecanismo de Camuflagem (Vantagem em '
        'Furtividade; Sobrecarga: invisibilidade); Foguetes de Investida '
        '(+1d8 force ao avançar 6 m, TR Força ou Derrubado); Aumento de '
        'Estrutura (Grande, carga dobrada; Sobrecarga: Enorme); Chapas '
        'Revestidas (+CA = metade do mod. Int; Sobrecarga: PV temporários); '
        'Módulo de Deslocamento (nado/escalada/voo = caminhada). Ganha '
        'aprimoramentos extras no 10º e 15º (total 3); no 10º pode '
        'Sobrecarregar 1 por 1 h (precisa Descanso Longo junto ao Defensor '
        'para repetir).',
    "engenheiro:Vínculo Arcano":
        '"O mesmo canal que me protege protege ele também." Efeito: no 10º '
        'nível, magias suas de alcance Pessoal afetam você e o Defensor; '
        'magias de reação (Escudo Arcano, Absorver Elementos) podem ter o '
        'Defensor como alvo no lugar de você.',
    "engenheiro:Especialização de Núcleo":
        '"O núcleo é uma decisão sobre o que ele foi criado para ser." '
        'Efeito: no 15º nível, 1 h de trabalho (ferramentas de funileiro) '
        'escolhe 2 núcleos entre Ofensivo, Defensivo, Batedor ou Arcano. '
        'Força/Destreza/Constituição do Defensor +4 (18/16/18). Ofensivo: '
        'Ataque Extra. Defensor: Defletir Ataque impõe Desvantagem em todos os '
        'ataques do alvo até o fim do turno. Batedor: deslocamento 18 m, '
        'Disparada/Desengajar como Ação Bônus. Arcano: Vantagem em TR contra '
        'magias só-nele; se passar e a magia for ≤4º círculo, ela é refletida '
        'no conjurador.',

    # ===== FERREIRO DE BATALHA (sub 150) =====
    "ferreiro:Proficiências do Ferreiro":
        '"Se eu fiz, aguenta mais do que o problema que viemos resolver." '
        'Efeito: proficiência com ferramentas de ferreiro (se já tiver, outras '
        'de artesão) e com armaduras pesadas.',
    "ferreiro:Magias do Ferreiro de Batalha":
        '"Cada arma que reforço vem com o feitiço certo." Efeito: sempre '
        'preparadas (Artífice, fora do limite): Nv 3 Destruição Trovejante, '
        'Escudo Arcano; Nv 5 Marca da Punição, Arma Espiritual; Nv 9 '
        'Destruição Cegante, Manto do Cruzado; Nv 13 Destruição Estonteante, '
        'Escudo de Fogo; Nv 17 Círculo de Poder, Arma Sagrada.',
    "ferreiro:Duplicar Infusão":
        '"Uma boa infusão nunca deveria servir só para uma lâmina." Efeito: '
        'no 3º nível, suas Infusões com pré-requisito de Arma, Armadura ou '
        'Escudo podem ser aplicadas em dois itens em vez de um. (Só contam '
        'como "Infusão de Armadura" as que dizem "Armadura" no pré-requisito; '
        'elmos/luvas/botas/cintos não contam.)',
    "ferreiro:Choque Arcano":
        '"O que machuca é a onda de energia que adiciono no impacto." Efeito: '
        'ao acertar com arma infundida por você (ou via Reação quando aliado '
        'com arma infundida sua acerta), causa dano de Energia (force) extra: '
        'Nv 3 1d6, Nv 5 2d6, Nv 9 3d6, Nv 15 4d6. Usos = mod. Inteligência '
        '(mín 1), só 1×/turno (recupera em Descanso Longo). Sem usos, pode '
        'gastar espaço de 1º+ para aplicar.',
    "ferreiro:Ataque Extra Mágico":
        '"Cada abertura é uma chance de acertar mais de uma vez." Efeito: no '
        '5º nível, ataca duas vezes na Ação de Ataque; pode substituir um '
        'desses ataques por um truque de Artífice (conjuração 1 Ação).',
    "ferreiro:Ajustes do Ferreiro":
        '"Se a arma de um aliado falha, eu trato como erro meu de projeto." '
        'Efeito: no 10º nível, em Descanso Longo (ferramentas de ferreiro) '
        'aprimora um nº de armas = mod. Inteligência (mín 1) por 8 h: contam '
        'como mágicas; 1×/turno do empunhador, +1d8 force ao acertar. Armas '
        'assim contam como infundidas para o Choque Arcano.',
    "ferreiro:Pax Armada":
        '"Armas bem-feitas mantêm você de pé enquanto o mundo tenta '
        'derrubar." Efeito: no 15º nível, usos de Choque Arcano = 2× mod. '
        'Inteligência (mín 2). Sempre que causar dano com Choque Arcano, ganha '
        'PV temporários iguais ao dano; quando o ativa via Reação para um '
        'aliado, esse aliado ganha os PV temporários. Quando você ou aliado '
        'ataca com arma de Ajustes do Ferreiro, pode trocar o +1d8 de dano por '
        '+1d8 na jogada de ataque (declarado após o dado, antes do resultado).',

    # ===== MAGIDUELISTA (sub 151) =====
    "magiduelista:Ferramentas do Ofício":
        '"Se a arma que dispara minha magia não for tão bem feita quanto a '
        'magia, algo está errado." Efeito: proficiência com ferramentas de '
        'entalhador de madeira (se já tiver, outras de artesão).',
    "magiduelista:Magias de Magiduelista":
        '"Se a magia não serve para vencer um confronto direto, eu não a '
        'mantenho." Efeito: sempre preparadas (Artífice, fora do limite): Nv 3 '
        'Escudo, Repreensão Infernal; Nv 5 Borrão, Raio Abrasador; Nv 9 '
        'Contramágica, Relâmpago; Nv 13 Rechaço, Muralha de Fogo; Nv 17 '
        'Deslocamento Temporal, Muralha de Força.',
    "magiduelista:Arma Arcana":
        '"Minha varinha é uma equação carregada." Efeito: em Descanso Longo, '
        '1 h com ferramentas de entalhador transforma um foco arcano em sua '
        'Arma Arcana (só 1 por vez; mantém propriedades; conta como foco '
        'arcano inclusive para Infusões). Potencialização Arcana: ao conjurar '
        'magia de Artífice usando-a como foco, +1d8 de dano a um alvo (mesmo '
        'tipo da magia, ou force). Estrutura Arcana: 2 componentes (Madeira '
        'Arcana, Núcleo Arcano), cada um recebe 1 Infusão de Varinha (não '
        'contam no limite de Infusões Conhecidas; só na Arma Arcana; trocáveis '
        'em Descanso Longo).',
    "magiduelista:Raio Arcano":
        '"Uma linha perfeitamente reta de energia pura." Efeito: como Ação, '
        'dispara Raio Arcano contra criatura a até 36 m — ataque mágico à '
        'distância (Inteligência); acerto = 1d10 + mod. Inteligência de '
        'Energia (force); conta como ataque de magia de Artífice. Raios por '
        'Ação: Nv 3 = 1, Nv 5 = 2, Nv 10 = 3, Nv 15 = 4 (alvos iguais ou '
        'diferentes, ataque separado por raio).',
    "magiduelista:Duelista Arcano":
        '"Se tenho que escolher entre atirar ou conjurar, não aperfeiçoei a '
        'coreografia." Efeito: no 5º nível, ao usar Raio Arcano pode conjurar '
        'um truque de Artífice (1 Ação) como Ação Bônus no mesmo turno.',
    "magiduelista:Saque Rápido":
        '"Duelos são sobre quem reage primeiro e melhor." Efeito: no 10º '
        'nível, adiciona o bônus de proficiência às jogadas de iniciativa. Ao '
        'usar Reação para conjurar magia de 1º+, dispara 1 Raio Arcano como '
        'parte da reação (antes da magia resolver). Se o raio acertar o alvo '
        'da magia: se a magia pede TR, o alvo faz com Desvantagem; se pede '
        'ataque mágico, você o faz com Vantagem (só no 1º alvo).',
    "magiduelista:Mestre Magiduelista":
        '"Minha Arma Arcana conduz uma sequência de decisões perfeitas." '
        'Efeito: no 15º nível — Conjuração Encadeada: após usar Raio Arcano '
        '(Ação), conjura uma magia de Artífice (1 Ação) como Ação Bônus no '
        'mesmo turno. Campo de Proteção Arcana: ao usar Reação para conjurar '
        'magia de 1º+, cria campo de raio 4,5 m; até o início do seu próximo '
        'turno, você e aliados na área recebem cobertura três-quartos contra '
        'ataques/efeitos de fora.',
}


SUBCLASSE_PREFIXES = {
    1:   "alquimista",
    3:   "armadurista",
    4:   "aprimorado",
    5:   "engenheiro",
    150: "ferreiro",
    151: "magiduelista",
}


def chave_para(sub_id, nome):
    if sub_id is None:
        return nome
    return f"{SUBCLASSE_PREFIXES[sub_id]}:{nome}"


if __name__ == "__main__":
    print(f"Total descrições: {len(DESCRICOES)}")
