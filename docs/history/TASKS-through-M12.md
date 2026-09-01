# Archived task detail through M12

This file preserves the complete M11 and M12 task definitions, acceptance
criteria, and evidence moved out of the active `TASKS.md` by T1261.

Earlier task history remains available at:

- [`TASKS-through-M10.md`](TASKS-through-M10.md), which links the M0--M8
  archives and preserves M9--M10 in detail;
- [`TASKS-through-M8.md`](TASKS-through-M8.md); and
- [`TASKS-through-M3.md`](TASKS-through-M3.md).

`AGENTS.md` remains the scientific contract. This archive is immutable
completed history and cannot override a later accepted ADR or active task.

---
# M11 — Experiment harness

## T1100 — Add immutable experiment configuration

**Depends on:** M10 gate

- [x] Define configs for correctness, gap, finite slots, scaling, and end-to-end runs.
- [x] Include exactness, support, model, grammar, seed, timeout, and hardware-relevant options.
- [x] Hash normalized configs.
- [x] Save the resolved config with every run.

**Acceptance criteria**

- [x] Re-running one config creates comparable metadata.

**Evidence:** `configs/experiments/q{1,2,3,4,5}_*_smoke_v1.toml` and
`src/mwpc_exact/experiments/config.py`; `python -m pytest -q
tests/exact_commit/test_experiment_config.py` -> 14 passed; two installed-CLI
materializations of Q1 produced byte-identical `resolved-config.json` files
with normalized SHA-256
`eb8d397d22cc6a65881ed49465079e01f571666e64e76f452aa2ac10e63506b4`;
`make check` -> Ruff clean, strict MyPy clean, 9 unit and 506 exact tests
passed; `python -m pytest -q` -> 523 passed; `make paper` -> `main.pdf` built.

## T1101 — Implement Q1 correctness experiment

**Depends on:** T1100, M3 gate, M6 gate

- [x] Run canonical, exhaustive, and randomized small instances.
- [x] Compare all available solvers.
- [x] Fail the experiment on any disagreement.
- [x] Output counts, sizes, seeds, timings, and mismatch fixtures.

**Acceptance criteria**

- [x] Reported agreement is computed, not manually entered.

**Evidence:** implementation commit `bd6b4455102f3b1a7603de8096b3380d4733b13e`;
`python scripts/exact_commit/run_q1_correctness.py --config
configs/experiments/q1_correctness_v1.toml --run-directory
results/raw/q1_correctness_v1/bd6b445 --summary-output
docs/evidence/t1101-q1-correctness-summary.json` from that clean commit -> 249/249
agreements (5 canonical, 144 exhaustive, 100 randomized), with each of the
direct exhaustive oracle, independent Python reference solver, and Rust
production solver reporting 167 `OPTIMAL` and 82 `INFEASIBLE_ON_SUPPORT`;
zero mismatch fixtures were emitted. Raw per-case records are in
`results/raw/q1_correctness_v1/bd6b445/q1-cases.jsonl`, and the versioned,
computed summary is `docs/evidence/t1101-q1-correctness-summary.json`.
`python -m pytest -q tests/exact_commit/test_q1_correctness.py
tests/exact_commit/test_t1101_evidence.py` -> 9 passed; `make check` -> Ruff
clean, strict MyPy clean, 9 unit and 515 exact tests passed; `python -m pytest
-q` -> 532 passed; `make test-rust-parser` -> Rust format, 17 unit, 3
randomized differential, library Clippy, and binding Clippy checks passed;
`make paper` -> `main.pdf` built (15 pages).

## T1102 — Implement Q2 heuristic optimality-gap experiment

**Depends on:** T1100, M10 gate

- [x] Replay identical instances through EPIC, serial, and exact.
- [x] Compute exact/heuristic score, cardinality, absolute gap, relative gap, equality rate, and runtime.
- [x] Include crafted adversarial cases.
- [x] Separate unit and confidence weighting if both are evaluated.

