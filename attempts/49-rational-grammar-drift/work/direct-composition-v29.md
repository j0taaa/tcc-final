# V29 — A competent classical composition recovers the advertised bound

2026-10-13. Written theoretical audit, without code, new tests, model forwards,
or numerical observations. It closes the *black-box-composition* objection
raised in the user's feedback. It does NOT assert that a previous paper
already prints the exact TV formula, or that publication priority is disproved.

## Primary result missed by the earlier comparison

[Chan, *Faster Core-Set Constructions and Data-Stream Algorithms in Fixed
Dimensions*](https://tmc.web.engr.illinois.edu/core.pdf), author manuscript
dated15 July2005, journal publication2006. Sections2.1/2.3/2.4 were read,
including the complete proofs of Theorem2.1, Corollary2.2 and Theorem2.6.
The author's [publication list](https://tmc.web.engr.illinois.edu/pub.html)
identifies the SoCG2004/CGTA2006 paper.

Theorem2.6 constructs a SUBSET epsilon-kernel for directional width in
dimension D, of size O(eta^{-(D-1)/2}), in time O(m+eta^{-(D-3/2)}).
For D=2 both size and additional construction cost are O(eta^-1/2).
This is not merely an existence theorem or a new randomized control.
It is an algorithmic theorem, with floor/square-root real-RAM primitives
declared in the paper. Do not silently replace that model by a bit theorem.

Its proof invokes constant-factor affine normalization, an outside square
grid, selection of ORIGINAL points through nearest-neighbor queries, and the
discrete-envelope algorithm. Theorem2.1's planar base case builds a convex
envelope after sorting slopes, then answers sorted queries by a scan.
Corollary2.2 reduces nearest neighbors to that envelope. This already covers
the two central algorithmic ideas previously credited only generically to
classical geometry: small original-point cores and efficient batched queries.

[Agarwal, Har-Peled and Varadarajan2004](https://www.sarielhp.org/p/01/fitting/)
are earlier epsilon-kernel antecedents; their author-draft Lemma3.6 explicitly
selects original points supporting projections. Chan simplifies these to
nearest ORIGINAL points. The particular old draft has a weaker construction
time; do not use it in place of Chan to manufacture a comparative advantage.

## Step1: turn a width kernel into a zonotope support kernel

Let G be m planar vectors and Z=sum_{g in G}[-g,g]. After exact canonical
sorting, its at most2m polygon vertices V are enumerated by the standard
edge walk. Already ordered input needs O(m) work. For every direction w,

    width(V,w) = 2 h_Z(w) = 2 sum_{g in G}|g.w|.

Take a width eta-kernel S subset V and put R=conv(S union -S). Since V is
centrally symmetric, R subset Z, and width(R,w)>=width(S,w). Both Z and R
are now centered, so dividing the width inequalities by2 gives

    (1-eta) h_Z(w) <= h_R(w) <= h_Z(w),  for EVERY w.

Every centered planar polygon is a zonotope. If z_0,...,z_{2r-1} are R's
vertices in boundary order, z_{i+r}=-z_i, its generators are

    c_i = (z_{i+1}-z_i)/2,   0<=i<r.

Indeed -sum_i c_i=z_0; the half-edge walk and its opposite enumerate R.
Their number is O(eta^-1/2). Thus a standard point-subset epsilon-kernel
already gives the support compressor required by Fu. No new approximation
principle, subset-to-support rate, or admissible-gate theorem is needed.

Preserve the vertex indices: mark S and -S in the original cyclic array,
then scan it. This restores boundary order in O(m), avoids a new hull sort,
and yields canonically ordered generators by one cyclic rotation. The kernel
need not output its selected indices sorted initially. Rank0/1 are exact.

## Step2: integer output is also available to this competitor

When G is integral, EVERY original polygon vertex is congruent to -sum G
modulo2. The selected z_i are original vertices, so the displayed c_i are
integers, each a signed sum of consecutive original generators. Symmetrizing
does not lose this parity. Therefore the output has no new denominators.

This is elementary polygon/parity bookkeeping, not a new difficulty specific
to A49. Chan's use of rounded coordinates to select a point does NOT round
the returned original point. Claiming that every classical kernel necessarily
outputs arbitrary real generators or unstable rational denominators would
weaken this comparator incorrectly.

Chan's published real-RAM time alone still does not prove full bit cost.
The next specialization removes that model gap using the same classical
envelope technique, exact rational normalization and the polygon order.

## Step3: exact rational batched nearest-original-vertex queries

The following is a reconstruction of the classical method, not a claim of a
new epsilon-kernel. It uses neither A49's nearest-EDGE sweep nor a new oracle.

For a rank-two centered polygon, choose a maximum-squared-norm vertex u,
then a vertex v maximizing |det(u,v)|; flip its sign so D=det(u,v)>0.
The usual rational cofactor map T=[u v]^-1 gives

    conv(+-e1,+-e2) subset K=TZ subset [-2,2]x[-1,1].

For x=alpha*u+beta*v, maximality of D gives |beta|<=1, and maximality of
||u|| gives |alpha|<=2. The inner inclusion uses the four chosen vertices.
This is a standard constant-factor fatness construction; the existing V27
proof is a complete elementary verification, not an invented geometric rate.

For integer k>=1 take the32k grid points of spacing1/k on the boundary of
[-4,4]^2. For each choose a closest ORIGINAL vertex of K, then keep it and
its opposite. There are at most64k retained vertices, hence32k generators.
If m<=k return G exactly and skip the grid.

To prove the guarantee, take unit w and an original vertex x maximizing w.x.
The ray x+t*w meets the outside square at p with t>=2. Choose a grid point
q=p+e on its side, ||e||<=1/(2k), including corners supplied by the adjacent
side. If z is a nearest original vertex to q, then x was an available choice:

    ||q-z||^2 <= ||q-x||^2,
    2t*w.(x-z) <= -||x-z||^2-2e.(x-z) <= ||e||^2.

Consequently h_K(w)-w.z<=1/(16k^2). Since h_K(w)>=1/2, the selected centered
hull has lower factor1-1/(8k^2) in EVERY direction. This is the standard
nearest-point epsilon-kernel argument used in Chan, with explicit rational
square constants. A constant-factor difference from the nearest-edge factor
does not distinguish the asymptotic TV bound.

For a right-side query (4,Y) and vertex (x_j,y_j), squared distance, after
dropping the common Y^2, is the line

    l_j(Y) = -2*y_j*Y + (4-x_j)^2 + y_j^2.

A convex polygon has two y-monotone boundary chains. Merge those chains in
O(m), retaining the smallest intercept for equal slopes. The lower envelope
of the resulting slope-ordered lines is constructed by the standard convex
hull stack; line intersections are compared by cross multiplication. Scan
the grid's increasing Y with one pointer through the envelope. Each line is
pushed/popped once and each query is processed once: O(m+k) operations.
Repeat for four quarter-turns. This is precisely the planar envelope/Voronoi
principle of Chan's Theorem2.1/Corollary2.2, with existing polygon order in
place of its radix sorting. There is no floor or floating projection.

All transformed points share denominator D. Multiplying coordinates by kD
makes grid, slopes, intercepts and comparisons integral. Their bits are
polynomial in the input coordinates and log(k+2). Only original integer
vertices are returned, so these auxiliary denominators do not propagate.
For unordered G the initial cost is O(m log(m+2)); for ordered G the whole
compression costs O(m+k)=O(m) after the exact-small-input shortcut.

## Step4: plug the classical kernel into Fu and charge the entire recurrence

[Fu2026](https://arxiv.org/html/2609.24235v1), Definition3.6/Assumption3.7,
Theorem3.8 and Section4.1, supply the support realization and admissible-gate
induction. Definition3.1 permits unnormalized coordinate features with a known
query vector; for the conditioned laws use the exact masses in (1/A,-1/B).
Thus conditioning does not require a new support-realization theorem.
Replacing the particular compressor in Algorithm1 preserves that
induction; its numerical running-time expression must be recomputed, not
reused verbatim from Lemma3.5.

For two products of n>=1 domains with at most q choices, retain paired weights.
The empty product has TV=0 and is returned exactly; an undefined zero-mass
conditioned law remains a refusal, never a certificate of zero distance.
The i-th diagonal-sum gate produces the q nonnegative diagonal images of the
preceding core. Canonical angular order is preserved; singular images collapse
to a line. A standard q-way merge costs O(qM log(q+2)), and the classical
compressor above costs O(qM). Choose

    rho=epsilon/[n*(1+epsilon)],
    k=ceil(sqrt(n*(1+epsilon)/(8epsilon))),
    M=O(sqrt(n/epsilon)).

The per-gate factor is at least1-rho. Bernoulli gives
(1-rho)^n>=1-n*rho=1/(1+epsilon). The root support at the exact normalized
query supplies L<=TV<=U<=(1+epsilon)L, including TV=0. No root mass is
estimated from the compressed norm. The work of ALL n gates is

    O(n*q*sqrt(n/epsilon)*log(q+2)).

This is the exact leading expression used as A49's candidate contribution,
not merely its epsilon exponent and not an epsilon^-1 algorithm in disguise.
Initial rational scaling, row validation, exact normalizers, grid computation
and output arithmetic are paid as in V27; canonical GCD reduction is bit work,
not a magically constant primitive. One global multiplier per Markov layer
likewise recovers the q^2 corollary by the same classical recurrence.

For a disjoint-scope event forest, union takes the minimum lower factor and
componentwise Cartesian product multiplies factors, even with signed cores.
The elementary two-child norm argument is a specialization of Fu's admissible
bilinear-gate principle. Bounded fan-in AND bounded exact leaf lists give
O(H*M^2 log(M+2)) and the same
O(H*(d/epsilon)*log(d/epsilon+2)) forest bound. The classical original-token
chart reduction from V7/V27 remains usable by this competitor too. For wide
unions or large exact leaf lists, retain the extra fan-in/input terms of V27;
the better bounded-arity expression is not a bound for every arbitrary CFG.

## Step5: bit stability also follows without excluding the strong competitor

Clear probabilities to integer weights once per original position, using
products of denominators if constant-arithmetic counting is needed. Inside
masses are computed exactly. On either coordinate axis, support containment
implies sum of absolute retained coordinates is at most the original event
mass. For distinct assignment events this is bounded by the product of the
position multipliers. At products scopes are disjoint; a nonempty scoped node
cannot repeat in an expanded derivation. Thus core, gate intermediates and
root masses have polynomial input bits. Geometry uses only the additional
polynomial-sized cofactors/line comparisons discussed above.

Hence *integer output, no positive-TV floor and polynomial bit stability* do
not provide a separating advantage over this direct classical composition.
There is no claim to have audited every constant or bit bound of Chan's
general higher-dimensional real-RAM implementation: the explicit planar
construction above is what closes that boundary here.

## Scientific disposition

- The current A49 mathematical bound is NOT refuted by this reduction.
- Its improvement over the particular published TV expressions remains a
  quantitative comparison, but that alone does not establish a substantial
  independent technical advance. A competent composition of existing
  epsilon-kernel geometry and Fu recovers the same full bound.
- This audit is NOT evidence that the exact combined TV theorem appeared
  previously in print; chronological priority of that observation is a
  different question. A short specialization/corollary might still be
  publishable, but that cannot satisfy the user's significance requirement
  by assertion or by claiming the ingredients were unavailable.
- V29 adds no new positive result or neural evidence. V25 remains FAILED0/36;
  V28 permits no additional smaller table width in its120 policies. A24 stays
  a separate applied result. Do not use new rounding audits to rescue this.
- The generalized word-chart bookkeeping is classical parsing plus
  representation faithfulness, not currently a separately demonstrated
  own comparative advantage. The main novelty/utility goal remains open.

The prior interpretation that the precision exponent itself could distinguish
A49 from competent classical alternatives must now be downgraded. The
remaining work needs a specific advantage not already delivered by this
composition; no new attempt or large implementation is started by this note.
