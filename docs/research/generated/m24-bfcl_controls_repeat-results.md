# M24 — comparação de políticas

Fase: secondary external pilot controls; same eight audited cases; no official BFCL score or new independent holdout. 48 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| catalog_map24 | 8/8 | 8/8 | 16 | 263.3 | 346.4 |
| greedy_confidence_0.2 | 8/8 | 8/8 | 42 | 1268.3 | 2351.8 |
| greedy_confidence_0.8 | 8/8 | 8/8 | 94 | 2899.9 | 6556.7 |
| epic_lexical_6 | 7/8 | 8/8 | 45 | 1138.0 | 1492.5 |
| epic_lexical_8 | 7/8 | 8/8 | 57 | 1357.7 | 2173.5 |
| epic_lexical_12 | 6/8 | 7/8 | 85 | 1688.3 | 2779.3 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): greedy_confidence_0.2.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