**Acceptance criteria**

- [x] Every gap row references a common instance ID and support scope.

**Evidence:** implementation commit `a8b4e7c499dbf67c7f33a5110e95b4b02738729d`;
`python scripts/exact_commit/run_q2_heuristic_gap.py --config
configs/experiments/q2_heuristic_gap_v1.toml --run-directory
results/raw/q2_heuristic_gap_v1/a8b4e7c --summary-output
docs/evidence/t1102-q2-heuristic-gap-summary.json` from that clean commit -> 6/6
successful paired rows over three common finite-support states in both `unit`
and `confidence` modes, with exact/brute-force score agreement in every row
and independently feasible serial and EPIC selected subsets. On these configured
synthetic cases, unit-weight totals were exact 7, serial 5, and EPIC 3, with
equality counts 1/3 and maximum absolute gaps 1 and 2 for serial and EPIC;
confidence-weight totals were exact 4.4, serial 4.2, and EPIC 2.4, with equality
counts 2/3 and 1/3 and maximum absolute gaps 0.2 and 1.1. Raw per-case records,
including common instance IDs, explicit support specifications, cardinalities,
absolute/relative gaps, and diagnostic single-repetition runtimes, are in
`results/raw/q2_heuristic_gap_v1/a8b4e7c/q2-gap-rows.jsonl`; the versioned,
computed summary is `docs/evidence/t1102-q2-heuristic-gap-summary.json`.
`python -m pytest -q tests/exact_commit/test_q2_gap.py
tests/exact_commit/test_t1102_evidence.py
tests/integration/test_q2_gap_replay.py
tests/integration/test_benchmark_instance_replay.py` -> 11 passed; `make check`
-> Ruff clean, strict MyPy clean, 9 unit and 523 exact tests passed; `python -m
pytest -q` -> 542 passed; `make test-rust-parser` -> Rust format, 17 unit, 3
randomized differential, library Clippy, and binding Clippy checks passed;
`make paper` -> `main.pdf` built (15 pages). The recorded runtimes are explicitly
smoke diagnostics, not publication benchmark measurements.

## T1103 — Implement Q3 finite-slot experiment

**Depends on:** T703, T1100

- [x] Run curated `Sigma*` counterexamples.
- [x] Decide whether to optionally mine real decoder states where abstract and
  finite decisions differ. The curated-only v1 explicitly records zero real
  states.
- [x] Record available slots, minimum required tokens, abstract decision, finite decision, and witness/reason.

**Acceptance criteria**

- [x] Results directly support the finite-slot claim.

**Evidence:** implementation commit `ac447a8644583052806c66f7b4deb39ac66f9378`;
`python scripts/exact_commit/run_q3_finite_slots.py --config
configs/experiments/q3_finite_slots_v1.toml --run-directory
results/raw/q3_finite_slots_v1/ac447a8 --summary-output
docs/evidence/t1103-q3-finite-slot-summary.json` from that clean commit -> 2/2
curated rows passed with config hash
`ac7e619520d69d7a86dd281e9d46a308f7f01d898e55e98583f921d531a09de6`.
Both concrete abstract `Sigma*` witnesses were CFG-valid and accepted, but each
needed two physical tokens (one content token plus required EOS) on a one-slot
canvas. Complete finite-path enumeration independently agreed with the finite
parser: one result was `INFEASIBLE_ON_SUPPORT`, and the other was an `OPTIMAL`
EOS-only witness `[1]` with objective 1 instead of the abstract objective 10.
The experiment deliberately used no real decoder states and records that count
as zero. Raw rows with slot accounting, both decisions, support hashes, and
witness/reason fields are in
`results/raw/q3_finite_slots_v1/ac447a8/q3-finite-slot-rows.jsonl`; the
versioned computed summary is
`docs/evidence/t1103-q3-finite-slot-summary.json`. `make
test-m7-counterexamples` reproduced both dependency fixtures; `python -m
pytest -q tests/exact_commit/test_finite_slot_counterexamples.py
tests/exact_commit/test_q3_finite_slots.py
tests/exact_commit/test_t1103_evidence.py` -> 10 passed; `make check` -> Ruff
clean, strict MyPy clean, 9 unit and 529 exact tests passed; `python -m pytest
-q` -> 548 passed; `make paper` -> `main.pdf` built (15 pages). The recorded
single-repetition runtimes are smoke diagnostics, not publication benchmarks.

