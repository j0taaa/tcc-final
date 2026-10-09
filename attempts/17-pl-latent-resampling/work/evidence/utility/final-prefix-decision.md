# Decisão de utilidade: reamostragem latente PL

Há benefício na redução de variância do gradiente, mas isso não estabelece que a mistura seja a melhor solução. Novidade e melhora da geração final não foram confirmadas.

Os seis documentos externos foram selecionados por hash antes dos forwards, sem injetar gabarito. Nas 12 configurações, uma réplica iid reduz a variância da cabeça real entre 8.75% e 40.06%. A razão custo x variância contra o original, usando o piso forte de custo neural, fica entre 0.6435 e 0.9305 nas medianas de três repetições; abaixo de 1 favorece reamostrar.

A enumeração com média condicional exata é a melhor dessas alternativas em 12/12 configurações. Ela é um controle competente: o alvo por evento tem poucas alternativas. A mistura não deve ser escolhida aí só porque a sua correção é mais geral.

A geometria foi recalculada offline por outro programa nos 12 casos. O erro máximo na checagem de norma contra autograd é 9.98e-08; o da derivada contra diferenças finitas é 1.44e-11. São testes numéricos de uma cabeça de aproximadamente 38,6 milhões de pesos/bias, não de todo o modelo nem uma curva de aprendizado.

## Custo e variância por configuração

| Documento / potência | Redução iid | Mistura: custo x variância / original | Enumeração: custo x variância / original |
|---|---:|---:|---:|
| prefixItems.json / 1 | 31.09% | 0.7449 | 0.3824 |
| prefixItems.json / 2 | 31.65% | 0.7361 | 0.3755 |
| additionalProperties.json / 1 | 36.74% | 0.6820 | 0.2678 |
| additionalProperties.json / 2 | 32.11% | 0.7368 | 0.3630 |
| dependentRequired.json / 1 | 29.79% | 0.7424 | 0.4073 |
| dependentRequired.json / 2 | 35.78% | 0.6905 | 0.2876 |
| ref.json / 1 | 39.64% | 0.6638 | 0.2142 |
| ref.json / 2 | 35.26% | 0.7223 | 0.3571 |
| uniqueItems.json / 1 | 40.06% | 0.6441 | 0.2068 |
| uniqueItems.json / 2 | 39.91% | 0.6435 | 0.2900 |
| unevaluatedProperties.json / 1 | 11.61% | 0.8931 | 0.7692 |
| unevaluatedProperties.json / 2 | 8.75% | 0.9305 | 0.8288 |

## Posterior auditado em lote

A campanha contém todos os nove inputs originais: oito compilam, gerando 48 eventos x 13 métodos x três repetições. Foram registrados 1,559,311 draws aceitos e 1518/1872 consultas completas de 1024 draws; a compilação recusada permanece inconclusiva. A mistura vence todos os controles concluídos em tempo de parede e CPU em 3/48 eventos pelas medianas. Em 0/48 eventos há redução mediana de pelo menos 20% em CPU e wall contra todos os controles concluídos, com sinal favorável nas três repetições. Esse critério foi declarado antes da nova rodada fortalecida; aplicá-lo às rodadas anteriores é análise exploratória. Pequenas diferenças na máquina compartilhada não provam superioridade robusta.

A consulta acima presume circuito disponível e inclui toda preparação do sampler. O JSON também fornece custos frios, cobrando compilação dos métodos por floresta e dispensando-a da enumeração JSON independente. Há 0/48 ganhos de pelo menos 20% nesse custo frio contra todos os controles concluídos. A medição comum de compilação inclui a preparação da proposta original, portanto esse valor frio é um teto conservador para o trabalho necessário do circuito.

