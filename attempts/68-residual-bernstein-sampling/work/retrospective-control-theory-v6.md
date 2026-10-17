# V6: a classical lazy integration control, before implementation

2026-10-17. V4/V5 and their original runs are frozen. This is a stronger
CONTROL, not a new contribution. It fills the outstanding coefficient-free/
retrospective comparison before any competitive timing protocol.

## Source and scope

Original Bardenet/Titsias2015, Section3.2, equations7--8 and the following
retrospective paragraph were read at
https://papers.nips.cc/paper_files/paper/2015/file/2f25f6e326adb93c5787175dda209ab6-Paper.pdf
(PDF pages4 and references page9). They compare a shared uniform with
successively refined probability bounds and cite Devroye1986. The general
retrospective mechanism is classical; their DPP bounds are not our HG bounds.
No claim to have read the complete book or executed their DPP code.

## Exact bounds for the SAME node kernel

Adopt V3's already written identity r=1/2+(T+E_nu g)/w and its supplied
|T|<=tbar, |g_i|<=V_i, B=sum nu_i V_i. The control receives the SAME quartic
envelope/moment identities; do not weaken it by withholding this information.
Before any f query, r lies in

    [1/2-(tbar+B)/w, 1/2+(tbar+B)/w].

Evaluate T only if necessary, using the shared m/4m stencils. After computing
g at a subset S, let A_S=sum_(i in S)nu_i g_i and
B_S=B-sum_(i in S)nu_i V_i. Then

    L_S=1/2+(T+A_S-B_S)/w <= r
        <= U_S=1/2+(T+A_S+B_S)/w.

Adding an index increases L by nu_i(g_i+V_i)/w and decreases U by
nu_i(V_i-g_i)/w. Both are nonnegative. Thus the bounds nest, remain within
the initial valid interval and collapse to the exact r after the finite HG
support has been visited. Endpoint high-level kernels equal1/2; base kernels
are the validated V4 scalar computation.

Draw ONE lazy fair-bit uniform. Return1 if it is below the current lower
bound,0 if it is above the current upper bound, otherwise refine. Reusing
the uniform is essential. At exhaustion the comparison is exact; ambiguous
equalities have probability0 in the iid-bit contract. Thus this is an exact
Bernoulli(r) draw, with no source resampling or truncated-tail approximation.
Preselected N and the whole factory law are unchanged.

## Preparation, order and persistent caches

Use the log-concave quartic-tilted HG weights already proved inV3. Locate
their mode with rational ratio binary search, then visit the largest remaining
weight by comparing the two neighbours of the visited central interval.
Contiguous unimodality makes this descending-weight order; exact recurrence
ratios update weights, avoiding repeated binomial products per point. Only
the initial normalized HG point needs balanced GMP binomials. No full table
is prepared. The order is deterministic and independent of f and the uniform.

Cache exact T, stencil values, visited sums and next frontiers per(n,k) when
persistent reuse is enabled. New calls use fresh uniform bits against those
same valid deterministic bounds and may refine further. At exhaustion cache
the exact scalar probability. Caches never retain random outcomes. A cold
call may inspect all m+1 points; no uniform6-query cap, expected constant
query count, optimality or timing theorem is claimed for this control.
It can nevertheless win on cheap formulas/repeated votes and must be measured.

All GMP operations, mode/weight work, source coins, RNG, f queries, cache
preparation and memory remain charged. This is a lazy alternative to exact
coefficient evaluation, so the coefficient-evaluation lower bound is NOT a
lower bound for it. V3's generic importance/sign framework remains classical.

## Prospective correctness stage, no performance gate

Freeze this proof/README update, then source/auditor before ONE run. Keep V4/
V5 unchanged. For every original H>0 fixture and n64/256, every k: enumerate
the full refinement chain independently with integer comb/Fraction; check
initial and every refined interval, nesting, residual/remaining-mass sums,
descending order and exact final probability against the original dense
definition. Check base/H0/endpoint handling separately.

Exhaust dyadic uniform prefixes for selected central/boundary chains, bounding
unresolved prefix mass rather than declaring empirical exactness. Execute
complete outer calls for ALL6 functions,p1/4,1/2,3/4,seeds0..7 and reuse false/
true, preserving every status and matched V5 source tape. Exercise repeated
conditional calls with fresh bits/monotone cache refinement, invalid degrees/
indices/methods and explicit pre-input RESOURCE_FAIL. Source/value requests
are simulated numerical coin inputs, not biological data or neural forwards.

No competitive times, full genealogy or independent usefulness test yet.
Only after these controls pass should the whole-cost protocol be frozen.
Priority, own useful advantage, publication significance and goal stay OPEN.
