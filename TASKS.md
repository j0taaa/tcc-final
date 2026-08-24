# TASKS.md — Exact MWPC for CFG-Constrained dLLMs

## How to use this file

This is the authoritative execution checklist for the remaining work. `AGENTS.md`
defines repository-wide behavior and scientific invariants;
`IMPLEMENTATION_PLAN.md` explains the design in prose.

Status convention:

- `[ ]` not completed;
- `[x]` completed and supported by evidence;
- `BLOCKED:` task cannot proceed, with a concrete reason recorded;
- `OPTIONAL:` not required for the minimum TCC implementation.

Rules:

1. Complete required tasks in dependency order.
2. A task is complete only when every acceptance criterion and required check passes.
3. Add commands, summarized outputs, artifact paths, and relevant commits to its `Evidence` field.
4. A correctness-gate failure blocks later integration and performance milestones.
5. Do not substitute measured values with estimates.
6. Do not redo completed milestones unless a regression, failed check, or explicit review finding invalidates their evidence.

## Current starting point

**M7 / T701.** M0 through M6 and T700 are complete at the immutable commits and
artifacts recorded below. The first incomplete required task is T701: compose
the finite token choices with the EOS/PAD automaton defined by ADR 0007. The
historical M0--M3 checklist remains archived in
[`docs/history/TASKS-through-M3.md`](docs/history/TASKS-through-M3.md).

Required milestones: **M0 through M13**.

Optional milestones: **O1 through O4**.

## Completed milestone summary

### M0 — Baseline, provenance, and reproducible environment

- [x] EPIC is pinned read-only at `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`.
- [x] Python/Rust environments and bindings were built and recorded.
- [x] Baseline Python, upstream Python, and Rust tests were frozen.
- [x] A model-free EPIC smoke path was recorded.

**Evidence:** immutable baseline commit
`b9f2179caadf8640fe026f7a73833cbda9755876`, `UPSTREAM.md`,
`docs/environment-baseline.md`, `docs/baseline-tests.md`, and
`docs/baseline-smoke.md`.

### M1 — Scientific contracts and stable data types

- [x] Status, exactness-scope, proposal, graph, result, and validator contracts exist.
- [x] Objective, candidate, support, and failure terminology is frozen in ADRs.
- [x] Public certificates are independently validated.

**Evidence:** implementation commits recorded in the archived checklist and the
current `docs/scientific-contract.md` plus ADRs 0001–0003.

### M2 — Token-aligned Python reference solver

- [x] Controlled CNF representation and normalization exist.
- [x] Lexical rewards and max-plus CKY are implemented.
- [x] Backtracking returns a certificate accepted by the independent validator.
- [x] Canonical examples cover incompatibility, greedy suboptimality, ambiguity,
  duplicate proposals, ties, and infeasibility.

**Evidence:** M2 gate at `6a5945bef2e9c6dc55ad8d0d02f91656215ac6aa`
and the implementation commits recorded in the archived checklist.

### M3 — Exhaustive oracles and randomized correctness

- [x] Completion and proposal-subset exhaustive oracles exist.
- [x] Deterministic random instances and offline replay fixtures exist.
- [x] CKY agrees with both oracles on the configured campaign.
- [x] The support-escape bug discovered by the campaign is fixed and regressed.
- [x] Scope enforcement now prevents pruned support from being mislabeled `FULL`,
  rejects explicit supports that omit committed tokens or use unmapped tokens,
  and fingerprints represented rows in result diagnostics.
- [x] Default CI and `make check` run the exact-commit suite.

**Evidence:** M3 gate commit
`e6ab2e2bcc8c6ce43b1092d7b5c8af9d14fa8c67`,
`docs/evidence/m3-differential-summary.json`, regression fixture
`tests/exact_commit/regressions/explicit-support-escape.json`, and the support
scope correction commit recorded by Git history.

**Configured-case scope:** the M3 campaign uses deliberately tiny finite
instances—two or three slots, a three-token toy vocabulary, and the recorded
acyclic/recursive grammar families. It is an executable regression gate for the
reference implementation, not a replacement for the formal proof and not a
claim over every possible CFG or support shape. The public token-aligned result
contract currently reports a zero-slot epsilon witness as `UNSUPPORTED`; M2 and
M3 completeness evidence is scoped to non-empty physical canvases.

---

# M4 — Generic weighted terminal-DAG reference solver

## T400 — Implement Python DAG validation and indexing

**Depends on:** M3 gate

**Target:** `src/mwpc_exact/reference/graph.py`

