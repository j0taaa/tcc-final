# M25 — confirmação externa pareada

family-disjoint public BFCL scalar queries; question/schema-derived finite support; own strict AST evaluator, not official BFCL score; all selected cases retained; two timing repetitions, not independent samples; secondary CIs unadjusted

| Método | Chamadas corretas 1 / 2 | Resultado numérico 1 / 2 | Forwards 1 / 2 | Mediana total (ms) | p95 (ms) |
|---|---:|---:|---:|---:|---:|
| epic_lexical_8 | 16 / 17 de 42 | não se aplica | 281 / 281 | 1990.4 | 2876.7 |
| epic_lexical_32 | 15 / 15 de 42 | não se aplica | 1181 / 1181 | 4609.5 | 6168.8 |
| epic_lexical_64 | 15 / 15 de 42 | não se aplica | 2353 / 2353 | 7382.3 | 10583.8 |
| catalog_map8 | 11 / 11 de 42 | não se aplica | 336 / 336 | 1162.1 | 1559.8 |
| confidence_0.8 | 5 / 5 de 42 | não se aplica | 757 / 758 | 36157.1 | 78816.6 |
| greedy_confidence_0.8 | 4 / 4 de 42 | não se aplica | 474 / 471 | 30711.8 | 96539.1 |
| exact_b64 | 3 / 3 de 42 | não se aplica | 192 / 192 | 8928.5 | 24677.2 |
| catalog_map64 | 2 / 2 de 42 | não se aplica | 42 / 42 | 206.8 | 349.0 |

Tempos incluem preparação e recuperação; duas medições agregadas por pedido antes da mediana.
Comparações pareadas e intervalos estão no JSON; bootstrap por pedido, não por execução.
A repetição não aumenta o número de tarefas independentes; diferenças secundárias não têm ajuste por multiplicidade.
