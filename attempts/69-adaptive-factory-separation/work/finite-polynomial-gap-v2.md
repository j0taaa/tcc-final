# V2 written corollary: arbitrarily large gaps already for finite polynomials

2026-10-17, AFTER V1's finite audits. New WRITTEN result; no new code, tests,
timings or source calls. Do NOT attribute it to the earlier oracle execution.
It uses V1's candidate infinite separation and classical compactness.

## Statement and constructive upper bounds

Retain V1's p_n,L_n,M_n,q_n,G_n,g_n and define the FINITE polynomial

    f_R(p)=1/4+(1/4)sum_(n=1)^R q_n g_n(p), R>=1.

It has an exact adaptive factory: V1's algorithm returns0 on its rare-branch
ticket whenever the sampled n exceeds R. Its source calls are pathwise no
greater than those of the infinite algorithm, so

    sup_(R,p) E_p T_R <= B < infinity.

Here B is the explicit uniform INPUT-call bound in V1; no added timing gate.
Every f_R also has an elementary preselected-batch implementation: if level
n<=R is reached, consume ALL M_n source calls before evaluating the finite
predicate; otherwise consume none. Its expected input size is exactly

    (1/4)sum_(n=1)^R q_n M_n=R/4.                         (1)

Thus every finite member is a legitimate finite-mean batch problem, without
depending on an infinite response as the only comparison target. That simple
control need not be optimal and is NOT the lower-bound comparator.

Let A_R be the infimum of E N over ALL preselected fully consumed batches
for the SAME f_R. Arbitrary output kernels/computation and knowledge of f_R
remain allowed. Then, CONDITIONAL ON V1's non-C2 proof being correct,

    A_R -> infinity.                                    (2)

Consequently, for every requested factor G there is an R0 such that, for
all R>=R0, every preselected implementation uses more than G B input calls
in expectation, while the adaptive one uses at most B for every p.
This is a qualitative existence result: no explicit useful R0 or rate for
A_R is provided. In particular it is NOT a finite measured large speedup.

## Compactness proof against every output rule

Suppose2 fails. An unbounded subsequence R_j admits preselected factories
with mean at most some fixed C (enlarge C by1 if infima are not attained).
Write pi_(j,m)=P(N_j=m), and let b_(j,m,k) in[0,1] be their conditional
output coefficients after averaging all order/auxiliary information, as in
V1 Section7. Put gamma_(j,m,k)=pi_(j,m)b_(j,m,k).

All these coordinates belong to[0,1], so a diagonal subsequence makes every
pi_(j,m) and gamma_(j,m,k) converge to pi_m and gamma_(m,k). Markov gives

    sum_(m>K) pi_(j,m) <= C/(K+1),

uniformly in j. Therefore sum pi_m=1; Fatou also gives sum m pi_m<=C.
The limits obey0<=gamma_(m,k)<=pi_m. For pi_m>0 define b_(m,k)=gamma/pi_m;
for pi_m=0 choose arbitrary coefficients in[0,1]. This specifies a valid
preselected factory of finite mean, allowing arbitrary real probabilities
as an even STRONGER comparison class if computability of these limits is
not established. The differentiability obstruction does not require their
computability.

For each finite K the truncated response polynomials converge coordinatewise
and uniformly in p. Their tails are bounded uniformly by C/(K+1), since
the Bernstein basis is a probability partition and the coefficients are in
[0,1]. Meanwhile f_(R_j) converges uniformly to V1's f by its q_n tail.
Passing first j->infinity and then K->infinity proves

    f(p)=sum_m pi_m sum_k b_(m,k)binom(m,k)p^k(1-p)^(m-k).

V1's classical derivative argument makes this C2 on every interior compact,
contradicting its non-C2 neighbourhood at p0. This proves2. It is a compactness
argument, not a new general compactness theorem or an algorithm for finding
an optimal batch/kernel or a useful threshold R0.

## Full-cost and relevance limits

The corollary compares expected INPUT calls. The V1 infinite program still
has pointwise finite expected full bit work versus infinite expected input
work of all preselected implementations. However2 supplies no quantitative
rate against the description/reading cost of a varying R or complete physical
latency of its finite programs. Do not silently infer a uniform finite-family
bit-work ratio, memory saving or hardware win. Parameter encoding, preparation,
auxiliary bits and the actual source cost remain necessary in an application.

This strengthens the mathematical candidate beyond a single infinite-mean
proof object, but a natural useful external consumer, a critical audit of
V1/V2 and specific priority remain OPEN. All finite members here are still
CONSTRUCTED, not external benchmark observations. The old audits did not
test this compactness argument. No further implementation, model capture or
article promotion is triggered just by this corollary.
