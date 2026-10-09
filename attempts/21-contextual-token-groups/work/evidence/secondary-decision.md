# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte adaptativo é a união dos top16 atuais/anteriores; sem tokens de referência. Reservas dos controles mantêm candidatos futuros inativos nas consultas. Métodos contextuais usam a mesma representação; classes globais são controles. seus números também aparecem. Não há comparação nativa com EPIC ou melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos SEM grupos contextuais e sinal favorável em todas as repetições predeclaradas. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. CPU/GPU declarados antes dos timings de21; seis casos frescos exigem nove repetições.

## development / cuda

1026 registros; 948 completos; 897 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

| Método | Status |
| --- | --- |
| monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| sat_cached_prefix | `{"complete": 51, "infeasible_on_support": 3}` |
| root_lex | `{"complete": 51, "infeasible_on_support": 3}` |
| root_speculative | `{"complete": 51, "infeasible_on_support": 3}` |
| rust_speculative | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_sat | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_root | `{"complete": 51, "infeasible_on_support": 3}` |
| lex_speculative | `{"complete": 51, "infeasible_on_support": 3}` |
| class_monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| class_sat | `{"complete": 51, "infeasible_on_support": 3}` |
| class_root_lex | `{"complete": 51, "infeasible_on_support": 3}` |
| class_speculative | `{"complete": 51, "infeasible_on_support": 3}` |
| class_reserve_64 | `{"complete": 51, "infeasible_on_support": 3}` |
| class_reserve_128 | `{"complete": 51, "infeasible_on_support": 3}` |
| enumeration | `{"complete": 30, "not_applicable": 24}` |
| context_monotone | `{"complete": 51, "infeasible_on_support": 3}` |
| context_root | `{"complete": 51, "infeasible_on_support": 3}` |
| context_sat | `{"complete": 51, "infeasible_on_support": 3}` |

| Documento / máscaras | Melhor controle completo (wall) | context_root (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | class_monotone | 0.078278 | 0.078285 | 1.000 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.099782 | 0.094344 | 0.945 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | root_lex | 0.065356 | 0.061533 | 0.942 | não |
| 05dacb44e44c / 8 | root_speculative | 0.093282 | 0.082539 | 0.885 | não |
| 05dacb44e44c / 16 | root_lex | 0.441823 | 0.329334 | 0.745 | não |
| 079f141a8f41 / 4 | monotone | 0.082140 | 0.081830 | 0.996 | não |
| 079f141a8f41 / 8 | lex_speculative | 0.096079 | 0.093546 | 0.974 | não |
| 079f141a8f41 / 16 | lex_root | 0.167871 | 0.167141 | 0.996 | não |
| 0a4b768afa25 / 4 | lex_speculative | 0.047394 | 0.047318 | 0.998 | não |
| 0a4b768afa25 / 8 | rust_speculative | 0.134443 | 0.134593 | 1.001 | não |
| 0a4b768afa25 / 16 | class_speculative | 0.360577 | 0.377623 | 1.047 | não |
| 0bb397173614 / 4 | lex_root | 0.084949 | 0.086497 | 1.018 | não |
| 0bb397173614 / 8 | lex_root | 0.155141 | 0.153480 | 0.989 | não |
| 0bb397173614 / 16 | class_reserve_64 | 0.365919 | 0.371036 | 1.014 | não |
| 0ce7169f4ded / 4 | class_speculative | 0.039872 | 0.039715 | 0.996 | não |
| 0ce7169f4ded / 8 | lex_monotone | 0.127010 | 0.126020 | 0.992 | não |
| 0ce7169f4ded / 16 | class_root_lex | 0.711578 | 0.826013 | 1.161 | não |

Lexer e quociente de classes são conhecidos; os resultados não provam novidade do princípio. Propagação AND/OR e otimização lexicográfica também são clássicas. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
