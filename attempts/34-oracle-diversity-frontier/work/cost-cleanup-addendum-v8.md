# Cost refinement: discarded-generator cleanup and cache scope

2026-10-11, during the label-free resource diagnostic; NOT a change to that
frozen producer/protocol. `full-cost-v3.md` is preserved. This makes its cost
contract explicit for an actual suspended native payload. It neither claims
new probability theory nor excuses a weak practical comparator.

Let C(U) be prefix-draw work, D(U) work to discard/close its suspended
generator, and V(U) complete retained continuation/consumption/cleanup work.
Each is integrable in one declared additive resource. Their conditional
means may depend on the class. Prefix draws themselves are iid from P;
all selected original payloads retain marginal P. No extra cross-prefix
adaptive memoization is assumed, beyond a fixed common head charged to F.

For an integrable class-only stopping rule N, Wald gives

    E sum_(i<=N) [C(U_i)+D(U_i)] = E N * (c+d).

The two selected payload marginals give expected sum of their hypothetical
discard costs2d and their actual complete-continuation costs2v. Only
unselected generators are actually discarded at the prefix. Consequently

    E total_pair = F + E N*(c+d) + 2*(v-d)
                 = F + E N*c + (E N-2)*d + 2*v.

There is no need to assume cleanup is free or independent of the class.
The previous corollary applies after the substitution c'=c+d, v'=v-d,
when its displayed nonnegative two-stage interpretation is used. If v'<0,
retain the explicit formula and derive the desired comparison directly;
do not invoke an interpretation requiring v'>=0. Cap12 has E N<=3, not
exactly3, so using3 gives a conservative work upper bound, not a measurement.

Real full-cache controls can make the cost of a later oracle draw depend
on previously visited states. Then this simple iid-cost Wald calculation
does not automatically describe their costs. Preserve exact output laws,
but measure complete physical work for those competitors; do not use this
formula to claim cost superiority against such a cache. Native recovery,
GPU state/clone/storage and output/verifier work also remain mandatory.

The frozen resource diagnostic charges actual auxiliary closes to prefixes,
actual first close to its tail, plus separate common initial forward,
grammar/prompt/load costs. It screens feasibility only, has NO competitor
latency/quality claim, and cannot establish a competitive complete decoder.
