# A39 — finite known randomness, unknown decoder decisions

2026-10-11. NEW direction written BEFORE code, timings or model forwards.
A38 is preserved independently. A38's unknown-iid-oracle frontier cannot
silently be applied when a caller can inspect/choose known uniform seeds.
This attempt brings that competent alternative into the mathematical model.

## Eight decision questions before implementation

1. **Real use.** Return two original recursive JSON/DSL trajectories from
   a CFG-constrained dLLM. Query only their first native decision for helper
   seeds; continue only the two retained original generators. All statuses,
   IDs, private RNG states and recovery policies remain original. The API
   consumer gets original marginal predictions with improved joint coverage,
   without a gold-dependent objective or changed temperature.
2. **Significance.** Uniform-seed sampling without replacement and empirical
   rank coupling are KNOWN. Candidate results: a finite-source robust
   simultaneous atom optimum, a sharp worst-placement query-cost optimum
   against ALL source-aware adaptive query algorithms, the explicit full-score
   covariance, and coverage/call Pareto order under sound observation
   coarsening. No claim that finite sampling correction itself is new.
   Specific priority and sufficiency for publication remain OPEN.
3. **Why choose it?** Every original trajectory marginal is preserved; for
   every terminal verifier pass@2 is no worse than two iid runs of the SAME
   native decoder. With the common initial prediction available to every
   control, expected total neural forwards remain equal. Against equivalent
   classical four/early pools, helper queries are skipped while preserving
   the FULL retained-pair law. Include cheap iid2/iid3, seed-half and uniform
   seed derangement, biased novelty, rank pools and informed methods. They
   can win; no universal superiority over all these different operations.
   The robust per-atom gain over uniform seed derangement is exactly
   `(t)_2*(M-t)_2/(M)_4`; cap3 cannot robustly improve it. Canonical atoms
   are not arbitrary final semantic-verifier unions.
4. **Without code?** `work/finite-source-theory-v1.md` states the source/query
   model, exact law, covariance, robust lower bounds and coarsening proof.
   `work/native-work-corollary-v1.md` separates expected neural work from
   total physical work. These are comparative results, not just correctness.
5. **Honest experiments.** First use exhaustive finite source populations and
   independent coefficient/law checks. Freeze a native pilot BEFORE new
   outputs, using input-only-ranked external records and all outcomes. A38
   v6 is observed development and cannot be relabelled. No manufactured
   checker delay, output-selected benchmark or weak seed control.
6. **Complete cost.** All first-decision queries, discarded helpers, parser
   retries, dense GPU sampling, head clones, RNG switching, continuations,
   setup and peak memory are counted. Equal expected model-forward count
   is not equal wall time. Finite without-replacement costs do NOT satisfy
   A38's iid Wald identity automatically; use prefix omissions instead.
7. **Strongest objection.** Known seed derangement already gives negative
   covariance for every score with TWO calls. The candidate does NOT dominate
   it for all scores; it targets nonnegligible semantic-class dependence,
   with extra first-decision work. Source-aware worst-placement optimality
   is not pointwise optimality for every labelled decoder. Informed knowledge
   of the decoder, source-code analysis and better batch policies can beat it.
8. **Defensible article.** Need original-source novelty audit, adversarial
   proof checking, minimal validated implementation and a useful measured
   full-cost use. The finite source is the actual uniform-seed policy, not an
   imaginary infinite exact-softmax decoder. No human review/publication or
   general EPIC win has occurred. A38 losses remain visible.

No implementation accompanies this first written version. The known rank
kernel will be copied by immutable commit/hash if this direction passes.
No code or results from another attempt will be imported mutably.
