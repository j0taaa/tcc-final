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

A campanha contém todos os nove inputs originais: oito compilam, gerando 48 eventos x 13 métodos x três repetições. Foram registrados 6,215,868 draws aceitos e 1512/1872 consultas completas de 4096 draws; a compilação recusada permanece inconclusiva. A mistura vence todos os controles concluídos em tempo de parede e CPU em 5/48 eventos pelas medianas. Em 3/48 eventos há redução mediana de pelo menos 20% em CPU e wall contra todos os controles concluídos, com sinal favorável nas três repetições. Esse critério foi declarado antes da nova rodada fortalecida; aplicá-lo às rodadas anteriores é análise exploratória. Pequenas diferenças na máquina compartilhada não provam superioridade robusta.

A consulta acima presume circuito disponível e inclui toda preparação do sampler. O JSON também fornece custos frios, cobrando compilação dos métodos por floresta e dispensando-a da enumeração JSON independente. Há 2/48 ganhos de pelo menos 20% nesse custo frio contra todos os controles concluídos. A medição comum de compilação inclui a preparação da proposta original, portanto esse valor frio é um teto conservador para o trabalho necessário do circuito.

| Método | Status das 144 consultas |
|---|---|
| mixture | {"complete": 144} |
| base | {"complete": 129, "unresolved": 15} |
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

