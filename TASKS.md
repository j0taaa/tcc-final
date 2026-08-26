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

**M11 / T1102.** M0 through M10, the M10.5 hardening pass, T1100, and T1101
are complete. The first incomplete required task is T1102: Q2 heuristic
optimality-gap experiment.

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

- [ ] Replay identical instances through EPIC, serial, and exact.
- [ ] Compute exact/heuristic score, cardinality, absolute gap, relative gap, equality rate, and runtime.
- [ ] Include crafted adversarial cases.
- [ ] Separate unit and confidence weighting if both are evaluated.

**Acceptance criteria**

- [ ] Every gap row references a common instance ID and support scope.

**Evidence:** `[command and artifacts]`

## T1103 — Implement Q3 finite-slot experiment

**Depends on:** T703, T1100

- [ ] Run curated `Sigma*` counterexamples.
- [ ] Optionally mine real decoder states where abstract and finite decisions differ.
- [ ] Record available slots, minimum required tokens, abstract decision, finite decision, and witness/reason.

**Acceptance criteria**

- [ ] Results directly support the finite-slot claim.

**Evidence:** `[command and artifacts]`

## T1104 — Implement Q4 scaling experiment

**Depends on:** T1100, M8 gate

- [ ] Sweep slots, top-`K`, graph size, grammar size, token byte length, and proposal count.
- [ ] Separate Python reference and Rust production backends.
- [ ] Record time breakdown, RAM, chart entries, nodes, and edges.
- [ ] Enforce resource/time limits and report censored/timeouts explicitly.

**Acceptance criteria**

- [ ] No timeout is plotted as a successful runtime or infeasibility.

**Evidence:** `[command and artifacts]`

## T1105 — Implement Q5 end-to-end experiment

**Depends on:** T904, T1100

- [ ] Freeze `[MODEL_ID]`, tokenizer revision, tasks, grammars, prompts, generation settings, and seeds.
- [ ] Run unconstrained, serial, EPIC, and exact as hardware permits.
- [ ] Record syntactic validity, functional metric when available, steps, batch sizes, fallbacks, support expansions, statuses, time, RAM, and VRAM.
- [ ] Save generated outputs and checker results.

**Acceptance criteria**

- [ ] Methods use the same prompts, model revision, and schedule unless the difference is documented.

**Evidence:** `[commands/configs/raw artifacts]`

## T1106 — Add robust timing and memory instrumentation

**Depends on:** T804, T1104, T1105

- [ ] Add warmup control.
- [ ] Synchronize CUDA around GPU timing.
- [ ] Exclude model load from per-instance time.
- [ ] Record repetitions.
- [ ] Compute median and IQR for runtime.
- [ ] Record CPU RAM and GPU peak memory where available.

**Acceptance criteria**

- [ ] Timing code contains no method-specific unfair setup inside the measured region.

**Evidence:** `[tests and sample output]`

**M11 gate**

- [ ] All five research-question experiments have executable scripts and versioned configs.

---

# M12 — Analysis, artifacts, and reproducibility

## T1200 — Implement run metadata capture

**Depends on:** M11 gate

- [ ] Capture git SHA and dirty status.
- [ ] Capture config hash.
- [ ] Capture model/tokenizer revisions and grammar hash.
- [ ] Capture Python, Rust, CUDA, PyTorch, and Transformers versions.
- [ ] Capture CPU, RAM, GPU, VRAM, OS, and thread settings.
- [ ] Capture all solver status counts.

**Acceptance criteria**

- [ ] Missing critical metadata causes a warning or failed publication-mode run.

**Evidence:** `[sample metadata]`

## T1201 — Separate raw, processed, and paper artifacts

**Depends on:** T1200

- [ ] Write immutable raw JSONL.
- [ ] Generate processed CSV/Parquet through scripts.
- [ ] Generate figures and LaTeX tables through scripts.
- [ ] Do not edit generated numbers manually.
- [ ] Store small publication artifacts and document external storage for large raw data.

**Acceptance criteria**

- [ ] Deleting processed outputs and rerunning scripts reproduces them from raw data.

**Evidence:** `[commands and paths]`

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
