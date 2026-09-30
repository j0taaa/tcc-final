# M25 — comparação de políticas

Fase: grounded external development; family-disjoint, own scalar AST checker. 234 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_32 | 14/26 | 25/26 | 741 | 5581.0 | 6625.1 |
| epic_lexical_8 | 13/26 | 24/26 | 168 | 2151.0 | 3008.0 |
| epic_lexical_64 | 12/26 | 25/26 | 1462 | 9537.2 | 10232.2 |
| catalog_map8 | 5/26 | 26/26 | 208 | 1456.1 | 1582.7 |
| catalog_map64 | 4/26 | 26/26 | 26 | 224.6 | 288.2 |
| exact_b64 | 2/26 | 26/26 | 122 | 11781.6 | 31948.2 |
| exact_b4 | 2/26 | 26/26 | 527 | 40070.0 | 87820.5 |
| greedy_confidence_0.8 | 0/26 | 13/26 | 253 | 25896.3 | 99418.4 |
| confidence_0.8 | 0/26 | 26/26 | 487 | 41245.6 | 80848.9 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): nenhuma.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
