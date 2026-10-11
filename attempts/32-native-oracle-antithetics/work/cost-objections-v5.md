# A32v5 written cost audit DURING the frozen v4 pilot

2026-10-11. This is a separate mathematical investigation, NOT a change to
v4's running producer/configuration, and no v4 record may inherit it. The
complete v4 protocol/source8fc0999 and independent archiveabdf242 remain
unchanged. Its small prefix already has real heads; this refinement is NOT
described as preregistered before every neural measurement.

## Eight questions revisited BEFORE any new implementation

1. Same operation: two native structured dLLM trajectories, unchanged first
   output and both native marginal laws. Frozen-head rows are cheap samples;
   no extra neural forward is needed merely to coordinate one node.
2. Sharp bounded-disagreement and minimax cost need genuine distinction from
   known factories. Removing an unnecessary bounded-stopping hypothesis makes
   a theorem stronger but does NOT automatically make its proof significant.
   The zero-order lower-bound principle and Bernoulli races are antecedents.
3. Need a comparator admitting random work: a walk optimal under a HARD bound
   can lose to a competent constant-EXPECTED-cost sampler. The fixed-n pool
   and the known-p control alone do not exhaust probability-blind competitors.
4. Two written results below: stronger lower bound without a hard stopping
   bound; counterexample to reading it as the best work/disagreement frontier.
5. Do not alter v4's gates after its heads. A newly recognized control must be
   included in an explicitly dated follow-up, before any positive claim;
   preserve and report the original campaign, including losses.
6. Expected row-work is not physical latency or forward work. Unbounded
   stopping must have explicit tails/budget/refusal treatment in software.
7. A simple known Bernoulli race uniformly improves a bounded walk's class
   effect under one expected-work comparison. This can destroy a naive claim
   of 'optimal cost therefore best practical method'. Do not hide it.
8. Specific priority, full expected-work frontier, meaningful neural effect
   and publication significance remain unresolved. No human review invented.

## A stronger minimax theorem, with no stopping bound

Fix n>=2, d=floor(n/2)+1 and B_n(p)=E[min(M/n,1-M/n)] for M~Bin(n,p).
Consider ALL probability-blind adaptive randomized factories reading iid
Bernoulli(p) bits, retaining the first bit X literally, terminating almost
surely for EACH p in(0,1), and producing Y with marginal p. Permit arbitrary
random stopping N, not necessarily bounded or exponentially tailed. Suppose
their disagreement flow satisfies

    J01(p)=J10(p)>=B_n(p) for EVERY p in(0,1).

Then

    sup_{0<p<1} E_p N >= d.

The bounded walk attains equality, so the infimum of this supremum over the
above much larger class is d. It does NOT mean the walk has the largest
disagreement at that expected cost.

### Proof

Equal marginals force J01=J10 and J11=p-J01<=p-B_n=O(p^d) near0. Consider
ANY positive-measure set alpha of auxiliary random decisions stopping after
k<d all-ones bits and outputting Y=1. That prefix and the SAME decisions
have probability alpha*p^k for every p, contradicting J11=O(p^d). Therefore
no such all-ones Y=1 leaf exists (null decisions ignored).

An all-ones leaf with Y=0 at ANY finite k is also impossible: it contributes
alpha*p^k to J10, whereas marginal preservation gives J10<=1-p near1.
Thus no output is possible on an all-ones prefix of length d-1. Coupling the
random stream with padded bits gives

    P_p(N>=d)>=p^(d-1),   E_p N>=d*p^(d-1).

Let p approach1. This requires neither endpoint termination, continuity of
E_p N nor a uniform tail. The walk's previously proved upper bound d supplies
attainment. For n=2/3, d=2 and the same reasoning applies. QED.

The argument is a direct positive-prefix/zero-order argument, related to
standard Bernoulli-factory impossibility arguments. Do NOT call that principle
an invention. The contribution would need to be the specific sharp combined
contract and a useful consequence, with closest prior results checked.

## Important counter-comparator: an ordinary Bernoulli race

Draw the original X,Y iid and retain X. If their classes differ, keep Y.
If their classes agree, repeatedly draw iid pairs Z,W until their classes
agree. Return Z if that common class differs from X, otherwise the original Y.
This uses only class observations and known independent external randomness;
full original row payloads can be retained. It is a standard race construction,
not claimed new here.

Write q=1-p and D=p^2+q^2. Initial collision has probability D. A pair of
auxiliary classes agrees with probability D>=1/2, so the number of auxiliary
pairs is geometric with mean1/D. The two class-transition flows are equal:

    p^2*q^2/D = q^2*p^2/D.

Therefore both original marginals are preserved, all score functions have
nonpositive covariance, and the disagreement flow is

    R(p)=pq + p^2*q^2/(p^2+q^2).

The expected TOTAL number of draws is EXACTLY

    E N = 2 + D*(2/D) = 4

for every p, endpoints included. The tail is uniformly geometric. Notice
J11=p^4/D; its order4 also implies minimax work>=4 by the preceding prefix
argument. Thus the race too is minimax work-optimal FOR ITS target flow.

For the bounded n=6 walk, delta6=(pq)^2*(1+2pq), its worst expected work is4.
But the race has the SAME worst expected work and strictly larger class flow
at EVERY interior p:

    R-B6 = (pq)^2*[1/(1-2pq)-(1+2pq)]
         = 4*(pq)^4/(1-2pq) > 0.

This is a concrete mathematical warning against presenting A32's minimax
result as an optimal expected-work/diversity frontier. Hard maximum6 and
random geometric work are different contracts; a real deployment that permits
bounded retries must also consider a truncated race.

If the race is stopped after R>=1 auxiliary pairs, keep original Y on all
unresolved branches, with NO new FAIL. Equal flows remain, now

    delta_R=(pq)^2*[1-(2pq)^R]/(1-2pq),
    E N=2+2*[1-(2pq)^R],   N<=2+2R.

At R=2 its flow equals B6 but its pointwise expected cost need not be the
walk's; at R>=3 it strictly improves B6 in flow, with expected work<4 and a
larger hard bound. Adding this competent control later cannot rescue a failed
v4 candidate; it can only make a claimed practical frontier harder to pass.

## Scope of sources checked during this audit

[Mendo2019](https://arxiv.org/pdf/1612.08923), Section3/Theorem3 ACTUALLY READ:
sequential Cramer–Rao lower bound for arbitrary fast factories of f,
E N >= p(1-p)f'(p)^2/[f(p)(1-f(p))]. This is a GENERAL prior cost lower bound;
no assertion that our lower-bound principle is new. The written prefix proof
above additionally works without fastness for its fixed paired target.

[Morina et al.2021](https://arxiv.org/html/1912.09229v2), Section3.2/
Propositions3.4--3.5 and3.5.1--3.5.2 ACTUALLY READ: rational dice factories,
reversible transition construction and Peskun maximality under fixed adjacency,
with CFTP expected-work upper bounds. It is a competent antecedent to
probability-blind reversible improvements; no invented universal optimality.

[Nacu–Peres2005](https://arxiv.org/pdf/math/0309222), Section6 reread: the
bounded reflection construction remains an EXACT prior reduction. Section5
also supplies positive-coefficient stopping/tail arguments. None of these
reads establishes that publication novelty of the combined A32 result exists.
