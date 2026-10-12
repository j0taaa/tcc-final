# A44 — Three-class empirical coupling with arbitrary-vector safety

2026-10-12. Written BEFORE this direction's implementation or observations.
This is a mathematical candidate; it is not confirmed publication novelty.
All A41/A42/A43 sources, negative controls and unresolved claims stay preserved.

## Eight scientific decision questions

1. **Use.** Two expensive dLLM noising loss/gradient evaluations of an actual
   CFG-valid JSON/DSL target, with cheap original corruption draws classified
   by three fixed structural/learned classes. The classifier must be fixed
   using earlier data; the current target evaluations do not select samples.
   Native generation is admissible only with a genuinely cheap informative
   source boundary; the rejected late-root application is not revived.
2. **Difference.** Empirical antithetics, ranked-set sampling, Bernstein
   coefficients and Fréchet bounds are OLD. The scoped candidate is an
   arbitrary-vector unconditional safety theorem at EVERY finite source
   budget for THREE unknown-mass classes, plus a simultaneous atom/minimax
   frontier. Its key analytic step is concavity of the square root of a
   binomial diagonal deficit. These conclusions may already be known.
3. **Choice.** Each original marginal is unchanged; any square-integrable
   vector has pair-average covariance no larger than iid2. At balanced
   classes the class-mean variance approaches the optimal half of iid2 at
   exponential rate in helper draws, with two expensive evaluations and
   constant payload storage. Compare to optimal cap-B source selectors,
   retained RSS, C4, known-mass inverses, seed derangement, count stratification
   and CV. No general domination of those different-information controls.
4. **Without code.** Write the empirical three-label Fréchet joint law,
   lift to original payloads, compute its binomial diagonals, and prove
   square-root concavity/triangle inequalities imply unconditional negative
   cross covariance. Prove the unknown-mass Bernstein frontier and balanced
   minimax class-contrast consequence. Do not infer them from a grid search.
5. **Experiments.** Initially independent finite source enumeration, payload
   aliases, sampler laws, rational matrix minors and explicit unfavorable
   comparisons. Only if the prior-art distinction and application survive,
   freeze a complete-cost external protocol before measuring model utility.
6. **Costs.** B original preparations/classifications, reservoir RNG and
   counters, at most four retained payloads, two forward/backward evaluations.
   Fitting and grammar analysis are charged. Fixed draw budget gives bounded
   helper work, not a wall-clock guarantee. Original noise support and all
   within-class residual variation are preserved; no finite-bank result is
   called a population or training guarantee.
7. **Objection.** This may be a short specialization of ranked-set/systematic
   sampling. A scalar RSS/CV control may win; three classes may explain little
   full-gradient variation. Larger budgets do NOT monotonically dominate C4
   for every target at nonuniform masses: preserve the known(.8,.1,.1)
   counterexample. More than three classes are outside the proposed theorem.
8. **Publication.** Need the actual closest primary theorem, complete proof,
   meaningful dLLM/CFG operation and cost advantage. No priority, human review,
   acceptance, model training, semantic gain or EPIC win is asserted.

Work is isolated in `work/`. The main article and maintained API stay unchanged.
Before a model implementation, verify the analytic step independently and
try to reduce the whole result to a known sampling theorem.

V1 reference is37 lines and uses only integer tickets and one reservoir per
class. Under producer090c357, the independent oracle passes12,844 rational
matrix laws, eight exhaustive original-source product families,360 exact
sampler RNG trees with aliases, and14 polynomial derivative/odd-budget
identities. It preserves the exact unfavorable C6-versus-C4 comparison.
These are correction/proof checks; no new model observations or practical gate.

V2 comparison proves true-balanced covariance domination of ALL six fixed
three-class RSS orders for B>=6; continuous RSS/CV/inverses remain allowed.
Independent enumeration passes354 budget/order checks under3ca3914. The first
oracle assertion confused random-order with BEST fixed-order RSS; its failure
under3f40152 is preserved, and the best adverse control is stronger. Complete
cost/variance thresholds expose demanding explained-gradient requirements.

V3 is a minimal falsification prototype, authorized by the counterexample
criterion, BEFORE an extensive application or novelty claim. It refines the
eight answers: use is ORIGINAL full-parameter training-objective gradients;
past teacher fits are charged/frozen; all six old public targets and32 fresh
corruptions each are used; strong continuous RSS and oracle-CV bank controls
are allowed. The diagnostic20% screen is declared before new gradients, even
with zero sampler overhead. Failure closes this classifier/application branch.
No optimizer update, full training, native EPIC or publication gate is implied.
See `work/feasibility-protocol-v3.json`; primary novelty remains unconfirmed.
