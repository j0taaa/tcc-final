# A41 — universal covariance control for structured-dLLM noising

2026-10-11. NEW direction WRITTEN before implementation/new model outputs.
A39/A40 native losses/limited observations stay untouched. This investigates
a different operation: repeated noising evaluations, not EPIC commitment.

## Eight scientific decision questions

1. **Real use.** Evaluate the stochastic ELBO/score of a CFG-valid JSON/DSL
   candidate (or a difference between two candidates) with fewer errors per
   neural evaluation; potentially compute repeated-example dLLM gradients.
   These are genuine dLLM operations, not replacing an appropriate rule learner
   with a dLLM. GLCs guarantee candidate structure and supply role/field metadata.
   No promise of exact sequence log likelihood or semantic correctness.
2. **Significance.** Empirical antithetics, negative covariance, Loewner matrix
   lifting and stochastic-gradient linearity are KNOWN. Candidate protagonist
   remains the exact unknown-class query frontier of A39, now applied where
   helper corruption draws require NO neural call/head cache. MIRROR/P-POTS
   are close published competitors, not omitted. This elementary corollary
   alone is insufficient novelty. Specific priority and publication remain OPEN.
3. **Why choose?** Two actual score/gradient evaluations, original individual
   noising marginals, and covariance no worse than iid2 for EVERY score/vector
   projection, without a monotonicity or correct proxy assumption. Seek material
   full-cost advantage against MIRROR, stratified timesteps, finite-source
   sampling without replacement, P-POTS and extra iid evaluations. Not a claimed
   universal dominance over those stronger/different objectives or a pass1 gain.
4. **Without code?** `work/noising-theory-v1.md` gives unbiasedness, exact
   covariance matrix, adaptive-classifier stop-gradient condition, arbitrary
   fixed-preconditioner consequences and a quadratic one-update theorem.
   A39 opaque-query minima are separately credited/delimited. No global
   nonconvex convergence or ranking-success inference from a variance bound.
5. **Honest experiments?** First original-source reduction and tiny exhaustive
   law/gradient oracles. Then freeze a real-model/corpus/control protocol before
   measuring variance-times-COMPLETE-cost or updates. All external documents
   selected by input eligibility/ranking, not gradient improvement. Constructed
   MIRROR counterexamples are proof objects, NOT model benchmarks.
6. **Full cost?** Up to4 cheap corruption/class draws,2 expensive original
   model evaluations, RNG/CPU/GPU transfers, grammar roles, any teacher/proxy
   preparation, output/gradient memory and bits. No fabricated verifier delay.
   Same-example iid2 is the matching MC operation; ordinary two-different-data
   training must also be included and can win through lower data variance.
7. **Strongest objection?** An analytic class-conditioned sampler may beat C4
   when masses/inverses are easy. MIRROR/timestep stratification can be better
   in real models. A proxy may predict very little gradient/score variation.
   Finite-source exactness is not an exact continuous-time integral. Copying a
   known sampler to JSON or proving an elementary matrix lift is not novelty.
8. **Publication gap?** Need the genuinely distinct query result, adversarial
   proof and complete original-prior audit; informative cheap grammar-related
   classes and a useful real-model effect with competent controls. No accepted
   paper, independent human review, trained dJev, new training run or EPIC win.

Initial scope is a minimal mathematical/reduction audit. The guarantee concerns
fixed-input Monte Carlo or conditional same-example noise, not improved training
from repeating a datum instead of two independent examples. A large training
implementation starts only after the distinct benefit has survived those
comparators. The current article remains A24; this is not yet a new protagonist.

## V2 — minimal matrix and original-gradient obligations

The independent finite oracle checks67 partitions for M=4/5, the complete
three-coordinate covariance matrix, every principal minor of -C and literal
source marginals. A10-line adapter invokes the expensive evaluator exactly
twice after3/4 cheap preparations. Dependencies/proof are OWN immutable copies
with `work/origin-v2.json`, rather than imports from a mutable attempt.

`work/mirror-counterexample-v2.md` precedes the code: a legitimate scalar
ReLU/softmax model gives MIRROR twice the variance of matching iid2. This is
a mathematical counterexample, NOT an external benchmark; the same document
records a CHEAPER analytic one-bit control with zero variance. The CPU/CUDA
autodiff check is only that constructed model, not MDLM/training evidence.

Ranked-set sampling is another direct classical objection now being audited:
cheap imperfect ranking already gives an unbiased estimator with no larger
variance than iid, without needing exact class masses. A41 cannot claim that
this generic property, the matrix lift or grammar metadata is a discovery.
Its exact cost/frontier difference and real-model usefulness remain unresolved.

## V3 — classical reduction and a separate label-query frontier

