# V19 — Ordered integer cores and a sharper product arithmetic bound

2026-10-12, BEFORE implementation/checks. Geometry, rotating sweeps and
multiway merging are classical. The candidate result is their quantitative
TV propagation bound, not a claimed new convex-approximation principle.
V18 and all earlier evidence remain immutable.

## Ordered core contract

Orient every nonzero integer pair into x>0 or x=0,y>0. This preserves its
absolute-projection norm. Sort by determinant and merge adjacent collinear
generators. Maintain the resulting angular order throughout the recurrence.
Equal-angle aggregation is exact. Zero/rank-one cases stay exact.

Given m ALREADY ORDERED generators and k>=1, construct the V3 endpoint core
in O(m) integer arithmetic operations, retaining the same64k rows and
1-1/(16k²) all-query factor. For unordered input add O(m log(m+2)) sorting.
If m<=k, return the exact ordered list before any outside grid. Otherwise
k<m, making O(m+k) work O(m). Output generators are again angularly ordered.

## A linear polygon without a second sort

For ordered distinct directions a_0,...,a_(m-1), start at z_0=-sum a_i and
walk by2a_i. The first m vertices followed by their opposites give the
strict convex boundary in CCW order. This is the usual exact zonotope
construction. All vertices retain common parities. Choose u/v and the same
integer cofactor normalization as V3, with diamond subset K subset
[-2,2]x[-1,1], in linear scans. No hull sort is necessary.

## Monotone outside-point queries

After each quarter-turn, process the8k right-side grid points in increasing
y in the TURNED frame. A closest point lies on the right chain. Its y is
nondecreasing as the query's y increases: adding the two minimizing-distance
inequalities at Y1<Y2 yields (Y2-Y1)*(t2-t1)>=0. Equivalently, the chain
distance is phi(t)+(t-Y)^2 with convex phi.

Squared distance to consecutive chain-segment intervals decreases until the
continuous minimizer, then increases. Maintain a segment pointer, advancing
while the next distance is <= the current distance. Choose the LAST edge in
a tie, so a shared-vertex plateau cannot move the pointer backwards. The
pointer advances at most the chain length over all8k queries. Every distance
comparison is an integer numerator/denominator cross multiplication.
Four chains therefore need O(m+k) work, including initial preparation.

Retain BOTH endpoint indices and their opposite indices in a Boolean array
of the original polygon length. Scan that array in original boundary order;
the selected polygon is already convex and symmetric. Divide its first
half-edge differences by2 to get integer generators. Their angular order
is cyclic; canonical orientation introduces at most one wrap. A linear scan
locates the smallest canonical angle, then rotates the list. This restores
ordered output without sorting. Parity/integer-coordinate, projection-error
and bit bounds are exactly the V3 proof; no rational projection is output.

## Products: q ordered streams, not one fresh sort

At position i let q_i<=q be the original alternatives and let the preceding
core have at mostM=64k pairs. For each nonnegative diagonal map
diag(a_i(v),b_i(v)), the image of the ordered core stays ordered. A singular
map collapses to a horizontal/vertical direction after canonical orientation,
and its zero images are omitted. Merge these q_i streams with an exact-angle
heap, aggregating collinear consecutive images. Work is O(q_i*M log(q_i+2));
the merged list feeds the linear ordered compressor above. No original token
event is lost: these are norm representations, not probability samplers.

Consequently, with the SAME calibrated k=ceil(sqrt(n*(1+epsilon)/(16epsilon))),
two rational products over n domains of size at mostq admit the SAME
deterministic interval L<=TV<=U<=(1+epsilon)L in

    O(n*q*sqrt(n/epsilon)*log(q+2))

integer arithmetic operations, PLUS input/scaling/exact-normalizer work.
Coordinates have O(input bits) length by the unchanged axis-norm invariant;
comparison/intermediate bit costs are polynomial in input bits and
log(n/epsilon+2). No minimum positive TV/mass, ideal real primitive or
independence assumption beyond the specified product is added. Empty product
TV=0 and zero head mass is undefined. The exact shortcut avoids huge grids
on small instances at extreme precision.

Compared with V8, the log(n/epsilon) sorting/query factor is removed for
products; general grammar-forest AND composition still has its previously
stated bound. This is a specified-algorithm upper-bound improvement, not a
lower bound for every deterministic TV solver or universal physical speed.
The strongest adaptive angular/scalar controls remain in any real comparison.

## Prospective adversarial checks and eight criteria

Before any new real audit: repeat ALL original geometry families at k=1/2/4,
checking ALL original/retained norm breakpoints. Independently enumerate
EVERY segment for each outside-grid query and compare the sweep distance;
ties may choose different endpoints, so compare distances, not vertex IDs.
Check ordered output after compression and diagonal maps, including zeros,
aliases of integer directions and singular maps. Repeat ALL1,167 existing
product cases and389 extreme-precision cases against independent original-ID
enumeration. No synthetic timing benchmark. A failure blocks real use.

Criteria1/6 retain the real numerical dLLM/GLC audit and complete costs.
Criteria2--4 sharpen the candidate deterministic TV theorem, explicitly
crediting classical ordered geometry; products are a corollary of the grammar
framework, not its only application. Criterion5 uses unchanged correctness
families; any later public run must keep every format/tolerance/strong control.
Criterion7 includes adaptive angular and exact small scalar competitors,
sorting/bit costs and the unchanged general-forest bound. Criterion8 still
requires a precise nearest-prior comparison and independent human judgement;
no publication/priority certainty follows from this refinement.