## T1104 — Implement Q4 scaling experiment

**Depends on:** T1100, M8 gate

- [x] Sweep slots, top-`K`, graph size, grammar size, token byte length, and proposal count.
- [x] Separate Python reference and Rust production backends.
- [x] Record time breakdown, RAM, chart entries, nodes, and edges.
- [x] Enforce resource/time limits and report censored/timeouts explicitly.

**Acceptance criteria**

- [x] No timeout is plotted as a successful runtime or infeasibility.

**Evidence:** implementation commit
`66b8b5d7ef908a40ea94018fbe3502cbc3a1c5c1`; `python
scripts/exact_commit/run_q4_scaling.py --config
configs/experiments/q4_scaling_v1.toml --run-directory
results/raw/q4_scaling_v1/66b8b5d --summary-output
docs/evidence/t1104-q4-scaling-summary.json` from that clean commit -> 84/84
independently validated `OPTIMAL` measurements across 21 one-axis points, two
repetitions, and the separate Python reference and Rust production backends.
All 42 paired backend comparisons used matching instance, grammar, and support
hashes and agreed on status and objective; there were zero mismatches,
timeouts, censored rows, errors, or unsupported outcomes under config hash
`fc27e36df5e957abd73f6dbd0d286dc6e890445d86580c1692f5362509546a4b`.
Raw rows with complete certificates, support scopes, component timing
breakdowns, isolated-worker peak RSS, chart entries, and token/terminal graph
node and edge counts are in
`results/raw/q4_scaling_v1/66b8b5d/q4-scaling-rows.jsonl`; the derived
plot-input file contains only uncensored conclusive rows at
`results/raw/q4_scaling_v1/66b8b5d/q4-scaling-plot-rows.jsonl`; and the
versioned computed summary is
`docs/evidence/t1104-q4-scaling-summary.json`. Each repetition ran in a fresh
2 GiB address-space-limited subprocess with a 10-second wall deadline for both
backends and the additional native Rust deadline. `python -m pytest -q
tests/exact_commit/test_q4_scaling.py
tests/exact_commit/test_t1104_evidence.py` -> 7 passed, including a
deterministic injected-timeout regression that retained `TIMEOUT`, emitted no
successful runtime, and produced no plot row. `make check` -> Ruff clean,
strict MyPy clean, 9 unit and 536 exact tests passed; `python -m pytest -q` ->
555 passed; `make test-rust-parser` -> Rust format, 17 unit, 3 randomized
differential, library Clippy, and binding Clippy checks passed; `make paper` ->
`main.pdf` built (15 pages). The recorded runtimes and RAM are diagnostic CPU
smoke measurements, not publication benchmark results.

## T1105 — Implement Q5 end-to-end experiment

**Depends on:** T904, T1100

- [x] Freeze `[MODEL_ID]`, tokenizer revision, tasks, grammars, prompts, generation settings, and seeds.
- [x] Run unconstrained, serial, EPIC, and exact as hardware permits.
- [x] Record syntactic validity, functional metric when available, steps, batch sizes, fallbacks, support expansions, statuses, time, RAM, and VRAM.
- [x] Save generated outputs and checker results.

**Acceptance criteria**

- [x] Methods use the same prompts, model revision, and schedule unless the difference is documented.

