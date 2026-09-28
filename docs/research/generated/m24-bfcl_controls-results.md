# M24 — comparação de políticas

Fase: secondary external pilot controls; same eight audited cases; no official BFCL score or new independent holdout. 48 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| catalog_map24 | 8/8 | 8/8 | 16 | 256.8 | 346.5 |
| greedy_confidence_0.2 | 8/8 | 8/8 | 42 | 1260.1 | 2326.1 |
| greedy_confidence_0.8 | 8/8 | 8/8 | 94 | 2880.7 | 6431.0 |
| epic_lexical_6 | 7/8 | 8/8 | 45 | 1192.9 | 1482.4 |
| epic_lexical_8 | 6/8 | 7/8 | 57 | 1358.6 | 2185.6 |
| epic_lexical_12 | 6/8 | 8/8 | 85 | 1719.6 | 2753.0 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): greedy_confidence_0.2.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
