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
