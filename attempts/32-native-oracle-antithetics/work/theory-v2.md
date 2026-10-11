# Streaming optimal oracle-budget curve — v2, v1 frozen separately

This refines the SAME eight-criterion contract: opaque native row sampler,
first trajectory unchanged, binary class fixed BEFORE noise, finite budget
n>=2. No known-p side information is used to coordinate. The cost question
now depends on n; v1's expected<=1 auxiliary bound applies only to n=4/5.
New scientific candidate is a STREAMING realization of the sharp curve,
not only a four-draw specialization. Novelty/application still unconfirmed.

## Algorithm, finite termination and exact native law

Keep X,Y~P iid and X literally. If their classes differ, return Y.
Otherwise start signed level d=2 and remaining=n-2. While remaining>=d:
draw a fresh native row Z; decrease remaining by1; increase d by1 if
c(Z)=c(X), otherwise decrease d by1. If d hits0, return this Z. If it
does not hit0 within the budget, return the ORIGINAL Y. Never return an
incomplete ranking or draw conditional on success; no output FAIL is added.
If remaining<d, hitting0 is impossible, so stopping early is exact.

At most n total oracle draws. Beyond the original tensor, storage is two
row payloads (original Y/latest Z) and two O(log n)-bit counters, independent
of n. P can include finite rounding/ties and arbitrary aliases; only calls
to the original sampler define P. There is no PL/CDF approximation.

## Flow and sharp bound for every n

Let p=P(c=1), q=1-p, z=pq. Suppose X,Y start in class j. A first passage
from2 to0 in2k auxiliary draws has k+1 opposite-class and k-1 same-class
draws. The number of such paths is the KNOWN Catalan number
C_k=binom(2k,k)/(k+1), by the classical ballot/reflection count.

Multiplying by the initial same-class pair probability makes the new
j->(1-j) flow C_k z^(k+1), identical in BOTH directions. Hence

    delta_n(p)=sum_{k=1}^{floor((n-2)/2)} C_k z^(k+1).

The law retains all full P marginals by equal flow, and

    Cov(f(X),f(Y_out))=-delta_n(p)(mu1-mu0)^2.

Payloads are still independent given returned classes: decisions read only
class bits; the returned final native row has its original P|class law.
It is not an idealized forced winner with an unrelated recovery tail.

The independent upper bound of v1, Section3, is

    J10 <= B_n(p)=E[min(M/n,1-M/n)], M~Binomial(n,p).

The STREAMING algorithm attains it for ALL p. Here is a proof that avoids
assuming the binomial/Catalan identity. Equal class flow already proves
E[Y|M=m]=m/n through uniqueness of the Bernstein polynomial coefficients.
If the first class is the strict minority (or balanced), opposite initial
Y is already returned; if initial Y agrees, the remaining signed walk must
hit0, because the total signed count at the end is<=0. Thus the minority
first bit always receives the opposite bit. The two conditional marginals
agree, so both off-diagonal conditional probabilities equal
min(m/n,1-m/n), precisely the conditional Fréchet upper bound. Therefore

    pq+delta_n(p)=B_n(p).

Odd n=2r+1 matches n=2r, since a passage from2 needs even length. At n<=3
the gain is zero; n=4/5 reproduces v1, attaining pq+p²q². The general
empirical-pool realization in v1 is a competent comparator with the SAME
optimal law. A competent pool also maintains per-class reservoirs and uses
O(V+log n) memory: comparing only to a naive n-row pool would be weak. This
refinement claims adaptive oracle-count economy versus the fixed-budget
pool, NOT a stronger law or a unique constant-memory principle.

## Uniform expected oracle-cost improvement over the compact fixed pool

Let r=floor((n-2)/2). Conditional on two initial rows of class j, denote its
probability by w. Stopping occurs when the auxiliary walk has r same-class
draws or opposite-class count exceeds same-class count by2. With odd n the
same stopping rule applies: no odd-length passage from2 to0 exists.

For each a=0,...,r-1, an untruncated iid sequence spends expected1/w draws
waiting at a accumulated same-class draws. The stopped walk spends no more.
Multiply by w², the probability of the initial same-class pair. This gives
at most w expected draws at each a. Add the two classes: p+(1-p)=1. Sum
over a. Endpoints follow directly (constant class stops after r draws).
Thus, for EVERY p,

    E[auxiliary draws] <= r,
    E[total draws] <= 2+r,

whereas the compact fixed-n pool pays n draws. At n=16 this is at most9
versus16 total row draws, at least43.75% expected oracle-count economy.
Near p=.5 the saving is larger. No MODEL forward reduction follows from
this row-oracle count. A vectorized pool can have lower physical latency
despite doing more arithmetic: it must enter the practical comparison.
This is NOT optimal expected-cost among every possible adaptive factory;
the proven optimality concerns disagreement under the worst-case budget n.

## Limit, oracle impossibility and illustration

The Catalan generating function (KNOWN) gives

    delta_infinity(p)=min(p,q)^2.

This is the Fréchet optimum for the CLASS, not for any unknown semantics.
Actually running the unbounded walk does not terminate with probability1
for every p: positive drift can escape without hitting0. Do not smuggle an
unbounded perfect sampler into the implementation. More generally, an
almost-surely finite p-blind algorithm cannot attain the exact optimum for
ALL p: its event11 would have probability max(0,2p-1), zero on an interior
interval and positive elsewhere; any finite output-leaf bitstring has
positive probability for every interior p. This is a known Bernoulli-factory
zero-set obstruction, not a new impossibility principle.

At p=.5 and A={c=1}, n=4 gives coverage .8125 versus iid .75. n=16 gives
coverage B16(.5)+.5, about .90181. These are mathematical illustrations,
NOT semantic model measurements or benchmarks favoring this method.
Uniform approximation to the class optimum costs n=Theta(epsilon^-2) near
p=.5 through the central-binomial tail. That classical asymptotic does not
mean n extra MODEL forwards: here n is frozen-head row sampler calls.

## Adaptive trajectory, costs and a necessary counterexample

V1's Markov telescope continues to hold with delta_n(s,t) in place of p²q²,
provided each n(s,t) and c(s,t) are fixed before noise. Therefore every
terminal verifier has pass@2>=original iid, and every mean score variance
is<=iid. First path remains native; all recovery/FAIL events count.

IMPORTANT: larger n improves LOCAL class energy, but does not automatically
dominate smaller n in the entire adaptive decoder. Counterexample: first
draw chooses a style bit; next draw gives a fair value bit independently of
style. Final event is value1. Different styles are different sufficient
terminal-output states, so only equal styles can couple the value draw.
If root coupling has energy a and value coupling has energy b, terminal
coverage is .75+(.5-2a)b. Increasing a lowers coverage even though each
method still dominates iid. Never claim global monotonicity in n or silently
select a favorable budget after measuring. Entire unchanged style+value
JSONs are required to support arbitrary terminal verifiers.

Cost: at most n-2 extra row draws per shared node, O(n V) arithmetic in the
worst case, O(V+log n) extra storage. Early unreachable-bound stopping saves
draws without bias. Original per-label Torch stream must be restored after
auxiliary draws. Header/class/key/parser/CPU/GPU/query/cache/forward/output
costs all count. Exactness and a sharp restricted-oracle bound do not prove
latency advantage or priority/publication worthiness. At n=4, expected
auxiliary draws remain1-pq; for larger n do not repeat this smaller bound.