**Evidence:** implementation commit
`c8587d26c02879fdc0996dd3db31038864d7a536`; the pinned executable config is
`configs/experiments/q5_end_to_end_v1.toml` (config hash
`0d7ff568b1a3b9d9d7fb6f0550e7e1837e64dab866583d5deeddaa23cddf8235`).
After installing `requirements/t904-live-cu128.txt`, the read-only EPIC binding,
and `crates/mwpc_parser_py` in `.venv-live`,
`.venv-live/bin/python scripts/exact_commit/run_q5_end_to_end.py --config
configs/experiments/q5_end_to_end_v1.toml --run-directory
results/raw/q5_end_to_end_v1/c8587d2 --summary-output
docs/evidence/t1105-q5-end-to-end-summary.json` from that clean commit -> all
four paired methods completed one configured diffusion step and one model
forward on the pinned local-only NF4 LLaDA revision. The comparison fingerprint
`d42225e38571331eeefa97dfd94f9bda506731edc958a27e27d026a7883ea5c3`
verifies the shared prompt, prompt tokens, model/tokenizer revisions, grammar,
target, seed, and generation schedule. All four independently checked outputs
were grammar-valid and exact target matches. The Rust exact method returned an
independently validated `OPTIMAL` certificate with objective
`3.2833624770448697`, four selected proposals in one batch, explicit top-1
`exact_on_support` scope, zero support expansions, zero empty optimal batches,
and zero fallbacks. Unconstrained, serial, and EPIC each made three one-token
selection decisions plus a recorded EOS suffix update. EPIC was enabled, but
the literal grammar exposed fewer than its configured minimum of two ordinary
candidates, so the regular-cover selector made no call and the EPIC loop used
three explicitly recorded serial-path fallbacks. Raw generated token IDs,
decoded outputs, independent checker results, exact witness/certificate,
statuses, batch and physical-update distributions, component profile, elapsed
time, process RSS, and CUDA peak allocation/reservation are in
`results/raw/q5_end_to_end_v1/c8587d2/q5-end-to-end-rows.jsonl`; the checked-in
computed summary is `docs/evidence/t1105-q5-end-to-end-summary.json`.
`python -m pytest -q tests/exact_commit/test_q5_end_to_end.py
tests/exact_commit/test_t1105_evidence.py` -> 8 passed. `make check` -> Ruff
clean, strict MyPy clean, 9 unit and 544 exact tests passed; `python -m pytest
-q` -> 563 passed. `make test-rust-parser` -> Rust format, 17 unit, 3
randomized differential, library Clippy, and binding Clippy checks passed;
the constrained-decoding regression command -> 19 passed and 4 expected
skips. `make paper` -> `main.pdf` built (15 pages). The recorded single
fixed-order runtimes and memory values are diagnostic smoke measurements, not
publication benchmark results; warmup and robust aggregation were deferred to T1106.
Those controls are implemented and evidenced separately by T1106; the T1105
single-run measurements remain diagnostic only.

## T1106 — Add robust timing and memory instrumentation

**Depends on:** T804, T1104, T1105

- [x] Add warmup control.
- [x] Synchronize CUDA around GPU timing.
- [x] Exclude model load from per-instance time.
- [x] Record repetitions.
- [x] Compute median and IQR for runtime.
- [x] Record CPU RAM and GPU peak memory where available.

**Acceptance criteria**

- [x] Timing code contains no method-specific unfair setup inside the measured region.

**Evidence:** implementation commit
`83ba41d1a29d84d8147319d33b85c6646d743b8e` adds a model-independent,
CPU-tested measurement boundary with accelerator synchronization immediately
before and after each timed call, per-call accelerator peak resets, a 1 ms
process-RSS sampler, type-7 median/IQR aggregation, and explicit error/timeout
exclusion. The Q5 driver now prepares method environments, observers, input
state, model/tokenizer loading, grammar compilation, and shared preprocessing
outside the timer. `configs/experiments/q5_timing_v1.toml` freezes one warmup
per strategy and eight balanced-cyclic measured repetitions, placing every
strategy twice in every order position.

