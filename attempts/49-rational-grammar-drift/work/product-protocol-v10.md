# Direct product corollary: mathematical algorithm and correctness gate

2026-10-12, BEFORE new code/results. Eight criteria are inherited from the
README and primary-comparison-v10. This does not change the grammar audit.

The quantitative product corollary must be materialized directly rather than
timed through an unnecessarily general binary forest. Two rational tables
share n nonempty finite original-ID domains; entries are nonnegative, row
masses positive and at most1. Normalize by exact per-row masses. For each
head/position clear denominators, start with core[(1,1)], then for each position
concatenate every token's diagonal image of the previous core and compress
once using V8. d=max(1,n), k=ceil(sqrt(d/epsilon)). Exact root normalizers are
the products of the integer row sums. Return the SAME rational[L,U] guarantee;
no ideal reals, stochastic failures, root-mass floor or omitted choices.

Reading/scaling costs O(nq); each step has at mostq*64k candidates, so the
written arithmetic bound is O(nq sqrt(n/epsilon) log(qn/epsilon+2)), with
polynomial input-bit arithmetic. Tiny instances may simply retain every row;
asymptotic improvement is a proof, not a timing selection.

Before measuring anything, compare to independent exact original-ID product
enumeration on ALL: (a) every ordered pair of binary rational rows of
denominator3 at n=1/2; (b) a fixed seeded list of ternary rows at n=1..5,
including zeros, unequal row masses, equal/near-equal and256-bit heads;
(c) all tolerances1,1/2,1/10. Include empty products, zero-row refusals,
misaligned domains and invalid tolerances. This is a correctness gate only.
No favorable corpus, competitive benchmark, new forward or main API change.

If checks pass, use the direct product code as the executable counterpart of
the manuscript's sharper recurrence. Randomized ICML2024 and linear-time
product algorithms remain competent alternatives; this is a deterministic
upper-bound result, not universal hardware dominance.
