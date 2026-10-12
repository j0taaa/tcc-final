# Smaller integer cores: a comparative theorem before implementation

2026-10-12. WRITTEN proof, not mechanized or independently reviewed. The
geometric approximation principle is CLASSICAL (Dudley1974; Har-Peled/Jones,
Theorem1.1, https://sarielhp.org/p/17/dudley_approx/dudley_approx.pdf).
Fu2609.24235 Definition3.6/Theorem3.8 supplies the gate-composition principle.
Neither is claimed as our invention. This refinement changes the quantitative
core bound, not the admitted-forest contract or the target distribution.

## Integer planar compression theorem

Given m integer vectors a_j in R^2 and integer k>=1, construct integer vectors
b_j, at most64k of them, such that for EVERY real w,

    (1-1/(16k^2)) sum_j |a_j.w| <= sum_j |b_j.w| <= sum_j |a_j.w|.

The construction costs O(m log(m+2)+mk) exact arithmetic operations. All
output coordinates are sums of signed input coordinates, with no new rational
denominators. Rank0/1 is compressed exactly. The bit size is polynomial in
the input bit length, independently of conditioning mass or positive TV.

### 1. Linear-time constant-factor normalization after sorting

Let Z=sum[-a_j,a_j]. Orient the nonzero a_j to the right half-plane and sort
by determinant. Walking from minus their sum, adding twice each sorted vector
and then its opposite, enumerates the polygon of Z. Its vertices are integers
with the SAME coordinate parities. Remove collinear vertices if desired.

Choose a vertex u of maximum squared Euclidean norm; choose a vertex v
maximizing |det(u,v)|. Rank2 gives D=|det(u,v)|>0. Reverse v if necessary so
det(u,v)=D. For T=[u v]^-1 and K=TZ,

    conv(+-e1,+-e2) subset K subset [-2,2] x [-1,1].

Indeed beta=det(u,x)/D has |beta|<=1 for every vertex x, hence all x in Z.
Writing x=alpha*u+beta*v, maximality of ||u|| and ||v||<=||u|| imply
|alpha|*||u||<=||x||+|beta|*||v||<=2||u||. The inner inclusion follows from
the four vertices +-u,+-v. Thus h_K(w)>=||w||_infinity>=||w||_2/2. All
coordinates of T are represented by the integer cofactors and D; no square
roots, Lewis weights or inverse-square-root primitive is required.

### 2. Outside square, nearest edges, original endpoints

On the boundary of [-4,4]^2 take the32k grid points with spacing1/k. For
each point find a nearest edge of K, using exact squared distances to segments.
Retain BOTH endpoints of that edge and their opposites. Let P be their convex
hull. At most128k vertices are retained, and P subset K.

Fix a Euclidean unit normal w and x in K maximizing w.x. The ray x+t*w
meets the outside square at a point p with t>=2, since K lies in the stated
inner rectangle. A grid point q on the same side satisfies ||q-p||<=1/(2k).
Let y be the Euclidean projection of q onto K. Projection optimality gives

    (q-y).(x-y) <= 0,
    t*w.(x-y) <= -||x-y||^2 -(q-p).(x-y)
               <= ||q-p||^2/4.

Therefore h_K(w)-w.y<=1/(32k^2). Because y belongs to the retained edge,
y belongs to P. Combining h_K(w)>=1/2 with homogeneity gives

    (1-1/(16k^2))*h_K(w) <= h_P(w) <= h_K(w).

This is the classical quadratic projection-error idea, implemented with
original edge endpoints. It does NOT claim new convex approximation geometry.
Exact squared segment distances require only integer cross-multiplication
after scaling the square grid by kD. No projection coordinate is output.

### 3. Integer generators without precision growth

Map the retained vertices back to Z. Their centrally symmetric hull has2r
vertices z_0,...,z_(2r-1) in boundary order, with z_(i+r)=-z_i. All have the
original common coordinate parities. Its generators are

    b_i=(z_(i+1)-z_i)/2, i=0,...,r-1.

They are INTEGERS, and sum[-b_i,b_i] is exactly this centered polygon: its
starting point is -sum b_i=(z_0-z_r)/2=z_0. Also, each such edge corresponds
to a consecutive interval of original polygon edges, so b_i is a sum of
oriented original a_j. The returned norm obeys the theorem for every query.
There are at most64k rows. Returning the exact original family when smaller
is valid and does not weaken the size bound.

### 4. Cost and geometric optimality boundary

Sorting/constructing the original polygon costs O(m log(m+2)). u,v are found
in O(m), not by enumerating all vertex pairs. Each of32k outside points scans
O(m) edges, then the retained hull can be computed in O(m log(m+2)) by sorting
the selected ORIGINAL vertices; r<=m. Thus cost O(m log(m+2)+mk). Integer
vertices, cofactors, squared distances and comparisons have polynomial input
bits; output is integer aggregation, so no nested rational projections occur.

The exponent1/2 is classically worst-case optimal for ALL-DIRECTION planar
zonotope representations. To see the order, approximate a circle by an
arbitrarily fine centrally symmetric rational polygon. An inscribed polygon
with2r vertices has an angular gap >=pi/r. At that gap's middle its support
is at most cos(pi/(2r)), whereas the circle has support1. An (1-eta) support
guarantee therefore needs r=Omega(eta^-1/2). A rational polygon can be made
arbitrarily close and scaled to integer common-parity vertices. This is NOT
a lower bound on computing ONE TV query or on all possible TV algorithms.

## Admitted-forest corollary and full bit cost

Use the forest-bit-proof-v2 contract: disjoint sum events, disjoint product
scopes, original token assignments exactly once, positive exact normalizers.
Replace its local compressor by the construction above, with integer

    k=ceil(sqrt(d/epsilon)).

Compute k with integer square-root/comparisons on the rational input, not a
real-arithmetic oracle. Its local loss <=epsilon/(16d), so the SAME induction
proves L<=TV<=min(1,(1+epsilon)L). Stored core bound is now

    M=O(sqrt(d/epsilon)), rather than O(d/epsilon) in our V1.

Coordinate-axis containment preserves V2's integer mass bound and O(ell)
bits, including near-identical heads, tiny valid mass and zero TV. Let V be
the largest exact leaf list, K0=max(V,M), and J=H*K0+K0^2. A deliberately
loose COMPLETE cost is O(H*J*(log(J+2)+sqrt(d/epsilon))*poly(ell+log J)),
with O(H*K0+J) integer storage; original-source compilation is separate and
charged, as in V2. For bounded fan-in/constant leaf lists, the gate core work
is O(H*(d/epsilon)^(3/2)) up to logs/bit operations.

Fu's ACTUAL Lemma3.5 bound is M=O(eta^-K), with compression arithmetic cost
O_K(m loglog(m+2)+m eta^-K). For paired heads K=2, its stated binary-product
instantiation has M=O((d/epsilon)^2) and up to O(H*(d/epsilon)^6) core work.
V3 improves these PUBLISHED upper bounds to exponents1/2 and3/2, respectively,
without extended-real primitives. It does NOT prove any other implementation
must attain Fu's bounds, beat a strengthened planar control, or run faster
on a model. In particular a competent geometry implementation may use the
same classical planar improvement; priority of this TV instantiation is OPEN.

For ordinary product heads, use the sequential diagonal-map/sum recurrence
instead of a wasteful general Cartesian product. Each step has q*M rows and
d=O(n), giving arithmetic cost

    O(n^2*q/epsilon + n*q*sqrt(n/epsilon)*log(q*n/epsilon+2)),

and the same complete rational bit accounting. This removes the log(1/TV)
dependence in Feng/Liu/Liu2309.14696 Theorem1's stated
O(q*n^2/epsilon*log q*log(n/(epsilon*TV))) bound. That is a comparison of
the stated arithmetic bounds, not a bit-cost dominance over their whole
implementation or over recent randomized product algorithms. Read their
full reduction before claiming novelty of this corollary.

## Falsification gate before code/measurements

Use exactly the V1 original integer families plus independently selected
polygon corners, signed rays, anisotropic/near-collinear huge coordinates,
rank0/1 and dense polygons. Check ALL original AND returned norm breakpoints,
integer outputs, cardinality and uniform1-1/(16k^2) factor. Reuse V2's complete
original-ID forest oracle with both compressors (no favorable subset). These
remain correctness checks. No new model capture, speed claim, main API,
paper promotion or publication confidence follows automatically.
