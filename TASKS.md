# TASKS.md — Exact MWPC for CFG-Constrained dLLMs

## How to use this file

This is the authoritative execution checklist. `AGENTS.md` defines repository-wide behavior and scientific invariants; this file defines what to build.

Status convention:

- `[ ]` not completed;
- `[x]` completed and supported by evidence;
- `BLOCKED:` task cannot proceed, with a concrete reason recorded;
- `OPTIONAL:` not required for the minimum TCC implementation.

Rules:

1. Complete required tasks in dependency order.
2. Do not mark acceptance criteria separately from the task; the task is complete only when every required checkbox under it is complete.
3. Add commands, outputs, artifact paths, and relevant commits to the `Evidence` line.
4. A correctness-gate failure blocks later integration/performance milestones.
5. Do not substitute measured values with estimates.

Current starting point: **M2 / T200**. M0 through the M1 gate are complete at the
immutable commits recorded below; no MWPC solver result is claimed by the M0
baseline.

Required milestones: **M0 through M13**.

Optional milestones: **O1 through O4**.

---

# M0 — Baseline, repository provenance, and reproducible environment

## T000 — Create the working fork and record upstream provenance

**Depends on:** none

- [x] Initialize the pinned read-only submodule `vendor/EPIC-Decoding` from `hyundong98/EPIC-Decoding`.
- [x] Record the exact upstream URL, default branch, and commit SHA in `UPSTREAM.md`.
- [x] Preserve `LICENSE` and `THIRD_PARTY_LICENSES.md`.
- [x] Verify that `.gitmodules` points to the official upstream and that the submodule is at the SHA recorded in `UPSTREAM.md`.
- [x] Confirm that no generated model weights, caches, or credentials are tracked.

**Acceptance criteria**

- [x] `UPSTREAM.md` identifies an immutable base commit.
- [x] `git status` contains no accidental generated files.
- [x] Existing license notices are unchanged.

**Evidence:** `./scripts/verify_upstream.sh` verified the official URL, `main`
branch, clean submodule, gitlink SHA `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`,
and the two notice hashes recorded in `UPSTREAM.md`; staged large/generated-file
and credential-assignment scans returned no findings. Frozen in
`b9f2179caadf8640fe026f7a73833cbda9755876`.

## T001 — Build a clean Python/Rust environment

**Depends on:** T000

- [x] Create `.venv` with Python 3.11.
- [x] Install the project editable dependencies.
- [x] Install Maturin.
- [x] Build `rustformlang_bindings` in release mode.
- [x] Verify that Python imports `rustformlang` from the newly built binding.
- [x] Record Python, pip, Rust, Cargo, compiler, and Maturin versions in `docs/environment-baseline.md`.

**Acceptance criteria**

- [x] `python -c "import constrained_diffusion, rustformlang"` succeeds.
- [x] The binding is rebuilt from the current checkout rather than an unrelated wheel.
- [x] Setup commands are repeatable from a clean shell.

**Required checks**

```bash
python -c "import constrained_diffusion, rustformlang; print('ok')"
```

**Evidence:** `make bootstrap` and `make bootstrap-epic` completed; Maturin built
the binding in release mode from `vendor/EPIC-Decoding/rustformlang_bindings`;
`python -c "import constrained_diffusion, rustformlang; print('ok')"` printed
`ok`; `python -m pip check` found no broken requirements. Versions, hardware,
package-metadata workaround, and relative import paths are in
`docs/environment-baseline.md`.

## T002 — Run and freeze baseline tests

**Depends on:** T001

- [x] Run the complete existing Python test suite before changing behavior.
- [x] Run the Rust library tests.
- [x] Record all passing/failing tests and runtime in `docs/baseline-tests.md`.
- [x] If a test fails before any changes, preserve the full failure and classify it as environment, dependency, or upstream behavior.
- [x] Create a baseline tag or immutable commit after recording results.

**Acceptance criteria**

- [x] There is a written baseline against which regressions can be distinguished.
- [x] No existing test is deleted or skipped to create a clean baseline.

**Required checks**

```bash
python -m pytest -q
cargo test --manifest-path rustformlang/Cargo.toml
```

**Evidence:** `python -m pytest -q`: 13 passed in 0.10 s;
`make test-upstream`: 406 passed, 8 pre-existing skips in 53.97 s;
`cargo test --manifest-path vendor/EPIC-Decoding/rustformlang/Cargo.toml`:
63 passed, 1 pre-existing ignored test. Full classifications and timings are in
`docs/baseline-tests.md`; immutable baseline commit:
`b9f2179caadf8640fe026f7a73833cbda9755876`.

## T003 — Run one existing decoder smoke path

**Depends on:** T001

- [x] Identify one existing constrained-decoding entry point that can run in the available environment.
- [x] Prefer a tiny/local fixture; do not make baseline CI depend on downloading a large model.
- [x] Record command, configuration, and output.
- [x] If no model artifact is available, run the deepest model-free path and document the missing external dependency.

**Acceptance criteria**

- [x] The existing EPIC path is understood well enough to identify the later exact-strategy hook.
- [x] The smoke path is documented without pretending unavailable model inference was run.

**Evidence:** `python scripts/smoke_epic_baseline.py` accepted `a b` and rejected
`a a` through the compiled CFG-on-terminal-graph path. Command, JSON output,
the raw-CFG deadlock regression/workaround, later LLaDA/Dream hook, and absence
of a local model checkpoint are recorded in `docs/baseline-smoke.md` and
`tests/integration/test_epic_baseline.py`.

## T004 — Add project documentation skeleton

**Depends on:** T000

- [x] Add `docs/decisions/` for architecture decision records (ADRs).
- [x] Add `configs/exact_commit/` for immutable experiment configurations.
- [x] Add `scripts/exact_commit/` for experiment and reproduction scripts.
- [x] Add `tests/exact_commit/`.
- [x] Add gitignored `artifacts/`, `results/raw/`, and model-cache paths.
- [x] Add a short README section pointing to `AGENTS.md`, `TASKS.md`, and the implementation plan.

**Acceptance criteria**

