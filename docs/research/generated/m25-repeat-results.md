# M25 — comparação de políticas

Fase: frozen grounded external confirmation; reversed method order. 336 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_8 | 17/42 | 40/42 | 281 | 1963.0 | 2869.3 |
| epic_lexical_32 | 15/42 | 41/42 | 1181 | 4637.7 | 6248.8 |
| epic_lexical_64 | 15/42 | 41/42 | 2353 | 7414.4 | 10597.3 |
| catalog_map8 | 11/42 | 42/42 | 336 | 1156.1 | 1623.2 |
| confidence_0.8 | 5/42 | 41/42 | 758 | 36134.8 | 78809.6 |
| greedy_confidence_0.8 | 4/42 | 24/42 | 471 | 30591.9 | 96449.7 |
| exact_b64 | 3/42 | 42/42 | 192 | 8959.2 | 24720.7 |
| catalog_map64 | 2/42 | 42/42 | 42 | 204.9 | 395.9 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): nenhuma.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
