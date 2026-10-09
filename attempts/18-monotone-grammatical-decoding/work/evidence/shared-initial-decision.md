# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte top16 inicial permanece fixo, sem tokens de referência injetados. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável nas três repetições. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cuda

540 registros; 489 completos; 438 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

| Método | Status |
| --- | --- |
| greedy_witness | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_integer | `{"complete": 51, "infeasible_on_support": 3}` |
| greedy_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| enumeration | `{"complete": 30, "not_applicable": 24}` |
| sat_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_lex | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_lazy_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_count_warm | `{"complete": 51, "infeasible_on_support": 3}` |

| Documento / máscaras | Melhor controle completo (wall) | rust_lex (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | rust_cached_prefix | 0.076248 | 0.081097 | 1.064 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.092462 | 0.089022 | 0.963 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | rust_count_warm | 0.073863 | 0.073353 | 0.993 | não |
| 05dacb44e44c / 8 | rust_count_warm | 0.118276 | 0.130450 | 1.103 | não |
| 05dacb44e44c / 16 | monotone | 0.338353 | 0.274368 | 0.811 | não |
| 079f141a8f41 / 4 | rust_cached_prefix | 0.082652 | 0.082179 | 0.994 | não |
| 079f141a8f41 / 8 | rust_lazy_prefix | 0.123621 | 0.107857 | 0.872 | não |
| 079f141a8f41 / 16 | enumeration | 0.163869 | 0.153630 | 0.938 | não |
| 0a4b768afa25 / 4 | rust_count_warm | 0.047866 | 0.048095 | 1.005 | não |
| 0a4b768afa25 / 8 | rust_cached_prefix | 0.125600 | 0.123868 | 0.986 | não |
| 0a4b768afa25 / 16 | lex_integer | 1.714541 | 0.459590 | 0.268 | não |
| 0bb397173614 / 4 | rust_lazy_prefix | 0.101045 | 0.105392 | 1.043 | não |
| 0bb397173614 / 8 | greedy_cached_prefix | 0.190062 | 0.184743 | 0.972 | não |
| 0bb397173614 / 16 | monotone | 0.524434 | 0.377632 | 0.720 | não |
| 0ce7169f4ded / 4 | greedy_cached_prefix | 0.039131 | 0.038774 | 0.991 | não |
| 0ce7169f4ded / 8 | greedy_cached_prefix | 0.118624 | 0.115948 | 0.977 | não |
| 0ce7169f4ded / 16 | monotone | 1.431521 | 0.617313 | 0.431 | não |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