The clean live command `.venv-live/bin/python
scripts/exact_commit/run_q5_end_to_end.py --config
configs/experiments/q5_timing_v1.toml --run-directory
results/raw/q5_timing_v1/83ba41d --summary-output
docs/evidence/t1106-q5-timing-summary.json` produced four successful warmups
and 32/32 successful measured rows. All eight exact rows were independently
validated `OPTIMAL`/`exact_on_support` certificates with zero fallbacks,
support expansions, or empty optimal batches. Raw rows are in the ignored run
directory; the versioned computed summary records runtime median/IQR, per-call
sampled CPU RSS, CUDA allocated/reserved peaks, clean commit/config hashes, and
an explicit non-publication interpretation. On this small instrumentation
sample, median seconds were unconstrained `0.037491226015845314`, serial
`0.0374991940043401`, EPIC `0.03962741300347261`, and exact
`0.15864853450329974`; these are not claimed as general model benchmarks.

`python -m pytest -q tests/exact_commit/test_robust_timing.py
tests/exact_commit/test_q5_end_to_end.py tests/exact_commit/test_t1106_evidence.py`
passed 14 tests; `make check` passed the upstream pin, Ruff, strict MyPy, 9
unit tests, and 551 exact-commit tests; `python -m pytest -q` passed all 570
tests. `make test-rust-parser` passed Rust formatting, 17 unit and 3 randomized
differential tests, plus strict parser/binding Clippy; the constrained-decoding
regression command passed 19 tests with 4 expected skips. `make paper` produced
the 15-page PDF.

**M11 gate**

- [x] All five research-question experiments have executable scripts and versioned configs.

---

# M12 — Analysis, artifacts, and reproducibility

## T1200 — Implement run metadata capture

**Depends on:** M11 gate

- [x] Capture git SHA and dirty status.
- [x] Capture config hash.
- [x] Capture model/tokenizer revisions and grammar hash.
- [x] Capture Python, Rust, CUDA, PyTorch, and Transformers versions.
- [x] Capture CPU, RAM, GPU, VRAM, OS, and thread settings.
- [x] Capture all solver status counts.

**Acceptance criteria**

- [x] Missing critical metadata causes a warning or failed publication-mode run.

**Evidence:** implementation commit
`f62765d69ac8fd30d197077ae189ecd1f5607f02`; clean computed sample
[`docs/evidence/t1200-run-metadata-sample.json`](docs/evidence/t1200-run-metadata-sample.json)
(SHA-256 `136e60fec7b679ed9274f821328380a9911d7ebeccb738254b24be2057fe52cf`).
The sample was generated from that clean commit with
`python scripts/exact_commit/run_q1_correctness.py --run-directory
/tmp/t1200-evidence-f62765d --summary-output
docs/evidence/t1200-run-metadata-sample.json`: all 249 cases agreed, the tree
was recorded clean, metadata integrity had no blockers, and status counts were
captured independently for the exhaustive, Python, and Rust solvers.

Q1--Q4 driver smokes completed with 249/249 Q1 agreement, 0 Q2/Q3 failures,
and 0 Q4 backend mismatches across 84 measurements. The live pinned LLaDA Q5
smoke completed unconstrained, serial, EPIC, and exact runs with 0 contract
failures; its diagnostic artifact recorded CUDA `12.8`, the pinned resolved
model/tokenizer revision, GPU/VRAM, four complete generation statuses, and one
exact `OPTIMAL` status. `python -m pytest -q
tests/exact_commit/test_run_metadata.py
tests/exact_commit/test_experiment_driver_metadata.py
tests/exact_commit/test_t1200_evidence.py` passed 10 tests, including warning
versus publication-failure behavior and the clean-worktree regression. `make
check` passed the upstream pin, Ruff, strict MyPy, 9 unit tests, and 561
exact-commit tests; `python -m pytest -q` passed all 580 tests. `make paper`
produced the 15-page PDF.

## T1201 — Separate raw, processed, and paper artifacts

**Depends on:** T1200

