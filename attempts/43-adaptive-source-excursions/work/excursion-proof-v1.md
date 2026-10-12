# Retained-source excursions: candidate written theorem

2026-10-11. This argument is written before code. Classical walk formulas,
path reversal, sequential likelihood information and negative covariance are
credited as principles. Scientific priority and practical usefulness remain OPEN.

## Operation and assumptions

Let Z1,Z2,... be IID ORIGINAL draws from ANY P, c:Z->{0,1} fixed before these
draws, and G a square-integrable finite vector. Include private future RNG in
Z when it will be consumed later. Keep aliases/repeated values as separate
IID positions. Selector reads labels only, never current G. Fix integer M>=2.
Let St=sum_{j<=t}(2c(Zj)-1) and

    N=inf{t>=2: St=0 or |St|=M}.

Return X=Z1 and Y=ZN. These are different original POSITIONS. There is no
finite worst-case query bound. No path-dependent fallback is specified.

Write p=P(c=1), q=1-p and J the joint law of the two labels. For0<p<1,
p!=q, ordinary gambler's ruin from1 in[0,M] gives

    J11=(p-q)*p^M/(p^M-q^M),
    J00=(p-q)*q^M/(p^M-q^M),
    J10=J01=pq*(p^(M-1)-q^(M-1))/(p^M-q^M).       (1)

At p=q=1/2, J11=J00=1/(2M), J10=J01=(M-1)/(2M).
At p=0 or1, N=M and both original labels are that deterministic label.

## Marginals, full sources and arbitrary-vector safety

A terminating label word stays strictly between0 and its eventual signed
barrier until termination. Reversing its increments again gives a legal
terminating word. If total displacement is0, reversed proper partial sums
are negatives of original suffix complements. If it is+M/-M, they are
M-St/-M-St; they stay in the same open interval. Reversal is a bijection
preserving the number of0/1 labels, hence their IID probability. It swaps
first and last labels. Thus both label marginals are p; equivalently(1)
has row sums p,q and J11-J00=p-q.

The selected LAST original value conditional on its label has P(.|c):
selection ignores within-class values, and each potential selected position
is an independent draw with that conditional law. The first is literally
retained. Conditional on the full label word, within-class residuals at the
two different positions are independent. Consequently both ORIGINAL source
marginals are P and

    Cov(G(X),G(Y))=-kappa*(mu1-mu0)(mu1-mu0)^T,
    kappa=p^2-J11>=0, mu_i=E[G|c=i].                 (2)

For p>q put r=q/p<1. Then J11=(p-q)/(1-r^M)<=p^2 because
r^M<=r^2 for M>=2. For p<q exchange labels; covariance is identical.
At balanced p, kappa=1/4-1/(2M). For M>2 and0<p<1 it is strictly
positive. Thus ANY projected score/gradient variance is never above iid2,
with strictness exactly when the two conditional projected means differ.
At balance, with within/between conditional covariance components,

    Cov((G(X)+G(Y))/2)=(V_within+(2/M)*V_between)/2.  (3)

This is not semantic accuracy, global nonconvex training, or wall-time speed.

## Exact expected source cost for EVERY p

From any interior walk position, M consecutive identical increments hit a
barrier. Their probability is at least p^M+q^M>=2^(1-M). Thus N is integrable
and has a geometric block tail. This is a conservative bound, not a practical
tail approximation. At p!=q, stopped Wald gives

    E[SN]=(p-q)E[N].

The terminal displacement is M times the signed repeat indicator
R=1_{labels11}-1_{labels00}; by the correct marginal law E[R]=p-q.
Therefore E[N]=M. At p=q, the remaining fair ruin time from1 is M-1,
and the first source adds1: again E[N]=M. Endpoints also give M exactly.
Only first/current source need storage; each discarded source is unscored.

## Balanced sharp expected-query bound: elementary KL argument

Consider ANY randomized sequential coupling valid for every unknown binary
mass p, returning labels of two materialized sources, retaining its original
first, and using only IID source information plus p-independent randomness.
It terminates almost surely for every0<p<1 and E_{1/2}N<infinity. Competitors
may clone sources, stop adaptively, and consult full raw metadata; the lower
bound chooses a source with one canonical raw value per label. No free class
masses, inverse source, extra score oracle or additional p-dependent data.

Let R as above and a=P_{1/2}(repeat). Universal marginal correctness forces
E_pR=2p-1. At balance its three-output law on R=(-1,0,1) is(a/2,1-a,a/2).
For p=1/2+h, let Qh be that output law. Stopped likelihood, bounded per-draw
log likelihood and Wald give the EXACT identity

    KL(full stopped experiment at1/2 || at1/2+h)
      = E_{1/2}N * kl(1/2 || 1/2+h)
      = 2E_{1/2}N h^2+O(h^4).                       (4)

Private auxiliary randomness contributes no likelihood. Data processing
bounds KL(P0||Qh) by(4). For0<a<1, Pinsker first implies Qh-P0=O(h).
Taylor expansion in this THREE-POINT interior simplex then gives

    KL(P0||Qh)=1/2 sum_r (Qh(r)-P0(r))^2/P0(r)+o(h^2).

Since sum_r r*(Qh(r)-P0(r))=2h, weighted Cauchy gives the squared sum at
least4h^2/a. Combining with(4) and taking h->0 proves

    E_{1/2}N * P_{1/2}(repeat) >=1.                  (5)

If a=0, a small nonzero h needs Qh(+1)+Qh(-1)>=2|h|, so
KL(P0||Qh)=-log Qh(0)>=2|h|, contradicting(4). If a=1, the same bound
follows either on the two positive atoms (Qh(0) can only increase KL) or
from E[N]>=1. Thus no differentiability of the stopping rule or uniform
expected-time assumption in a neighborhood was silently imposed.

Our excursion has a=1/M and E[N]=M, attaining(5) exactly. For balanced
unknown masses it is therefore optimal among ALL admitted adaptive couplings
at expected query budget M, not only among fixed-pool implementations.

With two balanced class-constant expensive outputs, relative pair variance
is2a. Thus minimal fraction at expected budget M is2/M. A fixed cap B
forces a>=choose(B,B/2)/2^B for even B, by the already known multinomial
Bernstein/Frechet argument. Its best fraction is twice that central binomial
probability, asymptotic sqrt(8/(pi*B)). The excursion reaches fraction epsilon
with expected2/epsilon draws, rather than cap of order1/epsilon^2. This
compares EXPECTED work to fixed cap; their worst latency contracts differ.
All actual source costs, tails and two expensive evaluations remain charged.

## CFG/dLLM corollary and unresolved significance

For a fixed CFG-valid JSON/DSL candidate and fixed dLLM parameters, P may be
the ORIGINAL timed corruption law (including appropriate loss weights in G)
or count-uniform noising for a time-independent model. A cheap binary proxy
must be fixed from earlier data/grammar analysis, not current evaluations.
Average the original gradient at first/last corruptions and update only after
the pair. This is an unbiased original-objective estimator with(2), M expected
cheap preparations and two forward/backward calls. Proxy misprediction cannot
raise any projected variance versus iid2. Unknown class masses need not be
computed. Inverse/count/CV/RSS competitors are not forbidden in practice.

If between-class trace fraction is R2, the balanced variance-times-work
comparison to iid2 improves only when

    [1-(1-2/M)*R2]*(1+complete_extra_cost_fraction)<1.

The corollary alone may be too generic to establish a CFG-specific scientific
contribution. Useful complete-gradient benefit, closest prior-art frontier,
human review and publication remain unconfirmed. A42's negative root test and
A41's stronger negative scalar/bias controls remain applicable evidence.
