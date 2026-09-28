# M24 — comparação de políticas

Fase: integration smoke, not selection or confirmation. 40 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| catalog_map4 | 2/2 | 2/2 | 12 | 674.0 | 679.0 |
| exact_b4 | 2/2 | 2/2 | 14 | 926.0 | 927.9 |
| margin_0.02 | 2/2 | 2/2 | 4 | 975.9 | 1014.2 |
| confidence_0.8 | 2/2 | 2/2 | 18 | 1202.4 | 1335.5 |
| epic_lexical_24 | 2/2 | 2/2 | 46 | 2174.6 | 2270.0 |
| margin_0.1 | 2/2 | 2/2 | 4 | 2603.8 | 4269.0 |
| exact_b1 | 2/2 | 2/2 | 48 | 3261.5 | 3353.6 |
| exact_multi3 | 1/2 | 2/2 | 3 | 217.3 | 277.4 |
| exact_b24 | 1/2 | 2/2 | 4 | 277.8 | 283.0 |
| exact_multi2 | 1/2 | 2/2 | 4 | 279.7 | 291.4 |
| epic_lexical_2 | 1/2 | 2/2 | 4 | 447.0 | 629.6 |
| exact_b12 | 1/2 | 2/2 | 7 | 463.3 | 522.0 |
| exact_b8 | 1/2 | 2/2 | 8 | 530.1 | 533.2 |
| confidence_0.2 | 1/2 | 2/2 | 8 | 533.1 | 535.3 |
| exact_review | 1/2 | 2/2 | 8 | 536.4 | 548.7 |
| confidence_0.5 | 1/2 | 2/2 | 10 | 663.2 | 665.7 |
| epic_lexical_4 | 1/2 | 2/2 | 8 | 718.1 | 841.9 |
| greedy_b8 | 1/2 | 2/2 | 8 | 829.0 | 900.1 |
| margin_0 | 1/2 | 2/2 | 4 | 909.6 | 937.1 |
| exact_b2 | 1/2 | 2/2 | 24 | 1568.8 | 1589.7 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): exact_b4, exact_multi3.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
