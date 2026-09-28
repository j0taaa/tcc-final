# M24 — comparação de políticas

Fase: external schema-defined pilot: ALL 8 finite-enum cases among 658 BFCL examples; own strict AST evaluator, not official BFCL score. 160 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| exact_b24 | 8/8 | 8/8 | 20 | 343.2 | 942.0 |
| exact_b8 | 8/8 | 8/8 | 32 | 614.4 | 810.9 |
| greedy_b8 | 8/8 | 8/8 | 32 | 768.7 | 1009.4 |
| confidence_0.2 | 8/8 | 8/8 | 42 | 785.8 | 1574.1 |
| catalog_map4 | 8/8 | 8/8 | 64 | 1063.7 | 1423.7 |
| exact_b4 | 8/8 | 8/8 | 64 | 1218.4 | 1667.6 |
| confidence_0.5 | 8/8 | 8/8 | 65 | 1293.3 | 2260.3 |
| confidence_0.8 | 8/8 | 8/8 | 94 | 1816.9 | 3541.4 |
| exact_b2 | 8/8 | 8/8 | 128 | 2420.3 | 3415.8 |
| exact_b1 | 8/8 | 8/8 | 256 | 4882.1 | 6722.9 |
| exact_b12 | 7/8 | 8/8 | 26 | 468.0 | 747.8 |
| exact_review | 7/8 | 8/8 | 28 | 623.7 | 1152.2 |
| epic_lexical_4 | 7/8 | 7/8 | 31 | 825.7 | 1304.1 |
| epic_lexical_24 | 7/8 | 8/8 | 141 | 2403.7 | 3089.7 |
| margin_0.02 | 6/8 | 8/8 | 19 | 1456.6 | 2501.9 |
| margin_0.1 | 6/8 | 8/8 | 19 | 1468.6 | 2408.1 |
| exact_multi3 | 5/8 | 8/8 | 8 | 160.0 | 213.7 |
| exact_multi2 | 5/8 | 8/8 | 11 | 204.6 | 310.9 |
| margin_0 | 5/8 | 8/8 | 16 | 1459.8 | 4361.0 |
| epic_lexical_2 | 4/8 | 8/8 | 16 | 970.7 | 1333.1 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): exact_multi3.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
