"""Descrições limpas de todas as 64 features de Bárbaro, escritas à mão a partir
do dump oficial (paginas/barbaro.html). Substituem o output do parser que tinha
resíduos de scraper (`id="spoiler-..."`, etc).

Chave: nome canônico (classe) OU 'slug:Nome' (subclasse).
Convenção igual aos druida/bardo_descricoes.py.
"""

DESCRICOES = {

    # ================= CLASSE (16 únicas, cobrem 24 entradas) =================
    "Fúria":
        '"Você sente o sangue esquentar e o mundo afunilar." Efeito: pode '
        'entrar em frenesi primitivo. Ativar (Ação Bônus, sem armadura '
        'pesada). Duração: 1 min; termina se ficar Inconsciente ou for alvo '
        'de efeito que acalme emoções; não pode encerrar voluntariamente. '
        'Manter: em cada turno, se não atacar nem for atacado, gaste Ação '
        'Bônus para mantê-la (senão termina ao fim do turno). Benefícios: '
        'Vantagem em testes de resistência e de habilidade de Força; ao '
        'acertar ataque corpo a corpo com Força, dano extra = metade do nível '
        'de Bárbaro (arred. cima); Resistência a Concussão, Cortante e '
        'Perfurante. Restrições: Desvantagem em testes de Inteligência; não '
        'pode conjurar nem manter Concentração. Usos = Bônus de Proficiência; '
        'recupera em Descanso Longo.',

    "Guerreiro Desprotegido":
        '"Couro, osso e cicatriz viraram a sua couraça." Efeito: Defesa '
        'Instintiva — sem armadura, CA = 10 + mod. Destreza + mod. '
        'Constituição (pode usar escudo; não acumula com outras fórmulas de '
        'CA). Golpes Desarmados: causam 1d6 + mod. Força de Concussão, '
        'aumentando para 1d8 no Nv 5, 1d10 no Nv 11, 1d12 no Nv 17.',

    "Maestria em Armas":
        '"Você domina o uso técnico de seus instrumentos de guerra." Efeito: '
        'escolha dois tipos de armas corpo a corpo (Simples ou Marciais); '
        'empunhando um deles, pode usar a propriedade de maestria associada. '
        'Treino Diário: em cada Descanso Longo, pode substituir um dos tipos '
        'escolhidos. Progressão: o número de armas dominadas aumenta conforme '
        'a tabela do Bárbaro.',

    "Ataque Imprudente":
        '"Você se joga para frente de propósito, abre a guarda." Efeito: ao '
        'fazer o primeiro ataque no seu turno, pode declarar Ataque '
        'Imprudente — Vantagem em todas as jogadas de ataque corpo a corpo '
        'com Força até o início do seu próximo turno; em troca, ataques '
        'contra você também têm Vantagem nesse período.',

    "Sentido de Perigo":
        '"O corpo responde antes da mente terminar a pergunta." Efeito: '
        'Vantagem em testes de resistência de Destreza. Não recebe o '
        'benefício se estiver Incapacitado (ou Cego/Surdo para a fonte do '
        'perigo).',

    "Caminho do Bárbaro":
        '"Totem, tempestade, sangue ou trilha solitária." Efeito: no 3º nível '
        'escolha um Caminho do Bárbaro (Arauto Rúnico, Coração Selvagem, '
        'Guardião Ancestral, Berserker, Zelote, Colosso de Batalha ou '
        'Feitiçaria Selvagem). Concede características no 3º nível e novamente '
        'nos níveis 6, 10, 14 e 18.',

    "Incremento de Atributo ou Talento":
        '"Você aprende a se lapidar como quem afia uma lâmina." Efeito: ao '
        'atingir os níveis 4, 8, 12, 16 e 19, escolha: Aumento de Atributo '
        '(+2 num atributo, ou +1 em dois; máximo 20); ou Talento (cujos pré-'
        'requisitos você atenda).',

    "Ataque Extra":
        '"O primeiro golpe abre caminho, o segundo decide." Efeito: sempre '
        'que realizar a Ação de Ataque no seu turno, pode realizar dois '
        'ataques em vez de um.',

    "Conhecimento Primitivo":
        '"Ouvir o que o ambiente conta é metade da vitória." Efeito: escolha '
        '1 perícia da lista do Bárbaro (Nv 1) e ganhe proficiência nela (se '
        'ainda não tiver). No 10º nível recebe de novo, escolhendo outra '
        'perícia da mesma lista.',

    "Característica de Caminho":
        '"O rito afunda até o osso." Efeito: você ganha a característica do '
        'seu Caminho do Bárbaro correspondente a este nível, conforme o '
        'Caminho escolhido no 3º nível.',

    "Ímpeto Selvagem":
        '"Um meio passo já vira investida." Efeito: Reflexo de Combate — '
        'Vantagem em testes de Iniciativa. Passo Acelerado — velocidade de '
        'caminhada +3 m. Avanço Furioso — ao entrar em Fúria, pode se mover '
        'até metade da velocidade imediatamente, como parte da mesma Ação '
        'Bônus.',

    "Fôlego Furioso":
        '"Você morde o ar e se recusa a cair." Efeito (só em Fúria): se cair '
        'a 0 PV em fúria e não morrer instantaneamente, faz TR de '
        'Constituição CD 10; sucesso fica com 1 PV em vez de cair '
        'Inconsciente. Cada reuso antes de descansar aumenta a CD em +5. A CD '
        'volta a 10 ao terminar Descanso Curto ou Longo.',

    "Fúria Devastadora":
        '"Quando acerta, o osso aceita sem discutir." Efeito: ao fazer Acerto '
        'Crítico com arma corpo a corpo, dano extra: Arma Comum +1d10; Arma '
        'Pesada ou Desarmado +1d12; Arma Leve +1d8. No Nv 17 a quantidade de '
        'dados dobra (+2d10/+2d12/+2d8). Fúria no Crítico: em Fúria, ao '
        'crítico com arma corpo a corpo de Força, adiciona o nível de Bárbaro '
        'inteiro como bônus de dano (em vez de metade).',

    "Instinto Brutal":
        '"Qualquer erro do inimigo vira oportunidade de ferida profunda." '
        'Efeito: ao fazer um ataque que use Força (no ataque e no dano), sua '
        'margem de crítico aumenta em 1 (ex.: 20 → 19-20; se já 19-20 → '
        '18-20).',

    "Ira Incontrolável":
        '"Agora a fúria não vem e vai rápido; ela fica." Efeito: Fúria '
        'Incessante — ao rolar Iniciativa, pode recuperar todos os usos '
        'gastos de Fúria (1×/Descanso Longo). Duração Estendida — sua Fúria '
        'agora dura 10 minutos; termina antes só se cair Inconsciente, for '
        'alvo de efeito que acalme emoções, ou se você decidir encerrá-la no '
        'seu turno (sem ação). Substitui a restrição de Nv 1 que impedia '
        'encerramento voluntário.',

    "Força Indomável":
        '"A sua própria Força se impõe." Efeito: ao fazer Teste de Habilidade '
        'de Força ou TR de Força, se o resultado final (com modificadores) '
        'for menor que o seu valor de atributo Força, pode usar o valor de '
        'Força no lugar do resultado.',

    "Avatar da Fúria":
        '"O fôlego vira fornalha, o sangue vira martelo." Efeito: no 20º '
        'nível, Força e Constituição +4 (máximo desses atributos passa a 26). '
        'Golpes Devastadores: em Fúria, ataques corpo a corpo com Força '
        'recebem bônus de dano adicional igual ao mod. de Constituição (além '
        'do bônus normal da Fúria).',

    # ================= CAMINHO DO ARAUTO RÚNICO (sid 14) =================
    "arauto:Runas Elementais":
        '"Cada marca é uma promessa que você faz para algo maior." Efeito: '
        'você domina 4 Runas Elementais — Chamas (Fogo), Tempestade (Elétrico/'
        'Trovão), Erosão (Ácido), Nevasca (Gelo). Vínculo Rúnico: gasta 1 hora '
        'talhando uma arma corpo a corpo ou de arremesso, tornando-a sua arma '
        'vinculada (só 1 por vez). Arauto Elemental: ao entrar em Fúria, '
        'escolhe uma Runa e cria aura de 3 m centrada em você (dura enquanto a '
        'Fúria). Resiliência Elemental: resistência ao tipo de dano da Runa '
        'ativa. Devastação Rúnica: como parte da Ação Bônus de entrar em Fúria '
        '(e como Ação Bônus depois), libera a runa — todas as criaturas na '
        'aura (incluindo aliados) sofrem dano elemental = bônus de dano da '
        'Fúria. Armamento do Arauto: em Fúria com a arma vinculada, pode '
        'trocar o tipo de dano da Fúria pelo da Runa ativa. Alteração da Runa: '
        'Ação Bônus troca a Runa ativa sem encerrar a Fúria. Chamado Rúnico '
        'Menor: aprende o truque Elementalismo (sem componentes materiais, '
        'Constituição como atributo).',

    "arauto:Armamento Rúnico Aprimorado":
        '"A arma vira extensão das próprias runas." Efeito: em Fúria '
        'empunhando a arma vinculada, ela ganha a propriedade Arremesso '
        '(6/18 m) e retorna imediatamente à sua mão ao final do ataque à '
        'distância (acertando ou errando).',

    "arauto:Essência Rúnica Entrelaçada":
        '"As runas vazam para o dia a dia." Efeito: ao terminar Descanso '
        'Curto/Longo, escolha uma Runa Guardiã — resistência ao dano dela '
        'mesmo fora de Fúria, mais um benefício: Chamas (Visão no Escuro 18 m, '
        'ou +9 m se já tem; incendeia objetos inflamáveis a 3 m como Ação); '
        'Tempestade (ignora altitude/ventos fortes; prende a respiração '
        'indefinidamente se consciente); Erosão (velocidade de escalada = '
        'caminhada; solidifica 1 m³ de solo instável a 3 m como Ação); '
        'Nevasca (velocidade de nado = caminhada; congela cubo de água de '
        '1,5 m por 1 h como Ação). Pode reescolher a cada descanso.',

    "arauto:Égide Primordial":
        '"As runas passam a segurar o mundo em volta de você." Efeito: em '
        'Fúria com a aura de Arauto Elemental ativa — aliados na aura não '
        'sofrem dano da Devastação Rúnica e ganham resistência ao tipo da '
        'Runa ativa enquanto na aura. Fortitude Rúnica: em Fúria, Ação Bônus '
        'concede a cada aliado escolhido na aura PV temporários = bônus de '
        'dano da Fúria (não acumulam, regra normal de PVT).',

    "arauto:Despertar Rúnico":
        '"Cada símbolo pulsa mais forte." Efeito (em Fúria com Runa ativa): '
        'CD da Runa = 8 + bônus prof. + mod. Constituição. Incineração '
        '(Chamas): ao reduzir criatura a 0 PV na aura, Reação libera explosão '
        '— inimigos escolhidos na aura sofrem Fogo = bônus de dano da Fúria. '
        'Brado da Tormenta (Tempestade): quando criatura falha TR na aura ou '
        'você acerta arremesso com a arma vinculada, Reação invoca raio = '
        'dano Elétrico/Trovão igual ao seu nível de Bárbaro. Terra Arrasada '
        '(Erosão): criatura que se move voluntariamente na aura faz TR '
        'Destreza vs. CD da Runa; falha sofre Ácido = bônus de dano da Fúria + '
        'fica Caída, sucesso metade. Prisão Frígida (Nevasca): criatura '
        'hostil que termina turno na aura faz TR Constituição vs. CD da Runa; '
        'falha sofre Gelo = bônus de dano da Fúria + velocidade 0 até fim do '
        'próximo turno dela, sucesso metade.',

    "arauto:Campeão das Runas":
        '"Você vira o próprio campo onde as runas são forjadas." Efeito: ao '
        'entrar em Fúria, resistência a TODOS os danos das Runas (Fogo, '
        'Elétrico, Trovão, Ácido, Gelo) — ainda escolhe uma Runa ativa para '
        'os demais efeitos. Aura Rúnica Espelhada: ao arremessar a arma '
        'vinculada e acertar alvo/ponto, gasta 1 uso de Fúria para criar uma '
        'aura espelhada de 3 m no local (dura 1 min ou até novo arremesso '
        'marcar outro; segue alvo móvel). Devastação Estendida: a Devastação '
        'Rúnica também atinge inimigos na aura espelhada. Despertar '
        'Ressonante: Reação ativa um efeito do Despertar Rúnico a partir da '
        'área marcada. Proteção Espelhada: aliados na aura espelhada recebem '
        'os benefícios da Égide Primordial. Como Ação Bônus você escolhe se o '
        'próximo arremesso criará/moverá a aura espelhada ou será ataque '
        'normal.',

    # ================= CAMINHO DO CORAÇÃO SELVAGEM (sid 15) =================
    "coracao:Despertar Bestial":
        '"O corpo lembra de coisas que o pensamento esqueceu." Efeito: ao '
        'entrar em Fúria (mesma Ação Bônus), manifesta traços animalescos. Em '
        'Fúria: Arsenal Primitivo — ataques desarmados causam Perfurante ou '
        'Cortante (à escolha); pode usar Ação Bônus para ataque desarmado com '
        'armas naturais. Aspectos Selvagens (escolha 1 por Fúria): Proteção '
        'Primal (resistência a todo dano exceto Força, Necrótico, Psíquico, '
        'Radiante); Predador Ágil (ao ativar Fúria, Desengajar + Correr na '
        'mesma Ação Bônus; repete com Ação Bônus em turnos seguintes); '
        'Caçador Alfa (aliados têm Vantagem em ataques contra inimigos a '
        '1,5 m de você). Dura enquanto a Fúria; reescolhe aspecto a cada '
        'Fúria.',

    "coracao:Empatia Selvagem":
        '"As feras reconhecem intenção." Efeito: Linguagem Instintiva — pode '
        'se comunicar verbalmente com Bestas e compreendê-las (som, gesto, '
        'instinto; ideias simples). Compreensão limitada à Inteligência/'
        'experiência da criatura (memórias básicas, perigo, território, fome, '
        'medo). Não encanta nem obriga — é compreensão mútua, não controle; a '
        'besta reage conforme sua natureza.',

    "coracao:Habilidade Bestial":
        '"O corpo decide sobreviver do jeito que der." Efeito: ao terminar '
        'Descanso Longo, escolhe uma Adaptação Fisiológica — adiciona mod. '
        'Constituição (mín +1) aos testes das 2 perícias associadas: Força '
        'Bruta (Atletismo, Intuição); Percepção Aguçada (Investigação, '
        'Percepção); Caçador Ágil (Furtividade, Sobrevivência). Só 1 ativa '
        'por vez, troca a cada Descanso Longo. Mobilidade Evolutiva '
        '(permanente): velocidade de escalada = caminhada (escala superfícies '
        'difíceis/tetos sem teste); velocidade de nado = caminhada (sem '
        'penalidade em correntezas normais).',

    "coracao:Instinto Predatório":
        '"O reflexo aprendeu exatamente onde dói mais." Efeito (em Fúria, ao '
        'usar a Ação Bônus de ataque desarmado com armas naturais e acertar): '
        'aplique 1 efeito — Investida Brutal (alvo fica Caído); Desafio '
        'Bestial (alvo tem Desvantagem em ataques que não sejam contra você '
        'até o fim do próximo turno dele); Mordida Laceral (recupera PV = '
        'mod. Força + mod. Constituição, mín 1). Só no ataque da Ação Bônus '
        'das armas naturais; escolhe 1 efeito por uso.',

    "coracao:Instinto Ancestral":
        '"Você ouve a natureza sem oração nem livro." Efeito: pode conjurar '
        'Comunhão com a Natureza apenas como Ritual, sem gastar espaço de '
        'magia. Atributo de conjuração: Sabedoria.',

    "coracao:Chamado da Caçada":
        '"A luta deixa de ser só sua." Efeito: ao entrar em Fúria (mesma '
        'ação), escolha até mod. Constituição criaturas dispostas (mín 1) que '
        'veja a 9 m. Vigor Primal: para cada criatura que aceitar, você '
        'recebe PV temporários = bônus de dano da Fúria (regra normal de '
        'PVT). Ferocidade Impiedosa: até o fim da Fúria, cada criatura que '
        'aceitou pode, 1×/turno ao acertar e causar dano, adicionar valor = '
        'bônus de dano da Fúria. Recarga: 1/Descanso Longo, ou gasta 1 uso de '
        'Fúria para reativar.',

    "coracao:Domínio da Fera Primordial":
        '"Difícil dizer onde termina a pessoa e começa o predador." Efeito '
        '(aprimora Despertar Bestial, em Fúria): Duplo Aspecto — escolhe 2 '
        'Aspectos Selvagens simultâneos. Mutação Aprimorada: Couraça Primal '
        '(resistência a todo dano incluindo Força/Necrótico/Radiante; só '
        'Psíquico não tem resistência); Predador Ágil (pode se Esconder ao '
        'fim do turno ao ativar Fúria e ao usar a Ação Bônus de Desengajar+'
        'Correr); Caçador Alfa (Reação: quando criatura a 1,5 m ataca um '
        'aliado, faz 1 ataque com arma natural contra ela, podendo aplicar 1 '
        'efeito de Instinto Predatório).',

    # ================= CAMINHO DO GUARDIÃO ANCESTRAL (sid 16) =================
    "guardiao:Guardiões Ancestrais":
        '"Um pequeno exército que não aceita ver ninguém atrás de você '
        'cair." Efeito (em Fúria): Aura Ancestral de 4,5 m centrada em você '
        '(dura enquanto a Fúria) — terreno difícil para inimigos; espíritos '
        'visíveis mas não-alvejáveis. Marca do Guardião: ao acertar criatura '
        'com arma ou desarmado, um espírito a marca até o início do seu '
        'próximo turno — marcada tem Desvantagem em ataques que não sejam '
        'contra você. Ataque Espiritual: Ação Bônus ordena o espírito a '
        'atacar uma criatura marcada (sem rolar ataque): dano = bônus de dano '
        'da Fúria como Energia (Força). Tudo encerra quando a Fúria acaba.',

    "guardiao:Escudo dos Antepassados":
        '"O espírito se põe na frente de quem ia ser acertado." Efeito '
        '(Reação): quando criatura que você veja a 9 m sofre dano, antes de '
        'aplicado role N d6 (N = mod. Constituição, mín 1) e some ao bônus de '
        'dano da Fúria — o dano sofrido é reduzido por esse total. Presença '
        'Protetiva: se a criatura também estiver na sua Aura Ancestral, ela '
        'ganha Resistência a todo o dano desse ataque (após a redução). '
        'Limitado pela Reação disponível.',

    "guardiao:Consultar os Espíritos":
        '"Você faz a pergunta certa, e os ancestrais mostram o caminho." '
        'Efeito: pode lançar Augúrio e Clarividência sem gastar espaço nem '
        'componentes materiais; atributo de conjuração Sabedoria. '
        'Clarividência envia um espírito invisível ao local. Recarga: 1× '
        'então só após Descanso Curto/Longo, ou gastando 1 uso de Fúria.',

    "guardiao:Eco Curativo":
        '"Cada impacto deixa um rastro que vira fôlego novo." Efeito: sempre '
        'que seus espíritos ancestrais causarem dano de Energia (Força), você '
        'recupera PV = metade do dano de Energia (Força) daquela instância. '
        'Não ultrapassa PV máximo; aplicado logo após o dano.',

    "guardiao:Espíritos Vingadores":
        '"A pancada que não chega em quem deveria, volta." Efeito (aprimora '
        'Escudo dos Antepassados): Vigilância Aprimorada — alcance da Reação '
        'de proteção sobe de 9 m para 18 m. Vingança Espiritual: se ao usar '
        'Proteção Espiritual o dano final for reduzido a 0 (após redução e '
        'resistências), a criatura atacante sofre dano de Energia (Força) = '
        'valor total reduzido pela reação. Só dispara se o dano chegar '
        'efetivamente a 0.',

    "guardiao:Legião dos Ancestrais":
        '"Uma legião que não cansa, não sangra e não esquece." Efeito: Aura '
        'Expandida — Aura Ancestral sobe de 4,5 m para 6 m. Investida da '
        'Legião: em Fúria com a aura, Ação Bônus faz todos os inimigos na '
        'aura sofrerem Energia (Força) = bônus de dano da Fúria; o espírito '
        'que marcou um alvo o ataca mesmo fora da aura pelo mesmo dano. '
        'Muralha dos Protetores: você e criaturas escolhidas a 6 m ganham '
        'Meia Cobertura (+2 CA, +2 TR Destreza) enquanto na aura.',

    # ================= CAMINHO DO BERSERKER (sid 17) =================
    "berserker:Fúria Inconsciente":
        '"Ameaça não entra fácil." Efeito (em Fúria): Indomável — não pode '
        'ser Enfeitiçado nem Amedrontado; se já estiver ao entrar em Fúria, '
        'esses efeitos ficam suspensos enquanto a Fúria durar. Centelha '
        'Colérica (em Frenesi): mantém os níveis de Exaustão mas suprime os '
        'efeitos negativos enquanto o Frenesi durar (voltam quando termina).',

    "berserker:Presença Intimidante":
        '"Seu olhar pesa mais que aço." Efeito: Crítico Aterrador — em Fúria, '
        'ao crítico com arma, a criatura fica Amedrontada de você por 1 min; '
        'ao fim de cada turno dela faz TR Sabedoria CD 8 + bônus prof. + mod. '
        'Força; sucesso encerra e fica imune por 24 h. Aço e Terror: '
        'proficiência em Intimidação (se não tiver) e soma o mod. de Força '
        'aos testes de Carisma (Intimidação).',

    "berserker:Sede de Sangue":
        '"O sangue derramado vira contagem silenciosa." Efeito (só em Fúria): '
        'Marca Sanguinária — ao acertar ataque corpo a corpo ou desarmado em '
        'inimigo, aplica 1 contador (2 se crítico), em várias criaturas. '
        'Devorador de Vidas: ao fim do seu turno, recebe PV temporários = '
        'mod. Constituição × número de Marcas aplicadas no turno; depois as '
        'marcas somem.',

    "berserker:Além da Queda":
        '"A sua causa não aceita que você pare antes da hora." Efeito (em '
        'Fúria): Imparável Exemplar — chegar a 0 PV não o deixa Inconsciente; '
        'continua agindo, mas ainda faz testes de morte no início de cada '
        'turno e sofre efeitos normais de estar a 0 PV. Morte Postergada: '
        'quando morreria por acumular falhas em testes de morte, gasta 1 uso '
        'de Fúria (sem ação) para se manter vivo até o início do seu próximo '
        'turno; se ainda estiver a 0 PV então, morre (a não ser que reuse); '
        'se for curado/estabilizado antes, a morte é evitada.',

    # ================= CAMINHO DO ZELOTE (sid 18) =================
    "zelote:Selo do Fanatismo":
        '"A causa que você escolheu gruda no corpo por dentro." Efeito (em '
        'Fúria): Resistência Consagrada — resistência a Necrótico e Radiante. '
        'Golpes Consagrados: ao entrar em Fúria escolhe Radiante ou '
        'Necrótico; ataques corpo a corpo e desarmados causam +1d6 desse tipo '
        '(1d8 no Nv 6, 1d10 no Nv 10, 1d12 no Nv 14). Selo do Sacrifício: '
        'Ação Bônus em criatura que acertou neste turno — dano adicional = '
        'bônus de dano da Fúria, do tipo escolhido.',

    "zelote:Obsessão Inquebrável":
        '"Você reza com os punhos." Efeito (em Fúria): uma vez por Fúria '
        'ativa, ao falhar em um teste de resistência, pode refazê-lo '
        'adicionando bônus = bônus de dano da Fúria à nova rolagem; deve usar '
        'o novo resultado, mesmo que pior.',

    "zelote:Grito de Cruzada":
        '"O grito acende olhar apagado e varre a dúvida." Efeito (Ação Bônus '
        'em Fúria): até 10 criaturas escolhidas a 18 m que possam ouvi-lo '
        'ganham Vantagem em jogadas de ataque e testes de resistência até o '
        'início do seu próximo turno. Recarga: 1/Descanso Longo, ou gasta 1 '
        'uso de Fúria (sem ação) para restaurar (não ativa nova Fúria).',

    "zelote:Forma do Guerreiro Sagrado":
        '"O rosto do juramento em plena guerra." Efeito: ao ativar Fúria, '
        'pode assumir a Forma do Guerreiro Sagrado (sem ação extra), por até '
        '1 min enquanto a Fúria durar ou até ficar Inconsciente; depois 1/'
        'Descanso Longo. Voo: velocidade de voo = caminhada, pode Pairar. '
        'Imunidade Consagrada: imune a Necrótico e Radiante. Revivescência '
        '(Reação): quando criatura a 9 m que você veja cairia a 0 PV, gasta 1 '
        'uso de Fúria e ajusta os PV dela para o seu nível de Bárbaro (não '
        'impede mortes instantâneas que ignorem PV).',

    "zelote:Retaliação":
        '"Perto de você, ninguém bate de graça." Efeito (em Frenesi): Fúria '
        'Encadeada — se pelo menos um ataque seu no turno for crítico (com '
        'qualquer arma corpo a corpo), faz 1 ataque corpo a corpo adicional '
        'como parte da Ação Bônus do Frenesi (máx 1 por turno mesmo com '
        'vários críticos). Sede de Vingança (Reação): quando criatura a 1,5 m '
        'faz um ataque contra você, faz 1 ataque corpo a corpo contra ela '
        'imediatamente, com a arma corpo a corpo que estiver empunhando.',

    # ================= CAMINHO DO COLOSSO DE BATALHA (sid 19) =================
    "colosso:Armadura Reforjada":
        '"Você trata a própria armadura como obra de forja." Efeito: '
        'proficiência com Ferramentas de Ferreiro. Em Descanso Curto, 1 hora '
        'aprimora uma armadura (só 1 aprimorada por vez). Armadura do '
        'Encouraçado: se a armadura aprimorada for mágica (+1/+2/+3), aplica '
        'esse bônus ao Golpe de Armadura (ataque e dano) e aos testes de '
        'Força (Atletismo) para empurrar/puxar/agarrar. Fúria Colossal: ao '
        'entrar em Fúria com a armadura aprimorada, pode ficar Grande até o '
        'fim da Fúria (se houver espaço; senão demais efeitos continuam). '
        'Ofensiva Aprimorada: em Fúria com a armadura aprimorada, ataques '
        'corpo a corpo (incl. Golpe de Armadura) causam +1d4 do tipo da arma.',

    "colosso:Investida Colossal":
        '"Seu avanço vira arma." Efeito: Golpe de Armadura — com a armadura '
        'aprimorada, ela conta como arma simples corpo a corpo (alcance '
        '1,5 m) causando 1d8 + mod. Força Concussivo; ao acertar pode aplicar '
        'um efeito de Ataque Desarmado (Empurrar/Derrubar). Colisão '
        'Imparável: ao entrar em Fúria, escolha inimigo visível; faz Disparada '
        'até 1,5 m dele e 1 Golpe de Armadura como parte da ativação. Ritmo '
        'do Aríete: em Fúria, se mover ≥ 6 m em linha reta até uma criatura, '
        'Ação Bônus faz 1 Golpe de Armadura nela ao fim do movimento.',

    "colosso:Colosso Armadurado":
        '"A armadura vira o jeito natural do seu corpo existir." Efeito: '
        'proficiência em armaduras pesadas; pode entrar em Fúria normalmente '
        'mesmo de armadura pesada (sem limitar habilidades). Atropelo Brutal: '
        'ao empurrar ou derrubar uma criatura via Investida Colossal (incl. '
        'efeitos do Golpe de Armadura), faz 1 ataque corpo a corpo adicional '
        'contra esse alvo como parte da mesma ação (antes ou depois de mover/'
        'derrubar).',

    "colosso:Investida Colossal Aprimorada":
        '"Meio passo já vira avanço." Efeito (em Fúria): Investida Acelerada '
        '— pode usar Disparada como Ação Bônus. Impacto Inescapável: ao usar '
        'essa Disparada, pode ativar a Investida Colossal na mesma Ação Bônus '
        '(incl. Golpe de Armadura ao fim do avanço) mesmo sem ter andado 6 m '
        'em linha reta antes; demais regras da Investida Colossal continuam.',

    "colosso:Retribuição Anã":
        '"Seu ferro não só aguenta pancada — ele responde." Efeito (em Fúria '
        'com armadura aprimorada e Golpe de Armadura): Espinhos Reativos — '
        'quando uma criatura o acerta com ataque corpo a corpo pela 1ª vez no '
        'turno dela, sofre 1d8 + mod. Constituição + bônus de dano da Fúria '
        'como Perfurante (máx 1×/criatura/turno). Golpe de Aprisionamento: ao '
        'acertar Golpe de Armadura, pode Agarrar o alvo em vez de Empurrar/'
        'Derrubar. Pressão Esmagadora: criatura Agarrada por você sofre, no '
        'início de cada turno seu, dano = dano base do Golpe de Armadura '
        '(1d8 + mod. Força + bônus de armadura mágica); não é ataque.',

    "colosso:Avanço de Titã":
        '"Você e a armadura viram uma coisa só." Efeito (em Fúria): Impávido '
        'Colosso — ao entrar em Fúria pode ficar Grande ou Enorme (se houver '
        'espaço) até a Fúria terminar; alcance dos ataques corpo a corpo '
        '+1,5 m. Corredor Inexorável: Ação Bônus para avanço em linha reta '
        'por até todo o deslocamento, atravessando espaço de criaturas '
        'menores/iguais sem provocar oportunidade. Momento de Destruição: a '
        '1ª vez que entra no espaço de cada criatura no avanço, ela faz TR '
        'Força CD 8 + bônus prof. + mod. Força; falha sofre 8d8 + mod. Força '
        '+ bônus de dano da Fúria de Concussão (você a empurra até 1,5 m; a '
        'última atingida que falhar fica Caída), sucesso metade. 1×/Fúria; '
        'gasta 1 uso de Fúria para repetir na mesma Fúria.',

    # ================= CAMINHO DA FEITIÇARIA SELVAGEM (sid 20) =================
    "feiticaria:Faro Arcano":
        '"Você fareja o que está escondido no ar." Efeito (Ação): aguça os '
        'sentidos — percebe magia como Detectar Magia em raio 18 m por até '
        '10 min. Termina antes se você entrar em Fúria. Usos = mod. '
        'Constituição (mín 1); recupera em Descanso Longo.',

    "feiticaria:Magia Selvagem":
        '"É caos. Mas é o seu caos." Efeito: CD da Magia Selvagem = 8 + bônus '
        'prof. + mod. Constituição. Ao entrar em Fúria, role 1d12 na Tabela '
        'de Magia Selvagem; o efeito dura até o fim da Fúria (sem '
        'concentração) salvo indicação. Tabela (d12): 1 Dreno Funesto (bônus '
        'de dano da Fúria vira Necrótico; 1×/turno ganha PV temp = dano '
        'necrótico causado, exceto vs. Mortos-Vivos); 2 Passo Instantâneo '
        '(Ação Bônus teleporta 9 m por turno); 3 Explosão Arcana (Ação Bônus: '
        'ponto a 9 m, criaturas em 1,5 m fazem TR Destreza vs. CD; falha 2× '
        'bônus de dano da Fúria de Força, sucesso metade); 4 Arma do Retorno '
        '(arma corpo a corpo ganha Arremesso 6/18 m e Leve; retorna à mão); '
        '5 Rebote Arcano (Reação quando criatura a 9 m causa dano: ela faz TR '
        'Destreza vs. CD; falha 2× bônus de dano da Fúria de Força); 6 '
        'Músculo de Vento (saltos dobrados); 7 Resiliência Adaptativa '
        '(resistência ao último tipo de dano sofrido; muda a cada novo tipo); '
        '8 Surto de Crescimento (como Aumentar de Aumentar/Reduzir; se não '
        'couber, role de novo); 9 Clarão de Guerra (luz 4,5 m; Ação Bônus: '
        'criatura na luz faz TR Constituição vs. CD ou fica Cega até o início '
        'do próximo turno dela); 10 Forma Fantasmal (atravessa criaturas/'
        'objetos como terreno difícil; não termina dentro deles); 11 Jardim '
        'Errante (vinhas em 4,5 m que se movem com você; terreno difícil para '
        'criaturas escolhidas, reescolhe a cada turno); 12 Fôlego Reaceso '
        '(recupera 1 uso de Fúria; role de novo e acumule o efeito).',

    "feiticaria:Ruptura Arcana":
        '"O que sua carne aprende a desfazer, transborda pros outros." '
        'Efeito (em Fúria): você e criaturas escolhidas a até 4,5 m ganham '
        'Resistência a todos os danos causados por magias.',

    "feiticaria:Magia Instável":
        '"Dor e falha viram gatilho." Efeito (Reação, em Fúria): quando você '
        'sofrer dano ou falhar em um teste de resistência, role 1d12 de novo '
        'na Tabela de Magia Selvagem — o novo resultado substitui o efeito '
        'atual. 1×/rodada (usa Reação). Se o resultado mandar "role de novo e '
        'acumule" (ex.: 12 Fôlego Reaceso), siga aquele texto.',

    "feiticaria:Caos Encarnado":
        '"O caos joga no seu time." Efeito (em Fúria, com Magia Selvagem): '
        'sempre que precisar rolar na Tabela de Magia Selvagem, role 2d12, '
        'veja os dois e escolha qual efeito se manifesta. Se escolher um '
        'resultado que mande rolar de novo e acumular, siga o texto; pode '
        'escolher o mesmo número já ativo se for vantajoso.',

    "feiticaria:Golpe Dissipador":
        '"Onde outros veem não passa, você vê nó mal amarrado." Efeito (em '
        'Fúria): em vez de 1 ataque na Ação de Ataque, golpeia uma criação de '
        'força mágica (esfera resiliente, muralha prismática, jaula de força '
        'etc.) a alcance corpo a corpo, gastando 1 uso de Fúria (sem encerrá-'
        'la); acerta automaticamente. Magia de 3º círculo ou menos: destruída '
        'instantaneamente. Magia de 4º+ : teste de Força CD 10 + nível do '
        'espaço usado; sucesso destrói, falha nada (uso de Fúria gasto). '
        'Usável quantas vezes tiver usos de Fúria e estiver em Fúria.',
}


SUBCLASSE_PREFIXES = {
    14: "arauto",
    15: "coracao",
    16: "guardiao",
    17: "berserker",
    18: "zelote",
    19: "colosso",
    20: "feiticaria",
}


def chave_para(sub_id, nome):
    if sub_id is None:
        return nome
    return f"{SUBCLASSE_PREFIXES[sub_id]}:{nome}"


if __name__ == "__main__":
    print(f"Total descrições: {len(DESCRICOES)}")
