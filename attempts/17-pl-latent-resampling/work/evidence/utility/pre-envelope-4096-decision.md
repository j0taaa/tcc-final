# Decisão de utilidade: reamostragem latente PL

Há benefício na redução de variância do gradiente, mas isso não estabelece que a mistura seja a melhor solução. Novidade e melhora da geração final não foram confirmadas.

Os seis documentos externos foram selecionados por hash antes dos forwards, sem injetar gabarito. Nas 12 configurações, uma réplica iid reduz a variância da cabeça real entre 8.75% e 40.06%. A razão custo x variância contra o original, usando o piso forte de custo neural, fica entre 0.6355 e 0.9299 nas medianas de três repetições; abaixo de 1 favorece reamostrar.

A enumeração com média condicional exata é a melhor dessas alternativas em 12/12 configurações. Ela é um controle competente: o alvo por evento tem poucas alternativas. A mistura não deve ser escolhida aí só porque a sua correção é mais geral.

A geometria foi recalculada offline por outro programa nos 12 casos. O erro máximo na checagem de norma contra autograd é 9.98e-08; o da derivada contra diferenças finitas é 1.44e-11. São testes numéricos de uma cabeça de aproximadamente 38,6 milhões de pesos/bias, não de todo o modelo nem uma curva de aprendizado.

## Custo e variância por configuração

| Documento / potência | Redução iid | Mistura: custo x variância / original | Enumeração: custo x variância / original |
|---|---:|---:|---:|
| prefixItems.json / 1 | 31.09% | 0.7393 | 0.3821 |
| prefixItems.json / 2 | 31.65% | 0.7286 | 0.3742 |
| additionalProperties.json / 1 | 36.74% | 0.6730 | 0.2677 |
| additionalProperties.json / 2 | 32.11% | 0.7307 | 0.3631 |
| dependentRequired.json / 1 | 29.79% | 0.7416 | 0.4073 |
| dependentRequired.json / 2 | 35.78% | 0.6836 | 0.2877 |
| ref.json / 1 | 39.64% | 0.6644 | 0.2138 |
| ref.json / 2 | 35.26% | 0.7213 | 0.3357 |
| uniqueItems.json / 1 | 40.06% | 0.6355 | 0.2051 |
| uniqueItems.json / 2 | 39.91% | 0.6358 | 0.2781 |
| unevaluatedProperties.json / 1 | 11.61% | 0.8926 | 0.7691 |
| unevaluatedProperties.json / 2 | 8.75% | 0.9299 | 0.8287 |

## Posterior auditado em lote

A campanha contém todos os nove inputs originais: oito compilam, gerando 48 eventos x 4 métodos x três repetições. Foram registrados 2,043,932 draws aceitos e 489/576 consultas completas de 4096 draws; a compilação recusada permanece inconclusiva. A mistura vence todos os controles concluídos em tempo de parede e CPU em 1/48 eventos pelas medianas. Em 0/48 eventos há redução mediana de pelo menos 20% em CPU e wall contra todos os controles concluídos, com sinal favorável nas três repetições. Esse critério foi declarado antes da nova rodada fortalecida; aplicá-lo às rodadas anteriores é análise exploratória. Pequenas diferenças na máquina compartilhada não provam superioridade robusta.

A consulta acima presume circuito disponível e inclui toda preparação do sampler. O JSON também fornece custos frios, cobrando compilação dos métodos por floresta e dispensando-a da enumeração JSON independente. Há 0/48 ganhos de pelo menos 20% nesse custo frio contra todos os controles concluídos. A medição comum de compilação inclui a preparação da proposta original, portanto esse valor frio é um teto conservador para o trabalho necessário do circuito.

| Método | Status das 144 consultas |
|---|---|
| mixture | {"complete": 138, "unresolved": 6} |
| base | {"complete": 129, "unresolved": 15} |
| single | {"complete": 144} |
| enumeration | {"complete": 78, "not_applicable": 60, "unresolved": 6} |

Eventos que satisfazem a comparação de medianas; os valores por repetição mostram a estabilidade, não são um intervalo de confiança:

{"case": "json-context0-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 1.2354896249963756, "cpu_ratio": 1.235402786101448, "cold_wall_ratio": 1.2074387931224466, "cold_cpu_ratio": 1.2073626308720224, "wall_ratios": [1.2879297252134854, 1.234014696117603, 1.2321110466553917], "cpu_ratios": [1.2881640098008782, 1.2339448361007597, 1.2320906878461722]}}}

## O que se pode afirmar

A operação é útil para estimar gradientes/estatísticas condicionais mantendo a política do passo. A identidade de covariância prova a redução de variância para a distribuição especificada; o experimento externo mostra essa redução em parâmetros reais e contabiliza custos. Isso não prova melhor acerto, velocidade de inferência ou convergência de um modelo treinado.

A contribuição candidata específica da mistura continua a garantia de condicionamento iid com custo esperado polinomial em um circuito racional, e a separação escrita contra qualquer proposta produto única. O [corolário de auditoria](conditional-audit-corollary.md) explica um uso sem a proposta descartada original e uma garantia de precisão. Não é superioridade sobre todos os algoritmos: agregação de somas, enumeração e MCMC com hipóteses adequadas continuam alternativas.

A [obstrução em bits do normalizador](normalizer-bit-obstruction.md) prova que, mesmo com taxas de confiança q em [1/4,3/4], escrever a fração exata de um evento PL pode exigir tamanho exponencial, embora amostrar seja polinomial. A rejeição simples também resolve essa família; o resultado justifica dispensar o normalizador na operação, sem atribuir exclusividade à mistura.

O controle MH estacionário, incluindo a moeda integrada, preserva a média e reduz variância sem exigir réplicas independentes. É clássico; não foi rebatizado como novidade. A alternativa exponencial de Caron-Doucet foi derivada, mas sua versão contínua exata não foi implementada: MH fornece o controle racional executável, sem inventar tempos para Gibbs.

Os tempos foram medidos sob carga concorrente, com clocks de processo e três repetições. O JSON publica também custos frios/reutilizados, CPU, recusas e amplitudes; não há intervalo de confiança de convergência ou promessa de 100% de ganho físico. Recursos recusados e a campanha bulk v1 interrompida estão preservados. Os contadores de tentativas de consultas interrompidas cobrem somente os draws aceitos registrados; o custo de todo o trabalho perdido entra no tempo medido.

EPIC é um decoder e não resolve esta operação de posterior PL/gradiente. Este relatório não anuncia superioridade sobre EPIC. A pesquisa de prioridade e a revisão humana permanecem pendentes; resultados positivos de gradiente não encerram o requisito de novidade para publicação.
