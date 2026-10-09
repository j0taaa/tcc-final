# Decisão de utilidade: reamostragem latente PL

Há benefício na redução de variância do gradiente, mas isso não estabelece que a mistura seja a melhor solução. Novidade e melhora da geração final não foram confirmadas.

Os seis documentos externos foram selecionados por hash antes dos forwards, sem injetar gabarito. Nas 12 configurações, uma réplica iid reduz a variância da cabeça real entre 8.75% e 40.06%. A razão custo x variância contra o original, usando o piso forte de custo neural, fica entre 0.6428 e 0.9301 nas medianas de três repetições; abaixo de 1 favorece reamostrar.

A enumeração com média condicional exata é a melhor dessas alternativas em 12/12 configurações. Ela é um controle competente: o alvo por evento tem poucas alternativas. A mistura não deve ser escolhida aí só porque a sua correção é mais geral.

A geometria foi recalculada offline por outro programa nos 12 casos. O erro máximo na checagem de norma contra autograd é 9.98e-08; o da derivada contra diferenças finitas é 1.44e-11. São testes numéricos de uma cabeça de aproximadamente 38,6 milhões de pesos/bias, não de todo o modelo nem uma curva de aprendizado.

## Custo e variância por configuração

| Documento / potência | Redução iid | Mistura: custo x variância / original | Enumeração: custo x variância / original |
|---|---:|---:|---:|
| prefixItems.json / 1 | 31.09% | 0.7434 | 0.3824 |
| prefixItems.json / 2 | 31.65% | 0.7353 | 0.3756 |
| additionalProperties.json / 1 | 36.74% | 0.6813 | 0.2679 |
| additionalProperties.json / 2 | 32.11% | 0.7724 | 0.3630 |
| dependentRequired.json / 1 | 29.79% | 0.7423 | 0.4071 |
| dependentRequired.json / 2 | 35.78% | 0.6889 | 0.2876 |
| ref.json / 1 | 39.64% | 0.6662 | 0.2145 |
| ref.json / 2 | 35.26% | 0.7197 | 0.3566 |
| uniqueItems.json / 1 | 40.06% | 0.6433 | 0.2068 |
| uniqueItems.json / 2 | 39.91% | 0.6428 | 0.2904 |
| unevaluatedProperties.json / 1 | 11.61% | 0.8929 | 0.7692 |
| unevaluatedProperties.json / 2 | 8.75% | 0.9301 | 0.8288 |

## Posterior auditado em lote

A campanha contém todos os nove inputs originais: oito compilam, gerando 48 eventos x 5 métodos x três repetições. Foram registrados 622,110 draws aceitos e 603/720 consultas completas de 1024 draws; a compilação recusada permanece inconclusiva. A mistura vence todos os controles concluídos em tempo de parede e CPU em 4/48 eventos pelas medianas. Em 0/48 eventos há redução mediana de pelo menos 20% em CPU e wall contra todos os controles concluídos, com sinal favorável nas três repetições. Esse critério foi declarado antes da nova rodada fortalecida; aplicá-lo às rodadas anteriores é análise exploratória. Pequenas diferenças na máquina compartilhada não provam superioridade robusta.

A consulta acima presume circuito disponível e inclui toda preparação do sampler. O JSON também fornece custos frios, cobrando compilação dos métodos por floresta e dispensando-a da enumeração JSON independente. Há 0/48 ganhos de pelo menos 20% nesse custo frio contra todos os controles concluídos. A medição comum de compilação inclui a preparação da proposta original, portanto esse valor frio é um teto conservador para o trabalho necessário do circuito.

| Método | Status das 144 consultas |
|---|---|
| mixture | {"complete": 144} |
| base | {"complete": 135, "unresolved": 9} |
| single | {"complete": 144} |
| enumeration | {"complete": 78, "not_applicable": 60, "unresolved": 6} |
| profiles | {"complete": 102, "unresolved": 42} |

Eventos que satisfazem a comparação de medianas; os valores por repetição mostram a estabilidade, não são um intervalo de confiança:

