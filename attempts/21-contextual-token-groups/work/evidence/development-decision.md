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

| Documento / máscaras | Melhor controle completo (wall) | context_monotone (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | class_monotone | 0.077158 | 0.078285 | 1.015 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.097974 | 0.094344 | 0.963 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | root_lex | 0.068755 | 0.061533 | 0.895 | não |
| 05dacb44e44c / 8 | root_speculative | 0.103809 | 0.082539 | 0.795 | não |
| 05dacb44e44c / 16 | root_lex | 0.585506 | 0.329334 | 0.562 | não |
| 079f141a8f41 / 4 | monotone | 0.082623 | 0.081830 | 0.990 | não |
| 079f141a8f41 / 8 | lex_speculative | 0.103135 | 0.093546 | 0.907 | não |
| 079f141a8f41 / 16 | lex_root | 0.168503 | 0.167141 | 0.992 | não |
| 0a4b768afa25 / 4 | lex_speculative | 0.048677 | 0.047318 | 0.972 | não |
| 0a4b768afa25 / 8 | rust_speculative | 0.134849 | 0.134593 | 0.998 | não |
| 0a4b768afa25 / 16 | class_speculative | 0.450076 | 0.377623 | 0.839 | não |
| 0bb397173614 / 4 | lex_root | 0.083975 | 0.086497 | 1.030 | não |
| 0bb397173614 / 8 | lex_root | 0.157830 | 0.153480 | 0.972 | não |
| 0bb397173614 / 16 | class_reserve_64 | 0.365430 | 0.371036 | 1.015 | não |
| 0ce7169f4ded / 4 | class_speculative | 0.039814 | 0.039715 | 0.998 | não |
| 0ce7169f4ded / 8 | lex_monotone | 0.126103 | 0.126020 | 0.999 | não |
| 0ce7169f4ded / 16 | class_root_lex | 1.151450 | 0.826013 | 0.717 | não |

Lexer e quociente de classes são conhecidos; os resultados não provam novidade do princípio. Propagação AND/OR e otimização lexicográfica também são clássicas. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
