# M24 — comparação de políticas

Fase: held-out request strings from frozen task pool; same calculator domain/templates. 700 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_24 | 89/100 | 99/100 | 2300 | 2351.4 | 2653.7 |
| confidence_0.8 | 87/100 | 100/100 | 792 | 1104.0 | 1624.2 |
| exact_b4 | 86/100 | 100/100 | 682 | 920.9 | 1225.4 |
| confidence_0.2 | 74/100 | 100/100 | 354 | 426.3 | 680.7 |
| epic_lexical_4 | 74/100 | 100/100 | 399 | 608.9 | 895.7 |
| epic_lexical_2 | 72/100 | 100/100 | 200 | 310.2 | 695.5 |
| exact_b24 | 54/100 | 100/100 | 210 | 282.6 | 430.5 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): confidence_0.8, exact_b4, confidence_0.2.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