- [x] Write immutable raw JSONL.
- [x] Generate processed CSV/Parquet through scripts.
- [x] Generate figures and LaTeX tables through scripts.
- [x] Do not edit generated numbers manually.
- [x] Store small publication artifacts and document external storage for large raw data.

**Acceptance criteria**

- [x] Deleting processed outputs and rerunning scripts reproduces them from raw data.

**Evidence:** implementation commit
`b463ca37a3225d5ca0eb688e0864fa7e66c1ce0b`; versioned build config
[`configs/analysis/t1201_q3_artifacts_v1.toml`](configs/analysis/t1201_q3_artifacts_v1.toml)
pins the clean two-row Q3 raw input at
[`docs/artifacts/raw/t1201_q3_finite_slots_v1/`](docs/artifacts/raw/t1201_q3_finite_slots_v1/)
(SHA-256 `454b2ec1efd6cff32913d501179050b0008eb974bc5ef4563bd6d62f0e2cd997`).
The producing rows record that implementation commit, `git_dirty=false`, zero
failures, and complete metadata. `make artifacts` generated the tracked CSV
and manifest under
[`docs/artifacts/processed/t1201_q3_finite_slots_v1/`](docs/artifacts/processed/t1201_q3_finite_slots_v1/)
and the generated LaTeX/SVG under
[`paper/generated/t1201_q3_finite_slots_v1/`](paper/generated/t1201_q3_finite_slots_v1/).
After both derived directories were moved aside, `make artifacts` rebuilt all
four files and `cmp` matched every original byte-for-byte; `make
artifacts-check` then independently recomputed and verified their hashes.
`tests/exact_commit/test_artifact_pipeline.py` covers deletion/rebuild,
create-only output, pinned-input validation, and hand-edit rejection;
`tests/exact_commit/test_t1201_evidence.py` verifies the versioned bundle.
`make check` passed the upstream pin, Ruff, strict MyPy, 9 unit tests, and 567
exact-commit tests; `python -m pytest -q` passed all 586 tests; `make paper`
produced the 15-page PDF. Storage and external-archive requirements are
documented in [`docs/artifacts/README.md`](docs/artifacts/README.md); T1201
does not claim an external large-run archive.

## T1202 — Implement statistical summaries

**Depends on:** T1201

- [x] Compute agreement and confidence intervals where appropriate.
- [x] Compute gap distributions and equality rates.
- [x] Compute runtime median/IQR and normalized overhead.
- [x] Compute fallback, timeout, and support-expansion rates.
- [x] Clearly separate per-step and per-generation quantities.

**Acceptance criteria**

- [x] Analysis code has unit tests for formulas and edge cases such as zero optimum.

**Evidence:** implementation commit
`8838ee0d41a27cd1f7bb87ae220ffee399901fae`; the versioned analysis config
[`configs/analysis/t1202_statistics_v1.toml`](configs/analysis/t1202_statistics_v1.toml)
pins the explicitly non-experimental synthetic formula fixture
[`docs/artifacts/raw/t1202_statistics_v1/statistical-observations.jsonl`](docs/artifacts/raw/t1202_statistics_v1/statistical-observations.jsonl)
(SHA-256 `2f91b80894b45cf9ea7b816d59e7daa95a87bf1dab40dd8ab04ceb36b8c215a9`).
`make statistics-check` independently rebuilt and byte-verified
[`docs/artifacts/processed/t1202_statistics_v1/statistical-summary.json`](docs/artifacts/processed/t1202_statistics_v1/statistical-summary.json)
(SHA-256 `40b236f2e5988eca6ccdbe9aa2cb22b5df4cda087dfea34bade4f19f6e34a776`).
The generated artifact records `benchmark_claim=false` and contains Wilson
95% intervals for agreement and equality; type-7 quartile, IQR, and mean
summaries for absolute and relative gaps; median runtime ratio and normalized
median overhead; and separately labeled optimizer-step and generation rates
for fallback, timeout, and support expansion. Exact-optimum-zero rows remain
in equality and absolute-gap summaries but are counted as undefined and
excluded from relative-gap summaries. Q5 generation summaries expose
generation rates while explicitly leaving unavailable step-level rates null
instead of inferring them from aggregated rows.

