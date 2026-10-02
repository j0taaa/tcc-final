# Budgeted commitment: real-state demonstration

Producing code: `ac0e5da9300db83adbacf2fee312bcca082d7aec`. Config: `configs/experiments/m28_budgeted_real_replay_v1.json` (SHA-256 `aa6ad04b72feb28438d8ec9a9d56734f4cfbfbced5cdafef8d414000d2a22413`).

The new rational budgeted method is executed here on authentic saved LLaDA states. This is offline replay, not a new denoising trajectory or an accuracy benchmark. The complete frozen cohort is 24 recursive-task snapshots and 12 steps of one geocoding request, each with two declared reward profiles.

Independent verification: **PASS**; 252 method jobs, 216 checked budget certificates. Optimal: 192; infeasible on support: 24.

Optimality certifies the declared proposal weights, finite support and physical-position budget. It does not certify that the witness answers the user's request correctly. Each physical canvas and probability is inherited unchanged; the ordinary profile removes only EOS/PAD rewards.

| Family | Inputs (both profiles) | Optimal caps | Infeasible caps | Timeout jobs | Median frontier seconds |
|---|---:|---:|---:|---:|---:|
| arithmetic | 16 | 48 | 0 | 0 | 0.714 |
| brackets | 16 | 48 | 0 | 0 | 0.337 |
| geocoding | 24 | 72 | 0 | 0 | 48.491 |
| nested_json | 16 | 24 | 24 | 0 | 1.852 |

Budget/profile variants are repeated measures. A single CPU repetition provides descriptive cost, not a statistical speed claim. Status counts retain all jobs; medians exclude unresolved jobs. Full worker time also includes proof serialization and replay of validated updates, so it is reported separately in the JSON summary.

## Same-input objective comparisons

Only an optimal exact result paired with an independently validated feasible batch enters an objective comparison. Unknown feasibility, infeasible native batches, errors and timeouts are not assigned a zero score. EPIC is its unchanged byte batch selector followed by a budget cap; these are not results for its full decoder, serial fallback or resampling. Native requests for serial fallback are excluded from scored comparisons rather than counted as zero-score losses. Minimum-batch filtering remains visible in native diagnostics.

| Family | Profile | Comparator | Feasible paired caps | Strict exact advantages | Largest reward gap |
|---|---|---|---:|---:|---:|
| arithmetic | all_primary | confidence_preselection | 16 | 0 | 0 |
| arithmetic | all_primary | unbudgeted_then_cap | 16 | 0 | 0 |
| arithmetic | ordinary_primary | confidence_preselection | 16 | 0 | 0 |
| arithmetic | ordinary_primary | epic_regular_cover_then_cap | 16 | 0 | 0 |
| arithmetic | ordinary_primary | unbudgeted_then_cap | 16 | 0 | 0 |
| brackets | all_primary | confidence_preselection | 16 | 0 | 0 |
| brackets | all_primary | unbudgeted_then_cap | 16 | 0 | 0 |
| brackets | ordinary_primary | confidence_preselection | 16 | 0 | 0 |
| brackets | ordinary_primary | epic_regular_cover_then_cap | 8 | 0 | 0 |
| brackets | ordinary_primary | unbudgeted_then_cap | 16 | 0 | 0 |
| geocoding | all_primary | confidence_preselection | 24 | 0 | 0 |
| geocoding | all_primary | unbudgeted_then_cap | 24 | 0 | 0 |
| geocoding | ordinary_primary | confidence_preselection | 24 | 0 | 0 |
| geocoding | ordinary_primary | epic_regular_cover_then_cap | 18 | 0 | 0 |
| geocoding | ordinary_primary | unbudgeted_then_cap | 24 | 0 | 0 |
| nested_json | all_primary | confidence_preselection | 8 | 4 | 0.82184946 |
| nested_json | all_primary | unbudgeted_then_cap | 8 | 0 | 0 |
| nested_json | ordinary_primary | confidence_preselection | 8 | 2 | 0.75067114 |
| nested_json | ordinary_primary | epic_regular_cover_then_cap | 8 | 0 | 0 |
| nested_json | ordinary_primary | unbudgeted_then_cap | 8 | 0 | 0 |