The full original-source law equals a symmetrized class-first PIVOTAL design
on a four-source pool. Imperfect ranked-set sampling also has the generic
matrix/iid guarantee. Neither balancing nor the covariance lift is new.
`work/ranked-pivotal-reduction-v3.md` records the primary sources actually
read, exact reductions, and cases where a competent ranked-set control wins.
The learned fixed ordering must remain an admissible control.

`work/label-cost-v3.md` distinguishes raw mask preparation from opaque
classification. Its written bound is4-4c2+2c3 CLASSIFIER calls, versus
4-2c2+c3 raw preparations, admitting unclassified returned states. It is
sharp for the stated conditionally balanced FOUR-POOL design under unknown
label placement and at least three permitted labels; it is NOT a lower bound
for every original-source sampler, analytical inverse, or known class map.
An already-computed original first score is retained; the key must have been
fixed BEFORE that score. Only one additional expensive score is required.
Equally competent pivotal controls may use the identical safe shortcuts.

The23-line independent label-lazy kernel has the same full source joint law.
Three new exact oracles compare all67 small partitions, pivotal and ranked-set
laws, query counts, and every early-return hidden-completion obstruction.
Together with v2, six offline tests pass. The isolated Lean specification
`work/NoisingObstructions.lean` verifies ONLY the finite local obstruction,
with kernel `decide`, no project axioms or admitted proof. It does not verify
the entire written probability/cost argument, Python or neural operation.

All eight criteria are reassessed at the end of the reduction note. Priority,
scientific significance, useful grammar-related proxy, external neural cost
benefit and publication remain OPEN. This is a pre-model reduction/oracle
audit, not a trained model, an EPIC comparison or a new article protagonist.

## V4 — all-budget atom frontier and a failed stronger generalization

`work/budget-frontier-v4.md` writes the arbitrary source-query cap theorem,
hypergeometric/Frechet lower bound and attaining grouped half-rotation,
including the same conditional-completeness argument as the own A39 proof.
Odd budgets equal the preceding even budget. The gain from2r to2r+2 has an
exact Catalan/falling-factorial expression; two new finite oracles check5556
population triples and the preserved counterexample.

This is a comparative ATOM frontier under opaque materialized-source queries,
not a class-query-only bound. At B=8, sizes(1,1,3,3), a union of singleton
classes has positive covariance1/48. Thus atom-optimal balanced larger pools
need NOT preserve the v2/v3 all-score guarantee; do not promote them as a
universally safe training extension. The full neural operation is still absent.
`work/primary-addendum-v4.md` records current LLaDA1.5/VRPO's already known
score variance/budget/common-noise controls and the stronger count formulation
for time-independent denoisers. This theorem's priority, significance and
practical consequence are still unresolved; it is not a publication victory.

## V5 — prospective real noising information audit

`work/information-contract-v5.md`/JSON freeze the SAME count-NELBO operation
as a strong known baseline, with time-independent pinned MDLM. ALL six old
external input-ranked A17 JSONs are DEVELOPMENT only; own document, loader
and config copies carry origin hashes. No old model outputs/code are imported.
Per document32 fit and64 new iid corruptions cost96 real forwards; full-V
float64 OUTPUT-BIAS gradients only, not the entire model/backbone or updates.
A fixed ridge/four-center proxy uses past noise observations before eval.

The minimum code checks lexical features, proxy dimensions, numerical bias
gradients against CPU/CUDA autodiff and finite-bank trace against independent
pivotal enumeration. This is NOT an external benchmark. The opt-in script
`work/noise_information.py` will preserve all outcomes/costs. Whole64-source
bank geometry has free known labels/masses and permits analytical inverse
controls; its covariance improvement CANNOT be reported as a useful opaque-
oracle performance victory. No new neural outputs exist yet. Setup fitting,
strong count/importance/CV/RSS/pivotal controls and priority remain charged/open.

## V6 — exact original count-noising source before the first neural observation

V5's declared finite seed map was not identical to the ideal count law; it
has ZERO external forwards and remains archived. The new standard integer
ticket/unranking representation gives EXACTLY uniform mask count and uniform
subsets within count, including latent aliases. The written corollary in
`work/exact-count-source-v6.md` links this to the original time-independent
normalized NELBO, not a finite seed-map approximation. This is correctness,
not a new uniform-sampling principle. Polynomial bit cost is explicit.

Criteria1/4/6/7 are refined: source preparation and known alias/count information
are charged/available to competitors. Opaque arbitrary-map query bounds do
NOT establish optimality over all mask-specific algorithms. Independent small
mask enumeration checks exact probabilities and aliases; numerical role,
proxy, CPU/CUDA bias-gradient and pivotal geometry checks remain. Protocol v6
is frozen before ALL actual model observations, still an information audit
on six old development inputs, not a competitive or publication gate.
