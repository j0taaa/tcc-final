# M24 — piloto externo pareado

eight schema-finite public BFCL cases; own strict AST evaluator, not official BFCL score; two repetitions, not independent samples; exploratory CIs

| Método | Chamadas corretas 1 / 2 | Resultado numérico 1 / 2 | Forwards 1 / 2 | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| catalog_map24 | 8 / 8 de 8 | não se aplica | 16 / 16 | 260.8 | 346.4 |
| exact_b24 | 8 / 8 de 8 | não se aplica | 20 / 20 | 345.3 | 941.1 |
| exact_b8 | 8 / 8 de 8 | não se aplica | 32 / 32 | 617.4 | 901.6 |
| greedy_b8 | 8 / 8 de 8 | não se aplica | 32 / 32 | 768.2 | 1003.7 |
| confidence_0.2 | 8 / 8 de 8 | não se aplica | 42 / 42 | 786.4 | 1585.4 |
| catalog_map4 | 8 / 8 de 8 | não se aplica | 64 / 64 | 1054.1 | 1417.5 |
| exact_b4 | 8 / 8 de 8 | não se aplica | 64 / 64 | 1216.8 | 1700.6 |
| greedy_confidence_0.2 | 8 / 8 de 8 | não se aplica | 42 / 42 | 1264.2 | 2339.0 |
| confidence_0.5 | 8 / 8 de 8 | não se aplica | 65 / 65 | 1317.8 | 2275.4 |
| confidence_0.8 | 8 / 8 de 8 | não se aplica | 94 / 94 | 1833.5 | 3555.8 |
| exact_b2 | 8 / 8 de 8 | não se aplica | 128 / 128 | 2437.8 | 3398.9 |
| greedy_confidence_0.8 | 8 / 8 de 8 | não se aplica | 94 / 94 | 2890.3 | 6493.8 |
| exact_b1 | 8 / 8 de 8 | não se aplica | 256 / 256 | 4953.3 | 6738.0 |
| exact_b12 | 7 / 7 de 8 | não se aplica | 26 / 26 | 467.0 | 750.7 |
| exact_review | 7 / 7 de 8 | não se aplica | 28 / 28 | 621.7 | 1134.5 |
| epic_lexical_4 | 7 / 7 de 8 | não se aplica | 31 / 31 | 817.7 | 1289.8 |
| epic_lexical_6 | 7 / 7 de 8 | não se aplica | 45 / 45 | 1193.8 | 1487.5 |
| epic_lexical_24 | 7 / 7 de 8 | não se aplica | 141 / 141 | 2391.5 | 3080.5 |
| epic_lexical_2 | 6 / 4 de 8 | não se aplica | 16 / 16 | 990.5 | 1332.4 |
| epic_lexical_8 | 6 / 7 de 8 | não se aplica | 57 / 57 | 1358.2 | 2179.6 |
| margin_0.1 | 6 / 6 de 8 | não se aplica | 19 / 19 | 1451.8 | 2407.6 |
| margin_0.02 | 6 / 6 de 8 | não se aplica | 19 / 19 | 1551.9 | 2915.1 |
| epic_lexical_12 | 6 / 6 de 8 | não se aplica | 85 / 85 | 1703.7 | 2766.2 |
| exact_multi3 | 5 / 5 de 8 | não se aplica | 8 / 8 | 160.2 | 210.4 |
| exact_multi2 | 5 / 5 de 8 | não se aplica | 11 / 11 | 202.3 | 308.6 |
| margin_0 | 5 / 5 de 8 | não se aplica | 16 / 16 | 1482.5 | 2835.8 |

Tempos incluem preparação e recuperação; duas medições agregadas por pedido antes da mediana.
Comparações pareadas e intervalos estão no JSON; bootstrap por pedido, não por execução.
A repetição não aumenta o número de tarefas independentes; diferenças secundárias não têm ajuste por multiplicidade.
