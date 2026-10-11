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

The first written version preceded all code. V2 now copies the known
40-line kernel independently from A38's immutable source (origin manifest),
and adds a 21-line uniform distinct-source lookup. Five exact tests enumerate
all270 partitions of4--6 sources, all raw Boolean verifiers, nonmonotone
scores, finite interpolation matrices and all60 four-source coarsenings.
The inexpensive derangement counterexample, weighted-cost counterexample
and failure of all-score variance monotonicity under coarsening remain.
These are independent finite proof obligations, NOT a model benchmark or
a proof by testing of the universal query lower bound. The complete active
suite passes164 tests; no native forward or timing accompanies v2.

All eight criteria above continue to apply. Mathematical plausibility now
has a minimal tested reference; criteria2,6 and8 remain open for priority,
useful full-cost magnitude and native implementation. No production change
or article promotion follows from this test result.

V3 freezes the new first-yield native pilot on ALL input-ranked SVAMP5--8,
with nine competent controls and all72 planned rows. V4 adds the opt-in
minimal adapter: original private generators, an immutable common head,
one-scope completion for simple controls, all helper/physical/memory costs
and runtime zero-helper-forward/unchanged-first checks. Its CPU/CUDA random
tapes, first/final snapshots, head-clone isolation and key exclusion of
input-prefix slots have been checked without a neural model. No new native
model outputs/timings yet. Criteria5--6 are now a concrete frozen protocol,
not satisfied usefulness claims. Priority, magnitude and publication remain
open; the A38 full-call losses and stronger seed controls remain relevant.

V5: complete72/72 original first-yield pilot,1595 new forwards,117 complete
and35 incomplete selected outputs, no errors. Runtime first retention and
zero helper forwards pass. Adaptive25 prefix queries vs full32, but iid2
and derangement need16; medians5.155s vs iid5.041s, pass2=3/8 vs4/8, more
memory. Descriptive pilot does NOT confirm useful overall superiority.
Original EOS-to-PAD suffix rewrites are recorded, never hidden as immutable
internal commits. All nine controls/all inputs/all outcomes are preserved.
Criteria2/3/6/8 remain unsatisfied for the requested publication/usefulness
goal; see `work/usefulness-decision-v5.md`. No main article promotion.

V6 contract BEFORE code/output: examine the COMPLETE first neural step,
preserving the original generator and requiring zero new helper forwards.
The fixed body-token observation excludes special suffix tokens. Existing
input/seed bank is a functional/information audit, not independent quality
evidence. All eight criteria are reevaluated in `work/first-step-contract-v6.md`;
if the boundary remains uninformative, changing its name cannot make it useful.

V7 prototype reads the pinned original no-grad generator frame without
mutating it; CPU/CUDA fast/fallback/immediate-failure boundary checks pass,
including original first/final IDs and caller random states. An opt-in
information audit on ALL old inputs/source seeds is prepared, with two
predefined full-original-ID regressions per input. No model output yet;
toy boundary tests do not establish an informative class or useful benefit.