Deterministic Q1/Q2/Q4 driver smokes produced 249/249 Q1 agreement with a
Wilson interval, six valid Q2 rows with three greedy gap observations, and 84
Q4 measurements with zero timeouts and a Wilson interval; these development
smokes are not claimed as publication benchmarks. Formula, validation,
artifact-integrity, zero-optimum, Wilson-boundary, and analysis-integration
regressions are covered by the T1202 tests. `make check` passed the upstream
pin, Ruff, strict MyPy over 66 files, 9 unit tests, and 585 exact-commit tests;
`python -m pytest -q` passed all 604 tests; `make paper` produced the 15-page
PDF.

## T1203 — Generate final tables and figures

**Depends on:** T1202

- [x] Correctness/oracle table.
- [x] Heuristic-gap table or distribution plot.
- [x] Finite-slot counterexample figure/table.
- [x] Runtime breakdown.
- [x] Scaling plot.
- [x] End-to-end summary.
- [x] Captions state support scope and model/task configuration.

**Acceptance criteria**

- [x] Every displayed value traces to a raw run ID.

**Evidence:** implementation commits
`490a762c53eb923a33e44c3e7dba9d0d1fb37d59` and
`bfaa544b76133eb905628ccc15b90449a2861b18`; the versioned build config is
[`configs/analysis/t1203_final_artifacts_v1.toml`](configs/analysis/t1203_final_artifacts_v1.toml).
It pins five newline-delimited raw inputs under
[`docs/artifacts/raw/t1203_final_results_v1/`](docs/artifacts/raw/t1203_final_results_v1/):
Q1 run `bd6b445` (249 rows, SHA-256 `62fb83b48c8809a3958df486b387e017ba245e97e4e74e475ca1fb55659ade8a`),
Q2 run `a8b4e7c` (6 rows, SHA-256 `1af3865368c0cff24bf75fe103354bd51e0bd42bd7a381ba1b3cec3538a0a2e1`),
Q3 run `ac447a8` (2 rows, SHA-256 `060957e2a68d71a30696b6406e43d737458f0a13ae0ca1abd750885220c3ce20`),
Q4 run `66b8b5d` (84 rows, SHA-256 `4ece645bc4b9a497623738b378bf58bba05805c6fa03bf49a555973dcf8a0765`),
and Q5 run `83ba41d` (32 rows, SHA-256 `1132d0f29561d7b3eca8a72d382c22422275f2f54eb462da264b4fc1da9508b4`).

`make final-artifacts` generated the machine-readable
[`final-results.json`](docs/artifacts/processed/t1203_final_results_v1/final-results.json)
(SHA-256 `fb7910781aadbaa9b8c6706703f03384c3115c14ca120cd1c8c8cdf04a84f04d`),
five LaTeX tables, the heuristic-gap distribution SVG, and the six-axis CPU
scaling SVG under
[`paper/generated/t1203_final_results_v1/`](paper/generated/t1203_final_results_v1/).
The generated
[`artifact-manifest.json`](docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json)
(SHA-256 `8a2900f023257297a53cef3c8f6a76a2288c9a6003a26a25bc23d6a2d9841293`)
records every input/output hash, raw run ID, model/revision, task
configuration, support policy, and `exact_on_support` per-step scope. The Q2
synthetic gap campaign and Q4 CPU scaling campaign remain diagnostics, and the
Q5 fixed-task live-model rows retain `benchmark_claim=false`; none is promoted
to a publication benchmark.

