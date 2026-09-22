# Recursive branching-support study

Generated from immutable raw JSONL. This is synthetic, feasibility-conditioned,
dirty-tree development evidence, not real-model or EPIC performance evidence.

- Unique family/seed states: 300.
- Shared seed clusters across families: 100.
- Repeated support/weight conditions: 1200.
- Correctness failure rows: 0.
- Width objective improvements: 62/600 paired objectives.
- Width monotonicity violations: 0.
- Raw SHA-256: `5e8cd203cca175ef911e14125b2d3acee9e3b5d4bd82ec1e4474a94c05808642`.

| Family | Width | Weights | Multiple valid completions | Greedy loses | Mean / max gap |
| --- | ---: | --- | ---: | ---: | ---: |
| arithmetic | 2 | integer_utility | 54/100 | 0/100 | 0.000 / 0.000 |
| arithmetic | 2 | unit | 54/100 | 0/100 | 0.000 / 0.000 |
| arithmetic | 4 | integer_utility | 87/100 | 0/100 | 0.000 / 0.000 |
| arithmetic | 4 | unit | 87/100 | 0/100 | 0.000 / 0.000 |
| brackets | 2 | integer_utility | 33/100 | 2/100 | 0.090 / 6.000 |
| brackets | 2 | unit | 33/100 | 3/100 | 0.030 / 1.000 |
| brackets | 4 | integer_utility | 100/100 | 2/100 | 0.040 / 3.000 |
| brackets | 4 | unit | 100/100 | 3/100 | 0.030 / 1.000 |
| nested_json | 2 | integer_utility | 53/100 | 0/100 | 0.000 / 0.000 |
| nested_json | 2 | unit | 53/100 | 0/100 | 0.000 / 0.000 |
| nested_json | 4 | integer_utility | 87/100 | 1/100 | 0.010 / 1.000 |
| nested_json | 4 | unit | 87/100 | 1/100 | 0.010 / 1.000 |

## Interpretation

Branching and loss are separate quantities: multiple valid completions need not
make greedy selection suboptimal. These states test correctness and characterize
this generator only. Exactness does not imply a typical real-model advantage.

Whole-selector timings and all status counts are in summary.json. The greedy
baseline repeatedly invokes the common finite-feasibility solver; it is not the
upstream serial decoder. No ratio here is an EPIC or end-to-end speedup.

Widths and weight modes share seeds. Do not treat the repeated conditions as
independent samples or pool them into a population confidence interval.
