# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum e tokenização do corpus são externos ao decoder. Suporte top16 inicial permanece fixo, sem tokens de referência injetados. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável nas três repetições. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cpu

324 registros; 273 completos; 222 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

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
| 017a7a6ddeb1 / 4 | sat_cached_prefix | 0.278842 | 0.279789 | 1.003 | não |
| 017a7a6ddeb1 / 8 | greedy_cached_prefix | 0.354880 | 0.355253 | 1.001 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.222884 | 0.222413 | 0.998 | não |
| 05dacb44e44c / 8 | lex_integer | 0.381229 | 0.370008 | 0.971 | não |
| 05dacb44e44c / 16 | lex_integer | 0.876633 | 0.880510 | 1.004 | não |
| 079f141a8f41 / 4 | sat_cached_prefix | 0.269839 | 0.269954 | 1.000 | não |
| 079f141a8f41 / 8 | greedy_cached_prefix | 0.292144 | 0.290987 | 0.996 | não |
| 079f141a8f41 / 16 | lex_integer | 0.648213 | 0.647248 | 0.999 | não |
| 0a4b768afa25 / 4 | greedy_cached_prefix | 0.164933 | 0.164518 | 0.997 | não |
| 0a4b768afa25 / 8 | greedy_cached_prefix | 0.493699 | 0.492577 | 0.998 | não |
| 0a4b768afa25 / 16 | sat_cached_prefix | 1.122775 | 1.120737 | 0.998 | não |
| 0bb397173614 / 4 | greedy_cached_prefix | 0.241509 | 0.241569 | 1.000 | não |
| 0bb397173614 / 8 | lex_integer | 0.447539 | 0.449416 | 1.004 | não |
| 0bb397173614 / 16 | sat_cached_prefix | 0.980860 | 0.966765 | 0.986 | não |
| 0ce7169f4ded / 4 | lex_integer | 0.159168 | 0.158752 | 0.997 | não |
| 0ce7169f4ded / 8 | greedy_cached_prefix | 0.502711 | 0.466491 | 0.928 | não |
| 0ce7169f4ded / 16 | lex_integer | 1.311460 | 1.325444 | 1.011 | não |

## heldout / cpu

648 registros; 345 completos; 282 comparações exatas de suporte/trajectory/output. 0/36 configurações atingem o critério.

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
| 0f5a3b55aa6b / 4 | sat_cached_prefix | 0.186759 | 0.187025 | 1.001 | não |
| 0f5a3b55aa6b / 8 | lex_integer | 0.484878 | 0.486449 | 1.003 | não |
| 0f5a3b55aa6b / 16 | sat_cached_prefix | 0.670490 | 0.672904 | 1.004 | não |
| 1357c5544492 / 4 | sat_cached_prefix | 0.300499 | 0.286454 | 0.953 | não |
| 1357c5544492 / 8 | greedy_cached_prefix | 0.363016 | 0.362576 | 0.999 | não |
| 1357c5544492 / 16 | — | — | — | — | inconclusivo/sem solução |
| 1c6ab02b22c0 / 4 | greedy_cached_prefix | 0.201893 | 0.201363 | 0.997 | não |
| 1c6ab02b22c0 / 8 | lex_integer | 0.369427 | 0.366753 | 0.993 | não |
| 1c6ab02b22c0 / 16 | greedy_cached_prefix | 0.603975 | 0.604119 | 1.000 | não |
| 1eaf0817e3a5 / 4 | lex_integer | 0.122834 | 0.122565 | 0.998 | não |
| 1eaf0817e3a5 / 8 | lex_integer | 0.289542 | 0.289721 | 1.001 | não |
| 1eaf0817e3a5 / 16 | greedy_cached_prefix | 0.554937 | 0.551915 | 0.995 | não |
| 23ebff3f6f31 / 4 | greedy_cached_prefix | 0.214981 | 0.214219 | 0.996 | não |
| 23ebff3f6f31 / 8 | — | — | — | — | inconclusivo/sem solução |
| 23ebff3f6f31 / 16 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 4 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 8 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 16 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 4 | greedy_cached_prefix | 0.163831 | 0.164299 | 1.003 | não |
| 339b1b4817bf / 8 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 16 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 4 | greedy_cached_prefix | 0.280158 | 0.277007 | 0.989 | não |
| 442469db94fd / 8 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 16 | — | — | — | — | inconclusivo/sem solução |
| 47d38d20de38 / 4 | greedy_witness | 0.270668 | 0.270325 | 0.999 | não |
| 47d38d20de38 / 8 | lex_integer | 0.370318 | 0.369070 | 0.997 | não |
| 47d38d20de38 / 16 | — | — | — | — | inconclusivo/sem solução |
| 6fff04fc461a / 4 | greedy_cached_prefix | 0.178091 | 0.178008 | 1.000 | não |
| 6fff04fc461a / 8 | greedy_cached_prefix | 0.339269 | 0.337364 | 0.994 | não |
| 6fff04fc461a / 16 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 4 | greedy_witness | 0.280414 | 0.279044 | 0.995 | não |
| 7dede5c098c5 / 8 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 16 | sat_cached_prefix | 1.411271 | 1.405510 | 0.996 | não |
| 9017269543e3 / 4 | — | — | — | — | inconclusivo/sem solução |
| 9017269543e3 / 8 | greedy_cached_prefix | 0.410204 | 0.409500 | 0.998 | não |
| 9017269543e3 / 16 | — | — | — | — | inconclusivo/sem solução |

