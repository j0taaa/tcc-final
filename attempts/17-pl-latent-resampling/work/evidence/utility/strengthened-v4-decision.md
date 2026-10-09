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

A campanha contém todos os nove inputs originais: oito compilam, gerando 48 eventos x 5 métodos x três repetições. Foram registrados 2,467,716 draws aceitos e 597/720 consultas completas de 4096 draws; a compilação recusada permanece inconclusiva. A mistura vence todos os controles concluídos em tempo de parede e CPU em 7/48 eventos pelas medianas. Em 4/48 eventos há redução mediana de pelo menos 20% em CPU e wall contra todos os controles concluídos, com sinal favorável nas três repetições. Esse critério foi declarado antes da nova rodada fortalecida; aplicá-lo às rodadas anteriores é análise exploratória. Pequenas diferenças na máquina compartilhada não provam superioridade robusta.

A consulta acima presume circuito disponível e inclui toda preparação do sampler. O JSON também fornece custos frios, cobrando compilação dos métodos por floresta e dispensando-a da enumeração JSON independente. Há 4/48 ganhos de pelo menos 20% nesse custo frio contra todos os controles concluídos. A medição comum de compilação inclui a preparação da proposta original, portanto esse valor frio é um teto conservador para o trabalho necessário do circuito.

| Método | Status das 144 consultas |
|---|---|
| mixture | {"complete": 144} |
| base | {"complete": 129, "unresolved": 15} |
| single | {"complete": 144} |
| enumeration | {"complete": 78, "not_applicable": 60, "unresolved": 6} |
| profiles | {"complete": 102, "unresolved": 42} |

Eventos que satisfazem a comparação de medianas; os valores por repetição mostram a estabilidade, não são um intervalo de confiança:

