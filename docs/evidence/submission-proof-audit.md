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


## M25 formulation clarification, 2026-09-30

The main feasible set explicitly uses the declared per-slot alternatives
`S_i`, and the token-aligned lexical score makes `a not in S_i` impossible.
Its CKY theorem assumes only fixed-length `H`; EOS/PAD restrictions are handled
by composition in the finite-lattice theorem. Production terminal expansion
is the compositional-byte `emit` map. The general lexical relation remains in
the supplementary source as an optional extension, not a live lexer claim.

The main graph pseudocode is now Algorithm 1; token-aligned and decoder
pseudocode remain supplementary. Historical algorithm numbers above refer
to the earlier audited manuscript.

These clarifications retain the same non-negative-score equivalence, positive
matched-ID recovery, neutral productions and finite-slot proof premises.
The optimizer still guarantees only one-step `exact_on_support`; the confidence
and budget policies keep the complete certificate separate from actual commits.
No theorem promises task correctness or future-trajectory optimality.

Final reproduction, tests and rendered-PDF evidence are recorded in
`docs/evidence/m25-delivery-verification.json`.

## M26 mathematical extension, 2026-09-30

The current main theorem numbers change: fundamental equivalence is Theorem 1,
finite slots is Theorem 2, and new resource-DAG, potential-certificate, universal
dominance, confidence-preselection and post-filter separation results are
Theorems 3–7. The old token-aligned/graph proofs and pseudocode are preserved
verbatim in `paper/supplement-foundations.tex`; earlier numbering and the
historical correspondence table above refer to that prior manuscript.

| Current statement | Construction / independent review | Result |
|---|---|---|
| Budgeted equivalence and resource compilation lemmas | `budgeted_commit.py`; token/subset oracle; duplicate/fixed-byte/EOS/PAD checks | Physical positions are charged once on the first original token arc, including epsilon controls. All witness matches and committed IDs are distinct fields; ordinary MWPC selected-set semantics remain intact. |
| Exact budget frontier | `reference/budgeted_parser.py`; 64 recorded-seed exhaustive DAG oracles; token/subset oracle | Epsilon closure keeps exact-cost states; strict-CNF nonempty children have smaller topological spans. Original arc backpointers preserve finite slots and rational scores. No unsafe pruning or global/future claim. |
| Independent optimality certificate | `reference/budget_certificate.py`; altered/missing bounds, feasible suboptimal witness, wrong scope/path regressions | Checker imports no optimizer, validates every upper-potential inequality, independently recognizes the path and requires equality with the upper bound. Tests are evidence of implementation, not substitutes for proof. |
| Universal same-input batch dominance | Budget definition and exactness theorem | Any feasible compared batch is in the optimizer's domain; all matched positive duplicate IDs at paid positions are included. Native EPIC runs with other support/resampling/gaps are outside this automatic comparison. |
| Infinite confidence/preselection family | Fixed regular language, constant weights; original pinned EPIC control flow with exact/universal cover oracles | Ratio 7/(6B) tends to zero by algebra and quantification over all B. Original control-flow tests do not claim a native lexer/model benchmark. |
| Infinite post-filter family | Same fixed language; fixed B=1; existing ordinary MWPC solver as independent regression baseline | Ratio 2/n tends to zero; optimal completion changes with budget. This is a strict objective extension, not a renamed full-MWPC optimum. |
| Capacity frontier and optimal irreversible update rounds | `budgeted_progress_update`; foreign-input, no-remasking/witness-retention and zero-reward fallback regressions | Minimum budget follows from the monotone exact frontier; ceil(M/B) update rounds follow from slot counting and witness filling. No model-call or semantic guarantee. |

Full proofs are in `paper/budgeted-math.tex` and
`docs/research/m26-mathematical-core.md`. Exact binary-rational input semantics,
CNF/empty-word handling, statuses, negative/invalid rewards, finite support and
bit-cost boundaries were reviewed against the implementation. Certificates prove
optimality for the given instance. At the M26 audit, the universal results
were written mathematics rather than proof-assistant formalizations; the M27
extension below adds explicitly scoped Lean coverage. The finite regression suite independently
compares all objectives and witness validity; it is not used to claim typical
accuracy or relevance. Final executed gates are recorded in
`docs/evidence/m26-mathematical-verification.json`.