- [x] Repository structure exists without moving unrelated upstream files.
- [x] Generated/large artifacts are ignored.

**Evidence:** `docs/decisions/README.md`, `configs/exact_commit/README.md`,
`scripts/exact_commit/README.md`, `tests/exact_commit/README.md`, root and paper
`.gitignore` files, and the README directory map; commit
`b9f2179caadf8640fe026f7a73833cbda9755876`.

---

# M1 — Scientific contracts and stable data types

## T100 — Create solver status and exactness-scope types

**Depends on:** T004

**Target file:** `src/mwpc_exact/types.py`

- [x] Add `SolveStatus` with `OPTIMAL`, `INFEASIBLE_ON_SUPPORT`, `TIMEOUT`, `UNSUPPORTED`, and `ERROR`.
- [x] Add `SupportKind` with `FULL`, `TOP_K`, and `EXPLICIT`.
- [x] Add immutable `ExactnessScope` metadata.
- [x] Validate `top_k`, vocabulary size, special tokens, and adaptive expansions.
- [x] Provide JSON-serializable conversion.

**Acceptance criteria**

- [x] Timeout cannot be represented as infeasible.
- [x] A top-`K` result cannot omit its value of `K`.
- [x] Round-trip serialization tests pass.

**Evidence:** `python -m pytest -q tests/exact_commit/test_exactness_scope.py
tests/unit/test_types.py`: 22 passed; `make check`: 12 unit tests passed with
Ruff and strict MyPy clean; `python -m pytest -q`: 27 passed. Implementation
commit: `f2beb93ddc1c0457296956d4c1c975fa7fc74ba7`.

## T101 — Define `Proposal` and proposal aggregation

**Depends on:** T100

- [x] Add immutable `Proposal(proposal_id, position, token_id, weight, model_confidence)`.
- [x] Reject duplicate proposal IDs.
- [x] Reject negative, NaN, and infinite weights.
- [x] Permit multiple proposals at one position.
- [x] Aggregate weights and proposal IDs for identical `(position, token_id)` choices.
- [x] Keep model confidence separate from the theorem-level weight.

**Acceptance criteria**

- [x] Duplicate proposal objects remain distinguishable by ID.
- [x] Aggregation returns the exact sum and exact set/list of IDs.

**Evidence:** `python -m pytest -q tests/exact_commit/test_proposals.py
tests/unit/test_types.py`: 21 passed; `make check`: Ruff and strict MyPy clean
with 12 unit tests passed; `python -m pytest -q`: 40 passed. Implementation
commit: `53d4e31b4c7ae7e06cb61dbc42ff5f8ef5494fa6`.

## T102 — Define graph, lattice, and result contracts

**Depends on:** T100, T101

- [x] Add `TokenArc`, `TerminalEdge`, `WeightedTerminalDAG`, and `ExactCommitResult` dataclasses or equivalent types.
- [x] Use stable integer IDs for nodes and edges.
- [x] Include witness tokens, terminal labels, graph-edge IDs, selected proposals, objective, scope, and diagnostics.
- [x] Ensure `OPTIMAL` construction requires certificate fields.
- [x] Ensure non-optimal statuses do not accidentally expose an uncertified objective as optimal.

**Acceptance criteria**

- [x] Invalid graph endpoints and malformed result/status combinations fail fast.
- [x] Result objects serialize to JSON metadata without losing IDs or status.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_graph_and_result_contracts.py tests/unit/test_types.py`:
23 passed; `make check`: Ruff and strict MyPy clean with 12 unit tests passed;
`python -m pytest -q`: 55 passed. Implementation commit:
`bb16f0f8bbe99f7c99af78095eb633853f586772`.

## T103 — Freeze objective and candidate semantics in ADRs

**Depends on:** T101

- [x] Create `docs/decisions/0001-objective-and-weights.md`.
- [x] Define arbitrary non-negative weights, `unit`, and `confidence` modes.
- [x] State that confidence sums are utilities, not joint probabilities.
- [x] Create `docs/decisions/0002-candidate-set-and-schedule.md`.
- [x] Define `C` as proposals from the `k_s` schedule-selected positions.
- [x] State that alternatives outside the proposal token carry zero proposal reward.
- [x] Define deterministic ordering and tie behavior.

**Acceptance criteria**

- [x] Code comments and ADR terminology use the same objective.
- [x] No unresolved ambiguity remains about whether the solver may commit more than `k_s` proposals.

**Evidence:** `docs/decisions/0001-objective-and-weights.md` and
`docs/decisions/0002-candidate-set-and-schedule.md`; `make check` passed with
Ruff, strict MyPy, and 12 unit tests; `python -m pytest -q tests/exact_commit`:
42 passed; full Python suite: 55 passed. Commit:
`d50bdc61ae139b88e4e5006dd5f537c344c6d23d`.

## T104 — Freeze exactness and failure terminology

**Depends on:** T100

- [x] Create `docs/decisions/0003-exactness-scope.md`.
- [x] Define exactness over full, explicit, and top-`K` support.
- [x] Define adaptive support expansion semantics.
- [x] Define `INFEASIBLE_ON_SUPPORT` versus global infeasibility.
- [x] Define timeout/error fallback logging.

**Acceptance criteria**

- [x] Every public result can be named without overstating its guarantee.
- [x] The TCC wording can be derived directly from this ADR.

**Evidence:** `docs/decisions/0003-exactness-scope.md` and aligned
`docs/scientific-contract.md`; `make check` passed with Ruff, strict MyPy, and
12 unit tests; `python -m pytest -q tests/exact_commit`: 42 passed; full Python
suite: 55 passed. Commit: `913f2edc5c9dab52f3afae00403cdf7508fff228`.

## T105 — Create an independent certificate validator interface

**Depends on:** T102

**Target file:** `src/mwpc_exact/validator.py`

- [x] Define validation checks without calling the weighted parser as an oracle.
- [x] Validate fixed positions, slot count, proposal matches, score, edge continuity, and result metadata.
- [x] Allow later injection of a boolean CFG recognizer and tokenizer/EOS validators.
- [x] Return structured validation failures, not a bare boolean.

**Acceptance criteria**

- [x] Unit tests detect deliberately corrupted witness tokens, scores, proposal IDs, and paths.

**Evidence:** `python -m pytest -q tests/exact_commit/test_validator.py`: 11
passed; `make check`: Ruff and strict MyPy clean with 12 unit tests;
`python -m pytest -q tests/exact_commit`: 53 passed; full Python suite: 66
passed. Implementation commit: `f4670378800de5e4fb1c5c58c9c468bce77b14fe`.

**M1 gate**

- [x] All M1 tasks complete.
- [x] `python -m pytest -q tests/exact_commit` passes.
- [x] Public terminology matches `AGENTS.md`.

---

# M2 — Token-aligned Python reference solver

## T200 — Implement a small internal CNF representation

**Depends on:** M1 gate

**Target:** `src/mwpc_exact/reference/grammar.py`

- [x] Define terminal and binary productions with stable IDs.
- [x] Define symbol tables for nonterminals and terminals.
- [x] Validate the start symbol and production references.
- [x] Provide an adapter from the repository CFG representation.
- [x] Document epsilon/unit-production assumptions.

**Acceptance criteria**

- [x] Handwritten CNF grammars round-trip through the representation.
- [x] Malformed grammars are rejected with useful messages.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_reference_grammar.py`: 10 passed; `python -m pytest -q
tests/exact_commit`: 63 passed; `make check`: upstream pin verified, Ruff and
strict MyPy clean, 12 unit tests passed. Implementation commit:
`50270412af92241277b813584639ef8b522836dc`.

