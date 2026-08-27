# TASKS.md — Exact MWPC for CFG-Constrained dLLMs

## How to use this file

This is the authoritative checklist for current and future work. `AGENTS.md`
defines stable scientific invariants; `IMPLEMENTATION_PLAN.md` explains the
design. Detailed completed evidence through M10 is archived in
[`docs/history/TASKS-through-M10.md`](docs/history/TASKS-through-M10.md).

Status convention: `[ ]` incomplete, `[x]` completed with immutable evidence,
and `BLOCKED:` a concrete gate failure. Complete required tasks in dependency
order, never substitute measurements with estimates, and do not redo a closed
milestone unless a regression invalidates its evidence.

## Current starting point

**M12 / T1202.** M0 through M11, the M10.5 hardening pass, and T1200--T1201
are complete. The first incomplete required task is T1202: statistical
summaries.

## Completed milestone summary

- **M0--M7:** pinned baseline, formal contracts, Python/Rust exact parsers,
  exhaustive gates, tokenizer-aware finite lattices, and EOS/PAD exactness.
- **M8:** proposals, adaptive support, typed validation/commit authority,
  fallbacks, profiling, and offline exact-step integration.
- **M9:** pinned LLaDA integration, baseline preservation, saved-logit loop, and
  one live correctness smoke.
- **M10:** shared frozen selector input, precise baseline adapters, guarded brute
  force, and versioned replay artifacts.
- **M10.5:** compact ranked support, pinned-EPIC integration CI, total selector
  deadlines, precise component-selector names, fair candidate-universe checks,
  executable exact/EPIC grammar alignment, and evaluation-package cleanup.

See `docs/evidence/`, `docs/decisions/`, and the archived checklist for exact
commits, commands, configured-case boundaries, and result counts.

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

- [ ] Compute agreement and confidence intervals where appropriate.
- [ ] Compute gap distributions and equality rates.
- [ ] Compute runtime median/IQR and normalized overhead.
- [ ] Compute fallback, timeout, and support-expansion rates.
- [ ] Clearly separate per-step and per-generation quantities.

**Acceptance criteria**

- [ ] Analysis code has unit tests for formulas and edge cases such as zero optimum.

**Evidence:** `[tests and outputs]`

## T1203 — Generate final tables and figures

**Depends on:** T1202

- [ ] Correctness/oracle table.
- [ ] Heuristic-gap table or distribution plot.
- [ ] Finite-slot counterexample figure/table.
- [ ] Runtime breakdown.
- [ ] Scaling plot.
- [ ] End-to-end summary.
- [ ] Captions state support scope and model/task configuration.

**Acceptance criteria**

- [ ] Every displayed value traces to a raw run ID.

**Evidence:** `[artifact paths]`

## T1204 — Write reproduction instructions

**Depends on:** T1201, T1203

- [ ] Document environment creation.
- [ ] Document binding build.
- [ ] Document model/data preparation without embedding secrets.
- [ ] Provide commands for each main table/figure.
- [ ] Distinguish CPU-only correctness reproduction from GPU end-to-end reproduction.
- [ ] Record expected artifact filenames, not unmeasured scientific values.

**Acceptance criteria**

- [ ] A clean-environment rehearsal reproduces at least the CPU correctness table.

**Evidence:** `[rehearsal log]`

**M12 reproducibility gate — blocking**

- [ ] Main claims trace to code, config, raw data, and generated artifacts.

---

# M13 — Synchronize implementation with the TCC

## T1300 — Fill implementation-method fields in LaTeX

**Depends on:** M12 gate

- [ ] Insert exact repository and upstream commits.
- [ ] Insert module/backend architecture.
- [ ] Insert grammar normalization and epsilon handling.
- [ ] Insert tokenizer byte semantics.
- [ ] Insert support/top-`K` policy and exactness wording.
- [ ] Insert candidate/weight policy.
- [ ] Insert EOS/PAD, timeout, tie, and fallback behavior.
- [ ] Insert model, tokenizer, hardware, and software versions.

**Acceptance criteria**

- [ ] No implementation field is filled from memory when an artifact can provide it.
- [ ] Paper claims match the actual code path.

**Evidence:** `[LaTeX commit and metadata source]`

## T1301 — Fill and analyze results

**Depends on:** T1203

- [ ] Import generated tables/figures.
- [ ] Report correctness campaign size and agreement.
- [ ] Analyze heuristic gaps.
- [ ] Analyze finite-slot findings.
- [ ] Analyze runtime/memory and the dominant component.
- [ ] Analyze end-to-end validity, fallbacks, and limitations.
- [ ] Report negative or null findings honestly.

**Acceptance criteria**

- [ ] Every number is generated by a script and traceable.
- [ ] No smoke-test result is presented as a benchmark conclusion.

**Evidence:** `[paper build and artifact links]`