## M27 certificate and bound mechanization (1 October 2026)

The implemented compact compiler charges only token-identifying closing arcs.
The portable v2 checker additionally verifies complete original-support graph
construction, EOS/PAD transitions, fixed slots, exact rewards and reconstructed
token/commitment metadata. It still imports no weighted optimizer. Historical
M26 graph-only proofs retain their explicit narrower verification scope.

Lean 4.34.0 proves resource-CFG upper-potential soundness, attained-bound
optimality and absent-root infeasibility, free-position relaxation, gap/ratio
and tightness reasoning, prefix emission/membership/node-count statements, and
conditional dominance, fixed offsets and capacity consequences. Five concrete
bridge profiles are kernel-checked, including exact scaling of binary64 0.1.
An altered root bound is rejected. Every audited axiom dependency is standard
Lean logic, with no project axiom, admission or native-decision shortcut.

The [formal coverage map](../../formal/README.md) names the actual propositions
and premises. Original-input compiler correspondence remains independently
checked **in Python**. Universal Python/Rust source refinement, complete DP
algorithm correctness, infinite-language separations and the update-round
formula are not silently claimed as Lean proofs. The written proofs and
independent oracles remain scientifically necessary. Execution evidence is
`m27-formal-checks.json` and `m27-final-checks.md`.

## Current M30 article correspondence (5 October 2026)

The preceding theorem numbers describe the historical unbudgeted source now
preserved verbatim in `paper/supplement-foundations.tex`. They must not be read
as the current main article's numbering. Its nine numbered theorems now map as
follows; all proofs have been inspected against the actual contracts.

| Main theorem | Statement and implementation | Formal boundary |
| --- | --- | --- |
| 1 | Exact budget frontier; `reference/budgeted_parser.py` and `budgeted_commit.py` | Full written induction in `supplement-resource-dp.tex`; Lean certifies resource upper potentials, not Python DP source completeness |
| 2 | Optimality-certificate soundness/completeness; `budget_certificate.py`, `budget_proof.py` | Universal soundness plus concrete original-graph kernel exports; Python checks original token/state correspondence |
| 3 | Same-input batch dominance | `Selection.lean` and written feasible-pair proof; does not equate different native EPIC supports |
| 4 | Confidence/preselection no constant approximation | Infinite-family written proof and unchanged upstream-selector regressions; not a model prevalence result |
| 5 | Post-filtered ordinary optimum can lose arbitrarily much | Infinite-family written proof plus exact enumeration; not an empirical win-rate claim |
| 6 | Conflict exactness and safe two-sided reuse; `conflict_commit.py`, `proof_reuse.py`, independent checker | `Conflicts.lean` covers master cover, transport and amortized queries; one constructed small conflict is additionally exported and checked. A 75-node real replay export timed out at 180 s, recorded in `m29-concrete-conflicts-lean.json`; no blanket concrete Lean pass is claimed |
| 7 | Disjoint token mass envelope and sharp conditional TV; `mass_certificate.py`, `mass_solver.py` | `Probability.lean` proves partition/ratio/scaled-L1/event algebra; independent exhaustive distribution controls check the implementation |
| 8 | Closed-yield and terminal-alphabet support coverage; `language_coverage.py` | Universal derivation-induction yield/alphabet/transport proofs, with full original-vocabulary Python checks; current coverage requires ABSENT EOS |
| 9 | Parallel-update data processing and conditional history-TV composition; `probabilistic_update.py` | Complete written event/coupling proof, exact small history-distribution controls; Lean checks finite error-budget arithmetic, not a full probabilistic coupling construction |

The geometric rejection-work identity is an explicitly established corollary,
not a measured timing result or a new sampling principle. The source-level
correctness of all Python, Rust, kernels, tokenizers and models remains outside
Lean. Tests and independently checked certificates complement, rather than
replace or overstate, this mathematical proof scope.
