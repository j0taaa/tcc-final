# V26 — Known final query, shared refinement for every compressor

Written BEFORE new implementation or V26 observations. V25 remains unchanged
and its entire360-row audit must finish/preserve before a new run. This is a
CLASSICAL optimization and error accounting refinement, not added novelty.

## Contract and algorithm

The exact root normalizers A,B are known before core propagation. At the root,
no future direction is needed: evaluate w=(B,-A) directly on the Cartesian
products/leaf choices of its alternatives. Use the already compressed child
cores; stream the pairs, summing abs(B*x-A*y)/(2*A*B). Do not compress those
root terms or their union. Disjoint root alternatives allow this scalar sum.
This removes a redundant all-direction representation and its materialization.
Every candidate/control compressor receives precisely this SAME shortcut.
Lower-node preparation/compression/budgets and original IDs remain unchanged.

Let alpha be the proved local lower factor of that compressor at the frozen
grid. Endpoints/hybrid have alpha=1-1/(16k²); angular/adaptive have
alpha=1-20/N. Let d0 be the maximal sum of the child error counts across any
root product alternative (zero for a root leaf/unit). No root compression
counts in d0. Keep the same conservative grid chosen from the OLD d>=d0.
If the streamed root result is L0, then

    alpha^d0 * TV <= L0 <= TV,
    U0 = min(1, L0/alpha^d0) <= (1+epsilon)*L0.

Proof: apply the established bilinear all-query invariant only to the two
children of each product, then sum disjoint alternatives. Their factors
multiply; using the largest error count gives the displayed lower bound.
The existing grid/Bernoulli inequality implies alpha^d0>=1/(1+epsilon).
This also covers TV zero, singleton laws and d0=0 exactly. No new inference
principle, optimizer, sampler or global generation guarantee appears.

The factor is rational. Its numerator/denominator have O(d0*log(k+N+2)) bits;
computing it is polynomial work, charged explicitly. Streamed root work is
linear in its candidate count, with constant scalar state aside from existing
child cores/large integers. A streamed algorithm must not inherit a cap on a
table it never materializes. The same150s/3GiB physical guards still apply.
No universal physical acceleration or final upper-bound improvement relative
to the OLD U follows automatically: L0 may increase. Recompute/report honestly.

## Eight-criterion update

1/2/4: same dLLM/CFG numerical-audit operation and quantitative theorem; this
optimization is known and contributes no new publication claim. 3/7: removing
needless root compression strengthens ALL four engines, including the fastest
angular control; it may favor a control rather than endpoints. 5: repeat all75
old independent word cases for all four engines before any larger application;
then all45 existing external pairs are DEVELOPMENT replay, not independent
confirmation of an amended implementation. Retain V25 as observed. 6: charge
root traversal/exact rational factor/process overhead; no omitted preparation.
8: nearest-prior/publication sufficiency and a relevant precision advantage
remain open. No new model forward, corpus or threshold is introduced here.
