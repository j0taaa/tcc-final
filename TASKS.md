# TASKS.md — Exact MWPC for CFG-Constrained dLLMs

## How to use this file

This is the authoritative checklist for current and future work. `AGENTS.md`
defines stable scientific invariants; `IMPLEMENTATION_PLAN.md` explains the
design. Detailed M0--M8 task evidence is archived in
[`docs/history/TASKS-through-M8.md`](docs/history/TASKS-through-M8.md).

Status convention:

- `[ ]` not completed;
- `[x]` completed and supported by immutable evidence;
- `BLOCKED:` cannot proceed, with a concrete reason;
- `OPTIONAL:` not required for the minimum TCC implementation.

Rules:

1. Complete required tasks in dependency order.
2. Close a task only after every acceptance criterion and required check passes.
3. Record commands, outputs, artifacts, and relevant commits in its Evidence field.
4. A correctness-gate failure blocks later integration and performance work.
5. Never substitute measurements with estimates.
6. Do not redo completed milestones unless a regression invalidates their evidence.

## Current starting point

**M9 / T900.** M0 through M8 are complete. The first incomplete required task
is T900: configuration and strategy dispatch.

Required milestones: **M0 through M13**. Optional milestones: **O1 through O4**.

## Completed milestone summary

- **M0:** pinned EPIC baseline and reproducible Python/Rust environment.
- **M1:** scientific contracts, statuses, scope metadata, and independent validation.
- **M2:** token-aligned Python max-plus CKY with reconstructible certificates.
- **M3:** exhaustive completion/subset oracles and deterministic differential gate.
- **M4:** generic weighted terminal-DAG reference parser and epsilon semantics.
- **M5:** independent Rust parser, PyO3 binding, timeouts, and differential gate.
- **M6:** finite tokenizer-aware token/byte lattice exact on represented support.
- **M7:** explicit EOS/PAD automaton, finite-slot validator, counterexamples, and gate.
- **M8:** proposal policy, first-feasible adaptive support, typed solve/commit boundary, fallbacks, profiling, and offline exact-step integration.

**Post-M8 corrections:** the production decoder now requires a typed
`ValidatedExactCommit` carrying the live independent validation report;
`total_timeout_seconds` rejects late results while documenting that Python
reference attempts are not interruptible; adaptive diagnostics name the
first-feasible stopping policy; campaign code lives in `mwpc_research`; and the
Rust CI path runs the complete current suite plus normal M6/M7 campaigns.

See the archived checklist and `docs/evidence/` for exact commits, commands,
configured-case boundaries, and campaign counts.

---

# M9 — EPIC/dLLM integration

## T900 — Add configuration and strategy dispatch

**Depends on:** M8 gate

- [ ] Add `serial|epic|exact` strategy option to the relevant CLI/config path.
- [ ] Add exact support, weight, timeout, EOS, backend, and fallback options.
- [ ] Keep default behavior backward compatible unless deliberately documented.
- [ ] Validate incompatible options early.

**Acceptance criteria**

- [ ] Existing commands without exact flags retain baseline behavior.
- [ ] Help/config output documents exactness scope.

**Evidence:** `[tests/CLI output]`

## T901 — Add exact hook to the first model adapter

**Depends on:** T900, T600

**Initial target:** `[CHOSEN_ADAPTER]`, likely an existing LLaDA-style constrained loop.

- [ ] Locate the point after logits/confidence and before heuristic/serial commitment.
- [ ] Reuse the baseline `k_s` schedule.
- [ ] Convert the current canvas and logits into the exact API.
- [ ] Commit returned positions/tokens to model tensors and decoded tracking state.
- [ ] Preserve prompt positions and active-block limits.
- [ ] Preserve baseline EOS handling according to the new documented semantics.

**Acceptance criteria**

- [ ] A fixed-logit test confirms the exact hook receives the intended canvas and candidate set.
- [ ] No exact-specific logic leaks into generic parser code.

**Evidence:** `[tests and commit]`

## T902 — Preserve serial and EPIC baselines

**Depends on:** T901

- [ ] Add regression tests for strategy dispatch.
- [ ] Confirm `serial` calls the original serial path.
- [ ] Confirm `epic` calls the existing regular-cover selector.
- [ ] Confirm `exact` does not mutate baseline functions.
- [ ] Compare fixed-seed or saved-logit baseline outputs before and after integration where deterministic.

