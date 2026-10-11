# A39 v1 — known finite source, opaque decisions and robust query optimality

2026-10-11. WRITTEN BEFORE prototype/timing/forwards. Sampling without
replacement, empirical transports, falling-factorial interpolation and
finite-population corrections are antecedents. The precise comparative
claims below are candidates; publication priority remains to be checked.

## Model, including source-aware controls

A known source has M>=4 indices with uniform original law. An opaque map
k assigns each source a canonical decision, with at least three PERMITTED
labels. Querying a source obtains its label and original payload; no
uncharged information about labels of unqueried sources is supplied. Source
indices are visible. Algorithms may adaptively choose any unqueried index,
reuse queried indices, clone the first output and use independent random
bits. The first source is the original uniform source and is retained
literally. The second must be uniform on ALL source indices for EVERY map k.
The two returned original payloads must be materialized, not unknown labels
promised for later without charging their query. At most four distinct
label queries are allowed, counting both outputs.

This is stronger information than an anonymous iid output oracle. It
includes systematic seed pairing and uniform source derangement. It does
NOT include free evaluation of k, known class counts or a cheap analytical
inverse of k. Those are legitimate practical alternatives outside this
opaque-query lower bound, not algorithms to handicap in an experiment.

Let n_i be class sizes; write (t)_r=t(t-1)...(t-r+1),
D=(M)_4, S2=sum n_i^2, and

    c2=sum (n_i)_2/(M)_2,   c3=sum (n_i)_3/(M)_3.

## Construction (known transport, adaptive omission)

Request distinct sources uniformly without replacement and apply the C4
equality-only rule written in A38, retaining the first and a nonfirst
queried source. That rule stops at three when keys2=3; with a repeated
first in a mixed three-prefix it stops on an independent fair coin;
otherwise it needs the fourth. The kernel will be copied independently
by source hash, not imported from mutable A38. No class sizes are used.

Pad omitted queries with virtual unused distinct sources to length four.
Conditional on an empirical class multiset, the output pair law is the
classical randomized grouped-rank half-rotation. Its second empirical
marginal is count_i/4. Uniform original source marginals follow by
exchangeability within each class, including its distinct original aliases.
The two retained source indices are always different.

## Exact class law and expected queries

The multiplicity patterns give

    J_ii=(n_i)_3*(2M-n_i-3)/D,                         (1)
    J_ij=n_i*n_j*[M^2+M(n_i+n_j)-n_i*n_j-S2-6M+7]/D   (i!=j).

For example,3i+1j has conditional diagonal1/2,4i has1,
2i+2j has cross mass1/2,2i+1j+1h has i-to-j mass1/4,
and four different labels have each ordered cross mass1/12.
These five patterns prove (1); hypergeometric multiplicities, not iid
probabilities, are used. Conditional source-level lifting is uniform
on DISTINCT sources within a class and independent uniform sources
between different classes. This matters for raw scores/aliases.

Inclusion-exclusion on the first three distinct sources gives

    E N=4-2c2+c3.                                    (2)

The full-four and safe-early same-law pools use4 and4-c2 respectively.
These are query counts, not model forwards or elapsed-time claims.

## Every full-source score, not just canonical indicators

Let f(s) be ANY real score of the original source's final payload, with
class means mu_i, total mean mu, centered means g_i=mu_i-mu and within-class
population variances sigma_i^2. Finite source means square integrability
is automatic for finite scores. The class covariance from (1) is

    C_class=[-(M^2-S2)*sum n_i^2*g_i^2
              -(sum n_i^2*g_i)^2
              +(4M-6)*sum n_i*g_i^2]/D.              (3)

The COMPLETE score covariance is

    Cov(f(X),f(Y))=C_class
                    -sum_(n_i>=2) J_ii*sigma_i^2/(n_i-1).  (4)