## development / cuda

324 registros; 273 completos; 222 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

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
| 017a7a6ddeb1 / 4 | greedy_cached_prefix | 0.109228 | 0.108734 | 0.995 | não |
| 017a7a6ddeb1 / 8 | greedy_cached_prefix | 0.142166 | 0.141808 | 0.997 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | greedy_witness | 0.096568 | 0.096572 | 1.000 | não |
| 05dacb44e44c / 8 | greedy_cached_prefix | 0.160549 | 0.160576 | 1.000 | não |
| 05dacb44e44c / 16 | lex_integer | 0.329627 | 0.332300 | 1.008 | não |
| 079f141a8f41 / 4 | greedy_cached_prefix | 0.120430 | 0.119970 | 0.996 | não |
| 079f141a8f41 / 8 | lex_integer | 0.142804 | 0.142378 | 0.997 | não |
| 079f141a8f41 / 16 | lex_integer | 0.354981 | 0.351081 | 0.989 | não |
| 0a4b768afa25 / 4 | lex_integer | 0.078237 | 0.077764 | 0.994 | não |
| 0a4b768afa25 / 8 | lex_integer | 0.185920 | 0.185830 | 1.000 | não |
| 0a4b768afa25 / 16 | sat_cached_prefix | 0.508970 | 0.512901 | 1.008 | não |
| 0bb397173614 / 4 | lex_integer | 0.120899 | 0.120494 | 0.997 | não |
| 0bb397173614 / 8 | sat_cached_prefix | 0.203270 | 0.205119 | 1.009 | não |
| 0bb397173614 / 16 | lex_integer | 0.415522 | 0.419195 | 1.009 | não |
| 0ce7169f4ded / 4 | lex_integer | 0.075049 | 0.075071 | 1.000 | não |
| 0ce7169f4ded / 8 | lex_integer | 0.170684 | 0.170641 | 1.000 | não |
| 0ce7169f4ded / 16 | lex_integer | 0.670925 | 0.681058 | 1.015 | não |

## heldout / cuda

648 registros; 345 completos; 282 comparações exatas de suporte/trajectory/output. 0/36 configurações atingem o critério.

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
| 0f5a3b55aa6b / 4 | greedy_cached_prefix | 0.091910 | 0.091619 | 0.997 | não |
| 0f5a3b55aa6b / 8 | sat_cached_prefix | 0.196874 | 0.198172 | 1.007 | não |
| 0f5a3b55aa6b / 16 | lex_integer | 0.288307 | 0.290356 | 1.007 | não |
| 1357c5544492 / 4 | greedy_cached_prefix | 0.110584 | 0.109895 | 0.994 | não |
| 1357c5544492 / 8 | greedy_cached_prefix | 0.140577 | 0.140721 | 1.001 | não |
| 1357c5544492 / 16 | — | — | — | — | inconclusivo/sem solução |
| 1c6ab02b22c0 / 4 | greedy_cached_prefix | 0.100823 | 0.101036 | 1.002 | não |
| 1c6ab02b22c0 / 8 | lex_integer | 0.164221 | 0.164394 | 1.001 | não |
| 1c6ab02b22c0 / 16 | lex_integer | 0.351328 | 0.349782 | 0.996 | não |
| 1eaf0817e3a5 / 4 | lex_integer | 0.073607 | 0.073145 | 0.994 | não |
| 1eaf0817e3a5 / 8 | lex_integer | 0.137429 | 0.138994 | 1.011 | não |
| 1eaf0817e3a5 / 16 | lex_integer | 0.248176 | 0.247732 | 0.998 | não |
| 23ebff3f6f31 / 4 | greedy_cached_prefix | 0.086073 | 0.085543 | 0.994 | não |
| 23ebff3f6f31 / 8 | — | — | — | — | inconclusivo/sem solução |
| 23ebff3f6f31 / 16 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 4 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 8 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 16 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 4 | greedy_cached_prefix | 0.075399 | 0.075809 | 1.005 | não |
| 339b1b4817bf / 8 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 16 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 4 | greedy_cached_prefix | 0.104450 | 0.104452 | 1.000 | não |
| 442469db94fd / 8 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 16 | — | — | — | — | inconclusivo/sem solução |
| 47d38d20de38 / 4 | lex_integer | 0.100070 | 0.099718 | 0.996 | não |
| 47d38d20de38 / 8 | greedy_cached_prefix | 0.156518 | 0.155304 | 0.992 | não |
| 47d38d20de38 / 16 | — | — | — | — | inconclusivo/sem solução |
| 6fff04fc461a / 4 | greedy_witness | 0.087740 | 0.087646 | 0.999 | não |
| 6fff04fc461a / 8 | greedy_witness | 0.153661 | 0.153333 | 0.998 | não |
| 6fff04fc461a / 16 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 4 | greedy_cached_prefix | 0.105915 | 0.106026 | 1.001 | não |
| 7dede5c098c5 / 8 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 16 | sat_cached_prefix | 0.710038 | 0.721796 | 1.017 | não |
| 9017269543e3 / 4 | — | — | — | — | inconclusivo/sem solução |
| 9017269543e3 / 8 | greedy_cached_prefix | 0.150225 | 0.149797 | 0.997 | não |
| 9017269543e3 / 16 | — | — | — | — | inconclusivo/sem solução |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