- [x] Validate state IDs, start/final states, edges, labels, weights, and DAG property.
- [x] Compute a deterministic topological order.
- [x] Index terminal edges by label and endpoint.
- [x] Reject malformed or cyclic graphs with explicit errors.

**Acceptance criteria**

- [x] Tests cover disconnected nodes, multiple final states, parallel edges, and cycles.

**Evidence:** implementation commit `6c22ae0c9c8cba54ecabefe0101a4b0e0a0b03e4`;
`python -m pytest -q tests/exact_commit/test_graph_index.py
tests/exact_commit/test_graph_and_result_contracts.py` (`20 passed`);
`python -m ruff check src/mwpc_exact/reference/graph.py
tests/exact_commit/test_graph_index.py` and `python -m mypy src` passed.

## T401 — Implement Python max-plus CFG-on-DAG parser

**Depends on:** T400, T201

- [x] Implement DP entries `(A, p, q)`.
- [x] Initialize from terminal edges.
- [x] Combine binary productions over valid intermediate states.
- [x] Use topological/span ordering that guarantees termination.
- [x] Store edge and binary backpointers.
- [x] Support multiple final states.

**Acceptance criteria**

- [x] String-chain DAGs produce the same result as token-aligned CKY.
- [x] Parallel paths with different scores choose the maximum.
- [x] Ambiguous grammars do not sum derivations.

**Evidence:** implementation commit `e57400c9e9437500a9b09c03832e9b7ad1556391`;
`python -m pytest -q tests/exact_commit/test_dag_parser.py
tests/exact_commit/test_graph_index.py` (`11 passed`); `python -m ruff check
src/mwpc_exact/reference/dag_parser.py tests/exact_commit/test_dag_parser.py`
and `python -m mypy src` passed.

## T402 — Implement graph-path brute-force oracle

**Depends on:** T400

- [x] Enumerate paths in tiny DAGs.
- [x] Recognize each terminal sequence independently.
- [x] Sum edge weights once.
- [x] Return the maximum valid path.
- [x] Guard against path explosion.

**Acceptance criteria**

- [x] Graph parser and path oracle agree on random tiny DAGs.

**Evidence:** implementation commit `d7ef4f507c9b3932602f91b48b4eb18da3fac147`;
`python -m pytest -q tests/exact_commit/test_graph_oracle.py
tests/exact_commit/test_dag_parser.py` (`10 passed`), including exact status and
objective agreement over seeds `0..249`; `python -m ruff check
src/mwpc_exact/reference/graph_oracle.py tests/exact_commit/test_graph_oracle.py`
and `python -m mypy src` passed.

## T403 — Define and implement epsilon normalization

**Depends on:** T400

- [x] Create `docs/decisions/0005-epsilon-edges.md`.
- [x] Define whether the external graph accepts epsilon edges.
- [x] If accepted, compute weighted epsilon closure on DAGs.
- [x] Saturate terminal arcs while preserving original-edge provenance.
- [x] Handle epsilon-only accepted paths when the CFG derives empty.
- [x] Reject epsilon cycles or general cycles.

**Acceptance criteria**

- [x] Normalized graph and direct path enumeration agree on fixtures.
- [x] Proposal weights are not duplicated by closure.

**Evidence:** `docs/decisions/0005-epsilon-edges.md`; implementation commit
`ed22c6f822678ed6ac6e25e22878c6ddbcf99260`; `python -m pytest -q
tests/exact_commit/test_epsilon_normalization.py tests/exact_commit/test_graph_oracle.py
tests/exact_commit/test_dag_parser.py tests/exact_commit/test_graph_index.py
tests/exact_commit/test_graph_and_result_contracts.py tests/exact_commit/test_validator.py
tests/exact_commit/test_token_aligned_certificate.py` (`56 passed`); `python -m
ruff check src tests/exact_commit/test_epsilon_normalization.py` and `python -m
mypy src` passed.

## T404 — Add graph differential/property tests

**Depends on:** T401, T402, T403

- [x] Random DAGs with parallel edges.
- [x] Random integer edge rewards.
- [x] Multiple final states.
- [x] Epsilon chains.
- [x] Same terminal string through different token provenance.
- [x] Infeasible graph/grammar intersections.

**Acceptance criteria**

- [x] 100% score agreement with the graph path oracle in the configured campaign.