Proof of (4): same-class sampling uses two distinct uniform sources,
so its conditional product is mu_i^2-sigma_i^2/(n_i-1). Across different
classes the product is mu_i*mu_j. Mean centering proves (3), using
sum n_i*g_i=0. This is not A38's independent within-class lifting.

If there are at least three positive classes,

    S2 <= (M-2)^2+2, hence M^2-S2>=4M-6.

This elementary bound follows by transferring mass between two positive
classes until all but the largest have size one. Also n_i^2>=n_i.
Every term in (3) is therefore nonpositive. With one class C_class=0.
For two positive classes put t=n_1, r=t(M-t). Direct expansion of (1) gives

    (t/M)^2-J_11 = r*[r-4+6/M]/D >=0,

because r>=M-1 and M-5+6/M=(M-2)(M-3)/M>=0.
Binary class covariance is the negative of this quantity times
(mu_1-mu_2)^2. Thus (3) and (4) are nonpositive in ALL cases.

Consequences: every terminal Boolean verifier has pass@2>=iid2 of the
same original decoder; every two-score mean has variance<=iid2; and
the best score first-order stochastically dominates iid2 by applying
the Boolean guarantee to each score threshold. No semantic answer is
needed by the algorithm. Strictness depends on the score/partition.

IMPORTANT competent countercontrol: uniform source derangement uses
two queries and has Cov=-Var(f)/(M-1) for EVERY f. It can beat C4 for some
scores. At M=4, partition(2,1,1) and Boolean source scores(1,0,1,0),
the C4 covariance is ZERO while derangement is strictly negative.
Do not claim C4 dominates that control, or rely only on seed-half.

## Robust simultaneous atom optimum against ALL source-aware queries

For each atom of size t define g4(t)=(t)_3*(2M-t-3)/D.
An algorithm's risk at t is its WORST joint diagonal over all assignments
of that atom to t source indices (other permitted labels arbitrary).

**Theorem.** Every universal source-aware cap4 algorithm has worst risk
at least g4(t). The construction attains g4(t) for EVERY atom/map at once.
This is robust optimum over unknown source placements. It is NOT the best
possible diagonal for each particular map: seed-half can achieve zero
for some maps and be bad for others.

Proof: randomly permute the known source addresses before running any
algorithm, undoing that permutation on emitted indices. Its source
marginals/cap/first retention remain valid. On an arbitrary hidden fixed
map, newly queried labels now arrive uniformly without replacement.
Virtual padding gives four observations. The conditional second empirical
marginal must be count_i/4, as proved by the following finite-grid argument.

For label counts n with sum M, universal marginal equality is

    sum_(|r|=4) [4!/prod r_j!]*prod (n_j)_(r_j)/(M)_4*z_i(r)=n_i/M.

The right side also equals that expression with z_i(r)=r_i/4 by the
mean of a hypergeometric sample. Coefficients are unique. To see this,
evaluate at nodes n_j=t_j for j<L and n_L=M-sum_(j<L)t_j, where
sum_(j<L)t_j<=4. Basis r_j has sum4. Each matrix entry is zero if some
r_j>t_j for j<L. Order rows/columns by total sum outside L: the matrix
is triangular, and its diagonal is

    prod_(j<L) t_j! * (M-sum_(j<L)t_j)_(4-sum_(j<L)t_j)>0.

It is invertible because M>=4. Thus each conditional second marginal is
r_i/4. The first has the same conditional marginal. Conditional Frechet
then forces diagonal at least max(0,r_i/2-1). Hypergeometric averaging
gives g4(t). The symmetrized risk is an average of original placements,
so some placement has at least that risk. The construction attains the
conditional bounds simultaneously by the five multiplicity patterns.

## Sharp query cost among robust simultaneous maximizers

The competent TWO-query uniform-source derangement has atom diagonal
t(t-1)/(M(M-1)). The four-query robust improvement over it is EXACTLY

    (t)_2*(M-t)_2/(M)_4.                         (4a)

It is positive for2<=t<=M-2, simultaneously for every atom, regardless
of its unknown source placement. This is a quantitative comparison with
a strong known-source control, not just a comparison with iid.

