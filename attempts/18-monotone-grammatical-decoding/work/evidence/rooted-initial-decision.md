# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte top16 inicial permanece fixo, sem tokens de referência injetados. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável nas três repetições. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cuda

864 registros; 795 completos; 744 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

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
| root_lex | `{"complete": 51, "infeasible_on_support": 3}` |
| root_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| root_lazy_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| root_count_warm | `{"complete": 51, "infeasible_on_support": 3}` |
| root_speculative | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_speculative | `{"complete": 51, "infeasible_on_support": 3}` |

| Documento / máscaras | Melhor controle completo (wall) | root_speculative (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | monotone | 0.076272 | 0.074279 | 0.974 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.094916 | 0.090059 | 0.949 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.059907 | 0.057023 | 0.952 | não |
| 05dacb44e44c / 8 | monotone | 0.098521 | 0.093396 | 0.948 | não |
| 05dacb44e44c / 16 | monotone | 0.239334 | 0.220675 | 0.922 | não |
| 079f141a8f41 / 4 | rust_lazy_prefix | 0.081077 | 0.080075 | 0.988 | não |
| 079f141a8f41 / 8 | lex_integer | 0.095610 | 0.100326 | 1.049 | não |
| 079f141a8f41 / 16 | greedy_witness | 0.159683 | 0.159176 | 0.997 | não |
| 0a4b768afa25 / 4 | rust_speculative | 0.051732 | 0.048061 | 0.929 | não |
| 0a4b768afa25 / 8 | root_lazy_prefix | 0.126238 | 0.125099 | 0.991 | não |
| 0a4b768afa25 / 16 | monotone | 1.702728 | 0.434522 | 0.255 | não |
| 0bb397173614 / 4 | root_lazy_prefix | 0.107045 | 0.093570 | 0.874 | não |
| 0bb397173614 / 8 | rust_speculative | 0.177478 | 0.168358 | 0.949 | não |
| 0bb397173614 / 16 | greedy_cached_prefix | 0.635945 | 0.454556 | 0.715 | não |
| 0ce7169f4ded / 4 | rust_cached_prefix | 0.039281 | 0.039063 | 0.994 | não |
| 0ce7169f4ded / 8 | rust_lazy_prefix | 0.118850 | 0.118019 | 0.993 | não |
| 0ce7169f4ded / 16 | monotone | 1.873046 | 0.418811 | 0.224 | não |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