| Método | Status das 144 consultas |
|---|---|
| mixture | {"complete": 144} |
| base | {"complete": 135, "unresolved": 9} |
| single | {"complete": 144} |
| enumeration | {"complete": 78, "not_applicable": 60, "unresolved": 6} |
| profiles | {"complete": 102, "unresolved": 42} |
| profiles_coarse2 | {"complete": 105, "unresolved": 39} |
| profiles_coarse4 | {"complete": 114, "unresolved": 30} |
| profiles_indexed1 | {"complete": 105, "unresolved": 39} |
| profiles_indexed2 | {"complete": 117, "unresolved": 27} |
| profiles_indexed4 | {"complete": 120, "unresolved": 24} |
| profiles_roomy1 | {"complete": 114, "unresolved": 30} |
| profiles_roomy2 | {"complete": 120, "unresolved": 24} |
| profiles_roomy4 | {"complete": 120, "unresolved": 24} |

Desenho temporal: Same events/seeds/repetition IDs across sequential campaigns; not simultaneous paired timings. Os controles por índices conservam a mesma lei
e são engenharia do comparador; não são apresentados como descoberta do TCC.
O estudo neural também foi comparado ao piso de sobrecusto zero de qualquer
sampler com uma réplica iid; a média condicional continua melhor nas 12
configurações e nos quatro escopos de custo, sem inventar timings neurais
para a representação por índices.

Eventos que satisfazem a comparação de medianas; os valores por repetição mostram a estabilidade, não são um intervalo de confiança:

