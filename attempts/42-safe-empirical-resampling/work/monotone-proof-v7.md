# Written safe six-pool refinement of C4; stronger blend still conjectural

Let P,c,G satisfy the IID specification of V6. Let J4 be the classical
four-pool joint class law. Prepare six IID ORIGINAL states; keep first.
If the unordered label profile is(3,3), use uniform minimum-repeat matching6.
Otherwise select three of the other five positions uniformly and use uniform
minimum-repeat matching on first plus those three. All indices are distinct;
original states/aliases need not be. Call this law H6.

The random four-subpool is four IID states unconditionally and realizes
J4. Conditional on six class counts its two original-position marginals are
uniform: subset selection and matching are exchangeable over positions,
with first kept literally by the joint row. Matching6 has the same conditional
original-position marginals. The count-only switch preserves both raw P
marginals. Different IID positions have independent raw residuals conditional
on their labels, so the cross covariance depends only on class means.

At profile(3,3), the random four-subpool has class profiles(3,1),(2,2),(1,3)
with probabilities1/5,3/5,1/5. Its class joint law is diagonal1/10 and
off-diagonal2/5. Matching6 has zero diagonal and off-diagonal1/2. The
difference is minus(1/10)*(e_i-e_j)*(e_i-e_j)^T. This count profile occurs
with probability20*pi^3*pj^3. Thus, exactly,

    J_H6 - J4 = -2 sum_(i<j) pi^3*pj^3 (ei-ej)(ei-ej)^T.       (1)

For conditional class means mu_i of a scalar target,

    Cov_H6(G1,G2)-Cov_C4(G1,G2)
      = -2 sum_(i<j) pi^3*pj^3 (mu_i-mu_j)^2 <=0.             (2)

It is strict iff class means are not all equal. The vector result follows
by applying(2) to every linear projection. Consequently every terminal
verifier's pass@2 is never worse than C4, when G is its conditional terminal
success indicator and both selected native continuations are preserved.
This composition is the same conditional-expectation principle already
recorded in A38/A31; it is not a new global diffusion principle.

At L balanced classes, the class-contrast variance reduction relative to iid2
is delta_H=1/L-1/L^2+2/L^4, versus delta4=1/L-1/L^2. For a binary balanced
classifier this is3/8 versus1/4; for four balanced classes it is25/128 versus
24/128. The latter improvement is small and is not physical timing.

## Exact obstruction to promoting matching6 as universal C4 domination

Take p=(4/5,1/10,1/10) and class score f=(0,1,-1). Its mean is zero.
The C4 cross covariance is-17/2500, while matching6's is-111/25000.
Thus matching6 has LARGER pair-mean variance by59/50000. Both are still
better than iid2. This is a mathematical counterexample, not a favourable
or unfavourable model benchmark. V6 claimed balanced, not universal, C4
dominance; do not silently strengthen it.

## Optional stronger blend — NOT YET PROVED

If the class palette has size at most L>=2, mix matching6 with probability
1/L and H6 otherwise, using an independent exact integer coin. Both preserve
P and are safe relative to iid2. The conjecture is that this blend dominates
C4 for all class probabilities. This would require, for all centered f,

    (L-1)*(f^T(J4-J_H6)f) >= f^T(J6-J4)f.                  (3)

Near p=(1-(L-1)*epsilon,epsilon,...,epsilon), minority contrasts show that
1/L is a NECESSARY upper bound for a universal blend coefficient: the
matching6 excess approaches(L-1) times the H6 correction. Sufficiency is
open. Failure of(3) will be preserved; no neural campaign depends on it.
