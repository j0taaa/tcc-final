# Submission proof-to-implementation audit

- Audit date: 2026-09-01
- Audited source base: `731e65ccc0ede25b523c10779948351da6d3c3e3`
- Audited reproducibility release implementation:
  `7b0d9aabeeaa3388b4b652b9e24d66f0da9b784d`
- Scope: every definition, theorem, corollary, proposition, algorithm, and
  proof in `paper/main.tex` that makes an implementation-dependent claim.

The governing contract is unchanged: optimization is per step and
`exact_on_support`; `TIMEOUT` and `INFEASIBLE_ON_SUPPORT` are distinct; an
`OPTIMAL` result requires a reconstructible witness and independently
recomputable objective; and the finite canvas, fixed positions, EOS/PAD
semantics, and duplicate proposal provenance must be preserved.

## Correspondence result

| Formal statement | Implementation inspected | Independent checks inspected | Result |
| --- | --- | --- | --- |
| Feasible completion and MWPC definitions; Theorem 1; Corollary 1 | `types.py`, `reference/lexical.py`, `token_lattice.py`, `decoder.py`, `validator.py`, and the completion/subset oracles | proposal, lexical, token-lattice, brute-force, certificate, validator, and decoder tests | Pass after correcting the manuscript's recovered set from every matched proposal to every matched **positive-weight** proposal. The code already enforced this convention; zero-weight IDs do not enter certificates or change the objective, while duplicate positive IDs remain represented. |
| Theorem 2 and Algorithm 1 (token-aligned weighted CKY) | `reference/_token_aligned_core.py`, `reference/grammar.py`, and `reference/normalization.py` | token-aligned examples, exhaustive completion/subset comparisons, normalization tests, and randomized differentials | Pass. The chart enumerates every strict-CNF terminal, binary production, and split; stable ties do not change the primary optimum; backtracking is independently re-scored. |
| Theorem 3 and Algorithm 2 (finite weighted terminal DAG) | `reference/dag_parser.py`, `reference/graph.py`, `reference/epsilon_normalization.py`, `crates/mwpc_parser/src/parser.rs`, and the PyO3 boundary | graph oracle/differential tests, epsilon-normalization tests, Rust/Python differentials, malformed-input tests, and timeout tests | Pass. Both solvers are independent exhaustive max-plus DPs over topological spans. A timeout returns its own status without an optimality or infeasibility certificate. |
| Theorem 4 (finite-slot exactness) | `token_lattice.py`, `byte_lattice.py`, `eos_lattice.py`, `finite_solver.py`, and `validator.py` | finite-lattice and EOS/PAD differentials, tokenizer-byte tests, finite-slot counterexamples, and validator corruption tests | Pass. Every token choice consumes one physical slot; byte and epsilon expansion retain original token-edge provenance; EOS/PAD witnesses still account for all slots. |
| Propositions 1--2 and Algorithm 3 (feasibility preservation and termination) | `decoder.py`, `validated.py`, the LLaDA adapter, and the Q5 exact execution path | decoder, validated-result, offline-step, saved-logit-loop, adapter, and Q5 evidence tests | Pass under the stated premises. Only masks are updated, optimal commits match a validated witness, zero-match progress uses a witness token, and exact commitments are not remasked. Non-optimal fallbacks retain their original status and receive no exact guarantee. |

## Correction made by this audit

The manuscript originally used `Match_C(y)` as the batch returned from an
optimal witness. That set can contain zero-weight proposals, whereas the
scientific data contract and all production certificate paths return exactly
the matched positive-weight proposals. The optimum-value equivalence was
unaffected, but the set-valued claim did not precisely describe the
implementation.

The revised proof defines `Match_C^+(y)`, proves both directions even when a
compatible set contains zero-weight indices, and uses the positive matched set
in Corollary 1, Algorithm 1, lattice provenance, and the theorem-to-code table.
A deterministic regression checks both the manuscript language and executable
zero-weight/duplicate behavior.

## Verification

- `python -m pytest -q tests/exact_commit/test_submission_proof_audit.py
  tests/exact_commit/test_t1300_paper_method.py
  tests/exact_commit/test_t1302_paper_limitations.py` -> 13 passed.
- `make check` -> upstream EPIC pin verified; Ruff and strict MyPy passed;
  11 unit tests and 669 exact-commit tests passed.
- `make bootstrap-rust-parser && make test-rust-parser` -> binding rebuilt;
  17 Rust unit tests and three randomized/oracle tests passed; formatting and
  Clippy passed for the parser and PyO3 crates.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q` -> 690 passed with the Rust
  binding loaded.
- `make paper` -> artifact hashes reverified and the article rebuilt without
  an overfull box or undefined reference. `pdfinfo paper/main.pdf` reported
  16 A4 pages. All 16 rendered pages were visually inspected for clipping,
  overlap, broken equations/tables, page numbering, and bibliography flow.

No theorem premise was weakened, no benchmark or model observation was added,
and no implementation-dependent placeholder was replaced. Subject to the
explicit finite-support and per-step limitations already stated in the paper,
the audited formal claims agree with the final implementation.
