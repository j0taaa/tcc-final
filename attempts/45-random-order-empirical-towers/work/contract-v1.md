# Random-label-order tower contract and prospective refutation protocol

2026-10-12. BEFORE code/output. This is a conjecture, not a theorem.

For IID original draws Z1,...,ZB, fixed labels c in 0,...,L-1 and count vector
r, take a uniform random permutation of the L label blocks independent of
source values/target G. Block i has 2r_i integer tickets. A uniform ticket T
and its antipode (T+B) mod(2B) define the symmetric conditional joint J(r).
Average over the uniform block order only for the independent mathematical
oracle. Zero-size blocks do not affect the law; uniformly permuting occupied
labels gives the same law. Every order has row sums r/B and diagonal
(2r_i/B-1)_+, a CLASSICAL Fréchet/half-shift property.

To retain Z1, given its label i sample the partner class from J(r)'s row
divided by r_i/B, then a uniform NONFIRST original slot of that class. A
positive diagonal implies r_i>=2. Conditional exchangeability preserves both
original marginals. Different selected IID slots preserve the full independent
within-class residual law; aliases/repeated raw states are not removed.

The OPEN question is whether, for EVERY unknown population p and B>=2,

    C_B(p)= E_{r~Multinomial(B,p)} J(r) - p p^T <= 0.

Neither conditional safety nor balanced symmetry establishes this statement.
It is enough to refute one admitted p/B and rational score f with f^TCf>0.
Such a certificate closes the proposed universal theorem, irrespective of
how many other cases pass. No model execution follows a refutation.

Prospective screen: L=4,5,6; even B=2,4,6,8,10,12 for L4/5 and B=2,4,6,8
for L6. Population cases are all positive integer compositions of denominator
8 for L4, 9 for L5 and 10 for L6 (permutation symmetry permits sorted unique
populations); additionally128 Dirichlet(alpha) populations per L/alpha,
alpha in{.1,1,10}, seed20261012045, and the explicit prior(.4,.3,.2,.1).
All planned populations remain available; a first numerical eigenvalue>1e-9
triggers exact rationalization/certificate and stops the negative-only screen.
No success claim follows absence of an obstruction. Failed assertions/errors
and partial records stay preserved; no threshold or source redefinition.

Independent oracle enumerates ALL count vectors with exact multinomial
coefficients, ALL occupied-block permutations and integer ticket antipodes.
It uses float only to locate an obstruction; a frozen follow-up computes the
full joint/score as fractions. Track profile counts, cases and source hashes.
No gradients, curated external victories, timers or changed neural protocol.
