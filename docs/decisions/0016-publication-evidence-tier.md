# ADR 0016: Separate diagnostic evidence from final-article evidence

- Status: Accepted
- Date: 2026-09-01

## Decision

M13 targets a final TCC article. The existing T1203 bundle remains a
reproducible diagnostic bundle: none of its `publication_mode=false` inputs is
renamed or promoted. The final article may use the existing Q1 configured
correctness campaign and Q3 curated counterexamples for their narrow claims,
but empirical gap, scaling, and end-to-end comparisons require new
`publication_mode=true` Q2, Q4, and Q5 runs.

The predeclared executable configurations are:

- `configs/experiments/q2_real_state_publication_v1.toml`;
- `configs/experiments/q4_scaling_publication_v1.toml`; and
- `configs/experiments/q5_structured_publication_v1.toml`, with tasks frozen by
  `configs/experiments/q5_structured_tasks_v1.toml`.

Their successful raw rows will feed a new
`m125_publication_results_v1` bundle. Neither these runs nor their derivatives
may overwrite `t1203_final_results_v1`. A configured run becomes article
evidence only after its raw rows, resolved configuration, metadata, independent
checks, and derived manifest are versioned and verified.

## Claim-to-evidence matrix

| Question | Current evidence supports | Current evidence does not support | Required final-article evidence |
| --- | --- | --- | --- |
| Q1 | Agreement with exhaustive oracles on all 249 configured finite-support cases; Wilson uncertainty only for the 100 seeded randomized cases | Global-vocabulary exactness, a population error rate for fixed cases, or representative runtime | Retain the pinned campaign and corrected T1251 presentation |
| Q2 | Illustrative canonical/adversarial behavior on three synthetic states in two weight modes | A representative mean EPIC/serial gap on model states | Replay 30 predeclared saved states from two tasks, three seeds, and five denoising steps through the same three selectors |
| Q3 | Existence of two finite-slot counterexamples and agreement with complete finite-path enumeration | Prevalence of false positives in model workloads | Retain the curated counterexamples and state that no prevalence estimate is made |
| Q4 | Executability, component capture, timeout handling, and Python/Rust agreement on the small CPU smoke | Representative workload scaling, stable sub-millisecond timing, or an isolated causal interpretation of `graph_size_scale` | Run 10 repetitions per point over the expanded ranges in the publication config, preserving censored rows and separate backends |
| Q5 | Live integration, exact certificate validation, and serial fallback behavior on one literal single-content-token task | EPIC parallel commitment, representative overhead, or useful-output improvement | Run two nontrivial structured tasks, three seeds, one warmup and 10 balanced measured repetitions; prove at least one EPIC regular-cover batch larger than one and independently check every output |

All exact results remain per-step `exact_on_support`. No campaign supports a
claim of global exactness over the full vocabulary or future denoising
trajectory.

## Minimum metadata and comparison rules

Every publication run must record the producing commit and clean-worktree
state, normalized config hash, seed, task/example ID, exact model and tokenizer
revisions, grammar hash, support policy and exactness scope, solver status
counts, hardware/software versions, component timings, memory peaks, selected
batches, fallbacks, support expansions, final outputs, and independent witness
or functional validation. Q2 selectors consume the same saved proposal/support
snapshot. Q5 strategies use the same prompt, seed, schedule, model revision,
and task grammar, with any unavoidable difference recorded explicitly.

## Stopping and resource rules

- The predeclared task, seed, repetition, and scale grids are not shortened or
  selectively replaced after observing results.
- Technical failures remain in raw evidence. A replacement attempt is allowed
  only for a documented infrastructure failure and must retain the failed row.
- `TIMEOUT`, `INFEASIBLE_ON_SUPPORT`, `UNSUPPORTED`, and `ERROR` remain distinct.
- Q4 uses a 2 GiB worker address-space limit and 30-second per-solver deadline;
  timeouts and censored rows are excluded from successful runtime distributions
  but included in status counts.
- Q5 uses local-only pinned model files, a 30-second exact-solver deadline, and a
  3,600-second run deadline. Missing local model assets block the run rather
  than triggering an unversioned download.
- Publication mode rejects dirty worktrees or missing critical metadata.

## Consequences

M13 may cite the old bundle only with its diagnostic labels. Broader Q2, Q4,
or Q5 conclusions are blocked until T1253--T1255 produce and verify the new
bundle. The theoretical and correctness claims do not depend on the exact
method outperforming a baseline in runtime or model quality.