{"case": "json-context0-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 1.197192547109542, "cpu_ratio": 1.197173125476362, "cold_wall_ratio": 1.135652143037211, "cold_cpu_ratio": 1.1356362078153872, "wall_ratios": [1.1933343701215382, 1.197192547109542, 1.1827749211114893], "cpu_ratios": [1.1933438976161959, 1.197173125476362, 1.1828182509042366], "cold_wall_ratios": [1.1354428935603538, 1.135652143037211, 1.125389939533836], "cold_cpu_ratios": [1.1354490822667227, 1.1356362078153872, 1.1254166981059837]}}}

{"case": "json-context1-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.0566540582553297, "cpu_ratio": 1.0567649075562424, "cold_wall_ratio": 1.0453401667193891, "cold_cpu_ratio": 1.0454280533765778, "wall_ratios": [1.0679925786744622, 1.0690131911992173, 1.026341225813638], "cpu_ratios": [1.0686487167221135, 1.0690906771341206, 1.0264392676341003], "cold_wall_ratios": [1.0542980134589943, 1.05527350518348, 1.0210808476349718], "cold_cpu_ratios": [1.0548153672969582, 1.0553349240937602, 1.021158925699465]}}}

{"case": "json-context2-8", "power": 2, "k": 1, "paired": {"base": {"wall_ratio": 1.12557035732105, "cpu_ratio": 1.1254202968186346, "cold_wall_ratio": 1.0622069011400839, "cold_cpu_ratio": 1.0621340489363291, "wall_ratios": [1.002297927705401, 1.1284130345693626, 1.010014072759784], "cpu_ratios": [1.004709841028393, 1.1283404599589626, 1.0099114366106885], "cold_wall_ratios": [1.0012485514940301, 1.063534180524205, 1.004960919499375], "cold_cpu_ratios": [1.002556251155076, 1.0634975807983902, 1.0049101915959295]}, "single": {"wall_ratio": 1.2064265487546817, "cpu_ratio": 1.206215621276542, "cold_wall_ratio": 1.1022626373375666, "cold_cpu_ratio": 1.1021605898633822, "wall_ratios": [0.9998644984235033, 1.209473431856745, 0.9890439496281229], "cpu_ratios": [1.0022728988530987, 1.2093454265648387, 0.9891249180291753], "cold_wall_ratios": [0.9999263768414556, 1.103639968319746, 0.9945724296967109], "cold_cpu_ratios": [1.0012336085833002, 1.1035755064484325, 0.9946124120855899]}, "profiles_indexed2": {"wall_ratio": 19.039762372429653, "cpu_ratio": 19.03916888878359, "cold_wall_ratio": 9.906759192440983, "cold_cpu_ratio": 9.906667683855256, "wall_ratios": [15.710354661375735, 19.4281596379718, 18.17953553621166], "cpu_ratios": [15.748085800574732, 19.428513859987802, 18.178978065180416], "cold_wall_ratios": [8.965504485241036, 10.08751214624594, 9.480607297198354], "cold_cpu_ratios": [8.977239734082222, 10.087575564433287, 9.480523430619844]}, "profiles_indexed4": {"wall_ratio": 10.515561389230003, "cpu_ratio": 10.514929184163616, "cold_wall_ratio": 5.683914413044824, "cold_cpu_ratio": 5.683702658363752, "wall_ratios": [9.440192068371367, 10.542118900202079, 10.129213950020857], "cpu_ratios": [9.45984281319291, 10.542212598825278, 10.128763822020808], "cold_wall_ratios": [5.558686744670848, 5.69101674161513, 5.49251990346992], "cold_cpu_ratios": [5.564315963833834, 5.690999204102891, 5.492393770428387]}, "profiles_roomy2": {"wall_ratio": 19.906172498287308, "cpu_ratio": 19.904692390810524, "cold_wall_ratio": 10.38268708565784, "cold_cpu_ratio": 10.382160310959511, "wall_ratios": [16.425259085768193, 20.084108031440053, 18.916982476815022], "cpu_ratios": [16.46399616682838, 20.080893730539728, 18.916084925956792], "cold_wall_ratios": [9.396213819989255, 10.458823168742924, 9.892647499984314], "cold_cpu_ratios": [9.408122392260003, 10.457112781044103, 9.892397599834148]}, "profiles_roomy4": {"wall_ratio": 11.016090464488785, "cpu_ratio": 11.014759121199049, "cold_wall_ratio": 5.978586739030619, "cold_cpu_ratio": 5.978028261953942, "wall_ratios": [9.089750428268252, 11.224143293138523, 10.510415474262622], "cpu_ratios": [9.110763853536476, 11.22362776021422, 10.509210011109758], "cold_wall_ratios": [5.410553056046831, 6.075229236794516, 5.7280779820507695], "cold_cpu_ratios": [5.417179071438763, 6.074901888365277, 5.727575871529217]}}}

## O que se pode afirmar

A operação é útil para estimar gradientes/estatísticas condicionais mantendo a política do passo. A identidade de covariância prova a redução de variância para a distribuição especificada; o experimento externo mostra essa redução em parâmetros reais e contabiliza custos. Isso não prova melhor acerto, velocidade de inferência ou convergência de um modelo treinado.

A contribuição candidata específica da mistura continua a garantia de condicionamento iid com custo esperado polinomial em um circuito racional, e a separação escrita contra qualquer proposta produto única. O [corolário de auditoria](conditional-audit-corollary.md) explica um uso sem a proposta descartada original e uma garantia de precisão. Não é superioridade sobre todos os algoritmos: agregação de somas, enumeração e MCMC com hipóteses adequadas continuam alternativas.

A [obstrução em bits do normalizador](normalizer-bit-obstruction.md) prova que, mesmo com taxas de confiança q em [1/4,3/4], escrever a fração exata de um evento PL pode exigir tamanho exponencial, embora amostrar seja polinomial. A rejeição simples também resolve essa família; o resultado justifica dispensar o normalizador na operação, sem atribuir exclusividade à mistura.

O controle MH estacionário, incluindo a moeda integrada, preserva a média e reduz variância sem exigir réplicas independentes. É clássico; não foi rebatizado como novidade. A alternativa exponencial de Caron-Doucet foi derivada, mas sua versão contínua exata não foi implementada: MH fornece o controle racional executável, sem inventar tempos para Gibbs.

Os tempos foram medidos sob carga concorrente, com clocks de processo e três repetições. O JSON publica também custos frios/reutilizados, CPU, recusas e amplitudes; não há intervalo de confiança de convergência ou promessa de 100% de ganho físico. Recursos recusados e a campanha bulk v1 interrompida estão preservados. Os contadores de tentativas de consultas interrompidas cobrem somente os draws aceitos registrados; o custo de todo o trabalho perdido entra no tempo medido.

EPIC é um decoder e não resolve esta operação de posterior PL/gradiente. Este relatório não anuncia superioridade sobre EPIC. A pesquisa de prioridade e a revisão humana permanecem pendentes; resultados positivos de gradiente não encerram o requisito de novidade para publicação.
