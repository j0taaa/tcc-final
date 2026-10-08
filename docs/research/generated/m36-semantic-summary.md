# M36: frozen MDLM / JsonLogic execution check

Capture code: `2be61a9773a016930dc407ab051d6f2d497704a0`. Seed: `20261007`.

Analysis script SHA-256: `fb351d57b4cf314c587db6d41f3b3540bb584cafc8ae757ce7bad64ff99cdb66`.

Independent enumeration: 108 rules, 8 records.

| Target | Status | Samples | Probability given syntax | Expected rejection trials |
|---|---|---:|---:|---:|
| stock_and_delivery_choice | exact_on_support | 16 | 0.000273526822 | 3655.94859 |
| alternate_permission | exact_on_support | 16 | 0.000183150305 | 5459.99635 |
| parity_not_represented_by_this_canvas | zero_valid_probability_on_support | 0 | 0 | never succeeds |

Probabilities and trial counts are rounded displays computed from archived exact fractions, not measured performance. Rejection means independent draws from the same syntax-conditioned product law; it is not native EPIC. This is an illustrative consumer check, not an external benchmark or a guarantee on unseen records. The archived capture also records the optional pinned consumer and full-logit audits; ordinary offline replay does not rerun those checks.

Generate: `python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1 --summary`.