**Acceptance criteria**

- [ ] No baseline code is deleted or silently redefined.

**Evidence:** `[tests and comparison artifact]`

## T903 — Add saved-logit end-to-end decoder test

**Depends on:** T901

- [ ] Record or synthesize logits for several denoising steps.
- [ ] Run the decoder loop without a live model.
- [ ] Confirm progress, state updates, and final grammar validity.
- [ ] Confirm event logs contain every step.

**Acceptance criteria**

- [ ] Test is deterministic, CPU-only, and offline.

**Evidence:** `[fixture and test]`

## T904 — Run one live-model smoke test

**Depends on:** T902, T903

- [ ] Load `[MODEL_ID]` and the exact tokenizer revision.
- [ ] Record dtype, quantization, and device settings.
- [ ] Run one small structured generation with `serial`, `epic`, and `exact` where feasible.
- [ ] Validate outputs and save raw metadata.
- [ ] Record any memory limitation honestly.

**Acceptance criteria**

- [ ] At least one exact end-to-end generation completes, or a precise model/hardware blocker is documented while offline integration remains passing.
- [ ] No benchmark claim is made from this smoke test alone.

**Evidence:** `[config, command, raw artifact]`

**M9 integration gate**

- [ ] Exact mode is reachable through a real adapter.
- [ ] Baseline modes remain available.
- [ ] Offline-loop and live-smoke evidence exist.

---

# M10 — Common baseline interface and fair comparison

## T1000 — Wrap serial selector in a common evaluation interface

**Depends on:** M9 gate

- [ ] Accept saved canvas, proposals, and support input.
- [ ] Return selected IDs, score, status, runtime, and witness if available.
- [ ] Preserve order semantics.

**Acceptance criteria**

- [ ] The same input can be fed to serial and exact selectors.

**Evidence:** `[tests and commit]`

## T1001 — Wrap EPIC heuristic selector in the common interface

**Depends on:** M9 gate

- [ ] Convert EPIC candidates and current words into common input/output.
- [ ] Record regular-cover and exact-shrink calls/diagnostics.
- [ ] Recompute selected score independently.
- [ ] Keep EPIC behavior unchanged.

**Acceptance criteria**

- [ ] Heuristic and exact receive identical proposals and weights in offline comparisons.

**Evidence:** `[tests and commit]`

## T1002 — Wrap brute force as a small-instance baseline

**Depends on:** T300, T402

- [ ] Expose a common result for tiny token-aligned and graph instances.
- [ ] Add explicit size guard and status.
- [ ] Use it in experiment scripts only when feasible.

**Acceptance criteria**

- [ ] Exact result matches brute force in the common harness.

**Evidence:** `[tests and commit]`

## T1003 — Define a shared benchmark-instance schema

**Depends on:** T1000, T1001, T1002

- [ ] Serialize canvas, support, proposals, weights, grammar ID/hash, and expected metadata.
- [ ] Support saved logits without storing model weights.
- [ ] Version the schema.
- [ ] Add schema validation and migration policy.

**Acceptance criteria**

- [ ] One file can replay serial, EPIC, exact, and brute force where applicable.

**Evidence:** `[schema and fixture]`

**M10 gate**

- [ ] Fair offline selector comparisons are possible from immutable instances.

---

# M11 — Experiment harness

## T1100 — Add immutable experiment configuration

**Depends on:** M10 gate

- [ ] Define configs for correctness, gap, finite slots, scaling, and end-to-end runs.
- [ ] Include exactness, support, model, grammar, seed, timeout, and hardware-relevant options.
- [ ] Hash normalized configs.
- [ ] Save the resolved config with every run.

**Acceptance criteria**

- [ ] Re-running one config creates comparable metadata.

**Evidence:** `[config paths and test]`

## T1101 — Implement Q1 correctness experiment

**Depends on:** T1100, M3 gate, M6 gate

- [ ] Run canonical, exhaustive, and randomized small instances.
- [ ] Compare all available solvers.
- [ ] Fail the experiment on any disagreement.
- [ ] Output counts, sizes, seeds, timings, and mismatch fixtures.

**Acceptance criteria**

- [ ] Reported agreement is computed, not manually entered.

**Evidence:** `[command and raw/summary artifact]`

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
