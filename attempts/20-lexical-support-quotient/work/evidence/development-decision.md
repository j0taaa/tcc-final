# Geração completa com política gulosa preservada

Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez são externos ao decoder em serviço já preparado. Suporte adaptativo é a união dos top16 atuais/anteriores; sem tokens de referência. Reservas dos controles mantêm candidatos futuros inativos nas consultas. Métodos com classes são implementações alternativas da mesma representação; seus números também aparecem. Não há comparação nativa com EPIC ou melhora semântica.

O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra todos os controles concluídos SEM classes e sinal favorável em todas as repetições predeclaradas. CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. CPU/GPU declarados antes dos timings de20; seis casos frescos exigem nove repetições.

## development / cuda

864 registros; 795 completos; 744 comparações exatas de suporte/trajectory/output. 0/18 configurações atingem o critério.

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

| Documento / máscaras | Melhor controle completo (wall) | class_monotone (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | root_lex | 0.078590 | 0.079158 | 1.007 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.099286 | 0.094139 | 0.948 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | root_lex | 0.069389 | 0.061584 | 0.888 | não |
| 05dacb44e44c / 8 | root_speculative | 0.107647 | 0.083063 | 0.772 | não |
| 05dacb44e44c / 16 | root_lex | 0.584651 | 0.329095 | 0.563 | não |
| 079f141a8f41 / 4 | lex_sat | 0.082306 | 0.082066 | 0.997 | não |
| 079f141a8f41 / 8 | lex_speculative | 0.102301 | 0.093294 | 0.912 | não |
| 079f141a8f41 / 16 | root_lex | 0.167184 | 0.166947 | 0.999 | não |
| 0a4b768afa25 / 4 | lex_speculative | 0.050284 | 0.047194 | 0.939 | não |
| 0a4b768afa25 / 8 | enumeration | 0.134077 | 0.133015 | 0.992 | não |
| 0a4b768afa25 / 16 | lex_speculative | 0.469836 | 0.377718 | 0.804 | não |
| 0bb397173614 / 4 | lex_root | 0.088663 | 0.083799 | 0.945 | não |
| 0bb397173614 / 8 | lex_root | 0.158683 | 0.154525 | 0.974 | não |
| 0bb397173614 / 16 | lex_speculative | 0.377735 | 0.366414 | 0.970 | não |
| 0ce7169f4ded / 4 | monotone | 0.039930 | 0.039609 | 0.992 | não |
| 0ce7169f4ded / 8 | rust_speculative | 0.126256 | 0.125570 | 0.995 | não |
| 0ce7169f4ded / 16 | lex_root | 1.705188 | 0.894805 | 0.525 | não |

Lexer e quociente de classes são conhecidos; os resultados não provam novidade do princípio. Propagação AND/OR e otimização lexicográfica também são clássicas. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