## T201 — Verify or implement grammar normalization

**Depends on:** T200

- [x] Test the upstream `to_normal_form()` behavior on epsilon, unit, recursive, and ambiguous grammars.
- [x] Decide whether to reuse it or implement a controlled normalizer.
- [x] Preserve a mapping from normalized productions to original symbols when needed for diagnostics.
- [x] Handle empty-string acceptance explicitly.

**Acceptance criteria**

- [x] A boolean enumerator confirms language preservation up to a configured small length for the normalization fixtures.
- [x] The decision is recorded in `docs/decisions/0004-grammar-normalization.md`.

**Evidence:** `python -m pytest -q tests/exact_commit/test_normalization.py
tests/exact_commit/test_upstream_normalization_audit.py`: 13 passed, including
the pinned upstream audit and bounded language comparisons through length five;
`python -m pytest -q tests/exact_commit`: 76 passed; `make check`: upstream pin
verified, Ruff and strict MyPy clean, 12 unit tests passed. Decision:
`docs/decisions/0004-grammar-normalization.md`. Implementation commit:
`f43eef975af715b690dd998c0bfc3f0c3c124d8a`.

## T202 — Implement lexical reward construction

**Depends on:** T101, T200

- [x] Build `score[position][terminal]` from canvas and proposals.
- [x] Use negative infinity for tokens conflicting with fixed positions.
- [x] Sum weights for duplicate matching proposals.
- [x] Use zero for allowed alternatives that match no proposal.
- [x] Preserve the matching proposal IDs for backtracking.

**Acceptance criteria**

- [x] Tests cover fixed conflicts, zero reward, duplicate proposals, and multiple alternatives.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_lexical_rewards.py`: 8 passed, covering fixed conflicts,
zero reward, duplicate proposals, multiple alternatives, alignment validation,
and empty terminal support; `python -m pytest -q tests/exact_commit`: 84 passed;
`make check`: upstream pin verified, Ruff and strict MyPy clean, 12 unit tests
passed. Implementation commit: `726012490ffed15de2787c4824a564c3b83bbf2a`.

## T203 — Implement CKY max-plus

**Depends on:** T201, T202

**Target:** `src/mwpc_exact/reference/token_aligned.py`

- [x] Allocate sparse or dense DP entries for `(nonterminal, i, j)`.
- [x] Initialize terminal spans.
- [x] Combine binary productions and split points.
- [x] Store terminal/binary backpointers.
- [x] Use a deterministic stable update rule on equal scores.
- [x] Return explicit infeasibility when the start entry is negative infinity.

**Acceptance criteria**

- [x] Hand-computed examples produce the expected score.
- [x] An ambiguous grammar does not double-count derivations.
- [x] Fixed positions are respected.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_token_aligned_cky.py`: 7 passed, covering a
hand-computed max-plus score, ambiguity, fixed and infeasible canvases, stable
ties, and explicit empty acceptance; `python -m pytest -q tests/exact_commit`:
91 passed; `make check`: upstream pin verified, Ruff and strict MyPy clean, 12
unit tests passed. Implementation commit:
`0a9aab19ecc2bcc05a4e8d268fad5ff760cff170`.

## T204 — Implement CKY certificate reconstruction

**Depends on:** T203

- [x] Reconstruct the terminal sequence from backpointers.
- [x] Recover all matched positive-weight proposal IDs.
- [x] Recompute the objective from proposal IDs.
- [x] Return `ExactCommitResult` with `SupportKind.FULL` or explicit small support.
- [x] Pass the result through the independent validator.

**Acceptance criteria**