**Evidence:** campaign implementation commit
`7702267312c364f6ed49e873123d641a67fbace8`; `python
scripts/exact_commit/run_m4_graph_differential.py` produced
`docs/evidence/m4-graph-differential-summary.json`: `2000/2000` seeds passed,
with `2000` status and objective agreements, `2694` independently validated
optimal certificates, and `38336` saturated-edge provenance validations. The
configured cases include `2000` epsilon-chain/parallel/provenance cases,
`1000` multiple-final cases, and `400` forced infeasible intersections.

**M4 gate**

- [x] Generic Python graph solver is certified against brute force.
- [x] Epsilon semantics are fixed and tested.

**Evidence:** T400--T404 evidence above; `python -m pytest -q` (`178 passed`);
`make check` verified the upstream pin, lint, strict typing, `12` unit tests,
and `165` exact-commit tests; `make paper` produced the 15-page PDF. The
configured M4 differential campaign had zero failures.

---

# M5 — Rust production parser and Python bindings

## T500 — Add Rust weighted graph/result structs

**Depends on:** M4 gate

**Target:** `crates/mwpc_parser/`

- [x] Define validated DAG, edge, support metadata, solver status, diagnostics, and certificate structs.
- [x] Use stable integer IDs.
- [x] Store `f64` scores and reject non-finite inputs.
- [x] Validate topological order and endpoints.
- [x] Keep the pinned EPIC Rust code read-only.

**Acceptance criteria**

- [x] Rust unit tests cover valid and invalid constructors.
- [x] Existing EPIC Rust tests still pass unchanged.

**Evidence:** implementation commit `9df61ec302e0cc6e9d6927db1850b40c8afc87f8`;
`cargo test --manifest-path crates/mwpc_parser/Cargo.toml` (`6 passed`);
`cargo clippy --manifest-path crates/mwpc_parser/Cargo.toml --all-targets -- -D
warnings` and crate-local `cargo fmt --check` passed; `cargo test
--manifest-path vendor/EPIC-Decoding/rustformlang/Cargo.toml` (`63 passed`, `1
ignored`) with the pinned submodule clean. The vendor-wide format check still
reports the pre-existing upstream formatting differences and was not changed.

## T501 — Implement Rust max-plus CFG-on-DAG DP

**Depends on:** T500

- [x] Implement terminal initialization.
- [x] Implement indexed binary combinations.
- [x] Avoid scanning impossible triples where straightforward indexing can eliminate them.
- [x] Preserve deterministic update order.
- [x] Return explicit infeasibility.

**Acceptance criteria**

- [x] Rust canonical examples match Python reference scores.
- [x] No panic occurs for valid infeasible inputs.

**Evidence:** implementation commit `a3f9650cfec8bd9e9e5bc7db707c69840d7c80e4`;
crate-local `cargo fmt --check` passed; `cargo test --manifest-path
crates/mwpc_parser/Cargo.toml` (`10 passed`), including the canonical score,
parallel-edge maximum, indexed-relaxation, and valid-infeasible cases.

## T502 — Implement Rust backtracking and provenance

**Depends on:** T501

- [x] Store terminal and binary backpointers.
- [x] Reconstruct terminal edge IDs in path order.
- [x] Reconstruct terminal labels.
- [x] Preserve token/proposal provenance supplied on edges.
- [x] Recompute the result score before returning.

**Acceptance criteria**

- [x] Returned edge path is continuous start-to-final.
- [x] Independent Python validator accepts converted certificates.

**Evidence:** implementation commit `236417fa64004d2001af2569dadd553d0bbe3c2f`
and repeated-provenance correction commit
`9c56a94673a9af1a610e5bcf37c6a67d1bb2c50e`; the Rust reconstruction tests
cover path order, terminal labels, graph/token edge IDs, repeated proposal
provenance, independent score recomputation, and corrupted backpointers.
Converted Rust certificates passed the independent Python validator in
`tests/exact_commit/test_rust_binding.py` and all `2,500` configured T506 cases.

## T503 — Add timeout and diagnostic handling

**Depends on:** T501

- [x] Implement deadline checks at bounded intervals.
- [x] Return `TIMEOUT`, never `INFEASIBLE`, after deadline.
- [x] Report chart entries, relaxations, graph size, grammar size, and elapsed parser time.
- [x] Add a deterministic timeout test hook without wall-clock flakiness.

**Acceptance criteria**

- [x] Timeout test is reliable.
- [x] Partial data is not exposed as an optimal certificate.

