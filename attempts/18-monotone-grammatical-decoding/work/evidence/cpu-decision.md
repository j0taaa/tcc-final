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
| 017a7a6ddeb1 / 4 | lex_integer | 0.279357 | 0.279394 | 1.000 | não |
| 017a7a6ddeb1 / 8 | greedy_cached_prefix | 0.353462 | 0.353773 | 1.001 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.224464 | 0.230651 | 1.028 | não |
| 05dacb44e44c / 8 | lex_integer | 0.464745 | 0.381984 | 0.822 | não |
| 05dacb44e44c / 16 | lex_integer | 0.964000 | 0.989489 | 1.026 | não |
| 079f141a8f41 / 4 | lex_integer | 0.273770 | 0.271787 | 0.993 | não |
| 079f141a8f41 / 8 | lex_integer | 0.296798 | 0.299500 | 1.009 | não |
| 079f141a8f41 / 16 | lex_integer | 0.662113 | 0.673315 | 1.017 | não |
| 0a4b768afa25 / 4 | lex_integer | 0.165346 | 0.164708 | 0.996 | não |
| 0a4b768afa25 / 8 | lex_integer | 0.522560 | 0.495252 | 0.948 | não |
| 0a4b768afa25 / 16 | lex_integer | 1.284813 | 1.436418 | 1.118 | não |
| 0bb397173614 / 4 | greedy_cached_prefix | 0.263945 | 0.248848 | 0.943 | não |
| 0bb397173614 / 8 | sat_cached_prefix | 0.454973 | 0.465700 | 1.024 | não |
| 0bb397173614 / 16 | lex_integer | 1.063433 | 1.031243 | 0.970 | não |
| 0ce7169f4ded / 4 | greedy_cached_prefix | 0.160314 | 0.159318 | 0.994 | não |
| 0ce7169f4ded / 8 | lex_integer | 0.495346 | 0.466452 | 0.942 | não |
| 0ce7169f4ded / 16 | lex_integer | 1.416562 | 1.818504 | 1.284 | não |

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
| 0f5a3b55aa6b / 4 | greedy_cached_prefix | 0.189696 | 0.186466 | 0.983 | não |
| 0f5a3b55aa6b / 8 | sat_cached_prefix | 0.501197 | 0.518967 | 1.035 | não |
| 0f5a3b55aa6b / 16 | lex_integer | 0.783104 | 0.740619 | 0.946 | não |
| 1357c5544492 / 4 | sat_cached_prefix | 0.303187 | 0.292515 | 0.965 | não |
| 1357c5544492 / 8 | greedy_cached_prefix | 0.382949 | 0.378058 | 0.987 | não |
| 1357c5544492 / 16 | — | — | — | — | inconclusivo/sem solução |
| 1c6ab02b22c0 / 4 | greedy_witness | 0.224702 | 0.225083 | 1.002 | não |
| 1c6ab02b22c0 / 8 | lex_integer | 0.389737 | 0.380252 | 0.976 | não |
| 1c6ab02b22c0 / 16 | lex_integer | 0.651815 | 0.665618 | 1.021 | não |
| 1eaf0817e3a5 / 4 | lex_integer | 0.126402 | 0.123182 | 0.975 | não |
| 1eaf0817e3a5 / 8 | greedy_cached_prefix | 0.298826 | 0.301571 | 1.009 | não |
| 1eaf0817e3a5 / 16 | lex_integer | 0.579548 | 0.590440 | 1.019 | não |
| 23ebff3f6f31 / 4 | lex_integer | 0.213610 | 0.212773 | 0.996 | não |
| 23ebff3f6f31 / 8 | — | — | — | — | inconclusivo/sem solução |
| 23ebff3f6f31 / 16 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 4 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 8 | — | — | — | — | inconclusivo/sem solução |
| 2cf2d4c86630 / 16 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 4 | greedy_witness | 0.177533 | 0.167749 | 0.945 | não |
| 339b1b4817bf / 8 | — | — | — | — | inconclusivo/sem solução |
| 339b1b4817bf / 16 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 4 | lex_integer | 0.277661 | 0.288994 | 1.041 | não |
| 442469db94fd / 8 | — | — | — | — | inconclusivo/sem solução |
| 442469db94fd / 16 | — | — | — | — | inconclusivo/sem solução |
| 47d38d20de38 / 4 | lex_integer | 0.267086 | 0.271036 | 1.015 | não |
| 47d38d20de38 / 8 | lex_integer | 0.477075 | 0.392978 | 0.824 | não |
| 47d38d20de38 / 16 | — | — | — | — | inconclusivo/sem solução |
| 6fff04fc461a / 4 | greedy_cached_prefix | 0.192374 | 0.183434 | 0.954 | não |
| 6fff04fc461a / 8 | lex_integer | 0.365429 | 0.359255 | 0.983 | não |
| 6fff04fc461a / 16 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 4 | sat_cached_prefix | 0.290994 | 0.284091 | 0.976 | não |
| 7dede5c098c5 / 8 | — | — | — | — | inconclusivo/sem solução |
| 7dede5c098c5 / 16 | lex_integer | 1.699333 | 2.312467 | 1.361 | não |
| 9017269543e3 / 4 | — | — | — | — | inconclusivo/sem solução |
| 9017269543e3 / 8 | greedy_cached_prefix | 0.407495 | 0.429417 | 1.054 | não |
| 9017269543e3 / 16 | — | — | — | — | inconclusivo/sem solução |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
