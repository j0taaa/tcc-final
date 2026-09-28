# M24 — comparação de políticas

Fase: held-out request strings from frozen task pool; same calculator domain/templates. 700 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_24 | 89/100 | 99/100 | 2300 | 2412.6 | 2710.6 |
| confidence_0.8 | 87/100 | 100/100 | 792 | 1109.6 | 1568.6 |
| exact_b4 | 86/100 | 100/100 | 682 | 924.4 | 1225.2 |
| epic_lexical_4 | 75/100 | 100/100 | 399 | 639.4 | 922.0 |
| confidence_0.2 | 74/100 | 100/100 | 354 | 431.6 | 689.1 |
| epic_lexical_2 | 72/100 | 100/100 | 200 | 309.6 | 704.6 |
| exact_b24 | 54/100 | 100/100 | 210 | 278.2 | 417.5 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): confidence_0.8, exact_b4, confidence_0.2.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
