# Candidate planar rational compression: written proof before prototype

For a finite multiset A of rational vectors a_j in R^2, define
F_A(w)=sum_j |a_j dot w|. Zero rows can be removed. The intended primitive
returns at most O(1/eta) RATIONAL generators C with

    (1-eta)F_A(w) <= F_C(w) <= F_A(w), for EVERY real w.

Aggregation/geometric normalization are established ideas. This note is not
a claim that their two-dimensional specialization is historically new.

## Rank zero/one

Empty input is exact. In rank one, orient each nonzero row along the same
ray (by its first nonzero coordinate), and replace all by their sum. Absolute
values factor through that ray, so this compression is exact.

## Rational normalization in rank two

Let Z=sum_j[-a_j,a_j]. Enumerate its polygon vertices using exact orientation,
angle comparisons and addition: orient rows into the right half-plane, sort
them by angle, start at minus their sum, and successively add twice each row;
include the antipodal vertices. No trigonometry is needed.

Select vertices u,v maximizing |det(u,v)|, which is positive in rank two.
Let T=[u v]^{-1}, computed rationally. For every x in Z, Cramer's rule and
the maximality of the determinant imply |(Tx)_i|<=1. It is sufficient to
maximize over vertices, since a linear functional reaches its maximum at a
vertex. Also TZ contains +/-e1,+/-e2. Therefore for every w,

    ||w||_infinity <= F_{TA}(w) <= ||w||_1,
    sum_j ||Ta_j||_1 = F_{TA}(e1)+F_{TA}(e2) <= 2.

This uses a maximum-area inscribed basis, not an exact real square-root or
Lewis-weight primitive. Brute pair comparison costs O(m^2) determinants
after sorting; no physical speed improvement is claimed.

## Compression with a finite rational grid

Orient b_j=Ta_j into the right half-plane and remember the sign applied to
the original a_j. Write b_j=r_j d_j, r_j=||b_j||_1>0. A half-diamond direction
is identified by sign(d_j[1]) and t_j=d_j[0] in[0,1]. Bucket by that sign and
floor(N*t_j), where N=ceil(8/eta); the endpoint t=1 may have its own bucket.
There are at most2(N+1) buckets. Directions in one bucket have L1 distance
at most2/N. Replace each bucket by the sum of its oriented ORIGINAL rows.

For a representative direction d of a bucket and any w, triangle inequality
gives

    0 <= sum_j |r_j d_j dot w| - |sum_j r_j d_j dot w|
       <= 2 sum_j r_j ||d_j-d||_1 ||w||_infinity.

Summing buckets and using sum r_j<=2 bounds loss by
(8/N)||w||_infinity <= eta F_{TA}(w). Undoing the invertible normalization
proves the claimed inequalities. The retained original-row sums are rational;
if the inputs are integers, the OUTPUT generators remain integers.

## Composition and the obligation that remains

For a disjoint union of event domains, norms add. For a Cartesian product,
the generator pair is componentwise multiplication. Holding the right row
fixed turns a query into a linear query on left rows, and conversely. Thus
the uniform compression guarantee composes multiplicatively through products
and by maximum error through disjoint sums. This is precisely Fu's known
admissible-gate argument; it is NOT a new FPTAS principle.

With maximal expanded derivation size d and local eta=epsilon/(2d), epsilon
in(0,1], accumulated lower loss is at most1-(1-eta)^d<=epsilon/2.
Since(1-epsilon/2)(1+epsilon)>=1, root output L satisfies

    L <= TV <= (1+epsilon)L.

Normalization constants must be computed EXACTLY outside signed compression;
the final query is(1/Z_P,-1/Z_Q). Applying this to an ambiguous sum of word
derivations is WRONG. A word-faithful packed forest, its complete bit bound,
and the exact distinction from existing approximation schemes remain to be
proved/audited before this is a scientific contribution.