{"case": "json-context0-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 2.469317748766204, "cpu_ratio": 2.469365208602252, "cold_wall_ratio": 2.1496476421914417, "cold_cpu_ratio": 2.149676464503069, "wall_ratios": [2.3983734462050315, 2.469317748766204, 2.429755486500546], "cpu_ratios": [2.398413949131878, 2.469365208602252, 2.429839919413149], "cold_wall_ratios": [2.104457683674095, 2.1496476421914417, 2.118255424019563], "cold_cpu_ratios": [2.104488564379801, 2.149676464503069, 2.1183113134636193]}}}

{"case": "json-context0-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.0924795025024767, "cpu_ratio": 1.0923678624359654, "cold_wall_ratio": 1.082056220322444, "cold_cpu_ratio": 1.081957169660605, "wall_ratios": [1.0743693160770247, 1.0943464499489797, 1.1030119297889975], "cpu_ratios": [1.0744405872316214, 1.0942785254945422, 1.103062862263336], "cold_wall_ratios": [1.065987216843888, 1.0837227870255948, 1.0913023369875101], "cold_cpu_ratios": [1.0660504603709604, 1.0836623985803535, 1.0913459465127555]}}}

{"case": "json-context1-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 1.3078301726536066, "cpu_ratio": 1.3078918700364663, "cold_wall_ratio": 1.2326749320459724, "cold_cpu_ratio": 1.2327179256055436, "wall_ratios": [1.375316148116068, 1.3053830590648798, 1.2900824587244766], "cpu_ratios": [1.374773607608065, 1.305461369959137, 1.2901795660812316], "cold_wall_ratios": [1.2835400804759738, 1.230930764535655, 1.2192602362192628], "cold_cpu_ratios": [1.283130132165556, 1.2309856530650687, 1.2193302040211156]}}}

{"case": "json-context1-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.806034100876175, "cpu_ratio": 1.8058303774594326, "cold_wall_ratio": 1.7200487948088856, "cold_cpu_ratio": 1.7198644468764248, "wall_ratios": [1.797944785765632, 1.7959975206839687, 1.8179917607034293], "cpu_ratios": [1.7981568142147963, 1.7959274502217968, 1.8183097100723482], "cold_wall_ratios": [1.713163181225859, 1.7110828869601415, 1.7302892268976848], "cold_cpu_ratios": [1.7133328653913376, 1.7110179632518518, 1.7305609427110717]}}}

{"case": "json-context2-8", "power": 2, "k": 1, "paired": {"base": {"wall_ratio": 1.1178308693169103, "cpu_ratio": 1.1174999625256246, "cold_wall_ratio": 1.0656424225134753, "cold_cpu_ratio": 1.0654593415859384, "wall_ratios": [1.024785042255513, 1.1237012925472043, 1.0264312532296498], "cpu_ratios": [1.0267710669865084, 1.1234588456180044, 1.0263556749074407], "cold_wall_ratios": [1.0147158472046802, 1.0687528590200672, 1.0147245921388814], "cold_cpu_ratios": [1.015882697035104, 1.0686169893015995, 1.0146827717167812]}, "single": {"wall_ratio": 1.1371402399879156, "cpu_ratio": 1.1369961325304188, "cold_wall_ratio": 1.07639948367583, "cold_cpu_ratio": 1.0763206765560072, "wall_ratios": [0.9827069196396725, 1.1431120687002558, 0.9681383005411126], "cpu_ratios": [0.9846073956461872, 1.1430589757138085, 0.968125717177381], "cold_wall_ratios": [0.9897324230615653, 1.0795413182903015, 0.982250159487048], "cold_cpu_ratios": [0.9908678996001153, 1.0795105134582648, 0.9822428065316395]}, "profiles_indexed2": {"wall_ratio": 15.21731995086016, "cpu_ratio": 15.216911446560568, "cold_wall_ratio": 8.893957922088003, "cold_cpu_ratio": 8.893873324890412, "wall_ratios": [13.096579514167713, 15.567400457837167, 14.543262825441024], "cpu_ratios": [13.1218265497091, 15.567954819131723, 14.542917830541331], "cold_wall_ratios": [8.158021966110134, 9.07007490110635, 8.518447303508264], "cold_cpu_ratios": [8.167391717923243, 9.070239878316315, 8.518390836305588]}, "profiles_indexed4": {"wall_ratio": 8.570280679442668, "cpu_ratio": 8.569846995616468, "cold_wall_ratio": 5.190957487248378, "cold_cpu_ratio": 5.1907873571548295, "wall_ratios": [7.998080135128826, 8.61528853901402, 8.269148499558895], "cpu_ratios": [8.011067145063286, 8.615544282488, 8.268766023372498], "cold_wall_ratios": [5.130843837398086, 5.206109045905756, 5.023199701033882], "cold_cpu_ratios": [5.135288317479565, 5.206171029906157, 5.023054859343638]}, "profiles_roomy2": {"wall_ratio": 15.89711921800871, "cpu_ratio": 15.89595665515922, "cold_wall_ratio": 9.313668929830875, "cold_cpu_ratio": 9.313165997504273, "wall_ratios": [13.68163951058191, 16.081789550358927, 15.122170927163637], "cpu_ratios": [13.707379897898987, 16.079480138842932, 15.121559765308767], "cold_wall_ratios": [8.543003731324143, 9.39709220562651, 8.881952831760406], "cold_cpu_ratios": [8.55243514912531, 9.395657131268244, 8.881748748968946]}, "profiles_roomy4": {"wall_ratio": 8.964902715580687, "cpu_ratio": 8.963816042137218, "cold_wall_ratio": 5.451799054430059, "cold_cpu_ratio": 5.451263827019722, "wall_ratios": [7.71552163130696, 9.150862008391094, 8.568366330163194], "cpu_ratios": [7.729665756516585, 9.15065367447266, 8.567456280522252], "cold_wall_ratios": [5.000686626862007, 5.544900572387303, 5.230892520306698], "cold_cpu_ratios": [5.005986189213464, 5.54469603570297, 5.23045142445562]}}}

## O que se pode afirmar

A operação é útil para estimar gradientes/estatísticas condicionais mantendo a política do passo. A identidade de covariância prova a redução de variância para a distribuição especificada; o experimento externo mostra essa redução em parâmetros reais e contabiliza custos. Isso não prova melhor acerto, velocidade de inferência ou convergência de um modelo treinado.

A contribuição candidata específica da mistura continua a garantia de condicionamento iid com custo esperado polinomial em um circuito racional, e a separação escrita contra qualquer proposta produto única. O [corolário de auditoria](conditional-audit-corollary.md) explica um uso sem a proposta descartada original e uma garantia de precisão. Não é superioridade sobre todos os algoritmos: agregação de somas, enumeração e MCMC com hipóteses adequadas continuam alternativas.

A [obstrução em bits do normalizador](normalizer-bit-obstruction.md) prova que, mesmo com taxas de confiança q em [1/4,3/4], escrever a fração exata de um evento PL pode exigir tamanho exponencial, embora amostrar seja polinomial. A rejeição simples também resolve essa família; o resultado justifica dispensar o normalizador na operação, sem atribuir exclusividade à mistura.

O controle MH estacionário, incluindo a moeda integrada, preserva a média e reduz variância sem exigir réplicas independentes. É clássico; não foi rebatizado como novidade. A alternativa exponencial de Caron-Doucet foi derivada, mas sua versão contínua exata não foi implementada: MH fornece o controle racional executável, sem inventar tempos para Gibbs.

Os tempos foram medidos sob carga concorrente, com clocks de processo e três repetições. O JSON publica também custos frios/reutilizados, CPU, recusas e amplitudes; não há intervalo de confiança de convergência ou promessa de 100% de ganho físico. Recursos recusados e a campanha bulk v1 interrompida estão preservados. Os contadores de tentativas de consultas interrompidas cobrem somente os draws aceitos registrados; o custo de todo o trabalho perdido entra no tempo medido.

EPIC é um decoder e não resolve esta operação de posterior PL/gradiente. Este relatório não anuncia superioridade sobre EPIC. A pesquisa de prioridade e a revisão humana permanecem pendentes; resultados positivos de gradiente não encerram o requisito de novidade para publicação.
