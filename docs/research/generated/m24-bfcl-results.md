# M24 — comparação de políticas

Fase: external schema-defined pilot: ALL 8 finite-enum cases among 658 BFCL examples; own strict AST evaluator, not official BFCL score. 160 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| exact_b24 | 8/8 | 8/8 | 20 | 348.0 | 940.2 |
| exact_b8 | 8/8 | 8/8 | 32 | 619.6 | 992.3 |
| greedy_b8 | 8/8 | 8/8 | 32 | 767.7 | 998.0 |
| confidence_0.2 | 8/8 | 8/8 | 42 | 787.1 | 1596.7 |
| catalog_map4 | 8/8 | 8/8 | 64 | 1039.9 | 1411.4 |
| exact_b4 | 8/8 | 8/8 | 64 | 1219.0 | 1733.6 |
| confidence_0.5 | 8/8 | 8/8 | 65 | 1342.2 | 2290.5 |
| confidence_0.8 | 8/8 | 8/8 | 94 | 1842.7 | 3570.1 |
| exact_b2 | 8/8 | 8/8 | 128 | 2456.7 | 3382.0 |
| exact_b1 | 8/8 | 8/8 | 256 | 4974.1 | 6753.2 |
| exact_b12 | 7/8 | 8/8 | 26 | 466.0 | 753.6 |
| exact_review | 7/8 | 8/8 | 28 | 619.7 | 1116.7 |
| epic_lexical_4 | 7/8 | 7/8 | 31 | 809.7 | 1275.4 |
| epic_lexical_24 | 7/8 | 8/8 | 141 | 2379.4 | 3071.3 |
| epic_lexical_2 | 6/8 | 8/8 | 16 | 987.5 | 1331.7 |
| margin_0.1 | 6/8 | 8/8 | 19 | 1450.5 | 2407.1 |
| margin_0.02 | 6/8 | 8/8 | 19 | 1521.0 | 4479.6 |
| exact_multi3 | 5/8 | 8/8 | 8 | 160.4 | 207.2 |
| exact_multi2 | 5/8 | 8/8 | 11 | 199.9 | 306.3 |
| margin_0 | 5/8 | 8/8 | 16 | 1378.2 | 2139.2 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): exact_multi3.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
