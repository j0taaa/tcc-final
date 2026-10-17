# Cold value-call corollary, analytical and restricted

2026-10-17. Written AFTER the coefficient audit, BEFORE any sampler/resource
benchmark. No timing or empirical gate is introduced. The V1 protocol/results
and all comparison limitations remain unchanged.

The positive-mixture algorithm in theory-v1.md evaluates one local coefficient
at its chosen degree n_J. At J=0 this needs3 f-values. For J>=1 its new
coefficient uses3 values and naive elevation of the old row uses at most
3(m+1) values, m=n_J/4. With no cross-output cache at all, the total is at
most3 at J=0 and3m+6 otherwise. Since

    P(J>=1)=2c/n0^(3/2),
    E[(n_J/4) 1_(J>=1)]=(7/2)c/sqrt(n0),

the expected number of value calls is at most

    3+(21/2)c/sqrt(n0)+6c/n0^(3/2).                           (8)

This counts actual f-queries, not unit-cost bit arithmetic. Binary splitting
changes the arithmetic but need not increase this query bound. Preparation,
coin calls, auxiliary bits and all integer work remain separately charged.

The ordinary Boolean-sum coefficient at an interior grid point requires all
n+1 values in the exact unrestricted value-oracle model, on a class with
strict norm/range slack allowing the unread-point bump argument; endpoints
only require1. This is an oracle-class bound, not a lower bound for a known
fixed formula. For a method using that coefficient at some preselected degree
N>=n0 independent of the coins, this gives the restricted lower bound

    E[value calls]>=1+n0[1-p^n0-(1-p)^n0].                    (9)

For metadata n0=16,c=9/4, the candidate bound(8) is1167/128.
On p in[1/4,3/4], the lower bound(9) is at least
1+16[1-(1/4)^16-(3/4)^16], which exceeds16.8. Thus the candidate's value-call
bound is less than55% of THAT lower bound, a greater than45% reduction in
this particular cold oracle-class comparison. This is an analytical resource
consequence, not an independently measured implementation gain.

Strong limitations: this does not compare the number of input p-coins or the
full latency of the two factories. The Boolean method may admit a smaller
initial degree; caching/preparation can amortize its value queries. A supplied
formula, derivative oracle or another local quasi-interpolant may remove its
query lower bound, and remain mandatory competent alternatives. The spline
formula is itself explicit, so do not describe this oracle bound as the
optimal practical way to simulate that known formula. The statistical target
and exactness must match before any performance comparison. No general claim
against Sevy/HNP/all classical factories or sufficient article novelty follows.
