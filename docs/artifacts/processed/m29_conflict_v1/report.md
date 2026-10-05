# Certified exact commitment with two-sided proof reuse

All methods use the same 72 original inputs, 36 saved LLaDA states and two reward profiles. All caps 0, 1 and 2 are retained. These are repeated measures, not 72 independent requests. No new model generation or semantic-quality benefit is claimed.

Independent original-input/certificate and complete-cohort audit: **PASS**.

The general conflict-learning/hitting-set and certificate principles are established. The implemented incremental contribution is exact budgeted token commitment with portable original-input proofs and two-sided reuse across changing logits/support.

## Mathematically established use

Every returned optimum maximizes the unchanged rational budget objective. A CFG conflict forbids its supersets; certified master covers upper-bound every feasible batch. Negative proofs transport under retained-support contraction; positive witnesses are revalidated and may survive expansion. If a stored witness attains the current master bound, exact commitment needs zero new CFG-oracle queries.

With H learned conflicts and T solves of budget at most B, feasibility queries are bounded by T+(B+1)H. In the documented fixed two-slot family, cold solving uses 4T queries and two-sided reuse uses four total. Proofs and correspondence are in `docs/research/m29-conflict-commitment.md`; Lean checks the specified cover, transport and query-count theorems, rather than claiming source-level refinement.

## Complete real-state timing

The DP computes the common frontier once. Other methods' times below sum the three budget queries per input, then take the median of their three repetitions and the median across all inputs of the family. DP has one fresh repetition. Solve time includes mandatory internal proof construction/checking; portable serialization and external verification are separate. Each worker uses the same pinned CPU.

| Family | DP | Ranked subsets | Conflict cold | Conflict reuse | Witness only | Two-sided reuse |
|---|---:|---:|---:|---:|---:|---:|
| arithmetic | 0.552284 | 0.040995 | 0.043187 | 0.042581 | 0.004164 | 0.004174 |
| brackets | 0.321001 | 0.032851 | 0.032819 | 0.034263 | 0.010587 | 0.010594 |
| geocoding | 45.007743 | 0.379035 | 0.471184 | 0.466508 | 0.233296 | 0.232901 |
| nested_json | 1.781790 | 0.110850 | 1.317688 | 0.606915 | 1.308658 | 0.601177 |

## Every comparator retained

| Comparator | Paired inputs | Two-sided faster | Median paired speed ratio |
|---|---:|---:|---:|
| resource_dp | 72 | 68 | 42.929 |
| ranked_subsets | 72 | 54 | 2.161 |
| conflict_cold | 72 | 68 | 2.740 |
| conflict_reuse | 72 | 66 | 2.174 |
| witness_only | 72 | 47 | 1.006 |

A ratio above one favors two-sided reuse. This is a measured computation comparison on the complete development/replay cohort; no population confidence or advantage over the full EPIC decoder follows. The simple ranked exact comparator remains visible even when it is faster.

## Query counts, including zero-reward cases

| Method | Budget results | CFG-oracle calls | Zero-call optima | Positive-reward zero-call optima |
|---|---:|---:|---:|---:|
| conflict_cold | 648 | 1077 | 0 | 0 |
| conflict_reuse | 648 | 768 | 0 | 0 |
| proof_reuse | 648 | 294 | 474 | 303 |
| ranked_subsets | 648 | 1044 | 0 | 0 |
| resource_dp | 216 | 0 | 0 | 0 |
| witness_only | 648 | 615 | 462 | 303 |

DP query counts are not applicable: it performs weighted resource parsing directly. The reference grammar oracle is unchanged across the other methods.

## Provenance and limits

The two-sided/witness-only follow-up was developed after seeing conflict-only costs on these inputs. Its config was frozen before execution; this is an engineering improvement evaluated on the same cohort, not held-out confirmation.

Status counts: `{"conflict_cold:completed": 648, "conflict_reuse:completed": 648, "proof_reuse:completed": 648, "ranked_subsets:completed": 648, "resource_dp:completed": 72, "witness_only:completed": 648}`.

Producing commits: `bb6613661bb2723e832aee443fc22012e724c6e1`, `e31b6517ff7b9d0762d6c4f4ffeb0479ea64a9a3`, `e60922525aad5fcab173209708ba573095d5720a`.

Configs, raw rows and compressed certificates are retained under `docs/artifacts/raw/m29_conflict_v1/`. The initial metadata-serialization failure occurred before any model-state evaluation. An interrupted run retained 68/72 DP measurements; four missing measurements were run separately. Two missing proofs were regenerated against their archived scores without replacing timing rows. Content-addressed `interruption-audit/inventory.json` retains every file from the failed/interrupted attempts; regeneration time is excluded from solve comparisons. Continuation metadata records all producing commits.

The method optimizes provided model weights; neither these proofs nor the timings certify correct interpretation of a request. Large conflict sets can make the master search expensive. Exact-on-support, finite slots and deadline/infeasibility distinctions remain explicit.
