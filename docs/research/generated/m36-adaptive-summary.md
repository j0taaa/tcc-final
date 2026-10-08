# Complete developmental execution-conditioning audit

Producing commit: `30e6ac38aac69ddc0e9ccad6c0ac06d36016fa9c`.
Config: `configs/experiments/m36_adaptive_semantics_v1.json`; raw: `docs/artifacts/raw/m36_adaptive_semantics_v1`.

All 256 labels x 3 seeds = 768 rows; 108 original-token programs; 17 positive labels. Every archived mass, core equivalence and returned path was checked by independent enumeration/execution.

This reuses one developmental MDLM canvas, not an external/held-out benchmark. Prefix timing is a finite control with a perfect precomputed oracle, not native CARS/EPIC. All methods receive identical archived rational probabilities; no model forward is timed.

| Method | Exact positive rows | Correct zero rows | Resource refusals | Median positive batch (ms) | Sum of all batch times (s) |
|---|---:|---:|---:|---:|---:|
| adaptive | 51 | 717 | 0 | 5.343 | 2.386072 |
| certified_core | 51 | 717 | 0 | 1.009 | 0.070941 |
| eager | 51 | 717 | 0 | 2.050 | 0.110042 |
| enumeration | 51 | 717 | 0 | 0.007 | 0.001437 |
| prefix_control | 51 | 717 | 0 | 0.611 | 0.319403 |

Shared CFG compile: 0.001592 s; full-profile eager preparation: 0.002862 s; enumeration/oracle preparation: 0.003114 s.
Core certification (once per label, not once per seed): 2.532941 s; core evaluation once per label: 0.232866 s.
Certified core sizes: `{1: 192, 2: 42, 3: 15, 4: 6, 6: 1}`; maximum adaptive rejections: 7.

Preparation is necessary and must be added before comparing total cost. Enumeration and full-profile inference share their preparation across all labels; core certification is shared only within a label. These are reusable controls. Four samples per positive row do not establish long-run amortization, denoising speed, universal superiority or scientific priority. Recorded slow paths and zeros are retained.

For independent rejection from the same syntax-conditioned token-product law, the expected trials are Z_syntax/Z_target. Across ALL positive labels: min 1.31205, median 2347.83, max 72150.7. These are derived geometric expectations, not timed rejection or native EPIC. Zero-probability labels never accept by rejection. The bounded adaptive stream and certified core instead report zero when their exact evaluations fit the caps.