## Application of the existing quality-bound theorem

As a post-hoc analysis, the existing M27 independent relaxation checker was applied to **all 128 feasible post-filtered batches**. Its lower and upper bounds coincide in **114** cases. In those cases, the existing witness plus this bound is sufficient to certify budgeted optimality, including under support expansion with unchanged proposals, weights, fixed slots, grammar and EOS/PAD semantics. No joint resource optimization is needed to check that certificate. Loose bounds remain loose; none is labelled optimal from the bound alone.

This is a deterministic certification analysis of every eligible raw batch, not a new hybrid-decoder latency experiment. It demonstrates a practical use of the proved bound; it does not infer a speedup from unmeasured execution. Exact bound values are in `summary.json`.

The split below exposes EOS/PAD and zero-reward contributions; zero reward is a valid but potentially trivial certificate, not evidence of useful content selection.

| Profile | Feasible batches | Tight bound | Zero reward | Tight with positive reward |
|---|---:|---:|---:|---:|
| all-primary | 64 | 60 | 0 | 60 |
| ordinary-primary | 64 | 54 | 10 | 52 |

## Every geocoding state (ordinary-token objective, budget two)

Request: `Find the geographic coordinates of "Belo Horizonte".` Every saved step is shown in order. Witnesses below are certified possible completions, not newly generated final model responses. Token positions are zero-based. The `all_primary` profile and all other caps are in the raw archive.

| Step | Fixed slots | Proposals | Committed positions | Reward | Witness |
|---:|---:|---:|---|---:|---|
| 0 | 0 | 8 | [1, 5] | 0.16818463 | `get_location(name='Find the geographic coordinates of')` |
| 1 | 18 | 7 | [0, 1] | 0.53830816 | `get_location(name='Belo Horizonte')` |
| 2 | 42 | 7 | [0, 1] | 0.90560091 | `get_location(name='Belo Horizonte')` |
| 3 | 44 | 7 | [0, 1] | 0.81538573 | `get_location(name='Belo Horizonte')` |
| 4 | 45 | 7 | [0, 1] | 0.92907861 | `get_location(name='Belo Horizonte')` |
| 5 | 47 | 7 | [0, 1] | 1.7865281 | `get_location(name='Belo Horizonte')` |
| 6 | 51 | 6 | [2, 7] | 0.15217831 | `get_location(name='Belo Horizonte')` |
| 7 | 53 | 6 | [2, 4] | 0.18112966 | `get_location(name='Belo Horizonte')` |
| 8 | 54 | 7 | [4, 6] | 1.995042 | `get_location(name='Belo Horizonte')` |
| 9 | 61 | 2 | [3, 9] | 0.059016388 | `get_location(name='Belo Horizonte')` |
| 10 | 62 | 1 | [9] | 0.99993515 | `get_location(name='Belo Horizonte')` |
| 11 | 63 | 0 | [] | 0 | `get_location(name='Belo Horizonte')` |

## Audit and reproduction

The first attempt was interrupted after harness bugs in finite-batch validation and infeasible-result reporting. It is preserved in `docs/artifacts/raw/m28_budgeted_real_v1/interrupted`; it supplies no final comparisons. The corrected run uses exactly the frozen cohort, weights, supports, methods and limits. Regression tests cover both bugs.

```bash
.venv/bin/python scripts/exact_commit/run_budgeted_real_replay.py \
  --verify docs/artifacts/raw/m28_budgeted_real_v1/completed
.venv/bin/python -m scripts.exact_commit.build_budgeted_real_results --check
```

`inputs/` retains every original scientific instance and source mapping; `proofs/` contains compressed portable original-input certificates; `rows.jsonl` records commitments, full witnesses, exact rational scores, all statuses, native baseline outputs and times. The manifest binds every raw file. Verification requires no model, GPU, network or reoptimization.
