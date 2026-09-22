# ADR 0023: Nontrivial MWPC evidence, distinct from the literal-task release

- Status: accepted for implementation; experiments pending
- Date: 2026-09-05
- Depends on: M15; supersedes no historical measurement

## Questions and claims

1. Does the solver remain correct on branching, recursively structured finite
   supports? Require independent recognition and exhaustive score agreement.
2. How often does finite-support greedy commitment lose reward, and how much
   computation buys the exact optimum? Compare identical saved inputs, report
   all statuses and zero gaps; a positive effect is not an acceptance gate.
3. Do real model states offer meaningful alternatives, and does local reward
   optimization improve end-to-end cost without sacrificing functional quality?
   This remains unanswered until actual nonliteral model experiments finish.

Weighted parsing and CFG/automaton intersection are established techniques.
The contribution is their application to the stated commitment objective,
finite token provenance and independently checkable certificates. This study
does not claim a new parsing paradigm or establish priority over all literature.

## Tasks and independent checks

Use three recursive raw-byte languages: two-type balanced brackets, fully
parenthesized arithmetic with single decimal digits and `+`/`*`, and nested JSON
arrays of single decimal digits. Whitespace is explicitly specified, not
silently stripped before grammar validation. Syntax checkers do not call the
CFG solver: use a bracket stack, a small recursive arithmetic evaluator, and
the standard JSON decoder with recursive type/number restrictions. Functional
tasks additionally check nesting/counts, arithmetic value and digit multiset,
or ordered flattened array contents. Grammar rules never encode a task answer.

## Generated paired study

Use seeds 160100--160199 for each family; four masked positions, support widths
2 and 4; unit and integer-utility weights (ranking uses normalized confidence).
A seeded valid string supplies fixed context and
one feasible support path (explicitly a synthetic feasibility-conditioned
study, never called real logits). Other alternatives are sampled before any
selector runs. Enumerate every completion in supports capped at 4096 paths.
Record both total paths and valid paths so singleton-valid cases cannot be
presented as meaningful optimization challenges. Reuse each state's weights
and alternative ordering across nested support widths. Store all inputs.

Compare the independent exhaustive oracle, Python exact, Rust exact, and the
existing finite-support greedy selector. Label that selector precisely; it is
not the upstream serial decoder. EPIC's abstract-gap selector must not be
silently equated with finite-support feasibility or modified to manufacture
comparable results. Actual EPIC comparisons belong in the live experiment or
in separately validated replay with explicit finite-support compatibility.

All oracle/solver disagreement is a correctness gate failure. No performance
conclusion follows from an invalid certificate. Record whole selector latency
including construction/validation, and the exact profiler's existing component
breakdown separately. Rotate selector order. These are exploratory CPU cost
measurements, not uncontended publication latency measurements.

Report paired distributions by family, support width and weight mode, with
infeasible/timeout/error counts. Seeds are the independent generated-state
units within each family; the same seed is shared across families, so a pooled
analysis would have 100 seed clusters, not 300 independent observations.
Widths and weights are repeated measurements, not additional samples.
Do not pool them into an inflated confidence interval. Include all seeds,
not only cases with a gap. Full-width scores must weakly dominate nested widths
for a fixed objective. Feasibility, branch count and support sensitivity are
reported independently of heuristic loss.

## Live pilot, then frozen confirmation

Pilot the pinned local LLaDA checkpoint on varied prompts in the same families.
Capture pre-commit states regardless of eventual success, with model top-K
tokens/probabilities, ordinary proposals, fixed canvas, EOS/PAD policy and model
revision; do not inject a target witness or discard singleton/infeasible rows.
Keep these artifacts separate from synthetic cases. Replay common supports at
K=2,4,8 where resources allow, with bounded solver time and explicit timeouts.

Use serial, EPIC and exact with identical prompts/model revisions and declared
budgets; unconstrained is a syntax/quality control. Compare actual forward calls,
syntax, independent functional success, and total latency, not just proposal
weight. Warm the model, synchronize CUDA for timing and rotate method order.
Repeated timing runs do not multiply the number of independent tasks. Separate
pilot and confirmation prompts/seeds; freeze confirmation only after feasibility
is known, retaining pilot failures and amendments. No tuning on confirmation.

Live experiments require a free GPU, already cached checkpoint, and recorded
source identity. Do not stop unrelated services or purchase compute. Initial
pilot budget: 12 prompts (4/family), 32 slots, at most 32 forwards, 5 seconds
per exact support attempt sequence and 60 seconds per generation, at most one
hour total. A process-level deadline must stop a runaway baseline safely.
If meaningful supports cannot be solved, report that result rather than shrink
the grammar to a literal answer. Confirmation sample size is a separate,
explicitly frozen amendment informed by pilot costs, not effect-seeking stopping.

## Provenance and completion

New immutable configs and exclusive-create run directories only. Record config,
grammar, inputs, software, git commit/dirty flag, seed, hardware and all status
counts. During development retain source hashes alongside diagnostic results;
do not turn a dirty-tree run into committed-code publication evidence. Final
manuscript updates require a frozen code/config commit and regenerated artifacts.
The existing literal-task results and article numbers remain unchanged.