{"case": "json-context0-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 2.4869890574411917, "cpu_ratio": 2.487103718470748, "cold_wall_ratio": 2.163098975327231, "cold_cpu_ratio": 2.163574218571251, "wall_ratios": [2.4941537689885593, 2.44281153533379, 2.607700312923661], "cpu_ratios": [2.4942346987981043, 2.443785266842423, 2.608409995093539]}}}

{"case": "json-context0-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.0924762791932237, "cpu_ratio": 1.0926303208636607, "cold_wall_ratio": 1.0817436565666467, "cold_cpu_ratio": 1.0818931702732901, "wall_ratios": [1.084186832308972, 1.0705635810521485, 1.09817691114851], "cpu_ratios": [1.084311662340607, 1.0706334556216346, 1.0983132418357187]}}}

{"case": "json-context1-16", "power": 1, "k": 8, "paired": {"single": {"wall_ratio": 1.3690297062347327, "cpu_ratio": 1.369162312402226, "cold_wall_ratio": 1.2836359711955314, "cold_cpu_ratio": 1.2837372713074988, "wall_ratios": [1.3142644135980646, 1.3454242448726168, 1.3690297062347327], "cpu_ratios": [1.3143159512818705, 1.345978094490138, 1.369162312402226]}}}

{"case": "json-context1-16", "power": 2, "k": 1, "paired": {"base": {"wall_ratio": 1.5124075820532668, "cpu_ratio": 1.512706265441783, "cold_wall_ratio": 1.4330597811786434, "cold_cpu_ratio": 1.4332985560983882, "wall_ratios": [1.4309866476780715, 1.4915903990476775, 1.5124075820532668], "cpu_ratios": [1.4304711317555667, 1.490991220008027, 1.512706265441783]}, "single": {"wall_ratio": 1.0076658376389174, "cpu_ratio": 1.0078687968898785, "cold_wall_ratio": 1.0064787604374588, "cold_cpu_ratio": 1.0066500812656891, "wall_ratios": [0.982340730245451, 1.008210249868898, 0.9806189314697817], "cpu_ratios": [0.9823315820885901, 1.008226952999243, 0.9808493023484286]}}}

{"case": "json-context1-16", "power": 2, "k": 8, "paired": {"single": {"wall_ratio": 1.842259942296621, "cpu_ratio": 1.842221735665912, "cold_wall_ratio": 1.7564790836582265, "cold_cpu_ratio": 1.75644487193313, "wall_ratios": [1.8599725302918768, 1.842259942296621, 1.752160996706971], "cpu_ratios": [1.8600486849204854, 1.842221735665912, 1.7520506332744528]}}}

{"case": "json-context2-4", "power": 2, "k": 2, "paired": {"base": {"wall_ratio": 6.2485157230382855, "cpu_ratio": 6.248530086160216, "cold_wall_ratio": 4.8318839740329835, "cold_cpu_ratio": 4.831809538379087, "wall_ratios": [6.468315761322648, 6.206507686994116, 6.1011623202576235], "cpu_ratios": [6.4680743097378475, 6.207379776611627, 6.101339572802354]}, "single": {"wall_ratio": 1.9604422460882078, "cpu_ratio": 1.96042813351827, "cold_wall_ratio": 1.7012083882334594, "cold_cpu_ratio": 1.7011825449276066, "wall_ratios": [1.9730443094738064, 1.9490277976361465, 1.9604422460882078], "cpu_ratios": [1.9729468352975013, 1.9493096300977872, 1.96042813351827]}, "enumeration": {"wall_ratio": 4.067201227024768, "cpu_ratio": 4.067343169452239, "cold_wall_ratio": 2.96941916980322, "cold_cpu_ratio": 2.9694569901894554, "wall_ratios": [4.1389549463099895, 4.0560101556806885, 4.048051348697221], "cpu_ratios": [4.138778362259296, 4.056682717341239, 4.0481718083449]}, "profiles": {"wall_ratio": 1.4508139667335522, "cpu_ratio": 1.450878482889847, "cold_wall_ratio": 1.3291343506534326, "cold_cpu_ratio": 1.329174157911928, "wall_ratios": [1.4662631022044053, 1.4481387597172122, 1.4508139667335522], "cpu_ratios": [1.4662610448688942, 1.4462275989276796, 1.450878482889847]}}}

{"case": "json-context2-8", "power": 2, "k": 1, "paired": {"base": {"wall_ratio": 1.093207444156669, "cpu_ratio": 1.093267514250993, "cold_wall_ratio": 1.0524758618514307, "cold_cpu_ratio": 1.0525085441944115, "wall_ratios": [1.0320059156284105, 1.0148657254077147, 1.1118833083579047], "cpu_ratios": [1.0320325646874635, 1.014853966883006, 1.112000614875805]}, "single": {"wall_ratio": 1.0297108805107766, "cpu_ratio": 1.0297687359772545, "cold_wall_ratio": 1.0167272482930358, "cold_cpu_ratio": 1.0167594580087869, "wall_ratios": [0.9120110776485599, 1.0321725535419333, 1.047301997982346], "cpu_ratios": [0.9120530258687449, 1.03207514178121, 1.0473086937712632]}}}

## O que se pode afirmar

A operação é útil para estimar gradientes/estatísticas condicionais mantendo a política do passo. A identidade de covariância prova a redução de variância para a distribuição especificada; o experimento externo mostra essa redução em parâmetros reais e contabiliza custos. Isso não prova melhor acerto, velocidade de inferência ou convergência de um modelo treinado.

A contribuição candidata específica da mistura continua a garantia de condicionamento iid com custo esperado polinomial em um circuito racional, e a separação escrita contra qualquer proposta produto única. O [corolário de auditoria](conditional-audit-corollary.md) explica um uso sem a proposta descartada original e uma garantia de precisão. Não é superioridade sobre todos os algoritmos: agregação de somas, enumeração e MCMC com hipóteses adequadas continuam alternativas.

A [obstrução em bits do normalizador](normalizer-bit-obstruction.md) prova que, mesmo com taxas de confiança q em [1/4,3/4], escrever a fração exata de um evento PL pode exigir tamanho exponencial, embora amostrar seja polinomial. A rejeição simples também resolve essa família; o resultado justifica dispensar o normalizador na operação, sem atribuir exclusividade à mistura.

O controle MH estacionário, incluindo a moeda integrada, preserva a média e reduz variância sem exigir réplicas independentes. É clássico; não foi rebatizado como novidade. A alternativa exponencial de Caron-Doucet foi derivada, mas sua versão contínua exata não foi implementada: MH fornece o controle racional executável, sem inventar tempos para Gibbs.

Os tempos foram medidos sob carga concorrente, com clocks de processo e três repetições. O JSON publica também custos frios/reutilizados, CPU, recusas e amplitudes; não há intervalo de confiança de convergência ou promessa de 100% de ganho físico. Recursos recusados e a campanha bulk v1 interrompida estão preservados. Os contadores de tentativas de consultas interrompidas cobrem somente os draws aceitos registrados; o custo de todo o trabalho perdido entra no tempo medido.

EPIC é um decoder e não resolve esta operação de posterior PL/gradiente. Este relatório não anuncia superioridade sobre EPIC. A pesquisa de prioridade e a revisão humana permanecem pendentes; resultados positivos de gradiente não encerram o requisito de novidade para publicação.
