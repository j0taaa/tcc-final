# Prospective contract: same six-pool law, arbitrary keys, distinct-input work

2026-10-17. Written BEFORE code or numerical solve. The README eight criteria
apply; actual useful full-cost consumption and sufficient priority remain open.

## Operation and information

An iid source supplies ORIGINAL payloads Z with fixed observable key c(Z)
in a countable permitted domain with arbitrarily many keys. P is unknown.
Keep X=Z1 literally; select a NONFIRST queried original payload Y using only
keys and independent randomness. At most six source draws. FAIL/aliases are
ordinary payloads, not discarded outcomes. A finite practical vocabulary is
allowed, but the universal rule may not presume only three keys are possible.

The FIXED target is the population ordered pair law obtained by six iid draws
and a uniformly random minimum-equal-key-edge perfect matching of the six
POSITIONS. Return position1 and its partner. This is classical; A42's written
six-proposal theorem already supplies the known covariance and atom properties.
No generic matching, class projection, covariance or factory invention is claimed.

Given a terminal named tape, the target row q(j) is its matching partner-key
distribution at position1. The candidate need match this row only AFTER
averaging ALL orders of every total multiset, conditioned on the first key.
It need NOT preserve q on each individual full tape. Bernstein uniqueness
makes those coefficient equalities equivalent to the specified ordered pair
law for every P. A class-only nonfirst selection then gives the same full raw
law: selected within-class residuals are independent P(.|key), including when
realized values coincide. This does not preserve a particular native pair/RNG.

## Written lower bound: nobody universally stops before four

Consider ANY stopped prefix of length n<=3. Choose a fresh key H not seen in
it and complete all6-n slots with H. It then occupies at least half the pool.
The optimal conditional diagonal and empirical margins force every non-H
first slot to pair with H. This is true for EVERY ordered tape with that
multiset: the forbidden non-H output probabilities have nonnegative Bernstein
coefficients and their average is zero. A stopped prefix could not have
returned H, so no positive stop probability is possible on that prefix.

An algorithm also cannot invent an unobserved key: the same stopped transcript
has positive probability under a P supported only on its seen keys, contradicting
the second marginal. Thus cloning first or using auxiliary randomness does not
avoid the argument. Every universal algorithm for this target needs N>=4.
The countably rich PERMITTED domain matters; known smaller alphabets/probability
information must not be excluded from a practical comparison by fiat.

## Classical optimal per-tape control and the16/3 distinct-tape bound

For any prefix s let a_j(s)=min_{t extends s}q_t(j), zero for unobserved j.
The cumulative probability of already outputting j is at most a_j(s) for
EVERY algorithm preserving q_t on EACH full tape. Classical nested common-part
allocation attains all these prefix bounds simultaneously, so this is a strong
complete control, not a fixed-pool straw baseline. Its preparation also costs.

Along a six-DISTINCT tape, no such control stops by length four: completion
ABCD -> ABCDBB forces partner B, while ABCDCC forces C, and ABCDDD forces D.
No single output is compatible with all these completions. The earlier-prefix
four-query bound covers lengths1..3.

At length five ABCDE, every seen nonfirst key has minimum q=1/6 over the
possible last draw. If another NONFIRST key is duplicated, the profile is
(2,1,1,1,1): partner has probability1/2 on that doubled class and1/6 on each
other singleton. Duplicating first gives1/4 on each of four others; a new key
gives1/5 on each of five others. Thus sum_j a_j=4/6=2/3. It follows

    E[N | every class on the full tape distinct]>=5+1/3=16/3.

The common-part control attains equality. This bound is only for per-TAPE
kernel preservation. It is NOT a lower bound16/3 for all population-law
factories; the latter have the weaker four-query bound.

## Candidate theorem and diffuse consequence, conditional on a valid primal

Seek a universal population-law rule with N=4 whenever its first four keys
are distinct. Together with the lower bound this would be SHARP on every
all-distinct full tape. The existence assertion is still a CONJECTURE here.

If certified, let kappa=sum_i p_i^2. A union bound gives probability of a
duplicate among six iid draws at most15*kappa. Both methods stop in[4,6].
For the candidate A and optimal per-tape control C,

    E N_A <=4+30*kappa,
    E N_C >=16/3-20*kappa.

Hence for ANY sequence of laws with kappa->0, the ratio tends to3/4:25%
fewer source queries against that ENTIRE per-tape class. The displayed bounds
already imply at least20% source saving when kappa<=2/345. These are written
population consequences, not selected benchmark wins or physical timings.
They say nothing about arbitrary other kernels, a P-aware iid shortcut or
full semantic/generation superiority. Collision benefit itself can be small
in this regime, which remains an application objection.

## Finite anonymous certificate

Represent a prefix by its restricted-growth string: first0; each unseen key
gets the next integer. There are Bell(n) prefixes of length n, n<=6. Variables
c_s give the probability of continuing after fixed prefix s, integrated over
auxiliary randomness; s_(s,j) probability of stopping NOW with seen key j.
There is no stop before a nonfirst representative of that key is available.
The first key0 is eligible only after appearing again. Set c_0=1. Every
child has reach c_parent, so

    c_s + sum_j s_(s,j)=c_parent(s),

with c_s=0 at length6. Missing variables are zero. Endpoint output probability
on a fixed full tape is the sum of its ancestral s_(s,j), with canonical labels
mapped back to actual keys. For each total multiset with first key0 and sorted
positive counts of other keys, require the average endpoint probabilities to
equal the matching target row. These finitely many representatives cover every
alphabet by label-renaming symmetry. A valid primal suffices for construction;
no completeness/novel polynomial bit-complexity theorem is presumed.

Impose c_0123=0, with NO cap/law parameter search. Minimize expected calls at
U3 only as a secondary comparison. A prefix of length n with k seen keys has
probability falling(2,k-1)/3^(n-1), zero for k>3. Cost is1 plus the sum of
these prefix probabilities times c_s over lengths1..5. Record all other
predeclared laws, not just a favorable U3 outcome.

## Execution/audit gates

Freeze independent solver/auditor source BEFORE the single solve. Existing
isolated NumPy2.2.6/SciPy1.15.3 only; HiGHS-ds60s and tolerances1e-9.
Propose zeros below1e-10 and Fraction denominators<=100000000, then exact
rational checks decide. Any numerical/rational failure is INCONCLUSIVE and
preserved; no increased cap, changed matching law or relaxed distinct condition.

The independent stdlib verifier must not import solver algebra. Rebuild all
rows/objective/dual, use ALL six-key named tails with first0, independently
enumerate15 perfect matchings, check every ordered conditional multiset row,
literal first/nonfirst availability, four-draw distinct stop, U3 cost and
zero exact dual gap. Recompute operational conditional stop probabilities
from reach, not mistake s for a reach-conditional probability. Check all five
old laws plus uniform2/4/6/128. Corrupt primal/dual rejection required.

No neural forward/model/head/labels/update or competitive timing is permitted
by this small proof validation. If feasible, next must audit all distinct-tape
common-part coefficients independently and find a real justified consumer.
Complete source costs obey finite Wald; coordinator/preparation/downstream
costs remain separate and no general20% latency follows.
