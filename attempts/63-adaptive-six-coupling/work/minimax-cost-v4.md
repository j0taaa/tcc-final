# V4 addendum — A written minimax consequence, before operational checks

2026-10-17. AFTER exact V3 policy inspection, BEFORE the extractor/reference/
operational auditor. This strengthens the intended consequence; it does not
retroactively redefine V1's objective or report an executed identity check.

For the deterministic V3 cap-six policy, direct grouping of stopping prefixes
gives six depth-four actions and seventeen depth-five actions. Set

    S_j=sum_i p_i^j, e2=p0*p1+p0*p2+p1*p2, e3=p0*p1*p2.

There is one depth-four all-equal pattern, one(3,1) pattern with first in the
majority, three(2,2) patterns, and one(1,3) pattern. Thus

    P(N=4)=S4+2(S3-S4)+3(S2^2-S4)
          =2*S3+3*S2^2-4*S4
          =1-2*e2+4*e2^2-10*e3.                         (1)

The depth-five actions comprise two(4,1), six permutations with anonymous
profile(3,1,1), and nine with profile(2,2,1). Each three-distinct-key pattern
sums over ALL six label assignments, so

    P(N=5)=2*(S4-S5)+12*e3*S2+18*e3*e2
          =2*e2-6*e2^2+10*e3+4*e2*e3.                 (2)

The policy has no earlier stop. Consequently

    E_P N=6-2*P(N=4)-P(N=5)
         =4+2*e2-2*e2^2+10*e3-4*e2*e3.               (3)

These group counts and the homogeneous polynomial identities MUST still be
checked independently from the operational table on all tapes; they are not
new measurements or fitted laws. At U3 the predicted stop probabilities are
11/27,34/81,14/81 at depths4,5,6 and the mean386/81.

## Theorem conditional on the checked extraction

For every iid original-payload law with three allowed keys, the key-only rule
has E_P N<=386/81. Indeed0<=e2<=1/3 and0<=e3<=1/27. The polynomial in(3) is
increasing in EACH coordinate throughout that rectangle:

    partial_e2=2-4*e2-4*e3 >=14/27>0,
    partial_e3=10-4*e2 >=26/3>0.

Both coordinate maxima are attained by uniform key masses. Thus(3) is maximized
at U3 with value386/81. The independent rational dual lower bound at U3
already applies to every universal algorithm in the declared cap-six contract
(including label-specific rules before symmetrization and first clones).
Therefore

    inf_A sup_P E_P N_A =386/81,

for unknown-law cap-six universal marginals, literal first and simultaneous
atom-optimal diagonals on three allowed keys. The SAME minimax value holds
for cap-seven algorithms, since V3 proves its U3 lower bound and the cap-six
achiever is allowed. Caps4/5 have the known A38 value31/9; this addendum does
not claim invention of the cap-four theorem or Bernstein degree elevation.

Raw P may have any within-key distribution: the rule reads only keys, so
its work formula and upper bound still hold. The lower bound needs only the
three-representative subfamily. This is a MINIMAX result, not pointwise optimality
of the policy at every nonuniform P. Other rules may beat it at a given P.

Relative to the fixed full-six atom achiever, expected source calls are reduced
by AT LEAST50/243 (20.576...%) for EVERY such P, with equality at uniform keys.
For iid complete source calls with finite mean work w(P), finite Wald gives
the same ratio in expected SOURCE work, including correlated failure/work.
Coordinator cost and asymmetric downstream utilities remain charged separately.
No actual wall/CPU, neural quality, external priority or publication follows.

The new substance to audit is the minimax stopped-work theorem/attaining rule,
not generic matching, negative dependence, LP or any old pilot's measurements.
An original useful full-cost application and a targeted antecedent review are
still necessary before considering the user's goal fulfilled.
