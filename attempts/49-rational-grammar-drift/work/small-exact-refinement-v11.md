# Small exact inputs: no pointless dependence on requested precision

2026-10-12, BEFORE code/checks. Refinement of the SAME operation, scientific
criteria and theorem; no new novelty claim, cases, comparator or benchmark.
All V1--V10 are already frozen independently and pushed.

After validating/filtering zero integer rows, if m<=k return the original
list. Its norm is EXACT, the cardinality is <=k<=64k and every coordinate
has the original bits. If m>k, perform the proven V8 construction. Its cost
O((m+k) log(m+2)) is then O(m log(m+2)). Thus compression has the stronger
arithmetic upper bound O(m log(m+2)), plus input/grid integer-bit work, for
EVERY precision. This is a standard adaptive exact shortcut, not new geometry
or an algorithm lower bound. Product/forest asymptotic bounds remain valid;
tiny exact inputs need not pay for a huge outside grid. Both old algorithms
and an exact enumerator deserve analogous small-input shortcuts in comparison.

Prospective checks: rerun ALL unchanged V8 geometric/independent projections
and75 original-ID forests; ALL unchanged1,167 V10 product checks. Change the
empty-product oracle's type to Fraction explicitly and assert exact type for
every nonundefined truth. Its former0.0 was exactly zero, not a failed core,
but the rational oracle should not introduce a floating operation.

Add correctness-only cases for ALL existing small product fixtures at
epsilon=2^-1024, independently enumerate their complete original distributions,
and require L=exactTV; k exceeds every intermediate finite list here, so no
approximate compression occurs. Include a four-row signed full-rank integer
input with k=2^512 and all original norm breakpoints. This falsifies an
unnecessary astronomical grid; it is not a favorable latency benchmark.
No new forward, public-head rerun or relabelled V9 timings. The V10 PDF and
its slower but valid upper bound remain immutable.
