# M25 — comparação de políticas

Fase: frozen grounded external confirmation; first timing repetition. 336 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_8 | 16/42 | 40/42 | 281 | 2040.7 | 2884.1 |
| epic_lexical_32 | 15/42 | 41/42 | 1181 | 4581.3 | 6088.8 |
| epic_lexical_64 | 15/42 | 41/42 | 2353 | 7359.0 | 10570.3 |
| catalog_map8 | 11/42 | 42/42 | 336 | 1144.7 | 1528.7 |
| confidence_0.8 | 5/42 | 41/42 | 757 | 36173.4 | 78823.6 |
| greedy_confidence_0.8 | 4/42 | 24/42 | 474 | 35470.3 | 96628.6 |
| exact_b64 | 3/42 | 42/42 | 192 | 8897.7 | 24633.7 |
| catalog_map64 | 2/42 | 42/42 | 42 | 190.5 | 293.7 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): nenhuma.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