**Evidence:** commits `236417fa64004d2001af2569dadd553d0bbe3c2f` and
`bcd0ab47a2b7f5336665d4d1af05a10a6510d929`; deterministic zero-work timeout
tests distinguish `TIMEOUT` from infeasibility and assert that objective and
certificate data are absent. Deadline checks cover bounded parser work and a
final post-reconstruction check prevents a late `OPTIMAL` result.

## T504 — Add Rust unit and randomized tests

**Depends on:** T501, T502, T503

- [x] Port canonical graph fixtures.
- [x] Add randomized small DAG tests against an independent oracle.
- [x] Cover parallel edges, ties, ambiguity, epsilon-normalization output, and multiple finals.
- [x] Run formatting checks.

**Acceptance criteria**

- [x] Rust suite is clean.

**Evidence:** implementation commit `3f074c9a76634783985c9eb4d48348b59fbb4193`;
`cargo test --manifest-path crates/mwpc_parser/Cargo.toml` passed `17` unit and
`3` integration tests, including `500` deterministic Rust-only path/Boolean-CYK
oracle seeds. Crate-local `cargo fmt --check` and strict `cargo clippy
--all-targets -- -D warnings` passed via `make test-rust-parser`.

## T505 — Expose the solver through PyO3

**Depends on:** T502, T503

**Target:** `crates/mwpc_parser_py/`

- [x] Add a Python-visible validated solve function and result conversion.
- [x] Convert labels and IDs losslessly.
- [x] Release the GIL around the CPU-intensive solve when safe.
- [x] Convert Rust status to Python `SolveStatus` without string ambiguity.
- [x] Keep bindings thin and avoid duplicating solver logic.

**Acceptance criteria**

- [x] Binding builds in release mode.
- [x] Malformed Python inputs produce clear exceptions.

**Evidence:** implementation commit `d64d43326b231eaab988e109b808ab56f98174a2`;
`(cd crates/mwpc_parser_py && ../../.venv/bin/maturin develop --release)` built
and installed the CPython 3.11 release binding. `tests/exact_commit/test_rust_binding.py`
passes lossless byte/string labels, stable IDs and provenance, actual Python
`SolveStatus` values, timeout separation, repeated proposal occurrences, and
clear malformed-input errors. Rebuild and Rust checks are documented as
`make bootstrap-rust-parser` and `make test-rust-parser`.

## T506 — Add Python/Rust differential tests

**Depends on:** T505

- [x] Run the same serialized random instances through both solvers.
- [x] Compare status, objective, certificate validity, and path reward.
- [x] Permit different optimum witnesses on ties.
- [x] Save any mismatch fixture automatically.

**Acceptance criteria**

- [x] 100% agreement on the configured normal and extended campaigns.

**Evidence:** campaign implementation commit
`2c64c324c7eb695f9587f961963dba2d5d5e1dca`; release binding rebuilt and
`python scripts/exact_commit/run_m5_rust_differential.py` passed `500/500`
normal and `2,000/2,000` extended cases with zero failures. Versioned summaries:
`docs/evidence/m5-rust-differential-normal-summary.json` and
`docs/evidence/m5-rust-differential-extended-summary.json`; configuration:
`configs/exact_commit/m5_rust_differential.toml`. Ties compare objective and
certificate validity rather than requiring identical witnesses; failures emit
the serialized M4 input and separate metadata under ignored `artifacts/`.

**M5 production-parser gate — blocking**

- [x] Python, Rust, and brute force agree.
- [x] Binding rebuild is documented.
- [x] Existing EPIC tests remain green or pre-existing failures are documented.

**Evidence:** the T506 summaries record zero cross-language/oracle mismatches;
`python -m pytest -q` passed `197` tests; `make check` passed the upstream pin,
lint, strict typing, `12` unit tests, and `184` exact-commit tests; `make
test-rust-parser` passed formatting, `20` Rust tests, and strict Clippy. The
pinned EPIC Rust suite passed `63` tests with `1` ignored and its pre-existing
compiler warnings; the targeted EPIC Python regressions passed `19` with `4`
documented upstream skips. The submodule remained clean at
`5b1b31098f34ed3691d2a9f4aae14fdf5839d072`; `make paper` produced the
15-page PDF.

---

# M6 — Finite token lattice and exact token provenance

## T600 — Audit and choose the tokenizer/model interface

**Depends on:** M5 gate

- [x] Identify candidate `[MODEL_ID]` and tokenizer revision.
- [x] Determine whether token-to-byte emission is compositional.
- [x] Test random sequences, whitespace, Unicode, byte fallback, added tokens, and special tokens.
- [x] Do not assume concatenated `decode([id])` equals full decoding.
- [x] Choose a compositional byte adapter, stateful detokenizer, or different model.
- [x] Record the decision in `docs/decisions/0006-tokenizer-byte-semantics.md`.

