# A37: all canonical outcomes, not a chosen correct answer

2026-10-11. Written after v1's independent small-law checks, BEFORE model
integration or measurement. This extends the eight criteria's breadth; it does
not fix v1's full-cost/priority gates or change its algorithm.

Let p_i be the probabilities of the countable canonical outcomes of a complete
dLLM/CFG sampling oracle. The canonical map is fixed without a gold answer.
Write c=sum_i p_i^2 and m=max_i p_i. For two independent outputs, collision
probability is c and expected distinct outcome count is2-c.

## Classical information-aware optimum

Every pair with both marginals p has collision probability at least

    c_min=max(0,2m-1).

The lower bound follows from J_ii>=max(0,2p_i-1); at most one mass exceeds1/2.
It is achievable: arrange the masses as consecutive intervals on the circle,
take uniform U, and sample the intervals containing U and U+1/2 modulo1.
An interval of length<=1/2 has no overlap with its half-turn, while the single
larger interval has overlap2m-1. This is a CLASSICAL probability-aware coupling,
not a new optimality theorem or a competitor to exclude. It requires the
canonical outcome probabilities/quantiles, not only their raw draws.

Thus the greatest possible collision reduction over iid, at unchanged
individual outcome laws, is

    D_opt=c-max(0,2m-1).

## Oracle-only constant for every distribution

The ideal A37 coupling satisfies

    c-Pr[k(X)=k(Y)] >= D_opt/13.                              (3)

Proof: for each i, apply the v1 canonical-event bound, calling its gain d_i.
If p_i<=1/2,

    d_i >= p_i^2*(1-p_i)^2/(3+p_i^2) >= p_i^2/13.

If m<=1/2, summing gives sum_i d_i>=c/13=D_opt/13.
If m>1/2, call its index j. For that outcome,

    d_j >= (1-m)^2 * m^2/(3+m^2) >= (1-m)^2/13.

All other masses are below1/2. Summing them gives

    sum_i d_i >= [(1-m)^2 + sum_(i!=j) p_i^2]/13 = D_opt/13.

Every d_i is nonnegative, so summation is legitimate for countably many keys
by monotone convergence. Their sum is exactly total collision reduction.
Degenerate m=1 has D_opt=0; no algorithm can create another original outcome.
The cap12 version has the conservative constant1023/13312 instead.

The constant1/13 is SHARP for this construction: use the same heavy outcome
of mass1/2 and m equiprobable wrong outcomes as v1 Section4. The heavy-outcome
gain tends to1/52. The sum of all other gains is at most sum p_i^2=1/(4m),
and tends tozero. D_opt tends to1/4, yielding ratio1/13. These distributions
are proof objects, not a dataset or claimed practical speed observations.

## Precise consequence and limitation

Without knowing probabilities, rankings, target answers or a semantic-quality
proxy, this yields a nonvanishing fraction of the greatest possible diversity
IMPROVEMENT for every canonical distribution. The classic four-draw binary
control with the SAME random hash yields1/16; it can cost less and remains a
control. No-replacement canonical sampling attains zero collisions when its
support allows it, but usually changes the second output marginal. If the
consumer accepts that change, no-replacement may be the better choice.

The same pair still has pass@2>=iid2 for EVERY verifier, and preserves each
original raw payload law. That weak dominance is not equivalent to a constant
semantic gain for an arbitrary set of many correct keys. Nor does diversity
mean correctness: two distinct outputs may both be incorrect.

For structured generation, equal canonical outcomes can represent the same
tool/configuration choice despite whitespace, field order or token aliases.
A pair consumer may wish to avoid repeating that choice while keeping each
individual proposal distribution. The consumer and its preservation need
must be demonstrated, not assumed to exclude better conventional methods.
The sampler's expected draw cost remains3 rather than iid2's2, and full
native timing, exact no-replacement controls and known-law coupling remain
unresolved application obligations. No superiority of complete EPIC generation
or publication priority follows merely from (3).
