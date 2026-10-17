# A66 — Audit adaptive averaging in an actual typed dLLM reader

2026-10-17. Contract and proof BEFORE this audit's reference, native-function
replay or numerical evidence. A65's terminal-kernel application stays CLOSED
negative. This operation concerns independent whole read packets, not helpers
from its final head. No neural campaign is proposed.

1. **Real operation.** vLLM's published `structured_diffusion` example answers
   Jev-shaped typed questions. Its `auto` policy expands from one to `m` reads
   if any first-read entropy exceeds a threshold, then averages every read.
   Audit the resulting estimator of the mean of ONE original noise read,
   conditional on a fixed prompt/template/shared thought. This target is a
   statistical interpretation, not a claim that the API promises unbiasedness
   or that its probabilities are calibrated to task answers. Source pinned at
   b05ede56168b5718c425c1493914e5e79f6b8181, Apache-2.0, copied independently.
   The finite-label templates form a regular subclass of structured languages;
   this is not new general CFG inference.
2. **Specific contribution candidate.** A source-level optional-sampling audit
   and a compatible aggregation reference using the SAME returned packets.
   Optional-sampling bias and conditioning the first estimate on a stopped
   sample are CLASSICAL. The eligible-packet mean below is a direct
   Rao--Blackwell application, NOT a new general estimator. Sufficient own
   originality for a paper is presently unsupported. A useful interface
   correction can be retained without promoting it to the TCC protagonist.
3. **Why choose it.** Under the declared iid, total-read model, remove the
   adaptive bias without extra read/model requests, while keeping outputs in
   the same product of simplexes and reducing convex risk relative to the
   FIRST read. No domination of the native adaptive mean or matched-cost
   fixed sampling is claimed. Controls: native `auto`, first read, fixed-m
   mean, an independent-count mixture with matched expected count (oracle
   trigger probability), independent pilot/sample splitting, and classical
   conditional-order symmetrization. The last control is EXACTLY equivalent;
   do not claim an algorithmic separation from it.
4. **Proof first.** `work/theory-v1.md` derives the native mean bias, the
   eligible-packet formula, its covariance reduction and costs. The results
   are written classical consequences, not software/finite-RNG proofs.
5. **Small validation only.** `work/protocol-v1.json` fixes rational finite
   packet laws, both signs of bias, zero/one trigger mass, m=1/2/4, joint
   question triggers, equality at the entropy threshold and a case where the
   native biased mean has LOWER squared error. Execute the ORIGINAL
   `decide_group` body with stub packet acquisition; no server/model/tokenizer,
   dataset rows, golds, new heads, training or timing benchmark. Freeze source
   before execution and preserve failures. This is a correctness/interface
   audit, not independent neural usefulness evidence.
6. **Full costs.** Same original stopping decision, packet count, seeds passed
   by the controller, failures and request order; add predicate checks and
   one vector accumulator over returned packets. No source cost disappears.
   Real parallel scheduling, server failures, shared thoughts and finite seed
   dependence need separate analysis. No automatic validity claim for the
   native `stderr`, which must not be copied as a corrected error bar.
7. **Fatal objections.** The target noise mean may not be the best forecast;
   removing estimator bias need not improve semantic quality or MSE. Native
   seed+offset reads are NOT certified iid by a stub replay. Conditioning on
   successful server returns can destroy the theorem's hypotheses. Classical
   stopped-sample conditioning already supplies the same algorithm and cost.
   These objections prevent a large campaign or article promotion on this
   rationale alone. This is not a new coupling toy or a revived A65 gate.
8. **Article gap.** A sufficiently original, practically important consequence
   beyond this classical correction, and measured benefit in a compatible
   real dLLM consumer against competent controls. No human review, priority,
   calibrated probabilities, neural speed/accuracy or achieved user goal is
   claimed. Overall research goal and T8809 remain OPEN.

The rejected early-stop lead duplicates A53; see
`docs/research/next-operation-audit-2026-10-17.md`. Sources and exact reading
scopes are in `work/primary-v1.md`. This folder preserves only the bounded
audit, independently of A53/A65. No mutable code from another attempt is used.
