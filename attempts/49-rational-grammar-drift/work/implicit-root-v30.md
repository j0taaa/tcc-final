# V30 — Exact scalar query of a Cartesian product, without expanding it

2026-10-13. Written before implementation or measurements. V29 remains valid:
the planar precision bound is obtainable by classical composition. This is a
small algorithmic optimization, not a replacement novelty claim or a new
rounding campaign. V25/V28 observations and all earlier sources stay frozen.

## Operation and theorem

Given integer planar generator lists A=((a_i,b_i)) and B=((c_j,d_j)) and an
integer query (u,v), compute exactly

    F(A,B;u,v) = sum_i sum_j |u*a_i*c_j + v*b_i*d_j|.

Generators may have negative coordinates, zero coordinates or duplicates;
empty lists are admitted. There is no probability, approximation or general
position hypothesis in this operation. It is the support function of the
generator-product zonotope, NOT a Hadamard product of point sets.

**Theorem.** With n=|B| and m=|A|, a rational-order search and two integer
prefix sums compute F with O(n log(n+2)+m log(n+2)) comparisons/arithmetic
operations and O(n) auxiliary integer storage, instead of materializing or
streaming all mn pairs. A and B may be swapped; choose the cheaper bound.
For input integers of at most beta bits, intermediate integer bit lengths are
O(beta+log(m+n+2)); the bound must be multiplied by the cost of arithmetic
and comparisons at that length. Reading A and B and writing the answer count.

This is an upper-bound improvement over Cartesian enumeration for this
specific query. It is NOT a lower bound on all algorithms. Sorting, prefix
sums, sign searches and likelihood-ratio thresholding are classical. Nothing
in this theorem proves sufficient new scientific content for publication.

## Proof

Flipping both coordinates of any generator multiplies each corresponding
summand by -1 and preserves its absolute value. Orient every B generator so
d_j>=0. Partition the d_j=0 generators from the others. The former contribute

    |u| * sum_i |a_i| * sum_{j:d_j=0} |c_j|,

exactly, including a zero query. For d_j>0, sort c_j/d_j by cross multiplication
of positive-denominator integers. Build prefix sums C_k=sum_{j<k}c_j and
D_k=sum_{j<k}d_j. No floating-point ratio or epsilon tie rule is used.

For a fixed A generator put s=u*a_i and t=v*b_i. The sign of
s*c_j+t*d_j is the sign of s*(c_j/d_j)+t. Thus the nonpositive values form a
prefix if s>0, a suffix if s<0, and all or none if s=0. Find its boundary by
binary search using the exact integer predicate s*c_j+t*d_j<=0.

If the sum of these nonpositive values is N_i, their total signed sum is
T_i=s*C_n+t*D_n. The absolute sum is T_i-2*N_i. A prefix/suffix sum gives N_i
in constant arithmetic after the search. Zero summands can be assigned to
either side. Summing all rows and the d=0 contribution proves the formula.
Empty B, u=0, s=0 and equal ratios need no special approximation. Counting
sort comparisons, prefix additions and m binary searches gives the bound.

Products contain at most three beta-bit factors. A prefix adds at most n
integers and the final sum at most mn products, so bit growth is at most
3*beta+O(log(m+n+2)), even with negative intermediates. The implementation
must keep exact integers throughout. Its optional work counters are not
latency measurements or machine-independent operation counts.

## Application without changing the certificate

At the known-query root in forest.py, a binary alternative currently streams
the generators (a_i*c_j,b_i*d_j). Its contribution is F(A,B;b,-a), where a,b
are the two exact root masses. Substituting the exact formula preserves the
integer numerator, lower endpoint, propagated error factor and upper endpoint
literally for EVERY admitted forest, head pair and compressor.

Leaf and empty alternatives remain exact scalar contributions. The parent
OR adds contributions; it does not take the absolute value of their sum.
Earlier compressed child cores, their construction costs and all grammar,
token, normalizer and model costs remain paid. No internal product is faster
by this theorem, no sampler/decoder output is changed, and no model evaluation
is avoided. A streaming pair count is still a logical expansion size, not
peak memory or work actually performed by the new query.

## Validation before performance claims

1. Independently enumerate signed small integer lists and queries; retain zero,
   duplicated, collinear, rank-deficient, extreme-bit and empty cases.
2. On the existing independent JSON/stack word oracle, compare BOTH root
   implementations for all four existing compressors, five head modes and
   three precision values. Require identical interval/error fields and verify
   them against word enumeration. Undefined mass remains undefined.
3. Do not run another neural/rounding campaign. If queried on existing captured
   plans, record cold preparation and query costs separately and treat them as
   development. No synthetic timing win or weakened control establishes use.

## Eight criteria and current disposition

1. Use: reduce the exact final scalar work of the existing frozen-head CFG
   certificate; this supports auditing a generator, not faster neural decoding.
2. Significance: the operation is explicit and the optimization is useful if
   this root cost matters, but its mathematical ingredients are elementary.
3. Comparator: matched integer Cartesian enumeration; a competent sorted
   threshold algorithm shares the same benefit and must be credited.
4. Proof: above, independent of code; no overall CFG complexity improvement is
   asserted until internal products and preparation are also accounted for.
5. Tests: exhaustive independent correctness, not a favorable benchmark.
6. Cost: sorting/prefix construction, exact bit arithmetic, child cores and
   all original preparation count; the query does not save a neural forward.
7. Objection: this can be a routine optimization available to others, and the
   root may be a small fraction of end-to-end work. Both objections stand.
8. Publication: this does NOT fulfill the requested scientific objective.
   The investigation must continue beyond this optimization; do not promote
   it as an EPIC win or silently revive the downgraded A49 novelty claim.
