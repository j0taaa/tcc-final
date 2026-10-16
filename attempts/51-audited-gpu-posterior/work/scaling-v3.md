# V3 — small shared directed frontend, before implementation

2026-10-16. V1's exact law proof remains unchanged. The next limited feasibility
step supplies a common directed lower/upper inside frontend to BOTH the proposed
word correction and the strong interval control; no timing gate is implied.

For bounded original input weights in[0,1] (the actual softmax-head contract),
convert each original binary64 value with explicit downward/upward conversion.
For each original-ID class, sum lower and upper values using explicit directed
binary-tree/blocked addition. Every original ID occurs once in its class; aliases
remain individual outcomes. For a graph edge, sum its DISJOINT class masses;
then sum edge_mass*next_beta over each source node. Lower arithmetic is .rm,
upper arithmetic .rp. Induction encloses the exact original rational mass.
Reject malformed negative/NaN/infinite inputs, duplicate original class IDs,
non-deterministic overlapping outgoing class labels, missing support, bad initial
root or terminal contract. Numerical lower0 may be inconclusive, not zero mass.

A numerical refinement to V1's suggested power-of-two scaling avoids dependence
on exponent/log routines: after computing a layer, take any observed finite
positive binary32 scale S (for example its largest upper beta). Divide EVERY
lower and upper node by this SAME S with directed division; save S's exact
binary bits. If successor beta represented physical mass divided by D, the
new beta represents physical mass divided by D*S. Record ALL scales so the
root bounds multiplied by their exact rational product enclose Z. For a future
max-ratio audit apply the SAME scales to its upper values, using upward division.
Thus M/L is unchanged by the common exact scale factor, and word acceptance
uses M_scaled * product(S). These identities do not require S to be a power of
two; only the directed division and exact scale product are trusted. Each saved
binary32 scale contributes at most149 fractional bits, charged to scalar work.
This is standard rescaled interval arithmetic, not a new result.

A nonfinite raw upper BEFORE rescaling is REFUSE: later normalization cannot
undo it. Underflow in an upper operation yields a positive minimum subnormal,
not zero; tests must exercise that instruction without .ftz. A zero upper may
prove zero only with all the stated enclosure/support premises. Scaling may
be imperfect and give an unusable interval; that is a recorded failure, never
permission to tighten the bound heuristically. Multi-device reductions, atomics,
FTZ and hidden fast-math transformations are not allowed in the trusted path.

First validation is independent enumerated tiny original-word laws, not only
agreement with the same recurrence in double precision. Optional REAL old-head
feasibility would use all15 known development states, input-selected before
running, no new forward, no timing advantage claim and all refusals preserved.
A subsequent cost campaign still requires both complete samplers/controls and
an immutable preregistration. This shared frontend alone cannot establish the
specific useful systems distinction or the user's goal.
