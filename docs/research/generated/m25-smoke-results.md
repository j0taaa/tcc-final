# M25 — comparação de políticas

Fase: development smoke after EPIC literal-regex integration correction; interrupted v1 preserved. 18 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| catalog_map8 | 2/2 | 2/2 | 16 | 1185.5 | 1212.9 |
| epic_lexical_32 | 2/2 | 2/2 | 56 | 3961.8 | 4329.3 |
| epic_lexical_64 | 2/2 | 2/2 | 115 | 6778.2 | 6874.4 |
| epic_lexical_8 | 1/2 | 2/2 | 13 | 1700.8 | 1867.8 |
| catalog_map64 | 0/2 | 2/2 | 2 | 251.2 | 295.4 |
| exact_b64 | 0/2 | 2/2 | 10 | 11048.6 | 16194.0 |
| exact_b4 | 0/2 | 2/2 | 35 | 17328.0 | 17430.8 |
| confidence_0.8 | 0/2 | 2/2 | 34 | 21933.0 | 25710.0 |
| greedy_confidence_0.8 | 0/2 | 2/2 | 34 | 40236.9 | 44010.7 |

Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): nenhuma.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