**Acceptance criteria**

- [x] The exact mapping used by the lattice is stated and tested.
- [x] Unsupported tokens are identified explicitly.

**Evidence:** implementation commit `0f49153610058c6e0918d79c1f3802c5031da6dd`
pins `GSAI-ML/LLaDA-8B-Instruct` and tokenizer revision
`08b83a6feb34df1a6011b80c3c00c7563e963b07`. ADR
`docs/decisions/0006-tokenizer-byte-semantics.md` defines the exact inverse
GPT-2 ByteLevel raw-byte mapping and rejects all added IDs `126080..126348`
from ordinary grammar emission; the versioned audit lists each of those 269
IDs individually. `HF_HOME=.cache/huggingface .venv/bin/python
scripts/exact_commit/audit_t600_llada_tokenizer.py --local-files-only` passed
the entire 126,080-token base vocabulary, all 256 raw byte values, all added
and special tokens, curated whitespace and Unicode cases, and 20,000 seeded
random sequences, producing
`docs/evidence/t600-llada-tokenizer-audit.json`. The evidence preserves the
deterministic `[47681, 102]` regression showing full decode `"👩"` versus
concatenated singleton decode `"��"`. `python -m pytest -q
tests/exact_commit/test_tokenizer_bytes.py
tests/exact_commit/test_t600_tokenizer_audit_evidence.py` passed 15 tests;
`make check` passed the upstream pin, Ruff, strict MyPy over 24 source files,
12 unit tests, and 199 exact-commit tests; `make paper` produced the 15-page
PDF.

## T601 — Implement per-position support construction

**Depends on:** T103, T104

**Target:** `src/mwpc_exact/support.py`

- [x] Accept logits or an explicit support map.
- [x] Include top-`K` tokens per masked position.
- [x] Include the proposal token if a later policy makes that necessary.
- [x] Include required special tokens according to configuration.
- [x] Use only the fixed token for committed positions.
- [x] Return validated `ExactnessScope` and support diagnostics.
- [x] Canonically serialize and fingerprint the represented rows.

**Acceptance criteria**

- [x] Support is deterministic for fixed logits and tie policy.
- [x] Fixed-position support cannot be widened or omit its committed token.
- [x] `FULL`, `TOP_K`, and `EXPLICIT` metadata matches represented alternatives.

**Evidence:** implementation commit
`f03b9fc3be1920d8060e364e970c0c24b63e87ea`. The model-independent
`src/mwpc_exact/support.py` accepts exactly one of a position-by-vocabulary
logit matrix or an explicit position map, ranks equal logits by ascending
token ID, supports recorded adaptive widths and configured proposal/special
additions, filters through explicit permitted-token semantics, and validates
fixed singleton rows plus `FULL`, `TOP_K`, and `EXPLICIT` scope claims. Its
immutable result serializes the exact rows, permitted token universe, scope,
construction diagnostics, and canonical SHA-256 fingerprints. The existing
token-aligned solver now uses the same canonical fingerprint helper. `python -m
pytest -q tests/exact_commit/test_support.py` passed 28 deterministic tests;
the focused support/scope run passed 35 tests. `make check` passed the upstream
pin, Ruff, strict MyPy over 25 source files, 12 unit tests, and 227
exact-commit tests; `python -m pytest -q` passed all 240 tests; `make paper`
produced the 15-page PDF.

## T602 — Implement layered token-lattice construction

**Depends on:** T101, T102, T601

**Target:** `src/mwpc_exact/token_lattice.py`

- [x] Add one physical boundary per canvas slot.
- [x] Add one token-choice path per supported token in a masked slot.
- [x] Add exactly one choice for fixed positions.
- [x] Attach aggregated reward and proposal IDs once per token choice.
- [x] Preserve absolute canvas position and token ID.
- [x] Validate that every complete token path consumes the configured number of slots.

**Acceptance criteria**

- [x] Enumerating tiny token lattices gives the Cartesian product of supports.
- [x] No path skips or consumes two alternatives for one slot.

