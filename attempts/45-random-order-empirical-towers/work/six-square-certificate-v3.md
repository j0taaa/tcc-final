# Explicit sum-of-squares addendum to the six-proposal proof

Written before the new V3 algebra checks. Use the notation and operation of
six-class-proof-v3.md; no new consumer or all-budget assertion is added.

The two Cauchy inequalities can be made an EXACT identity. Put

    L_i=p_i(1-p_i-z),
    s_i as in equation(5) of the proof,
    R=2z+6z²+2w+4v.

Then the unconditional class covariance is

    C(f) = -sum_i s_i b_i²
           -4 sum_(i<j) L_i L_j (b_i-b_j)²
           -R sum_(i<j) p_i p_j (b_i-b_j)².           (7)

Proof: sum_i L_i=z and sum_i p_i=1 imply

    z sum_i L_i b_i²-(sum_i L_i b_i)²
        =sum_(i<j) L_i L_j (b_i-b_j)²,
    sum_i p_i b_i²-(sum_i p_i b_i)²
        =sum_(i<j) p_i p_j (b_i-b_j)².

Substitute these two elementary weighted-variance identities in equation(2).
The remaining coefficient is exactly equation(4), expanded positively in(5).
There is no missing multiplicative z in the pairwise term: it is already the
sum of the L weights in the variance identity.

All coefficients in(7) are nonnegative, and s_i>0 on positive support with
at least two classes. Thus this is a dimension-independent written square
certificate, not an eigenvalue observation or a finite-population extrapolation.
Independent rational checks should compare the FULL joint-law quadratic form
with(7), not merely test its already nonnegative coefficients in isolation.
Prior sufficient novelty and real usefulness remain separate open obligations.
