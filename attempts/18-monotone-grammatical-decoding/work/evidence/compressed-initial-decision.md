# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte top16 inicial permanece fixo, sem tokens de referência injetados. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável nas três repetições. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cuda

486 registros; 426 completos; 375 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

| Método | Status |
| --- | --- |
| greedy_witness | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_integer | `{"complete": 51, "infeasible_on_support": 3}` |
| greedy_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| enumeration | `{"complete": 18, "not_applicable": 36}` |
| sat_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_lex | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_lazy_prefix | `{"complete": 51, "infeasible_on_support": 3}` |

| Documento / máscaras | Melhor controle completo (wall) | rust_lex (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | rust_lazy_prefix | 0.099295 | 0.099900 | 1.006 | não |
| 017a7a6ddeb1 / 8 | rust_lazy_prefix | 0.127607 | 0.126047 | 0.988 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.091852 | 0.092772 | 1.010 | não |
| 05dacb44e44c / 8 | lex_integer | 0.142269 | 0.153576 | 1.079 | não |
| 05dacb44e44c / 16 | monotone | 0.433076 | 0.313101 | 0.723 | não |
| 079f141a8f41 / 4 | rust_lazy_prefix | 0.110158 | 0.108052 | 0.981 | não |
| 079f141a8f41 / 8 | rust_lazy_prefix | 0.167142 | 0.138667 | 0.830 | não |
| 079f141a8f41 / 16 | monotone | 0.473362 | 0.347879 | 0.735 | não |
| 0a4b768afa25 / 4 | rust_lazy_prefix | 0.059296 | 0.062339 | 1.051 | não |
| 0a4b768afa25 / 8 | rust_lazy_prefix | 0.184787 | 0.174071 | 0.942 | não |
| 0a4b768afa25 / 16 | monotone | 1.892123 | 0.499568 | 0.264 | não |
| 0bb397173614 / 4 | greedy_witness | 0.157604 | 0.117600 | 0.746 | não |
| 0bb397173614 / 8 | monotone | 0.318461 | 0.200542 | 0.630 | não |
| 0bb397173614 / 16 | monotone | 0.725532 | 0.408252 | 0.563 | não |
| 0ce7169f4ded / 4 | rust_lazy_prefix | 0.053803 | 0.056757 | 1.055 | não |
| 0ce7169f4ded / 8 | rust_cached_prefix | 0.151614 | 0.147589 | 0.973 | não |
| 0ce7169f4ded / 16 | monotone | 1.524216 | 0.659560 | 0.433 | não |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
