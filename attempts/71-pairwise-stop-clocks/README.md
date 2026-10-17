# A71 — Pairwise-independent stopping clocks for finite inference batches

Written BEFORE implementation or new scientific execution. This is a
DIFFERENT operation from A70/previous diversity samplers. A70's closed
applications and all earlier gates remain intact. User goal is still OPEN.

1. **Real use.** Complete a finite, closed batch of DIFFERENT stochastic
   text-generation requests, such as an offline evaluation minibatch returning
   all its individually scored responses. Installed Transformers4.52.2
   `_sample` keeps forwarding/padding the batch until every row finishes.
   Preserve each response law AND every pair's joint law, so any linear mean
   of individual scores has the SAME expectation/variance as independent runs.
   Change only higher-order dependence to reduce batch tail/padding. This is
   a justified AR-inference TCC scope; no default dLLM/CFG adaptation is claimed.
   Refillable serving/GRPO/pass@K/independent joint datasets are different uses.
2. **Own candidate difference.** The proposed contribution is the ONLINE
   stopping-clock interface plus a trajectory/round-count guarantee while
   retaining pairwise-independent COMPLETE outputs. Its count law is the
   CLASSICAL Dawson--Sankoff extremal moment law, with ordinary Bernoulli/
   checkerboard-copula lifting and inverse cumulative hazards. Do not call
   those principles new. A written simultaneous-avoidance/trajectory bridge
   is the candidate specialization; sufficient priority/significance are
   UNCONFIRMED. A passing oracle alone will not justify an article protagonist.
3. **Why choose it.** In the declared private-continuation contract, maximum
   decode rounds are stochastically no larger than iid; all marginal/pairwise
   output statistics remain identical. A constructed rare-long-response family
   has a constant model-round saving, without changing any individual length
   law or average-score variance. Full latency is unmeasured. Competent
   controls: iid native sampling with static and compacted batches, pairwise
   affine-field clocks, other classical moment/copula couplings and length
   bucketing. A Dawson--Sankoff lift is the SAME mechanism, not an adversary
   we purport to beat. Full common clocks are a useful relaxed-contract control
   but generally destroy pairwise independence.
4. **Proof first.** work/theory-v1.md defines private conditional nonterminal
   paths, root clocks, classical moment law, pairwise independence, convex
   size-bias avoidance argument, copula domination and the online bridge.
   It delimits exchangeable-cut optimality and the classic rare-tail bound.
   No every-copula, every-backend or full-wall-time optimum is claimed.
5. **Honest experiment.** Only the SMALL exact-rational/counterexample audit
   in work/protocol-v1.md is selected now. It compares to independent recursive
   Markov enumeration and all moment-polytope vertices, and retains adverse
   compacted-cost/hash-clock cases. No model/corpus/head/training/latency
   campaign is triggered by the written result alone. A future neural test
   needs a prospective input-only corpus/model/gate and full-cost controls.
6. **Complete cost.** Native probabilities, all head/normalization/conditional
   draws, root-clock generation/comparisons, precision/fallback, batching/
   compaction, KV/padding, output and setup must count. Exact rational root
   thresholds can grow O(TB) bits; a fixed float clock is not proved exact.
   Shape-dependent numerical kernels can invalidate per-request independence.
   Round dominance covers fixed shape or affine active-row work plus a round
   overhead, not arbitrary compacted GPU cost or refillable-server throughput.
7. **Fatal objections.** Classical sources may already contain the entire
   specialization. EOS uncertainty may contribute almost no batch tail;
   caps/private content lengths may dominate. Compaction/refill can remove
   the cost, clock/precision overhead can exceed savings. Pairwise independence
   does NOT preserve nonlinear batch metrics/pass@K or the full iid joint law.
   A concave compacted cost can even worsen; preserve that counterexample.
8. **Article gap.** Independently audit specific priority, software numerical/
   batch contract and actual useful stopping variability, then show a relevant
   complete benefit against competent engines and classic couplings on new
   input-only workloads. No human review, publication, practical advantage,
   new dLLM result or fulfilled user goal is claimed at this stage.

Decision: admit only the frozen bounded proof/oracle audit. The aim is a useful
positive inference contribution, not a catalogue of samplers or a new name for
classical moment bounds. Consolidate only if scientific difference and actual
use survive the controls; do not promote constructed examples as a neural win.

V1[result](work/result-v1.md): source697908b3 BEFORE ONE direct0.31 K/q cells,
244 independent moment vertices/210 avoidance optima,992 CDF vectors and
524288 adaptive joint scenarios pass;672 complete individual/pair word
probabilities match recursive native enumeration. All required adverse
compaction/common-clock/affine-control cases are retained. No neural/model/
training/competitive latency or adequate priority has been established.