Four queries are NECESSARY for any strictly positive robust improvement
over that control. For cap3, the same finite-grid empirical marginal proof
with degree3 gives conditional diagonal>=max(0,2r/3-1). Averaging it over
the three-sample hypergeometric count yields

    (t)_2*(M-t)/(M)_3 + (t)_3/(M)_3
       =(t)_2/(M)_2,

exactly the two-query derangement diagonal. Thus no source-aware cap<=3
algorithm can guarantee a smaller atom diagonal for all placements at any
size t. This does not prohibit improving selected known placements, or
different verifier unions; fixed-cap coefficient clipping is a known tool.

Require a universal algorithm to have diagonal<=g4(n_i) for EVERY map
and EVERY atom (its robust optimal guarantee), not only one favourable map.
For any fixed class-count vector n, its worst-placement expected query
count is at least4-2c2+c3. The construction has exactly this expectation
on every placement, hence attains this minimax value.

Proof: source symmetrization can only lower the worst placement cost.
Its diagonal already has the lower bound above, so all nonnegative
conditional coefficients must attain the Frechet minima. For count_i=2
the diagonal is zero and singleton first must return the repeated class.
Therefore no one/two-query stop is possible with three permitted labels:
an unseen completion could force an unqueried class or forbid the only
queried class. Three distinct first labels always require query four.

For distinct i,j, on prefixes i,i,j and i,j,i, an early stop cannot return
i: a fourth new class would make count_i=2. In a virtual3i+1j multiset,
diagonal coefficient1/2 requires sum2 over its four placements. Singleton
first contributes0; i,i,i,j contributes at most1; the two mixed prefixes
contribute at most their continuation probabilities. Consequently those
two probabilities sum to at least1. Their equal without-replacement
prefix weight is(n_i)_2*n_j/(M)_3. Summing gives an additional request-four
probability at least c2-c3. Three distinct prefixes contribute1-3c2+2c3.
Thus E N>=3+(1-3c2+2c3)+(c2-c3)=4-2c2+c3.

This is WORST-placement optimum at fixed counts, not a pointwise claim
for every unsymmetrized algorithm on every map. Free source information
about unqueried labels, different query caps or different pair objectives
change the comparator class. Actual neural maps are a restricted subclass;
the minimax theorem is not a lower bound for all conceivable dLLM algorithms.

## Sound coarsening: coverage and fewer actual prefix queries

Let a coarser label be a fixed function of the finer one. Keep a Boolean
consumer f measurable with the COARSER label fixed on both sides. Write
A for its number of successful sources, B=M-A, C_A=sum_success n_i^2,
C_B=sum_failure n_i^2. Equations(3)--(4), with zero within-class variance,
give the pass@2 improvement over iid2:

    [B^2*C_A+A^2*C_B-C_A*C_B-(4M-6)*A*B/M]/D.

Coarsening merges only successful classes or only unsuccessful classes.
It increases C_A,C_B; the two partial derivatives B^2-C_B and A^2-C_A
are nonnegative. Thus every such coverage and every best-score threshold
is no worse. This does NOT imply all-real-score variance monotonicity.

Merging class sizes u,v changes the expected query count by

    uv*[3(u+v)-4M+2]/[M(M-1)(M-2)]<0.             (5)

More strongly, with the SAME first-four distinct-source tape and the SAME
early-stop coin, N_coarse<=N_fine on every tape: any fine b=c remains
coarse b=c, and any fine repeated-first early stop remains a coarse early
stop or becomes b=c. Thus nonnegative variable query-four work is saved
pathwise when the fine algorithm needs four and the coarse one needs three.
No iid Wald identity is assumed. Different key/downstream costs still
need full accounting; the two retained-pair laws change after coarsening.

No prototype, native output, timing or priority confirmation accompanies
this first mathematical version. The finite-grid symmetrization obligation
and closest prior reductions are to be independently audited before use.