T1251 later corrected only the Q1 uncertainty presentation from the same
pinned raw rows. The current `final-results.json`, manifest, and correctness
table hashes are respectively
`b72d6fd08429e3eb3c18fca4e5788a4fe3617a62a1972deedd6801cd176884d0`,
`06e9e8d86441b4f35a0fb863654b797081a62608ea729e7bab3dc870ea2f369f`,
and `119fd38aeec70ef870941fe13a528a62170bb8e20bebf5f0b0842033e2fdad7b`;
the five raw input hashes are unchanged.

A clean delete/rebuild followed by `diff -qr` reproduced both derived
directories byte-for-byte, and `make final-artifacts-check` independently
recomputed and verified every artifact. All five tables compiled in a
five-page render rehearsal and were visually checked alongside both SVGs for
clipping, overlap, and legibility. `python -m pytest -q
tests/exact_commit/test_final_artifacts.py
tests/exact_commit/test_t1203_evidence.py` -> 6 passed; `make check` -> upstream
pin verified, Ruff clean, strict MyPy clean over 67 files, 9 unit tests and 591
exact-commit tests passed; `python -m pytest -q` -> 610 passed; `make paper` ->
`main.pdf` built (15 pages).

## T1204 — Write reproduction instructions

**Depends on:** T1201, T1203

- [x] Document environment creation.
- [x] Document binding build.
- [x] Document model/data preparation without embedding secrets.
- [x] Provide commands for each main table/figure.
- [x] Distinguish CPU-only correctness reproduction from GPU end-to-end reproduction.
- [x] Record expected artifact filenames, not unmeasured scientific values.

**Acceptance criteria**

- [x] A clean-environment rehearsal reproduces at least the CPU correctness table.

**Evidence:** implementation commit
`28a42e4d93791d32d0d356a6234023cee93dc242`; the authoritative
[`REPRODUCING.md`](REPRODUCING.md) documents the Python 3.11 CPU environment,
exact Rust and pinned EPIC binding builds, versioned raw-data boundary, commands
and expected filenames for all five tables and two figures, CPU experiment
reruns, and the separately isolated optional CUDA environment. Model weights
remain in an external Hugging Face cache at the exact configured revision;
credentials are neither embedded nor written to captured logs, and Q5 remains
local-files-only with no external task dataset.

`make rehearse-cpu-correctness` ran
[`scripts/rehearse_cpu_correctness.sh`](scripts/rehearse_cpu_correctness.sh)
from the clean implementation commit. It cloned that commit into a new
temporary checkout, initialized EPIC at
`5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, created a new `.venv` with
`make bootstrap`, moved the tracked derivatives aside inside the disposable
clone, ran `make final-artifacts`, and byte-compared the regenerated
`paper/generated/t1203_final_results_v1/correctness-oracle-table.tex` with its
tracked reference. The rehearsal emitted `T1204_CPU_REHEARSAL=PASS` and SHA-256
`b5af0c912778ac5bfecee95354de6b1fdd6820aad71359aedbd179b7f3329694`, then
`make final-artifacts-check` verified the complete regenerated bundle. The
temporary checkout was removed at exit.

`python -m pytest -q tests/exact_commit/test_reproduction_instructions.py` ->
3 passed, covering manifest-to-document filename synchronization, CPU/GPU and
scope wording, credential safety, shell syntax, clean-clone behavior, and the
non-destructive temporary-directory policy. `make check` -> upstream pin
verified, Ruff clean, strict MyPy clean over 67 files, 9 unit tests and 594
exact-commit tests passed; `python -m pytest -q` -> 613 passed; `make paper` ->
`main.pdf` built (15 pages). No GPU/model rerun was needed or claimed for this
CPU reproduction acceptance test.

**M12 reproducibility gate — blocking**

- [x] Main claims trace to code, config, raw data, and generated artifacts.

**Gate evidence:** `REPRODUCING.md` records the explicit path from
`src/mwpc_research/final_artifacts.py` and its CLI through the pinned T1203
analysis config and versioned Q1--Q5 JSONL rows to `final-results.json`, the
hash manifest, and each generated LaTeX/SVG artifact. The clean rehearsal and
T1203 evidence tests independently verified that chain.

---

