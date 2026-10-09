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

| Documento / máscaras | Melhor controle completo (wall) | class_root_lex (s) | Controle (s) | Razão controle/candidata | Critério |
| --- | --- | ---: | ---: | ---: | --- |
| 017a7a6ddeb1 / 4 | root_lex | 0.080412 | 0.079158 | 0.984 | não |
| 017a7a6ddeb1 / 8 | enumeration | 0.097302 | 0.094139 | 0.967 | não |
| 017a7a6ddeb1 / 16 | — | — | — | — | inconclusivo/sem solução |
| 05dacb44e44c / 4 | root_lex | 0.066013 | 0.061584 | 0.933 | não |
| 05dacb44e44c / 8 | root_speculative | 0.094616 | 0.083063 | 0.878 | não |
| 05dacb44e44c / 16 | root_lex | 0.449392 | 0.329095 | 0.732 | não |
| 079f141a8f41 / 4 | lex_sat | 0.082329 | 0.082066 | 0.997 | não |
| 079f141a8f41 / 8 | lex_speculative | 0.098551 | 0.093294 | 0.947 | não |
| 079f141a8f41 / 16 | root_lex | 0.168612 | 0.166947 | 0.990 | não |
| 0a4b768afa25 / 4 | lex_speculative | 0.049463 | 0.047194 | 0.954 | não |
| 0a4b768afa25 / 8 | enumeration | 0.134106 | 0.133015 | 0.992 | não |
| 0a4b768afa25 / 16 | lex_speculative | 0.378229 | 0.377718 | 0.999 | não |
| 0bb397173614 / 4 | lex_root | 0.087137 | 0.083799 | 0.962 | não |
| 0bb397173614 / 8 | lex_root | 0.157088 | 0.154525 | 0.984 | não |
| 0bb397173614 / 16 | lex_speculative | 0.377396 | 0.366414 | 0.971 | não |
| 0ce7169f4ded / 4 | monotone | 0.040094 | 0.039609 | 0.988 | não |
| 0ce7169f4ded / 8 | rust_speculative | 0.126273 | 0.125570 | 0.994 | não |
| 0ce7169f4ded / 16 | lex_root | 0.820343 | 0.894805 | 1.091 | não |

Lexer e quociente de classes são conhecidos; os resultados não provam novidade do princípio. Propagação AND/OR e otimização lexicográfica também são clássicas. Os ganhos que esta avaliação estabelecer pertencem à implementação e integração delimitadas. Não provam prioridade histórica ou significância para publicação; revisão humana permanece ausente.