**Evidence:** implementation commit
`fb1021bf8acfeab6b5f06622df9a46a2fdaec8b3`. The model-independent
`src/mwpc_exact/token_lattice.py` constructs canonical boundaries `0..n` and
one stable-ID `TokenChoice` per represented `(position, token_id)`, requiring
every choice to cross exactly `position -> position + 1`. It retains the
validated support and exactness scope, aggregates duplicate proposal rewards,
attaches every represented positive proposal ID exactly once, excludes
zero-weight IDs from selected-set provenance, and records proposals absent
from pruned support explicitly. Deterministic `TokenLatticePath` enumeration
and independent path validation make the finite-slot/Cartesian-product
invariant executable without assigning placeholder bytes before T603.
`python -m pytest -q tests/exact_commit/test_token_lattice.py` passed 14 tests;
`make check` passed the upstream pin, Ruff, strict MyPy over 26 source files,
12 unit tests, and 241 exact-commit tests; `python -m pytest -q` passed all 254
tests; `make paper` produced the 15-page PDF.

## T603 — Implement token-to-byte expansion

**Depends on:** T600, T602

**Target:** `src/mwpc_exact/byte_lattice.py`

- [x] Expand each token path into exact byte-labeled edges.
- [x] Attach reward/proposal provenance exactly once.
- [x] Preserve token-edge identity through expansion.
- [x] Handle multi-byte UTF-8 and byte fallback.
- [x] Define behavior for empty-emission and special tokens.
- [x] Avoid prefix sharing in the first version unless provenance is proven safe.

**Acceptance criteria**

- [x] Concatenated bytes of every enumerated tiny path equal the adapter's full detokenization.
- [x] Score is independent of token byte length.
- [x] Distinct token IDs with identical bytes remain distinguishable.

**Evidence:** implementation commit
`cecebd706693901baacaca834f146e82480eb201`. The dependency-free
`src/mwpc_exact/byte_lattice.py` maps every canonical token choice through the
audited `CompositionalByteLevelAdapter` into a private, non-empty chain of
integer byte-labeled `TerminalEdge`s. Every byte edge retains the stable token
edge ID; only the first byte carries the token's aggregate reward and positive
proposal provenance. Canonical intermediate nodes and edge IDs, one-to-one
token/terminal edge maps, independent complete-path validation, and
JSON-compatible diagnostics make the construction replayable. Prefix and
identical-byte alternatives never share internal states. Adapter/scope
vocabulary mismatches, unsupported controls/specials, and empty emissions fail
explicitly. `python -m pytest -q tests/exact_commit/test_byte_lattice.py`
passed 11 deterministic tests, including independent terminal-DAG enumeration,
multi-byte UTF-8 fragments, raw byte `0xff`, fixed slots, score invariance,
same-bytes/different-token provenance, and duplicate-reward rejection. `make
check` passed the upstream pin, Ruff, strict MyPy over 27 source files, 12 unit
tests, and 252 exact-commit tests; `python -m pytest -q` passed all 265 tests;
`make paper` produced the 15-page PDF.

## T604 — Add byte-level grammar fixtures

**Depends on:** T201, T603

- [x] Add an arithmetic-expression byte grammar.
- [x] Add a small DSL byte grammar.
- [x] Add a clearly named JSON subset grammar if manageable.
- [x] Document accepted syntax and deliberate omissions.
- [x] Add valid/invalid sample corpora.

**Acceptance criteria**

- [x] Boolean parser classifications match fixture labels.
- [x] Grammar names do not overstate subsets as complete languages.

**Evidence:** implementation commit
`73b563a8a98d7a6464673c6789cf17b2bc885db1`.
`src/mwpc_exact/reference/byte_grammars.py` defines deterministic source and
normalized byte CFGs for `arithmetic_expression_bytes_v1`,
`tiny_assignment_dsl_bytes_v1`, and the deliberately scoped
`lower_ascii_json_value_subset_v1`. The exact syntax and omissions are recorded
in `tests/exact_commit/fixtures/byte_grammars.md`; the versioned corpus in
`tests/exact_commit/fixtures/byte_grammar_corpus.json` contains 50 cases (22
accepted and 28 rejected). `python -m pytest -q
tests/exact_commit/test_byte_grammars.py` passed 7 tests, recomputing every
corpus classification with the independent Boolean CNF recognizer and checking
deterministic construction, byte-only terminal labels, fixture names, and
scope documentation. `make check` passed the upstream pin, Ruff, strict MyPy
over 28 source files, 12 unit tests, and 259 exact-commit tests; `python -m
pytest -q` passed all 272 tests; `make paper` produced the 15-page PDF.

## T605 — Connect token lattice to the generic exact solver

**Depends on:** T603, T604, T505