{"case": "json-context0-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 1.2091819757982118, "cpu_ratio": 1.2092682148993181, "cold_wall_ratio": 1.1442111484517903, "cold_cpu_ratio": 1.1443381673316955, "wall_ratios": [1.209000234855385, 1.2162851105938566, 1.3019326779554734], "cpu_ratios": [1.2090349516747483, 1.2163620553546963, 1.3025399984237265]}}}

{"case": "json-context1-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.0402040749964583, "cpu_ratio": 1.0402428675385886, "cold_wall_ratio": 1.032658183347722, "cold_cpu_ratio": 1.0326896783838062, "wall_ratios": [1.098740556100751, 1.0766784137431815, 0.9762957589392987], "cpu_ratios": [1.098766835707367, 1.0767380732246536, 0.9760513270447233]}}}

{"case": "json-context2-4", "power": 2, "k": 2, "paired": {"base": {"wall_ratio": 3.0443035589306118, "cpu_ratio": 3.0439440659110897, "cold_wall_ratio": 2.197034328262195, "cold_cpu_ratio": 2.196811212265633, "wall_ratios": [3.180268574290143, 3.0443035589306118, 2.8836609471199868], "cpu_ratios": [3.1800587788783616, 3.0439440659110897, 2.8841698008827263]}, "single": {"wall_ratio": 1.0656202784538975, "cpu_ratio": 1.0656327093256384, "cold_wall_ratio": 1.0384237094321398, "cold_cpu_ratio": 1.0384305831663165, "wall_ratios": [1.106988159186173, 1.0662151858155058, 1.0425818159259976], "cpu_ratios": [1.1069637598737747, 1.0659766405286366, 1.0427758056567868]}, "enumeration": {"wall_ratio": 6.568370662163446, "cpu_ratio": 6.568395741090592, "cold_wall_ratio": 3.8460849559313433, "cold_cpu_ratio": 3.8460590975276743, "wall_ratios": [6.814388809975317, 6.577459693955283, 6.535532917147368], "cpu_ratios": [6.814149712296748, 6.577179560534508, 6.536700962368966]}, "profiles": {"wall_ratio": 1.382574064784435, "cpu_ratio": 1.3822891782924278, "cold_wall_ratio": 1.2240148174908683, "cold_cpu_ratio": 1.223845643596049, "wall_ratios": [1.3920918167508305, 1.382574064784435, 1.3815948455176528], "cpu_ratios": [1.3921104882226503, 1.3822891782924278, 1.3817737731026496]}}}

{"case": "json-context2-8", "power": 2, "k": 1, "paired": {"base": {"wall_ratio": 1.1048306104569015, "cpu_ratio": 1.1049209694869058, "cold_wall_ratio": 1.0511325232311817, "cold_cpu_ratio": 1.051173142215274, "wall_ratios": [1.0144624972594225, 0.9958669475830909, 1.115686484843002], "cpu_ratios": [1.0145780088146925, 0.9958573870576191, 1.1154731423850726]}, "single": {"wall_ratio": 1.092050534631999, "cpu_ratio": 1.0923084358998847, "cold_wall_ratio": 1.0448988714269527, "cold_cpu_ratio": 1.0450216266688597, "wall_ratios": [0.9201011970155741, 1.0934791081783186, 1.1019018262985811], "cpu_ratios": [0.9201664736055448, 1.0936284701455201, 1.1015767185907654]}}}

## O que se pode afirmar

A operação é útil para estimar gradientes/estatísticas condicionais mantendo a política do passo. A identidade de covariância prova a redução de variância para a distribuição especificada; o experimento externo mostra essa redução em parâmetros reais e contabiliza custos. Isso não prova melhor acerto, velocidade de inferência ou convergência de um modelo treinado.

A contribuição candidata específica da mistura continua a garantia de condicionamento iid com custo esperado polinomial em um circuito racional, e a separação escrita contra qualquer proposta produto única. O [corolário de auditoria](conditional-audit-corollary.md) explica um uso sem a proposta descartada original e uma garantia de precisão. Não é superioridade sobre todos os algoritmos: agregação de somas, enumeração e MCMC com hipóteses adequadas continuam alternativas.

A [obstrução em bits do normalizador](normalizer-bit-obstruction.md) prova que, mesmo com taxas de confiança q em [1/4,3/4], escrever a fração exata de um evento PL pode exigir tamanho exponencial, embora amostrar seja polinomial. A rejeição simples também resolve essa família; o resultado justifica dispensar o normalizador na operação, sem atribuir exclusividade à mistura.

O controle MH estacionário, incluindo a moeda integrada, preserva a média e reduz variância sem exigir réplicas independentes. É clássico; não foi rebatizado como novidade. A alternativa exponencial de Caron-Doucet foi derivada, mas sua versão contínua exata não foi implementada: MH fornece o controle racional executável, sem inventar tempos para Gibbs.

Os tempos foram medidos sob carga concorrente, com clocks de processo e três repetições. O JSON publica também custos frios/reutilizados, CPU, recusas e amplitudes; não há intervalo de confiança de convergência ou promessa de 100% de ganho físico. Recursos recusados e a campanha bulk v1 interrompida estão preservados. Os contadores de tentativas de consultas interrompidas cobrem somente os draws aceitos registrados; o custo de todo o trabalho perdido entra no tempo medido.

EPIC é um decoder e não resolve esta operação de posterior PL/gradiente. Este relatório não anuncia superioridade sobre EPIC. A pesquisa de prioridade e a revisão humana permanecem pendentes; resultados positivos de gradiente não encerram o requisito de novidade para publicação.
