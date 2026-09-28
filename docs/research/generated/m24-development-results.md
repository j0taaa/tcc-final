# M24 — comparação de políticas

Fase: exploratory development, first 30 M22 v4 requests; no held-out claim. 600 gerações finais; revisão inclui duas fases.

Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. MAP usa catálogo canônico e não é o parser de produção.

| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| confidence_0.8 | 28/30 | 30/30 | 203 | 942.0 | 1485.5 |
| epic_lexical_24 | 28/30 | 30/30 | 685 | 2162.5 | 2387.6 |
| exact_b1 | 28/30 | 30/30 | 720 | 3166.2 | 3260.8 |
| catalog_map4 | 27/30 | 30/30 | 180 | 670.3 | 692.6 |
| exact_b4 | 27/30 | 30/30 | 206 | 801.6 | 1232.2 |
| margin_0.1 | 27/30 | 30/30 | 68 | 979.6 | 1152.1 |
| confidence_0.2 | 24/30 | 30/30 | 100 | 409.9 | 540.7 |
| exact_b8 | 24/30 | 30/30 | 114 | 521.0 | 547.6 |
| confidence_0.5 | 24/30 | 30/30 | 128 | 604.7 | 820.9 |
| margin_0.02 | 24/30 | 30/30 | 62 | 893.2 | 1183.4 |
| exact_b2 | 24/30 | 30/30 | 362 | 1581.1 | 1679.7 |
| exact_b12 | 23/30 | 30/30 | 86 | 399.1 | 426.4 |
| greedy_b8 | 23/30 | 30/30 | 114 | 721.3 | 930.8 |
| epic_lexical_4 | 22/30 | 30/30 | 120 | 521.5 | 888.3 |
| exact_multi3 | 21/30 | 30/30 | 36 | 140.8 | 276.5 |
| epic_lexical_2 | 21/30 | 30/30 | 60 | 261.6 | 686.3 |
| exact_review | 20/30 | 30/30 | 119 | 519.4 | 766.4 |
| exact_multi2 | 19/30 | 30/30 | 45 | 208.1 | 276.5 |
| exact_b24 | 19/30 | 30/30 | 62 | 271.7 | 410.5 |
| margin_0 | 19/30 | 30/30 | 62 | 885.8 | 1106.6 |

Candidatas pela regra congelada: confidence_0.8, exact_b4, confidence_0.2.

Acurácia observada não prova superioridade populacional. Todos os métodos e falhas estão incluídos.
