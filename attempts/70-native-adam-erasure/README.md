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

V1 source803fce79 was frozen before ONE build/audit; build succeeded but the
child died with signal11. Loader-only diagnosis confirms generic `step`
resolved to libc's legacy symbol. Failed source/raw artifacts/exit are
preserved; see[the failed result](work/result-v1-failed.md). No passing primary
audit is claimed. V2's[linkage-only protocol](work/protocol-v2-linkage.md)
keeps all numerical criteria/grid/cap and requires NEW independent source
files/commit before a corrected run. Criteria1--8 stay in force; this repair
does not establish novelty, practical use, whole latency or the user goal.

V2 source39ac2f4d passes ALL768 predeclared scalar cases:384 weight freezes,
128 nontrivial fresh-moment erasures,288 exact-rational short trajectories,
474 finite primitive checks and144 enclosure cells.17 primitive nonfinite
outputs are outside contract, not successes. A later source inspection found
an overflow-bound admission corner; see[the scoped V2 result](work/result-v2.md).

V3 protocol078441d9 BEFORE source37b5b984/ONE direct0 repairs only the bound/
native-range admission. All original768 output/work rows stay identical;
EIGHT adverse regressions and four context refusals pass, six with exact
fallback for an unavailable bound. See[the current result](work/result-v3.md).
These are constructed correctness fixtures, NOT measured workload frequencies
or latency/quality gains. The written adaptive trace theorem is conditional
on the declared operation/interface, not an implementation proof for every
PyTorch/CUDA/GS-Scale kernel. Criteria1--8 still require actual consumer/FP
instantiation, priority and complete benefit before a substantive build.

V4 rechecks ALL eight criteria in[the consumer audit](work/consumer-audit-v4.md)
BEFORE a resource screen. NNCP motivates exact adaptive probabilities, but
the open CPU/FP32 route uses beta1=0, different native operations, memory/
clipping/coder work and optional retraining state. Published GPU/Apex and
closed LibNC modes are distinct. Classical beta1=0 weight skipping and
finite-format exact jump tables are mandatory controls, not new inventions.
Only[the fixed optimistic resource gate](work/protocol-v4-resource.md) is
selected: eliminate ALL input-embedding optimizer cost in a common full
component cycle. No actual A70/codec adapter is built from scalar success;
priority/use/full-cost/positive goal stay OPEN. Negative screen has an
explicit stopping rule; no favorable-case/cap/thread/vocabulary rescue.

V4[resource result](work/result-v4-resource.md): ALL56 measured records,
8 warmups+1 setup,65 real forwards/backwards/updates, no accumulated training.
Both frames fail the frozen gate0/2 even with the embedding update FREE;
ideal_single/native_single paired medians are .979/.979 and .994/.994
wall/CPU. This NNCP CPU/FP32 component application is CLOSED, without a
full-codec/A70 adapter campaign. Static checkerV4b passes; a separate receipt
addendum distinguishes actual start producercc36fab5 from end HEADda74d38b.
Criterion reassessment in the result keeps priority/use/full benefit/goal OPEN.

V5[consumer/native-contract audit](work/native-contract-v5.md), before code,
reassesses all eight criteria: (1) actual CTR row lookups are a separate real
use, but one source's coupled decay violates the zero-gradient premise and
another literal no-decay CPU run has only450 updates; (2) interval/FMA tools
are classical, specific priority/significance OPEN; (3) no competent-control
or full-cycle win is established; (4) a WRITTEN native lerp counterexample
blocks blanket monotonicity transfer and a CLASSICAL expression-box proof
gives sound nonvacuous admission; (5) only a fixed108-call primitive audit
is selected before source, not another consumer campaign; (6) model/RNG/
state/export/native partition/full costs remain obligations; (7) short gaps,
decay and equally good classical controls may eliminate benefit; (8) useful
frequency, actual full native adapter, strong total benefit and adequate own
priority remain required. No large build/article promotion or fulfilled goal.

V5[finite native result](work/result-v5-native.md): source242028fd BEFORE
ONE direct0,108 prescribed primitive calls/1800 coordinate checks; all24
tiny boxes pass. Adverse arbitrary-interval endpoint transfer is correctly
refused. No counterexample to zero-anchored admission, no new generic interval
theory, no neural forward/update/timing benefit. Both source consumer scopes
and outstanding native/software/full-cost obligations are explicit. Present
application expansion is declined without a different justified use/advantage;
priority and positive goal remain OPEN.