## T1302 — Update limitations and theorem-to-code correspondence

**Depends on:** T1300, T1301

- [ ] State exact-on-support limitations.
- [ ] State tokenizer and byte-level language limitations.
- [ ] State the CFG syntax-versus-semantics limitation.
- [ ] State per-step versus trajectory optimality.
- [ ] State timeout and resource limits.
- [ ] Add a table mapping theorem assumptions to code/config enforcement.

**Acceptance criteria**

- [ ] No theorem assumption is silently violated by the reported experiment.

**Evidence:** `[paper section/commit]`

## T1303 — Fill AI-use declaration

**Depends on:** T1300

- [ ] Name tools, providers, and versions used.
- [ ] State purposes: planning, drafting, review, coding assistance, and related uses.
- [ ] Identify affected sections/components.
- [ ] State that the author reviewed proofs, code, references, and results.
- [ ] Ensure no fabricated data or unattributed text is included.

**Acceptance criteria**

- [ ] Declaration satisfies the institutional regulation.

**Evidence:** `[paper section]`

## T1304 — Create final reproducibility release

**Depends on:** T1301, T1302, T1303

- [ ] Run full Python tests.
- [ ] Run Rust tests and formatting.
- [ ] Rebuild bindings.
- [ ] Re-run publication configs or verify immutable artifacts.
- [ ] Build the final LaTeX PDF.
- [ ] Create a release tag.
- [ ] Archive configs, small raw evidence, processed data, figures, tables, and reproduction instructions.
- [ ] Record known limitations and any non-reproducible external dependency.

**Acceptance criteria**

- [ ] Repository and paper point to the same release commit.
- [ ] Worktree is clean or intentional untracked artifacts are documented.

**Evidence:** `[test summary, tag, archive paths]`

**Required project completion gate**

- [ ] M0–M13 complete.
- [ ] All scientific-contract rules in `AGENTS.md` hold.
- [ ] Correctness evidence is 100% on configured oracle campaigns.
- [ ] Exact end-to-end mode and baselines are reproducible.
- [ ] TCC contains no fabricated or unsupported implementation/result fields.

---

# OPTIONAL O1 — Exact cardinality budget

## O100 — Extend objective with `|B| <= k`

**Depends on:** Required project stable

- [ ] Add a budget dimension or formally equivalent semiring/state construction.
- [ ] Prove recurrence and complexity.
- [ ] Compare with candidate-set truncation semantics.
- [ ] Add brute-force tests.

**Acceptance criteria**

- [ ] Exact budgeted solver agrees with exhaustive subsets.

---

# OPTIONAL O2 — Deterministic lexer transducer

## O200 — Replace byte grammar with token-lattice × lexer composition

**Depends on:** Required byte-level path stable

- [ ] Define lexer state, maximal munch, priority, whitespace, comments, and keyword rules.
- [ ] Compose without losing token provenance or slot count.
- [ ] Validate against an independent lexer on complete strings.
- [ ] Reuse lexeme-level EPIC CFGs only when semantics match exactly.

**Acceptance criteria**

- [ ] Every accepted witness produces the same lexeme sequence as the declared lexer.

---

# OPTIONAL O3 — Incremental parsing across denoising steps

## O300 — Reuse chart/lattice state safely

**Depends on:** Required solver correct and profiled

- [ ] Identify unchanged graph regions between steps.
- [ ] Define invalidation rules.
- [ ] Preserve exactness under updates.
- [ ] Compare incremental and full-recomputation certificates.

**Acceptance criteria**

- [ ] Scores and certificates match full recomputation on all tests.

---

# OPTIONAL O4 — Lazy/full-vocabulary support

## O400 — Add trie/lazy token expansion

**Depends on:** Required top-`K` solver stable

- [ ] Share token byte prefixes without merging token provenance.
- [ ] Generate arcs lazily from parser demand or admissible-prefix analysis.
- [ ] Prove pruning safety.
- [ ] Compare with explicit full support on small vocabularies.

**Acceptance criteria**

- [ ] Lazy and explicit support return equal optimum and valid provenance.

---

# Final evidence index

Fill this section only with real artifacts.

- Baseline commit: `b9f2179caadf8640fe026f7a73833cbda9755876`
- Upstream EPIC commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- Token-aligned correctness artifact: `docs/evidence/m3-differential-summary.json`
- Rust/Python differential artifact: `[TO BE RECORDED]`
- Finite-slot counterexample artifact: `[TO BE RECORDED]`
- Heuristic-gap experiment artifact: `[TO BE RECORDED]`
- Scaling experiment artifact: `[TO BE RECORDED]`
- End-to-end experiment artifact: `[TO BE RECORDED]`
- Reproduction release/tag: `[TO BE RECORDED]`
- Final TCC PDF/source commit: `[TO BE RECORDED]`
