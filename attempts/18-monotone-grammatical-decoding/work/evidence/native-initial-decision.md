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
| 017a7a6ddeb1 / 4 | lex_integer | 0.114921 | 0.105124 | 0.915 | não |
| 017a7a6ddeb1 / 8 | monotone | 0.145834 | 0.137393 | 0.942 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | monotone | 0.117277 | 0.092782 | 0.791 | não |
| 05dacb44e44c / 8 | lex_integer | 0.204686 | 0.154427 | 0.754 | não |
| 05dacb44e44c / 16 | monotone | 1.712815 | 0.314760 | 0.184 | não |
| 079f141a8f41 / 4 | greedy_cached_prefix | 0.122764 | 0.116116 | 0.946 | não |
| 079f141a8f41 / 8 | monotone | 0.221065 | 0.137827 | 0.623 | não |
| 079f141a8f41 / 16 | greedy_cached_prefix | 0.752736 | 0.346452 | 0.460 | não |
| 0a4b768afa25 / 4 | rust_lazy_prefix | 0.066506 | 0.070646 | 1.062 | não |
| 0a4b768afa25 / 8 | monotone | 0.216578 | 0.179618 | 0.829 | não |
| 0a4b768afa25 / 16 | monotone | 2.611167 | 0.496591 | 0.190 | não |
| 0bb397173614 / 4 | lex_integer | 0.198637 | 0.119996 | 0.604 | não |
| 0bb397173614 / 8 | lex_integer | 0.416260 | 0.202429 | 0.486 | não |
| 0bb397173614 / 16 | monotone | 1.014792 | 0.410733 | 0.405 | não |
| 0ce7169f4ded / 4 | rust_lazy_prefix | 0.058368 | 0.062036 | 1.063 | não |
| 0ce7169f4ded / 8 | rust_cached_prefix | 0.167660 | 0.151731 | 0.905 | não |
| 0ce7169f4ded / 16 | monotone | 2.769256 | 0.655645 | 0.237 | não |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
