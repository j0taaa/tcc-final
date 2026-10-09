# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum e tokenização do corpus são externos ao decoder. Suporte top16 inicial permanece fixo, sem tokens de referência injetados. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável nas três repetições. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cuda

324 registros; 273 completos; 222 comparações exatas de suporte/trajectory/output. 1/18 configurações atingem o critério.

| Método | Status |
| --- | --- |
| greedy_witness | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_integer | `{"complete": 51, "infeasible_on_support": 3}` |
| greedy_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| enumeration | `{"complete": 18, "not_applicable": 36}` |
| sat_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |

| Documento / máscaras | Melhor controle completo (wall) | Monotone (s) | Controle (s) | Razão controle/monotone | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | greedy_cached_prefix | 0.106706 | 0.108896 | 1.021 | não |
| 017a7a6ddeb1 / 8 | greedy_cached_prefix | 0.140993 | 0.141301 | 1.002 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.097214 | 0.103203 | 1.062 | não |
| 05dacb44e44c / 8 | lex_integer | 0.242431 | 0.171394 | 0.707 | não |
| 05dacb44e44c / 16 | lex_integer | 0.437047 | 0.436559 | 0.999 | não |
| 079f141a8f41 / 4 | greedy_cached_prefix | 0.119360 | 0.118689 | 0.994 | não |
| 079f141a8f41 / 8 | lex_integer | 0.144860 | 0.146156 | 1.009 | não |
| 079f141a8f41 / 16 | lex_integer | 0.361690 | 0.370829 | 1.025 | não |
| 0a4b768afa25 / 4 | lex_integer | 0.077608 | 0.076803 | 0.990 | não |
| 0a4b768afa25 / 8 | greedy_cached_prefix | 0.182781 | 0.186864 | 1.022 | não |
| 0a4b768afa25 / 16 | lex_integer | 0.657993 | 0.784466 | 1.192 | não |
| 0bb397173614 / 4 | greedy_witness | 0.121598 | 0.125367 | 1.031 | não |
| 0bb397173614 / 8 | sat_cached_prefix | 0.205395 | 0.218791 | 1.065 | não |
| 0bb397173614 / 16 | lex_integer | 0.505311 | 0.484706 | 0.959 | não |
| 0ce7169f4ded / 4 | lex_integer | 0.074426 | 0.073337 | 0.985 | não |
| 0ce7169f4ded / 8 | greedy_cached_prefix | 0.167284 | 0.167895 | 1.004 | não |
| 0ce7169f4ded / 16 | lex_integer | 0.749557 | 1.174950 | 1.568 | sim |

## heldout / cuda

648 registros; 345 completos; 282 comparações exatas de suporte/trajectory/output. 1/36 configurações atingem o critério.

| Método | Status |
| --- | --- |
| greedy_witness | `{"complete": 63, "infeasible_on_support": 45}` |
| lex_integer | `{"complete": 63, "infeasible_on_support": 45}` |
| greedy_cached_prefix | `{"complete": 63, "infeasible_on_support": 45}` |
| monotone | `{"complete": 63, "infeasible_on_support": 45}` |
| enumeration | `{"complete": 30, "infeasible_on_support": 6, "not_applicable": 72}` |
| sat_cached_prefix | `{"complete": 63, "infeasible_on_support": 45}` |

| Documento / máscaras | Melhor controle completo (wall) | Monotone (s) | Controle (s) | Razão controle/monotone | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 0f5a3b55aa6b / 4 | greedy_cached_prefix | 0.094404 | 0.092034 | 0.975 | não |
| 0f5a3b55aa6b / 8 | sat_cached_prefix | 0.206079 | 0.213405 | 1.036 | não |
| 0f5a3b55aa6b / 16 | lex_integer | 0.384247 | 0.347356 | 0.904 | não |
| 1357c5544492 / 4 | greedy_cached_prefix | 0.114836 | 0.116138 | 1.011 | não |
| 1357c5544492 / 8 | lex_integer | 0.148496 | 0.157606 | 1.061 | não |
| 1357c5544492 / 16 | — | — | — | — | inconclusivo/sem solução |
| 1c6ab02b22c0 / 4 | greedy_cached_prefix | 0.105232 | 0.101403 | 0.964 | não |
| 1c6ab02b22c0 / 8 | lex_integer | 0.170369 | 0.175887 | 1.032 | não |
| 1c6ab02b22c0 / 16 | lex_integer | 0.400347 | 0.397866 | 0.994 | não |
| 1eaf0817e3a5 / 4 | lex_integer | 0.076344 | 0.073270 | 0.960 | não |
| 1eaf0817e3a5 / 8 | lex_integer | 0.141289 | 0.147761 | 1.046 | não |
| 1eaf0817e3a5 / 16 | lex_integer | 0.256416 | 0.262924 | 1.025 | não |
| 23ebff3f6f31 / 4 | lex_integer | 0.088715 | 0.088601 | 0.999 | não |
| 23ebff3f6f31 / 8 | — | — | — | — | inconclusivo/sem solução |
| 23ebff3f6f31 / 16 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 4 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 8 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 16 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 4 | lex_integer | 0.077588 | 0.080731 | 1.041 | não |
| 339b1b4817bf / 8 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 16 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 4 | lex_integer | 0.107930 | 0.109788 | 1.017 | não |
| 442469db94fd / 8 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 16 | — | — | — | — | inconclusivo/sem solução |
| 47d38d20de38 / 4 | greedy_cached_prefix | 0.102587 | 0.104491 | 1.019 | não |
| 47d38d20de38 / 8 | lex_integer | 0.250407 | 0.172721 | 0.690 | não |
| 47d38d20de38 / 16 | — | — | — | — | inconclusivo/sem solução |
| 6fff04fc461a / 4 | greedy_cached_prefix | 0.089269 | 0.090740 | 1.016 | não |
| 6fff04fc461a / 8 | lex_integer | 0.161315 | 0.164953 | 1.023 | não |
| 6fff04fc461a / 16 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 4 | greedy_cached_prefix | 0.109900 | 0.110152 | 1.002 | não |
| 7dede5c098c5 / 8 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 16 | lex_integer | 0.954544 | 1.533826 | 1.607 | sim |
| 9017269543e3 / 4 | — | — | — | — | inconclusivo/sem solução |
| 9017269543e3 / 8 | greedy_cached_prefix | 0.157759 | 0.167406 | 1.061 | não |
| 9017269543e3 / 16 | — | — | — | — | inconclusivo/sem solução |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
