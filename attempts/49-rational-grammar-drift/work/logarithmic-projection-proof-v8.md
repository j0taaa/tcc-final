# Exact polygon queries and the sharper comparative cost

Written2026-10-12 BEFORE code/checks. Nearest-point queries on convex polygons
are CLASSICAL, not claimed as a new geometric data structure. This supplies
an explicit exact-integer implementation/argument for V3's outside-square
queries and sharpens the TV-algorithm bound. V6's slow first public audit is
retained and still running; no completed timings are relabelled.

## Query lemma

Let the centrally symmetric convex polygon K lie in [-2,2]x[-1,1], and take
q=(4,Y). Its projection y onto K has outward normal q-y with POSITIVE first
coordinate. It therefore belongs to the right boundary chain: from the
RIGHTMOST minimum-second-coordinate vertex to the RIGHTMOST maximum-second-
coordinate vertex in CCW order. With redundant collinear vertices removed,
second coordinates increase strictly along this chain; top/bottom horizontal
edges end at those rightmost endpoints and need not be traversed.

Write this boundary as x=f(t), where f is a concave piecewise-linear function
of the second coordinate t. Since4-f(t)>0 and -f(t) is convex,

    D(t)=(4-f(t))^2+(Y-t)^2

is STRICTLY convex. Thus the sequence of squared distances to its ordered
vertices decreases then increases (a two-vertex equality is allowed). Binary
search using D(t_j)<=D(t_(j+1)) finds a minimum vertex in O(log(m+2)) exact
integer comparisons, even with nonuniform vertex spacing. Its neighboring
one/two segments contain the continuous minimizer: a convex function's
minimum lies between the neighbors of its discrete minimum. Compute the
exact squared distance to these two segments by integer cross-multiplication
and retain the closer segment's ORIGINAL endpoints.

Rotate each of the four outside-square sides to the right side by an integer
quarter-turn. The normalized polygon remains inside [-2,2]^2, strictly left
of the right-side query. The same argument applies. Build the four right
chains in O(m) total work. Grid points are scaled by kD as in V3, so no new
real arithmetic, approximate nearest neighbor or numerical tie test occurs.
Any exact tie chooses an edge containing the same unique projection point;
endpoint sets may differ, but V3's ALL-query containment proof still holds.

## Changed costs, unchanged guarantee/cardinality/bit bound

Each of32k outside points now costs O(log(m+2)) arithmetic operations, rather
than scanning m edges. Sorting the original polygon and selected hull costs
O(m log(m+2)), and normalization/chains cost O(m). Therefore V3's SAME
integer64k-row,1-1/(16k^2) compressor costs

    O((m+k)*log(m+2))

exact operations on polynomial-bit integers. Rank0/1 costs O(m); the logarithm
can be1 there. Source preparation, exact inside normalizers and integer
generator preservation remain charged and unchanged.

For an admitted bounded-fan-in forest with constant exact leaf lists, put
M=O(sqrt(d/epsilon)). A product generates O(M^2) rows, a sum O(M), and all
gate compressions take O(M^2 log(M+2)). The complete core arithmetic cost is

    O(H*(d/epsilon)*log(d/epsilon+2)), storage O(H*M+M^2),

times the previously explicit polynomial integer-bit cost. General large
leaf lists/high fan-in use the V3 J bound with O(H*(J+M)*log(J+2)). This is
a refined upper bound, not a lower bound on all competing algorithms.

For ordinary product heads, the sequential diagonal-map/sum recurrence has
q*M rows per step and d=O(n), yielding

    O(n*q*sqrt(n/epsilon)*log(q*n/epsilon+2))

arithmetic operations plus input/normalizer work and polynomial bit cost.
This improves the precision exponent of Feng/Liu/Liu2309.14696 Theorem1's
stated deterministic arithmetic bound (epsilon^-1) to epsilon^-1/2, and
Fu2609.24235's stated paired-head bound (epsilon^-4) as well. Fu ALREADY
removes the log(1/TV) dependence in its real-arithmetic model; do not claim
that removal as our discovery. Specific priority of this sharper TV bound
is still being audited. Classical convex approximation is the ingredient,
not an invented competitor restriction. Recent randomized product methods
remain different, competent controls; no physical timing dominance claimed.

## Prospective falsification

Before another public audit, compare the fast edge's exact squared distance
against an independent scan of EVERY original polygon edge, on every side,
all original integer families, irregular spacing/corners and large anisotropy.
Check all original/returned norm breakpoints and all original-ID forests as
before. Keep the SAME six public format/tolerance cases and controls; changing
the query implementation does not authorize dropping unfavorable inputs.