- [x] Corrupting any backpointer or score is detected by tests.
- [x] The reconstructed sequence is accepted by an independent CFG recognizer.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_token_aligned_certificate.py`: 7 passed, including
terminal/binary backpointer and score corruption, independent Boolean CFG
recognition, and a second public-certificate validation; `python -m pytest -q
tests/exact_commit`: 98 passed; `make check`: upstream pin verified, Ruff and
strict MyPy clean, 12 unit tests passed. Implementation commit:
`d4f7bb27e1ed02fe48cda36566f6ef1e57b82720`.

## T205 — Add canonical token-aligned examples

**Depends on:** T204

- [x] Add a case where all proposals are compatible.
- [x] Add a case where proposals are individually compatible but jointly incompatible.
- [x] Add a case where greedy confidence order is suboptimal.
- [x] Add a case with several optimum witnesses.
- [x] Add an infeasible fixed canvas.
- [x] Add duplicate proposals.

**Acceptance criteria**

- [x] Expected values are explained in test comments or fixture documentation.

**Evidence:** `tests/exact_commit/fixtures/token_aligned_examples.md` and
`tests/exact_commit/test_token_aligned_examples.py`; focused run: 6 passed.
Implementation commit: `38ebc779b05066eb4c74e720acdedacd0e325295`.

**M2 gate**

- [x] All M2 tasks complete.
- [x] Targeted tests pass.
- [x] The solver has no model/tokenizer dependency.

**Gate evidence:** `python -m pytest -q tests/exact_commit`: 104 passed;
`python -m pytest -q`: 117 passed; `make check`: upstream pin verified, Ruff
and strict MyPy clean, 12 unit tests passed; `make paper`: PDF built; import
audit found no `torch`, `transformers`, `rustformlang`, or
`constrained_diffusion` imports in `src/mwpc_exact/reference/`.

---

# M3 — Exhaustive oracles and randomized correctness

## T300 — Implement exhaustive completion oracle

**Depends on:** M2 gate

**Target:** `src/mwpc_exact/reference/brute_force.py`

- [x] Enumerate all completions over a supplied finite per-position support.
- [x] Filter fixed-position violations.
- [x] Use an independent CFG recognizer.
- [x] Compute reward directly from proposals.
- [x] Return all or one deterministic optimum for tiny inputs.
- [x] Enforce a maximum search-size guard.

**Acceptance criteria**

- [x] Oracle results match manually computed fixtures.
- [x] Search-size overflow is explicit, not an accidental hang.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_completion_oracle.py`: 7 passed, including manual
objectives, all-optimum enumeration, fixed/infeasible canvases, duplicate IDs,
and an explicit pre-enumeration search guard; `python -m pytest -q
tests/exact_commit`: 111 passed; `make check`: upstream pin verified, Ruff and
strict MyPy clean, 12 unit tests passed. Implementation commit:
`53ec2d48aea3f75ea135539e4987491273673a6d`.

## T301 — Implement exhaustive subset oracle

**Depends on:** T300

- [x] Enumerate proposal subsets.
- [x] Test compatibility through existence of a completion.
- [x] Compute the best compatible subset weight.
- [x] Preserve a witness for the selected subset.

**Acceptance criteria**

