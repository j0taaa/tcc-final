# A70 — Lazy Adam with certified erasure of unobserved rounded state

2026-10-17. Written BEFORE code or execution. A DIFFERENT numerical contract
from the real-arithmetic reconstruction audited in M95. Only a minimal
correctness/counterexample prototype is selected at this stage.

1. **Real operation.** Reconstruct an unused sparse embedding coordinate
   before its next model read, and its optimizer state after the next gradient,
   preserving a DECLARED binary32 Adam recurrence. Dense Adam semantics on
   zero gradients are a real Keras/TPU API contract; GS-Scale demonstrates
   the deferred-update operation in graphics. SparseAdam changes that law.
   No native PyTorch/GPU/GS-Scale equivalence is asserted without matching
   their actual operation order/FP environment. This is another justified TCC
   scope; no new dLLM/CFG use or successful real workload is claimed yet.
2. **Candidate own difference.** After certifying that ALL remaining zero-
   gradient parameter writes are absorbed by rounding, keep moments implicit.
   Bound their rounded decay cheaply; at the next real gradient, assign a
   concrete moment only if both interval endpoints produce the SAME nonzero
   rounded result. Otherwise replay the exact moments. Candidate consequence:
   exact read/next-state bits despite skipping both nonlinear weight updates
   and some long rounded-moment recurrences, rather than approximating their
   real-arithmetic sum. Absorption, interval arithmetic, loop summaries and
   Ziv-style endpoint tests are CLASSICAL, not inventions. Whether this
   optimizer-specific combination is sufficiently original/useful is OPEN.
3. **Why choose it.** On certified long gaps the declared native trace is
   preserved with at most H native zero steps and O(log h) counter bit work,
   instead of h zero steps. This is a conditional operation count, NOT a
   lower bound against all algorithms or a measured speedup. Mandatory
   controls include vectorized eager native Adam, exact lazy replay, weight-
   absorption with moment-only replay, GS-Scale-style real reconstruction,
   geometric/block interval controls, and generic interval-state erasure.
   Existing approximate methods may be cheaper and fully adequate for users.
4. **Proof first.** work/theory-v1.md defines the exact FP operation order,
   tail guard, rounded-state enclosure, endpoint admission, fallback and an
   adaptive-training induction. Its bounded-exponent enclosure charges bit
   work for binary gaps. These are WRITTEN proofs, not mechanized or reviewed.
   It does not claim skipping weight decay, EMA, arbitrary native kernels or
   unobserved writes whose state is actually consumed by another operation.
5. **Prospective validation.** work/protocol-v1.md freezes one SMALL binary32
   audit before source/build. Exact rational primitive oracle, declared C
   native recurrence, every predeclared scalar case, signed-zero/rounding
   boundary controls and fallbacks. This is correctness and nonvacuity only;
   no competitive campaign, new model, training or labels are triggered by it.
6. **Complete cost.** Count the head replay, schedule preparation/range bound,
   timestamp/implicit-state storage, integer/Fraction bounds, endpoint tests,
   fallback, final materialization and model/state/RNG requirements. The
   binary32 proof's constants include the finite exponent range; no arbitrary
   precision format is claimed constant cost. Native snapshots of moments
   may force full replay. Real gradient frequency/whole wall/CPU cost remain
   to be evaluated before any practical benefit assertion.
7. **Fatal objections.** A known exact sparse optimizer/compiler may subsume
   the construction. Generic interval erasure can supply the SAME guarantee;
   it is a real control, not excluded. Long gaps/fresh-gradient erasure may
   be too rare; most GS-Scale delays are short. Replaying up to H states can
   lose to a bandwidth-efficient dense kernel. Rounded real powers do not
   reconstruct repeated rounding. An FP32 master cannot be treated as frozen
   merely because its BF16 projection stayed fixed. Any kernel-order, hidden
   state, schedule or rounding-mode mismatch invalidates the identity claim.
8. **Article gap.** Audit priority, validate the actual numerical contract,
   identify a natural workload with relevant successful certificates, and
   show complete benefit against all strong controls before a large build.
   No priority, whole-training result, practical speedup, human review or
   publication is confirmed. The user's positive goal remains OPEN.

Decision: admit only the bounded numerical correctness prototype of this
specific observable-state contract. Do not promote generic absorption,
deferred Adam, or a passing scalar audit as the scientific result requested.
