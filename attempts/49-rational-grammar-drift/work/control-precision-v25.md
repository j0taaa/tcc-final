# Ideal-control robustness, before inspecting independent precision ratios

Written during the unchanged V25 campaign, BEFORE its precision gate is
evaluated. No case/tolerance/method, measured source or original gate changes.
This extra mathematical check can only QUALIFY/REDUCE a usefulness claim.
Never attribute its conclusions or postprocessing costs to the old timer.

Let S=2^64, delta=1/S, n be the number of physical slots, and N the number
of admitted forest nodes. The bounds below are LOWER bounds on the ideal
control UPPER bounds, not lower bounds on TV. If their minimum is at least
2U_candidate, a2x precision gain survives removal of control-rounding errors.
This tests every45 pair mechanically; no positive case is chosen here.

## Classical sampler overlap

At a node, downward product rounding contributes at most one delta for a
binary product, and the final downward division contributes one delta.
The sum of maximal-coupling alternative weights is at most one, so errors
propagate by the maximum of child-error sums, plus at most2delta. Empty-scope
units are exactly one. A nonempty scoped node cannot repeat in one expanded
derivation, by disjoint product scopes. Thus root error is at most2N/S.
It follows that the observed full/common minimum obeys

    U_overlap - 2N/S <= U_overlap,ideal <= U_overlap.

The exact common-support loss is unchanged and its multiplier is at most one.
Exact rational coupling itself has polynomial bit length under this scoped
contract: each nonempty node's positive A_v*B_v denominator occurs at most
once in any expanded term. The global product of those denominators clears
all terms and has O(N*ell) bits. The use of64 dyadic bits was an efficiency
choice, not a claim that exact coupling is infeasible.

## Hellinger-based upper

Every nonzero integer atom x*y>=1. Flooring S*sqrt(x*y) therefore loses at
most the relative fraction delta. Positive inside propagation loses at most
(1-delta)^n in affinity, or (1-delta)^(2n) in squared affinity. If the reported
ceil-root upper is h, the ideal upper has lower bound

    sqrt(max(0, 1 - [1-max(0,h-delta)^2]/(1-delta)^(2n))).

This applies to both full and common-support affinities. A rational floor
square-root of this expression is a still-valid lower bound.

## Scale-aware chi-square upper

V18's atom shift64+max denominator bit length bounds the relative atom
rounding by delta, including very small rational probabilities. The positive
inside quantity1+chi_upper is at most (1+delta)^n*(1+chi_ideal). If the reported
conditional bound is c=min(1,ceil_sqrt(chi_upper)/2), then

    min(1, sqrt(max(0, [1+max(0,2c-delta)^2]/(1+delta)^n-1))/2)

is a lower bound on the ideal chi-square control, for BOTH directions. Clipping
at one remains safe. Again take an exact rational floor square-root.

## Combining the controls

Likelihood-range bounds and common-support losses are exact rationals.
Transform each common-support conditional lower bound by the same exact
loss+common_mass*bound formula, then take the minimum of ALL ideal-control
lower bounds. Require this minimum>=2U_candidate for an additional robust2x
claim; keep/report the ORIGINAL64-bit predicate and ALL failures separately.
If it fails, the published observations remain valid but cannot demonstrate
that2x gain against arbitrary-precision versions of the scalar controls.

This is classical error analysis and strengthens the comparison. It adds
no novelty claim, statistical speed gate, neural forward or empirical family.
