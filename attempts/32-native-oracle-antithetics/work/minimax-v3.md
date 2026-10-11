# A stronger cost question after finding Nacu–Peres2005 — written v3

Written2026-10-11 AFTER v2 oracles and native FAKE432 replays. This is a
theoretical refinement; no neural heads have been acquired for A32. Do not
relabel the walk construction as new: Section6/Proposition24 of Nacu–Peres,
[Fast simulation of new coins from old](https://arxiv.org/pdf/math/0309222),
already realizes a Bernstein clipping polynomial by reflection/first passage.
Our off-diagonal event is their return event with the initial positive-step
case removed, plus the symmetric class. In notation there,

    B_n(p)=Q_n(p)-p,
    Q_n(p)=E[min(2M/n,1)].

This is an EXACT reduction to the published construction, not an analogy.
The ballot count, Bernstein form, shortcutting and p-blind construction are
not inventions. Earlier v1/v2 sources remain accessible and will not be
rewritten to imply this antecedent was already resolved before implementation.

## Eight criteria, refinement of the same A32 contract

1. Application remains two native EPIC/dLLM structured candidates and a final
   verifier. No model/head/value changes; full ranking/recovery preserved.
2. General antithetics/reflection/factories are KNOWN. Candidate difference:
   sharp disagreement budget AND minimax expected work among ALL admitted
   adaptive optimal factories, not merely a weak fixed-n pool comparison.
   Specific priority and practical magnitude still OPEN; mathematical truth
   does not by itself establish sufficient incremental significance.
3. Prefer the method if exact native law and first response matter, class
   probabilities are unavailable, and its improvement pays total costs.
   Include compact and batched pools and density-aware alternatives.
4. The new lower bound concerns ANY adaptive n-bounded p-blind factory with
   first bit retained, native second marginal for every p and attained B_n
   for every p. It gives an exact minimax expected-oracle-work optimum.
   It does not count model forwards or give arbitrary semantic strictness.
5. Check small stopping trees independently; attempt to falsify stronger
   pointwise optimality using optimization BEFORE claiming or formalizing it.
   Such exhaustive trees are mathematical oracles, NOT practical benchmarks.
6. The native head row call can be cheaper than a forward but full physical
   cost/caching/divergence still matters. Expected oracle saving is not wall
   superiority. Restricted balanced p intervals could admit faster methods.
7. If a published optimal-factory result subsumes this sharp/minimax result,
   reclassify it; do not publish a proof of a known method as a discovery.
   Nacu–Peres is already extremely close. A faster known-p method and zero
   class/terminal relationship can erase use in this specific integration.
8. Publication needs checked nearest sources, an independently assessable
   proof, genuine application and magnitude. No human review, editorial
   decision or A32 neural gain exists. No unrestricted EPIC victory claim.

## Theorem — exact minimax expected row-oracle work

Let n>=2 and d=floor(n/2)+1. Let F_n contain ALL randomized algorithms that:

* receive iid Bernoulli(p) bits, p unknown, external randomness independent
  of p, and no density/side information;
* retain B1 literally and output a second bit Y of marginal Bernoulli(p)
  for EVERY p in[0,1];
* use a stopping time N<=n and attain disagreement flow B_n(p) for EVERY p.

Then

    inf_{A in F_n} sup_{p in[0,1]} E_p[N_A]=d.

The bounded streaming walk of v2 attains this value. The same inf/sup holds
on p in(0,1), using the supremum rather than a maximum at endpoints.

### Lower bound, independent of the walk

For a budget-optimal pair, J11(p)=p-B_n(p). Its Bernstein coefficients are

    E[1_{B1=1,Y=1}|M=m]=max(0,2m-n)/n.

To justify this without assuming conditional optimality, recall that each
conditional disagreement is bounded by min(m,n-m)/n. All binomial weights
are strictly positive for interior p. Equality of their sum with B_n(p)
forces equality coefficient by coefficient. Marginal preservation supplies
E[B1|M=m]=E[Y|M=m]=m/n, giving the displayed J11 coefficients.

Consequently J11(p)=O(p^d) as p->0: its first nonzero Bernstein coefficient
has m=d. Consider the ALL-ONES input path at p=1. Marginal preservation
requires Y=1 almost surely. Suppose a positive amount alpha of external
randomness stopped at some k<d on this path. Those SAME external decisions
and the finite all-ones prefix occur with probability alpha*p^k for every
interior p, and output the event11. Thus

    J11(p)>=alpha*p^k,

contradicting J11(p)=O(p^d). Hence N>=d almost surely at p=1. Symmetry gives
the same lower bound at p=0. This argument covers random output decisions,
invented output bits and non-walk adaptive trees; no artificial weak control
is selected. Bounded N makes E_p[N] continuous in p, so the supremum over
interior p is also at least d.

### Upper bound

V2's expected-cost lemma proves E_p[auxiliary]<=r=floor((n-2)/2) for every
p, by comparing occupancy at each same-class count with a geometric wait.
Add the two original draws: E_p[N]<=2+r=d. At endpoints the walk stops after
exactly d total draws. It already attains B_n(p), so it belongs to F_n and
matches the lower bound. QED.

## Limits, and a next falsifiable question

This is minimax optimal expected work under an EXACTLY declared information
contract, and optimum disagreement under bounded work. It is NOT yet a
proof that the same walk minimizes E_p[N] separately at each interior p.
Nor does maximizing local disagreement maximize complete decoder coverage;
v2's style/value counterexample remains valid. The oracle endpoint bound
does not imply optimality when a usable p interval or density is known.

A small independent stopping-tree optimization can ask whether pointwise
optimality fails. Retain all counterexamples/dual residuals. If it holds in
small n only, label it as finite evidence/conjecture rather than a theorem.
No benchmark data or new neural forward can prove priority in the literature.
