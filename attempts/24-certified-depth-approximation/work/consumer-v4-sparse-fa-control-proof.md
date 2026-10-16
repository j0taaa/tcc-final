# Mandatory classical sparse FA / quotient control

Written BEFORE its code or timing. This is a competent stronger comparator,
not a new scientific direction or claimed invention. The eight A24 criteria
still apply. Native Mosaic's dense E×V emission, N×E transition and N×N flow
buffers are properties of those implementations, not of automata inference.
FactorDLM's quotient law, FlashSampling/group recovery, A28 and ordinary
sparse HMM forward/backward are antecedents. Do not claim a memory/latency
win for A24 by excluding this straightforward control.

Use the SAME deterministic symbolic original-token-class graph. An edge is
a set of whole refined global classes; every original word still has one
path. At slot p, aggregate original weights w_p(t) into q_p(c). Fixed rows
are point masses on their original IDs. Edge weight is the sparse incidence
sum sum_{c in edge} q_p(c). No dense E×V mask is necessary.

Backward beta at p is the sum over outgoing edge weight times beta at p+1;
forward alpha is analogous by destination. Segment log-sum-exp implements
these textbook sums without dense transition or N×N flow matrices. From the
current node, draw an outgoing edge proportional to edge weight times suffix
mass; then a class proportional to q_p on that edge; then an ORIGINAL token
proportional to its original weight within that class. This is standard
conditional disintegration and gives the original-word posterior in real
arithmetic. The first draw advances to that edge's destination.

For confidence, edge coefficient at p is alpha_p(src)*beta_{p+1}(dst).
Transpose sparse incidence sums coefficients into classes. Multiply by q_p,
normalize over classes, and multiply selected class marginal by
w_p(t)/q_p(c). Every physical slot conserves the same accepting mass. A class
with zero weight has zero marginal and is never sampled. The padding/EOT
graph is the already proved one, with no separate alias or EOS policy.

With M edge/class memberships, V original IDs, C classes, E edges, N nodes
and n slots, direct arithmetic work is O(n(V+M+E+N)), plus up to O(nV) for
selected original-ID recovery. Live storage is O(M+V+n(E+N+C)), excluding
the input head itself. Sparse incidence and its transpose, grouping, graph
construction, device copies, every kernel and actual output all cost. The
explicit-stack graph may itself be exponentially large; compact CFG controls
remain necessary. Sparse does not prove global dominance or make a giant
graph free to construct.

The opt-in implementation will use float32/float64 Torch sparse/reductions
and original-ID categorical draws. It is numerically approximate, like the
native GPU controls; no rational/finite-RNG exactness is asserted. Small
independent JSON+EOT/PAD enumerations must check the law's real-arithmetic
marginals and observed sample/confidence accuracy, aliases and fixed rows,
on CPU/CUDA. Zero/NaN cases explicitly refuse rather than silently changing
the law. This control is an independent HMM implementation, not an execution
of an unchanged native Mosaic sampler. Require it in a subsequent fair cost
protocol, including preparation/caches, before a positive operational claim.

## Stronger fixed-canvas DAG control, before implementation/timing

The complete initial canvas already yields a layered deterministic DAG.
It is not necessary to repeat a merged automaton's N/E states at all n
positions. Supply this straightforward additional control too. Retain only
the states/arcs reachable and coaccessible at EACH physical layer, using
the same language-only CPU compilation and whole-class memberships.

Build one sparse incidence row per actual DAG arc. Its column for class c
at position p is p*C+c. Multiplying the flattened fresh class weights gives
all arc weights in O(M) work. Backward/forward segmented sums operate only
on that layer's actual arcs/nodes. Transposed incidence computes all class
coefficients at once; normalize separately by physical position as above.
Sampling follows the current layered node and then an outgoing arc, class
and ORIGINAL ID. At a fixed position determinism forces its arc and ID, so
skip all random draws there. Every marginal/word law follows from the same
weighted-DAG identities; no new parsing or sparse-HMM theorem is asserted.

Here E,N,M are TOTAL retained DAG sizes, not sizes repeated n times. Runtime
is O(nV+M+E+N) plus original-ID recovery, storage O(nV+M+E+N+nC) including
the input. Compilation may still be exponential and must be paid. This
control is obligatory before crediting a known unneeded n-fold repetition
as an A24 advantage. It needs the same independent numerical/cached-canvas
oracles. Add both fp32/fp64 variants BEFORE the development timing protocol
is frozen; earlier unexecuted protocol draft stays separately preserved.
