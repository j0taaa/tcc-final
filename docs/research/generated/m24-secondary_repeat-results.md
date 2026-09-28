# M24 — comparação de políticas

Fase: secondary exploratory ablations on the frozen confirmation requests; does not alter primary comparison. 400 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| greedy_confidence_0.8 | 91/100 | 100/100 | 785 | 2279.1 | 3717.5 |
| greedy_confidence_0.2 | 73/100 | 100/100 | 359 | 786.7 | 1360.7 |
| exact_multi3 | 59/100 | 100/100 | 131 | 144.5 | 277.8 |
| catalog_map24 | 58/100 | 100/100 | 100 | 116.4 | 120.0 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): greedy_confidence_0.8, greedy_confidence_0.2, exact_multi3.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