- [x] Build a model-independent `solve_exact_commit` path from canvas, support, and proposals to the Rust result.
- [x] Convert the terminal-edge certificate back to token IDs and proposal IDs.
- [x] Validate the result independently.
- [x] Add a Python-backend switch for debugging.

**Acceptance criteria**

- [x] Tiny tokenizer-aware cases match enumeration of token paths.
- [x] Python and Rust backends return equal scores.

**Evidence:** implementation commit
`520f34c33dafe6a34804716909c498e1daa63f81`.
`src/mwpc_exact/finite_solver.py` exposes the Rust-default `solve_exact_commit`
bridge and explicit `ExactBackend.PYTHON` debugging switch over an already
validated finite support. It reconstructs complete private byte paths into
exactly one token per physical slot, cross-checks Rust-reported token-edge
provenance, independently recomputes selected positive proposals and objective,
and runs the Boolean grammar, tokenizer-byte, graph-path, fixed-position,
support, and slot checks before returning `OPTIMAL`. Missing Rust bindings yield
`UNSUPPORTED`; invalid backend certificates yield `ERROR`; `TIMEOUT` and
`INFEASIBLE_ON_SUPPORT` retain distinct payload-free results. Top-K scope is
preserved as exactness on represented support. `python -m pytest -q
tests/exact_commit/test_finite_solver.py` passed 16 deterministic tests with the
release Rust binding, covering tiny path enumeration, variable-length tokens,
same-byte/different-ID choices, multiple matching proposal IDs, fixed slots,
top-K scope, infeasibility, timeout, missing bindings, corrupted certificates,
and equal Python/Rust scores. The focused Rust binding/differential/bridge run
passed 31 tests. `make test-rust-parser` passed formatting, 20 Rust tests, and
strict Clippy; `make test-m5-differential` again passed 500 normal and 2,000
extended cases with zero failures. `make check` passed the upstream pin, Ruff,
strict MyPy over 29 source files, 12 unit tests, and 275 exact-commit tests;
`python -m pytest -q` passed all 288 tests; `make paper` produced the 15-page
PDF.

## T606 — Add finite-lattice randomized tests

**Depends on:** T605

- [x] Generate small token vocabularies with variable byte strings.
- [x] Include same-byte/different-ID tokens.
- [x] Include multi-byte tokens and fixed positions.
- [x] Compare the exact solver with token-path enumeration.
- [x] Save failures as regression fixtures.

**Acceptance criteria**

- [x] 100% agreement in configured campaigns.

**Evidence:** implementation commit
`8d951f0777e4c22f8be286bd559ab3467be69fa0`.
`src/mwpc_exact/finite_differential.py` defines a versioned, replayable seed
schema and a direct Cartesian-product token-path oracle that derives emitted
bytes, all represented positive proposal IDs, and objective values from the
serialized vocabulary/support/proposals without consulting either parser. The
generator forces variable and multi-byte emissions, same-byte distinct token
IDs, multiple proposal IDs on one choice, zero weights, and integer rewards in
every case; half of all seeds contain a fixed position and one quarter force an
infeasible grammar intersection. Every expanded byte path is independently
checked for path validity, exact bytes, score, and proposal provenance before
the Python debugging and Rust production results are compared with enumeration.
Any mismatch writes the exact instance plus failure metadata under the ignored
configured artifact directory; the deterministic serialization path and an
injected failure are covered by tests.

`make test-m6-differential` ran the immutable
`configs/exact_commit/m6_finite_lattice_differential.toml` campaigns against
commit `8d951f0777e4c22f8be286bd559ab3467be69fa0`: the normal campaign passed
500/500 seeds and the extended campaign passed 2,000/2,000 seeds with zero
failures. Together they exhaustively enumerated and audited 42,396 finite token
paths, with both `OPTIMAL` and `INFEASIBLE_ON_SUPPORT` represented. Versioned
summaries are
`docs/evidence/m6-finite-lattice-differential-normal-summary.json` and
`docs/evidence/m6-finite-lattice-differential-extended-summary.json`.
`python -m pytest -q tests/exact_commit/test_finite_differential.py
tests/exact_commit/test_finite_solver.py` passed 22 focused tests. `make
test-rust-parser` passed formatting, strict Clippy, and 20 Rust tests. `make
check` passed the upstream pin, Ruff, strict MyPy over 30 source files, 12 unit
tests, and 281 exact-commit tests; `python -m pytest -q` passed all 294 tests;
`make paper` produced the 15-page PDF.

**M6 gate**

- [x] A finite tokenizer-aware byte lattice is exact on its represented support.
- [x] Provenance and score survive expansion.

