# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte adaptativo é a união dos top16 atuais/anteriores; sem tokens de referência. Reservas dos controles mantêm candidatos futuros inativos nas consultas. Não há comparação nativa com EPIC, nem promessa de melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos e sinal favorável em todas as repetições predeclaradas. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.

## development / cuda

1026 registros; 939 completos; 888 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

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
| sat_reserve_32 | `{"complete": 51, "infeasible_on_support": 3}` |
| sat_reserve_64 | `{"complete": 51, "infeasible_on_support": 3}` |
| sat_reserve_128 | `{"complete": 42, "infeasible_on_support": 3, "unresolved": 9}` |

| Documento / máscaras | Melhor controle completo (wall) | root_lex (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | rust_lex | 0.079452 | 0.079453 | 1.000 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.098273 | 0.095035 | 0.967 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | lex_integer | 0.061147 | 0.062344 | 1.020 | não |
| 05dacb44e44c / 8 | root_speculative | 0.084593 | 0.082416 | 0.974 | não |
| 05dacb44e44c / 16 | root_speculative | 0.329265 | 0.335514 | 1.019 | não |
| 079f141a8f41 / 4 | lex_integer | 0.081982 | 0.081467 | 0.994 | não |
| 079f141a8f41 / 8 | root_speculative | 0.105480 | 0.098697 | 0.936 | não |
| 079f141a8f41 / 16 | sat_reserve_64 | 0.170821 | 0.169630 | 0.993 | não |
| 0a4b768afa25 / 4 | rust_speculative | 0.055661 | 0.048940 | 0.879 | não |
| 0a4b768afa25 / 8 | root_count_warm | 0.135138 | 0.133916 | 0.991 | não |
| 0a4b768afa25 / 16 | root_speculative | 1.952708 | 1.795325 | 0.919 | não |
| 0bb397173614 / 4 | rust_lex | 0.107640 | 0.104099 | 0.967 | não |
| 0bb397173614 / 8 | rust_speculative | 0.256157 | 0.169482 | 0.662 | não |
| 0bb397173614 / 16 | rust_speculative | 0.690058 | 0.488903 | 0.708 | não |
| 0ce7169f4ded / 4 | rust_lex | 0.040444 | 0.039914 | 0.987 | não |
| 0ce7169f4ded / 8 | rust_speculative | 0.127382 | 0.126238 | 0.991 | não |
| 0ce7169f4ded / 16 | lex_integer | 2.549051 | 3.547850 | 1.392 | não |

A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