- [x] Completion optimum, subset optimum, and CKY optimum agree on canonical fixtures.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_subset_oracle.py`: 8 passed, including three-way
agreement on all six canonical fixtures, duplicate-ID witness preservation,
and the subset-count guard; `python -m pytest -q tests/exact_commit`: 119
passed; `make check`: upstream pin verified, Ruff and strict MyPy clean, 12
unit tests passed. Implementation commit:
`3d6ad2b0666e8de36ef81b317b347410e8068c1e`.

## T302 — Add deterministic random instance generators

**Depends on:** T300, T301

- [x] Generate small acyclic/recursive CFG fixtures with bounded language lengths.
- [x] Generate finite supports, fixed positions, proposals, duplicate proposals, and integer weights.
- [x] Record seeds.
- [x] Serialize a failing instance to JSON.
- [x] Avoid generators that only produce trivial all-compatible cases.

**Acceptance criteria**

- [x] A seed reproduces the same case exactly.
- [x] Generated cases include feasible and infeasible instances.

**Evidence:** `src/mwpc_exact/reference/random_instances.py` and `python -m
pytest -q tests/exact_commit/test_random_instances.py`: 6 passed, covering
seed reproducibility, versioned JSON replay, offline artifact I/O, both grammar
families, feasible/infeasible seeds, conflicts, integer weights, and duplicate
choices; `python -m pytest -q tests/exact_commit`: 125 passed; `make check`:
upstream pin verified, Ruff and strict MyPy clean, 12 unit tests passed.
Implementation commit: `8a458b48b7a26a9411142fece647ff4a7ad32cec`.

## T303 — Add property-based/differential test suite

**Depends on:** T302

- [x] Compare CKY, completion oracle, and subset oracle.
- [x] Check monotonicity when support is expanded.
- [x] Check that removing a proposal does not increase optimum score.
- [x] Check that fixing a position preserves or reduces the feasible optimum.
- [x] Check selected IDs and reconstructed score.
- [x] Run a smaller deterministic set in normal tests and a larger campaign via script.

**Acceptance criteria**

- [x] Normal test campaign has 100% agreement.
- [x] Extended campaign writes summary and failing seed artifacts.

**Evidence:** `python -m pytest -q
tests/exact_commit/test_differential_campaign.py`: 3 passed, including a
32-seed normal campaign and injected-failure artifact replay; `python
scripts/exact_commit/run_m3_differential.py`: 2,000/2,000 seeds passed with
10,000 three-way comparisons, 23,538 certificate validations, and 2,000 checks
each for support expansion, proposal removal, and fixed positions. Artifact:
`docs/evidence/m3-differential-summary.json`, produced from commit
`05504c1f21aedadd16e1f8995d8f4501a6823f46`. The campaign first exposed and
regressed the per-position support bug fixed in commit
`f312bdd6e43238160e22990254061957299ad476`.

## T304 — Establish regression corpus

**Depends on:** T303

- [ ] Add `tests/exact_commit/regressions/`.
- [ ] Store every discovered minimal failing instance.
- [ ] Add a loader that runs all regression fixtures.
- [ ] Document fixture schema.

**Acceptance criteria**

- [ ] Regression suite is deterministic and runs offline.

**Evidence:** `[paths and tests]`

**M3 correctness gate — blocking**

- [ ] CKY equals both exhaustive oracles for all configured cases.
- [ ] Independent certificates validate.
- [ ] Any failure has been minimized and fixed.
- [ ] No tokenizer, Rust optimization, or model integration begins before this gate.

---

# M4 — Generic weighted terminal-DAG reference solver

## T400 — Implement Python DAG validation and indexing

**Depends on:** M3 gate

**Target:** `src/mwpc_exact/reference/graph.py`

- [ ] Validate state IDs, start/final states, edges, labels, weights, and DAG property.
- [ ] Compute a deterministic topological order.
- [ ] Index terminal edges by label and endpoint.
- [ ] Reject malformed or cyclic graphs with explicit errors.

**Acceptance criteria**

- [ ] Tests cover disconnected nodes, multiple final states, parallel edges, and cycles.

**Evidence:** `[tests and commit]`

## T401 — Implement Python max-plus CFG-on-DAG parser

**Depends on:** T400, T201

- [ ] Implement DP entries `(A, p, q)`.
- [ ] Initialize from terminal edges.
- [ ] Combine binary productions over valid intermediate states.
- [ ] Use topological/span ordering that guarantees termination.
- [ ] Store edge and binary backpointers.
- [ ] Support multiple final states.

**Acceptance criteria**

- [ ] String-chain DAGs produce the same result as token-aligned CKY.
- [ ] Parallel paths with different scores choose the maximum.
- [ ] Ambiguous grammars do not sum derivations.

**Evidence:** `[tests and commit]`

## T402 — Implement graph-path brute-force oracle

**Depends on:** T400

- [ ] Enumerate paths in tiny DAGs.
- [ ] Recognize each terminal sequence independently.
- [ ] Sum edge weights once.
- [ ] Return the maximum valid path.
- [ ] Guard against path explosion.

**Acceptance criteria**

- [ ] Graph parser and path oracle agree on random tiny DAGs.

**Evidence:** `[tests and campaign result]`

## T403 — Define and implement epsilon normalization

**Depends on:** T400

- [ ] Create `docs/decisions/0005-epsilon-edges.md`.
- [ ] Define whether the external graph accepts epsilon edges.
- [ ] If accepted, compute weighted epsilon closure on DAGs.
- [ ] Saturate terminal arcs while preserving original-edge provenance.
- [ ] Handle epsilon-only accepted paths when the CFG derives empty.
- [ ] Reject epsilon cycles or general cycles.

**Acceptance criteria**

- [ ] Normalized graph and direct path enumeration agree on fixtures.
- [ ] Proposal weights are not duplicated by closure.

**Evidence:** `[ADR, tests, commit]`

## T404 — Add graph differential/property tests

**Depends on:** T401, T402, T403

- [ ] Random DAGs with parallel edges.
- [ ] Random integer edge rewards.
- [ ] Multiple final states.
- [ ] Epsilon chains.
- [ ] Same terminal string through different token provenance.
- [ ] Infeasible graph/grammar intersections.

**Acceptance criteria**

- [ ] 100% score agreement with graph path oracle in configured campaign.

**Evidence:** `[commands and result artifact]`

**M4 gate**

- [ ] Generic Python graph solver is certified against brute force.
- [ ] Epsilon semantics are fixed and tested.

---

# M5 — Rust production parser and Python bindings

## T500 — Add Rust weighted graph/result structs

**Depends on:** M4 gate

**Target:** `rustformlang/src/cfg/weighted_graph.rs`

- [ ] Define validated DAG, edge, support metadata, solver status, diagnostics, and certificate structs.
- [ ] Use stable integer IDs.
- [ ] Store `f64` scores and reject non-finite inputs.
- [ ] Validate topological order and endpoints.
- [ ] Export the module without altering existing boolean graph APIs.

**Acceptance criteria**

- [ ] Rust unit tests cover valid and invalid constructors.
- [ ] Existing Rust tests still pass.

**Evidence:** `[tests and commit]`

## T501 — Implement Rust max-plus CFG-on-DAG DP

**Depends on:** T500

- [ ] Reuse normalized CFG data where safe.
- [ ] Implement terminal initialization.
- [ ] Implement indexed binary combinations.
- [ ] Avoid scanning impossible triples where straightforward indexing can eliminate them.
- [ ] Preserve deterministic update order.
- [ ] Return explicit infeasibility.

**Acceptance criteria**

- [ ] Rust canonical examples match Python reference scores.
- [ ] No panic occurs for valid infeasible inputs.

**Evidence:** `[tests and commit]`

## T502 — Implement Rust backtracking and provenance

**Depends on:** T501

- [ ] Store terminal and binary backpointers.
- [ ] Reconstruct terminal edge IDs in path order.
- [ ] Reconstruct terminal labels.
- [ ] Preserve token/proposal provenance supplied on edges.
- [ ] Recompute the result score before returning.

**Acceptance criteria**

- [ ] Returned edge path is continuous start-to-final.
- [ ] Independent Python validator accepts converted certificates.

**Evidence:** `[tests and commit]`

## T503 — Add timeout and diagnostic handling

**Depends on:** T501

- [ ] Implement deadline checks at bounded intervals.
- [ ] Return `TIMEOUT`, never `INFEASIBLE`, after deadline.
- [ ] Report chart entries, relaxations, graph size, grammar size, and elapsed parser time.
- [ ] Add a deterministic test hook for timeout without relying on wall-clock flakiness.

**Acceptance criteria**

- [ ] Timeout test is reliable.
- [ ] Partial data is not exposed as an optimal certificate.

**Evidence:** `[tests and commit]`

## T504 — Add Rust unit and randomized tests

**Depends on:** T501, T502, T503

- [ ] Port canonical graph fixtures.
- [ ] Add randomized small DAG tests against a Rust or serialized Python oracle.
- [ ] Cover parallel edges, ties, ambiguity, epsilon normalization output, and multiple finals.
- [ ] Run formatting checks.

**Acceptance criteria**

- [ ] Rust suite is clean.

**Evidence:** `[commands and summary]`

## T505 — Expose the solver through PyO3

**Depends on:** T502, T503

**Targets:** `rustformlang_bindings/src/cfg.rs` and Python wrapper

- [ ] Add Python-visible graph/result classes or one validated solve function.
- [ ] Convert labels and IDs losslessly.
- [ ] Release the GIL around the CPU-intensive solve when safe.
- [ ] Convert Rust status to Python `SolveStatus` without string ambiguity.
- [ ] Preserve existing binding API behavior.

**Acceptance criteria**

- [ ] Binding builds in release mode.
- [ ] Malformed Python inputs produce clear exceptions.
- [ ] Existing binding tests pass.

**Evidence:** `[build/test commands]`

## T506 — Add Python/Rust differential tests

**Depends on:** T505

- [ ] Run the same serialized random instances through both solvers.
- [ ] Compare status, objective, certificate validity, and path reward.
- [ ] Permit different optimum witnesses on ties.
- [ ] Save any mismatch fixture automatically.

**Acceptance criteria**

- [ ] 100% agreement on the configured normal and extended campaigns.

**Evidence:** `[commands, case counts, artifacts]`

**M5 production-parser gate — blocking**

- [ ] Python, Rust, and brute force agree.
- [ ] Binding rebuild is documented.
- [ ] Existing EPIC tests remain green or pre-existing failures are documented.

---

# M6 — Finite token lattice and exact token provenance

## T600 — Audit and choose the tokenizer/model interface

**Depends on:** M5 gate

- [ ] Identify candidate `[MODEL_ID]` and tokenizer revision.
- [ ] Determine whether token-to-byte emission is compositional.
- [ ] Test random sequences, whitespace, Unicode, byte fallback, added tokens, and special tokens.
- [ ] Do not assume concatenated `decode([id])` equals full decoding.
- [ ] Choose either a compositional byte adapter, stateful detokenizer, or a different model.
- [ ] Record the decision in `docs/decisions/0006-tokenizer-byte-semantics.md`.

**Acceptance criteria**

- [ ] The exact mapping used by the lattice is stated and tested.
- [ ] Unsupported tokens are identified explicitly.

**Evidence:** `[model/tokenizer revision, tests, ADR]`

## T601 — Implement per-position support construction

**Depends on:** T103, T104

**Target:** `src/mwpc_exact/support.py`

- [ ] Accept logits or an explicit support map.
- [ ] Include top-`K` tokens per masked position.
- [ ] Include the proposal token even if a future policy changes selection.
- [ ] Include required special tokens according to configuration.
- [ ] Use only the fixed token for committed positions.
- [ ] Return `ExactnessScope` and support diagnostics.

**Acceptance criteria**

- [ ] Support is deterministic for fixed logits and tie policy.
- [ ] Fixed-position support cannot be widened accidentally.
- [ ] Top-`K` metadata is correct.

**Evidence:** `[tests and commit]`

## T602 — Implement layered token-lattice construction

**Depends on:** T101, T102, T601

**Target:** `src/mwpc_exact/token_lattice.py`

- [ ] Add one physical boundary per canvas slot.
- [ ] Add one token choice path per supported token in a masked slot.
- [ ] Add exactly one choice for fixed positions.
- [ ] Attach aggregated reward and proposal IDs once per token choice.
- [ ] Preserve absolute canvas position and token ID.
- [ ] Validate that every complete token path consumes the configured number of slots.

**Acceptance criteria**

- [ ] Enumerating tiny token lattices gives the Cartesian product of supports.
- [ ] No path skips or consumes two alternatives for one slot.

**Evidence:** `[tests and commit]`

## T603 — Implement token-to-byte expansion

**Depends on:** T600, T602

**Target:** `src/mwpc_exact/byte_lattice.py`

- [ ] Expand each token path into exact byte-labeled edges.
- [ ] Attach reward/proposal provenance exactly once.
- [ ] Preserve token-edge identity through expansion.
- [ ] Handle multi-byte UTF-8 and byte fallback.
- [ ] Define behavior for empty-emission/special tokens.
- [ ] Avoid prefix sharing in the first version unless provenance is proven safe.

**Acceptance criteria**

- [ ] Concatenated bytes of every enumerated tiny path equal the adapter’s full detokenization.
- [ ] Score is independent of token byte length.
- [ ] Distinct token IDs with identical bytes remain distinguishable.

**Evidence:** `[tests and commit]`

## T604 — Add byte-level grammar fixtures

**Depends on:** T201, T603

- [ ] Add an arithmetic-expression byte grammar.
- [ ] Add a small DSL byte grammar.
- [ ] Add a clearly named JSON subset grammar if manageable.
- [ ] Document accepted syntax and deliberate omissions.
- [ ] Add valid/invalid sample corpora.

**Acceptance criteria**

- [ ] Boolean parser classifications match fixture labels.
- [ ] Grammar names do not overstate subsets as complete languages.

**Evidence:** `[grammar/test paths]`

## T605 — Connect token lattice to generic exact solver

**Depends on:** T603, T604, T505

- [ ] Build a model-independent `solve_exact_commit` path from canvas/support/proposals to Rust result.
- [ ] Convert terminal-edge certificate back to token IDs and proposal IDs.
- [ ] Validate the result independently.
- [ ] Add a Python-backend switch for debugging.

**Acceptance criteria**

- [ ] Tiny tokenizer-aware cases match enumeration of token paths.
- [ ] Python and Rust backends return equal scores.

**Evidence:** `[tests and commit]`

## T606 — Add finite-lattice randomized tests

**Depends on:** T605

- [ ] Generate small token vocabularies with variable byte strings.
- [ ] Include same-byte/different-ID tokens.
- [ ] Include multi-byte tokens and fixed positions.
- [ ] Compare exact solver with token-path enumeration.
- [ ] Save failures as regression fixtures.

**Acceptance criteria**

- [ ] 100% agreement in configured campaigns.

**Evidence:** `[commands and artifacts]`

**M6 gate**

- [ ] A finite tokenizer-aware byte lattice is exact on its represented support.
- [ ] Provenance and score survive expansion.

---

# M7 — EOS/PAD and finite-slot exactness

## T700 — Freeze EOS/PAD semantics

**Depends on:** M6 gate

- [ ] Inspect `[MODEL_ID]` special-token behavior.
- [ ] Create `docs/decisions/0007-eos-pad-semantics.md`.
- [ ] Define whether EOS is required, optional, or absent in each task.
- [ ] Define legal tokens after EOS.
- [ ] Define whether PAD emits no grammar symbol.
- [ ] Define the physical slot count and effective content endpoint.

**Acceptance criteria**

- [ ] Every path has unambiguous token and content length semantics.

**Evidence:** `[ADR path]`

## T701 — Implement EOS/PAD regular constraint

**Depends on:** T700

- [ ] Compose token choices with `BEFORE_EOS`/`AFTER_EOS` state.
- [ ] Permit only configured transitions.
- [ ] Consume all physical slots even when grammar content ends early.
- [ ] Preserve proposal weights on EOS/PAD choices.
- [ ] Normalize any resulting epsilon edges safely.

**Acceptance criteria**

- [ ] Invalid normal-token-after-EOS paths do not exist.
- [ ] Valid EOS/PAD paths reconstruct all physical token IDs.

**Evidence:** `[tests and commit]`

## T702 — Extend independent validator for finite slots

**Depends on:** T701, T105

- [ ] Check exact physical slot count.
- [ ] Check EOS position and post-EOS tokens.
- [ ] Check effective terminal sequence.
- [ ] Check fixed special-token positions.
- [ ] Produce precise error messages.

**Acceptance criteria**

- [ ] Deliberately malformed EOS/PAD witnesses are rejected.

**Evidence:** `[tests and commit]`

## T703 — Create finite-slot counterexample corpus

**Depends on:** T701

- [ ] Construct cases accepted by an abstract `Sigma*` gap representation.
- [ ] Prove/enumerate that each requires more token slots than available.
- [ ] Confirm finite lattice returns `INFEASIBLE_ON_SUPPORT` or a lower feasible alternative.
- [ ] Store human-readable explanation and machine fixture.

**Acceptance criteria**

- [ ] At least one minimal counterexample is suitable for the TCC figure/table.

**Evidence:** `[fixture and command]`

## T704 — Run finite-slot randomized/differential tests

**Depends on:** T702, T703

- [ ] Compare finite token-path enumeration with solver.
- [ ] Randomize EOS position, PAD, fixed slots, and supports.
- [ ] Check that every optimal certificate consumes exactly the configured slots.

**Acceptance criteria**

- [ ] 100% agreement in configured campaign.

**Evidence:** `[commands and artifacts]`

**M7 finite-slot gate — blocking**

- [ ] EOS/PAD semantics are implemented and independently validated.
- [ ] Finite-slot counterexamples exist and reproduce.

---

# M8 — Exact commit policy, support expansion, fallback, and profiling

## T800 — Implement schedule-compatible proposal policy

**Depends on:** T103, M7 gate

**Target:** `src/mwpc_exact/proposal_policy.py`

- [ ] Accept model token predictions and confidence values.
- [ ] Select the same `k_s` candidate positions used by the baseline schedule.
- [ ] Create one primary proposal per candidate position.
- [ ] Implement `unit` and `confidence` weights.
- [ ] Preserve absolute position indices.
- [ ] Emit deterministic proposal IDs.

**Acceptance criteria**

- [ ] Given saved logits, policy output is deterministic.
- [ ] Number of proposals is at most `k_s`.

**Evidence:** `[tests and commit]`

## T801 — Implement the exact optimizer orchestration API

**Depends on:** T605, T702, T800

**Target:** `src/mwpc_exact/solver.py`

- [ ] Validate canvas/proposals/support.
- [ ] Build token and byte lattices.
- [ ] Call configured backend.
- [ ] Reconstruct tokens/proposals.
- [ ] Run independent validation.
- [ ] Return structured result and diagnostics.

**Acceptance criteria**

- [ ] API works from explicit saved logits/support without loading a model.
- [ ] Invalid certificate becomes `ERROR`, never silently committed.

**Evidence:** `[tests and commit]`

## T802 — Implement adaptive support expansion

**Depends on:** T601, T801

- [ ] Add `initial_k`, growth policy, `k_max`, and total timeout config.
- [ ] Retry only on `INFEASIBLE_ON_SUPPORT`, not arbitrary errors.
- [ ] Ensure each expansion is a superset of the previous support.
- [ ] Record attempts, graph sizes, times, and final scope.
- [ ] Stop deterministically.

**Acceptance criteria**

- [ ] Optimum score never decreases across support expansions.
- [ ] Final result records every attempted K.

**Evidence:** `[tests and commit]`

## T803 — Implement progress and failure fallbacks

**Depends on:** T801

**Target:** `src/mwpc_exact/decoder.py`

- [ ] For `OPTIMAL` with nonempty selected set, commit exactly those proposals.
- [ ] For `OPTIMAL` with zero proposal score/set, choose one masked witness token using the documented deterministic rule.
- [ ] For timeout/error, invoke configured serial or EPIC fallback.
- [ ] Record fallback type and reason.
- [ ] Do not label fallback result as optimal.

**Acceptance criteria**

- [ ] Each feasible no-remasking step commits at least one slot.
- [ ] The witness remains compatible after commitment.
- [ ] Fallback metrics distinguish witness-progress from error fallback.

**Evidence:** `[tests and commit]`

## T804 — Add component-level profiling

**Depends on:** T801

**Target:** `src/mwpc_exact/profiling.py`

- [ ] Time proposal policy, support, token lattice, byte expansion, parser, backtracking, validation, and commit update separately.
- [ ] Record graph nodes/edges, chart entries, proposals, support sizes, and expansions.
- [ ] Keep profiling optional and low-overhead when disabled.
- [ ] Produce JSON-serializable events.

**Acceptance criteria**

- [ ] Sum/breakdown is internally consistent within measurement overhead.

**Evidence:** `[tests/sample event]`

## T805 — Add offline exact-step integration tests

**Depends on:** T802, T803, T804

- [ ] Use fixed canvases and logits tensors.
- [ ] Test full compatible batch.
- [ ] Test strict optimal subset.
- [ ] Test empty matched set with witness-progress fallback.
- [ ] Test support expansion.
- [ ] Test timeout fallback.
- [ ] Test fixed positions and EOS/PAD.

**Acceptance criteria**

- [ ] Tests run on CPU and without network/model weights.

**Evidence:** `[tests and commit]`

**M8 gate**

- [ ] One complete exact decoding step works offline with a certified witness.

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

**Initial target:** the selected existing adapter, likely the LLaDA-style constrained loop or `[CHOSEN_ADAPTER]`.

- [ ] Locate the point after logits/confidence and before heuristic/serial commitment.
- [ ] Reuse the baseline `k_s` schedule.
- [ ] Convert current canvas and logits into the exact API.
- [ ] Commit returned positions/tokens to model tensors and decoded tracking state.
- [ ] Preserve prompt positions and active-block limits.
- [ ] Preserve baseline EOS handling according to the new documented semantics.

**Acceptance criteria**

- [ ] A fixed-logit test confirms exact hook receives the intended canvas and candidate set.
- [ ] No exact-specific logic leaks into generic parser code.

**Evidence:** `[tests and commit]`

## T902 — Preserve serial and EPIC baselines

**Depends on:** T901

- [ ] Add regression tests for strategy dispatch.
- [ ] Confirm `serial` calls the original serial path.
- [ ] Confirm `epic` calls the existing regular-cover selector.
- [ ] Confirm `exact` does not mutate baseline functions.
- [ ] Compare fixed-seed/saved-logit baseline outputs before and after integration where deterministic.

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

- [ ] Load `[MODEL_ID]` and exact tokenizer revision.
- [ ] Record dtype/quantization/device settings.
- [ ] Run one small structured generation with `serial`, `epic`, and `exact` where feasible.
- [ ] Validate outputs and save raw metadata.
- [ ] Record any memory limitation honestly.

**Acceptance criteria**

- [ ] At least one exact end-to-end generation completes or a precise model/hardware blocker is documented with the offline integration still passing.
- [ ] No benchmark claim is made from this smoke test alone.

**Evidence:** `[config, command, raw artifact]`

**M9 integration gate**

- [ ] Exact mode is reachable through a real adapter.
- [ ] Baseline modes remain available.
- [ ] Offline loop and live smoke evidence exist.

---

# M10 — Common baseline interface and fair comparison

## T1000 — Wrap serial selector in common evaluation interface

**Depends on:** M9 gate

- [ ] Accept saved canvas/proposals/support input.
- [ ] Return selected IDs, score, status, runtime, and witness if available.
- [ ] Preserve order semantics.

**Acceptance criteria**

- [ ] Same input can be fed to serial and exact selectors.

**Evidence:** `[tests and commit]`

## T1001 — Wrap EPIC heuristic selector in common interface

**Depends on:** M9 gate

- [ ] Convert `BatchCandidate` and current words into common input/output.
- [ ] Record regular-cover and exact-shrink calls/diagnostics.
- [ ] Recompute selected score independently.
- [ ] Keep EPIC behavior unchanged.

**Acceptance criteria**

- [ ] Heuristic and exact receive identical proposals and weights in offline comparisons.

**Evidence:** `[tests and commit]`

## T1002 — Wrap brute force as small-instance baseline

**Depends on:** T300, T402

- [ ] Expose a common result for tiny token-aligned and graph instances.
- [ ] Add explicit size guard and status.
- [ ] Use it in experiment scripts only when feasible.

**Acceptance criteria**

- [ ] Exact result matches brute force in the common harness.

**Evidence:** `[tests and commit]`

## T1003 — Define shared benchmark instance schema

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

## T1100 — Add immutable experiment config system

**Depends on:** M10 gate

- [ ] Define YAML/JSON configs for correctness, gap, finite slots, scaling, and end-to-end runs.
- [ ] Include all exactness, support, model, grammar, seed, timeout, and hardware-relevant options.
- [ ] Hash normalized configs.
- [ ] Save resolved config with every run.

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

- [ ] Timing script contains no method-specific unfair setup inside the measured region.

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
- [ ] Capture Python/Rust/CUDA/PyTorch/Transformers versions.
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
- [ ] Store small publication artifacts; document external storage for large raw data.

**Acceptance criteria**

- [ ] Deleting processed outputs and rerunning scripts reproduces them from raw data.

**Evidence:** `[commands and paths]`

## T1202 — Implement statistical summaries

**Depends on:** T1201

- [ ] Compute agreement and confidence intervals where appropriate.
- [ ] Compute gap distributions and equality rates.
- [ ] Compute runtime median/IQR and normalized overhead.
- [ ] Compute fallback/timeout/support-expansion rates.
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
- [ ] Record expected artifact filenames, not expected scientific values unless already measured.

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
- [ ] Insert model/tokenizer/hardware/software versions.

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
- [ ] Analyze runtime/memory and dominant component.
- [ ] Analyze end-to-end validity, fallbacks, and limitations.
- [ ] Report negative or null findings honestly.

**Acceptance criteria**

- [ ] Every number is generated by a script and traceable.
- [ ] No smoke-test result is presented as a benchmark conclusion.

**Evidence:** `[paper build and artifact links]`

## T1302 — Update limitations and theorem-to-code correspondence

**Depends on:** T1300, T1301

- [ ] State exact-on-support limitations.
- [ ] State tokenizer/byte-level language limitations.
- [ ] State CFG syntax-versus-semantics limitation.
- [ ] State per-step versus trajectory optimality.
- [ ] State timeout/resource limits.
- [ ] Add a table mapping theorem assumptions to code/config enforcement.

**Acceptance criteria**

- [ ] No theorem assumption is silently violated by the reported experiment.

**Evidence:** `[paper section/commit]`

## T1303 — Fill AI-use declaration

**Depends on:** T1300

- [ ] Name tools, providers, and versions used.
- [ ] State purposes: planning, drafting, review, coding assistance, etc.
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
- [ ] Build final LaTeX PDF.
- [ ] Create release tag.
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

- [ ] Add budget dimension or a formally equivalent semiring/state construction.
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
- [ ] Compare incremental and full recomputation certificates.

**Acceptance criteria**

- [ ] Scores/certificates match full recomputation on all tests.

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

- Baseline commit/tag: `[TO BE RECORDED]`
- Upstream EPIC commit: `[TO BE RECORDED]`
- Correctness campaign artifact: `[TO BE RECORDED]`
- Rust/Python differential artifact: `[TO BE RECORDED]`
- Finite-slot counterexample artifact: `[TO BE RECORDED]`
- Heuristic-gap experiment artifact: `[TO BE RECORDED]`
- Scaling experiment artifact: `[TO BE RECORDED]`
- End-to-end experiment artifact: `[TO BE RECORDED]`
- Reproduction release/tag: `[TO BE RECORDED]`
- Final TCC PDF/source commit: `[TO BE RECORDED]`