---

# M7 — EOS/PAD and finite-slot exactness

## T700 — Freeze EOS/PAD semantics

**Depends on:** M6 gate

- [x] Inspect `GSAI-ML/LLaDA-8B-Instruct` special-token behavior.
- [x] Create `docs/decisions/0007-eos-pad-semantics.md`.
- [x] Define whether EOS is required, optional, or absent in each task.
- [x] Define legal tokens after EOS.
- [x] Define whether PAD emits no grammar symbol.
- [x] Define the physical slot count and effective content endpoint.

**Acceptance criteria**

- [x] Every path has unambiguous token and content-length semantics.

**Evidence:** `docs/decisions/0007-eos-pad-semantics.md` pins the first
production profile to the versioned LLaDA tokenizer audit, records the
configured EOS/PAD alias at token ID `126081`, and retains EPIC's additional
`<|eot_id|>` termination behavior without editing the vendor baseline. It
defines explicit `ABSENT`, `REQUIRED`, and test-only `OPTIONAL` task profiles;
the `BEFORE_EOS`/`AFTER_EOS` transition contract; canonical PAD-only suffixes;
zero grammar emission with per-slot proposal provenance; and independently
recomputable physical-slot, EOS-position, content-endpoint, and byte-length
semantics. The offline evidence regression now fixes the EOS/PAD alias and EOT
control observations. The focused tokenizer/evidence run passed 17 tests;
`make check` passed the upstream pin, Ruff, strict MyPy over 30 source files,
12 unit tests, and 283 exact-commit tests; `python -m pytest -q` passed all 296
tests; `make paper` produced the 15-page PDF.

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
- [ ] Prove or enumerate that each requires more token slots than available.
- [ ] Confirm the finite lattice returns `INFEASIBLE_ON_SUPPORT` or a lower feasible alternative.
- [ ] Store a human-readable explanation and machine fixture.

**Acceptance criteria**

- [ ] At least one minimal counterexample is suitable for the TCC figure/table.

**Evidence:** `[fixture and command]`

## T704 — Run finite-slot randomized/differential tests

**Depends on:** T702, T703

- [ ] Compare finite token-path enumeration with the solver.
- [ ] Randomize EOS position, PAD, fixed slots, and supports.
- [ ] Check that every optimal certificate consumes exactly the configured slots.

**Acceptance criteria**

- [ ] 100% agreement in the configured campaign.

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

- [ ] Validate canvas, proposals, support, and scope consistency.
- [ ] Build token and byte lattices.
- [ ] Call the configured backend.
- [ ] Reconstruct tokens and proposals.
- [ ] Run independent validation.
- [ ] Return structured result and diagnostics.

**Acceptance criteria**

- [ ] API works from explicit saved logits/support without loading a model.
- [ ] Invalid certificate becomes `ERROR`, never silently committed.

**Evidence:** `[tests and commit]`

## T802 — Implement adaptive support expansion

**Depends on:** T601, T801

- [ ] Add `initial_k`, growth policy, `k_max`, and total-timeout config.
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

- [ ] For `OPTIMAL` with a nonempty selected set, commit exactly those proposals.
- [ ] For `OPTIMAL` with zero proposal score/set, choose one masked witness token using the documented deterministic rule.
- [ ] For timeout/error, invoke the configured serial or EPIC fallback.
- [ ] Record fallback type and reason.
- [ ] Do not label a fallback result as optimal.

**Acceptance criteria**

- [ ] Each feasible no-remasking step commits at least one slot.
- [ ] The witness remains compatible after commitment.
- [ ] Fallback metrics distinguish witness progress from error fallback.

**Evidence:** `[tests and commit]`

## T804 — Add component-level profiling

**Depends on:** T801

**Target:** `src/mwpc_exact/profiling.py`

- [ ] Time proposal policy, support, token lattice, byte expansion, parser, backtracking, validation, and commit update separately.
- [ ] Record graph nodes/edges, chart entries, proposals, support sizes, and expansions.
- [ ] Keep profiling optional and low-overhead when disabled.
- [ ] Produce JSON-serializable events.

**Acceptance criteria**

- [ ] Sum and breakdown are internally consistent within measurement overhead.

**Evidence:** `[tests/sample event]`

## T805 — Add offline exact-step integration tests

**Depends on:** T802, T803, T804

- [ ] Use fixed canvases and logits tensors.
- [ ] Test a fully compatible batch.
- [ ] Test a strict optimal subset.
- [ ] Test an empty matched set with witness-progress fallback.
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
