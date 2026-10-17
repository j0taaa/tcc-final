# V2 — Correct local diagnostic, insufficient own contribution

2026-10-16, AFTER the four rational oracles, BEFORE any real-head readout.
Decision: KEEP AS DIAGNOSTIC/CONTROL; DO NOT PROMOTE THE GENERIC MECHANISM.
No new neural or old-head numerical campaign is triggered by this derivation.
This is a novelty/benefit audit, not an empirical refutation of finite-update
importance sampling. A52 V18's different numeric-gradient gate stays unchanged.

## What was actually checked

The written contract/theory was committed as
f5833c29bfd1bd2bf16af3a2d3aaeddf9a9bfffc BEFORE reference.py/test_reference.py.
The independent enumerator uses Python JSON parsing plus recursive-value
validation; the reference instead propagates stack/phase states. It checks
ALL173 positive observed actions in four small original-ID cases,1038 second
moments for six controls, variable EOS, fixed future IDs/EOS, aliases and zero
proposal weights. It also checks ALL87 visible/459 augmented adaptive paths
with state-dependent heads/planners, target return reweighting, unchanged
policies, invalid actions/gates and a changed-hard-preimage counterexample.

Initial four tests PASS0.275s; formatted source four tests PASS0.276s. Logs
stay separate. Full maintained315 tests PASS88.281s, exit0; focused Ruff passes.
These are exact rational correctness tests, not latency, semantic quality,
native floating-RNG validation or independent human review. There were ZERO
model/head readouts, forwards, new decoder/auxiliary draws, labels or updates.

## Closest additional original source

Vergari, Choi, Liu, Teso and Van den Broeck2021, *A Compositional Atlas of
Tractable Circuit Operations for Probabilistic Inference*. The author's
publication page links the FINAL NeurIPS paper:

https://yoojungchoi.github.io/publications/VergariNeurIPS21/

https://yoojungchoi.github.io/files/VergariNeurIPS21.pdf

Actual reading here: introduction/definitions2.1--2.2, Theorem3.5 and its
adjacent support-recursion explanation, Theorem4.1 and its full main-text proof
with Table2. AppendixC's restatement was located; do not claim the entire
34-page paper or all appendix proofs were read. This is NOT only a workshop
abstract, secondary summary or new citation inferred from the title.

Theorem3.5 already takes restricted real powers of smooth deterministic
decomposable circuits in linear time. The text explicitly explains that sums
with disjoint support allow branchwise powers, keep the same circuit structure,
and permit compact multiplication of circuits with the same support structure.
Theorem4.1 composes powers, products and integration for Renyi divergences.

Our conditional moment is the alpha2 power/product integral with explicit
normalizing scalars. In the particular common grammar/unary model it is even
more transparently the identity

    [1_G(x) prod_i a_i(x_i)]^2 / [1_G(x) prod_i b_i(x_i)]
      = 1_G(x) prod_i a_i(x_i)^2/b_i(x_i)

on positive common support, with the corresponding first-EOS terminal factor.
This uses the SAME grammar, not the intersection of two unrelated grammars.
Original aliases are summed before that operation for the class control.
It is therefore inappropriate to claim a new inference operation or compare
only with a generic unnecessarily quadratic circuit-product implementation.

Together with MIPS's variance identity and PAPL's planned-transition
marginalization, this establishes a direct CLASSICAL composition. We have not
found or proved a substantive own separating advantage. This does not prove
that no later application/systems specialization can be useful; it does
prevent treating these formulas and toy checks as the requested contribution.

## Boundaries and next decision

The diagnostic isolates conditional auxiliary uncertainty, not visible-path
overlap, global ESS or target return accuracy. Ordinary exact evidence supplies
the SAME visible ratio. A length-only control already pays the same two inside
passes; ID-class controls may remove most avoidable noise without full collapse.
No meaningful comparison is established by beating only augmented full IS.

Do not spend new heads or start training just because these four tests pass.
A future independent direction needs a real consumer and an own useful
computational/statistical distinction BEFORE extensive implementation. Known
old heads may be used only under a separately frozen question/control/resource
protocol; they are development and cannot confirm novelty or general usefulness.
The user's positive scientific goal remains OPEN, and this negative mechanism
audit is not its intended final product.
