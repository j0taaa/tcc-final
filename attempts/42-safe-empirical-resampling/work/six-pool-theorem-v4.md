# Six-source matching: unconditional covariance theorem

This is a **written, partly computer-assisted mathematical result**, not a
measurement of dLLM training, a claim of literature priority, or a publication
decision. The finite certificates below are rational/polynomial proof objects;
they are not benchmarks. The maintained decoder/article are unchanged.
The all-even-budget unconditional conjecture is still open.

## Operation and theorem

Let a known finite set of M>=6 original addresses carry an arbitrary fixed
class map. Aliases remain separate addresses. Retain an originally uniform
address X, sample five other distinct uniform addresses, and consider the
resulting unordered six-element pool. Uniformly select a perfect matching
having the fewest equal-class edges. Return X and its matching partner Y.
There are only15 labeled perfect matchings on six elements. The class map
must be fixed before these draws, independently of their expensive scores.

**Theorem.** X and Y are both uniform on the original M addresses. For every
finite-vector function G on those addresses,

    Cov(G(X),G(Y)) <= 0                     (Loewner order).
    Cov((G(X)+G(Y))/2) <= Cov(G(U))/2       (U uniform).

Every class atom containing t original addresses has joint diagonal g6(M,t),
the atom frontier defined/proved under the opaque universal SOURCE-cap model
in A41/work/budget-frontier-v4.md. In particular,

    g4(M,t)-g6(M,t) = 2 (t)_3 (M-t)_3 / (M)_6.

The improvement is strict exactly when 3<=t<=M-3. It does not say that
every union of classes improves over the four-source design, or that this
method dominates ranked-set sampling, analytical controls, or two draws
without replacement for every score. The frontier's literature priority
remains unresolved; its information restrictions are essential.

## Marginals, atom probabilities and within-class residuals

Conditional on a pool, X is uniform on its six original addresses. Every
matching permutes those addresses, so Y is also uniform; averaging pools
gives both original marginals. Minimal equal-class edges occur only in a
majority class, and their number is max(0,r_h-3). Thus the conditional atom
diagonal is max(0,2r_i/6-1). The pool counts are hypergeometric, proving g6.
The exact falling-factorial expression for its numerator is

    D*g6(M,t) = t(t-1)(M-2)(M-3)(M-4)(M-5)
              -t(t-1)(M-t)(M-t-1)(M-4)(M-5)
              -2t(t-1)(t-2)(M-t)(M-t-1)(M-t-2),

where D=(M)_6. This follows from the already written Catalan increments,
not floating point eigenvalues.

Let n_i be the original positive class sizes, p_i=n_i/M, and J the joint
class matrix after averaging all pools. Conditional on two distinct classes,
the two raw addresses are independent uniform in their respective classes.
Conditional on two addresses in the same class, they are a uniform ordered
distinct pair. Therefore, for any scalar score with class means f_i and
within-class variances sigma_i^2,

    Cov(G(X),G(Y)) = f^T(J-pp^T)f
                     - sum_{n_i>=2} J_ii sigma_i^2/(n_i-1).

It suffices to prove J-pp^T<=0. Checking every linear projection proves the
vector assertion. Single-class populations are ordinary uniform distinct
pairs and are covered separately. Two classes are covered by J_ii=g6<=g2<p_i^2:
the symmetric covariance matrix has zero row sums, hence is negative
semidefinite. When M=6 the pool is the whole population; the all-even-size
conditional theorem in conditional-matching-proof-v2.md applies directly.

## Exact joint polynomial and square identity

Put S_k=sum_i n_i^k. The v3 counting derivation, over **all** six-source
profiles, gives for i!=j

    D J_ij = n_i n_j W(n_i,n_j),

where

    W(x,y) = M^4 + M^3(x+y-15) - M^2 S2
      +2M^2(x^2+y^2)-15M^2(x+y)+85M^2
      -M S2(x+y)+15M S2-2M S3
      -M(x^3+y^3)-2Mxy(x+y)+15Mxy+30M(x+y)-195M
      +S2^2+S2xy-30S2+S4+xy(x^2+y^2)-30xy+148.

That derivation uses labeled matching completion counts and the classical
set-partition inclusion-exclusion for distinct other classes. Its2,658
independent rational pair checks are validation of the derivation, not a
replacement for its algebraic argument or a variance proof.

Center f so sum_i n_i f_i=0. Define

    A=M^2-S2>0, d=15M-30,
    T=sum_i n_i^2(M-n_i)^2,
    B0=A^2+T-dA, c0=30M^2-126M+120>0,
    a_i=n_i f_i, h=sum_i n_i a_i,
    t_i=n_i(2M-n_i), b_i=a_i+(h/A)n_i.

Direct expansion yields the identity

    D f^T(J-pp^T)f
      = -sum_i (B0+A t_i)b_i^2
        +(B0+A M^2)/M^2 * (sum_i n_i b_i)^2
        -c0 sum_i a_i^2/n_i.                         (1)

For checking (1), the diagonal correction is
g6*D-n_i^2 W(n_i,n_i)=-n_i^2(B0+A t_i)-n_i c0.
The mixed terms of W on sum_i a_i=0 are
(S2+d)h^2-2h sum_i n_i t_i a_i. Substitution of b and
sum_i n_i b_i=h M^2/A gives (1). The independent certificate verifier
checks these two polynomial identities exactly.

If B0>=0, K=B0+A M^2>0 and

    B0+A t_i-K n_i/M = (M-n_i)(B0+A M n_i)/M >=0.

Weighted Cauchy with sum_i n_i/M=1 proves
sum_i(B0+A t_i)b_i^2 >= K(sum_i n_i b_i)^2/M^2.
Equation(1) is nonpositive. No numerical covariance estimate is used here.

## Infinite populations reduce to a fixed symbolic boundary

For M>=28, a population without a strict majority has S2<=M^2/2, so
A>=M^2/2>=15M-30=d and B0>=0.

For a strict majority h=M-r and r>=8, A>=2hr and T>=h^2 r(r+1).
The latter follows by keeping the majority term h^2 r^2 and using
sum(minority n_i^2)>=r and M-n_i>=h. Also2hr>=d/2: since h>=r+1,

    2hr-d/2 >= 2r^2-13r+15/2 >0, for r>=8.

A(A-d) is increasing for A>=d/2. Thus

    B0 >= hr [ h(5r-29)-30r+60 ].

For r=8,9,10 use h>=28-r; the bracket is respectively at least40,94,138.
For r>=11 use h>=r+1; it is at least5r^2-54r+31>0. Consequently all these
populations also satisfy B0>=0.

If the minority total r<=3, every six-source pool contains at least three
majority members. Its class joint law is the star law. Averaging gives
J_hj=p_j (j!=h), J_hh=2p_h-1, and all other entries zero. For a p-centered
f its quadratic form is -f_h^2, as in the conditional theorem.

There remain the38 integer partitions of r=4,5,6,7, with M>=2r+1.
Group minority classes having equal original size. A repeated minority size
is at most3; its individual g6 diagonal is zero, so its contrast modes have
eigenvalue -J_ij<=0. The constant-on-groups space is tested by its compressed
matrix. Because (J-pp^T)1=0, subtracting the majority score removes that
coordinate without changing the form. At most three minority size types
remain. The104 principal minors of -M^2 D (J-pp^T) on those coordinates are
recorded as exact polynomials. Every coefficient is nonnegative after
substitution M=u+2r+1. Hence all principal minors are nonnegative for u>=0,
which proves positive semidefiniteness for every integer M in these families.
The verifier independently rebuilds the specified joint/compressed matrix
from the v3 formula and verifies every determinant, shift and coefficient.

## Finite rational boundary, explicitly computer-assisted

For M=6..27 there are14,723 positive integer population partitions. Excluding
the already proved cases B0>=0, one/two classes, M=6 and strict-majority r<=7
leaves exactly289 populations, all of size at most17. No class-count limit
is imposed. Equal-size class contrasts are checked separately. The remaining
compressed negative covariance form, with one coordinate removed using its
zero row sums, has an explicit rational factorization L diag(d_j) L^T with
every d_j>=0. The published certificate contains the integer matrix, exact
fraction entries of L and d, and the contrast numerators for each population.
The verifier reconstructs every matrix/factorization and checks exhaustive
coverage of this declared finite boundary. These are finite mathematical
sign certificates, **not** a machine-checked Lean proof of the general
theorem, the sampler, or the dLLM software. Replacing this finite boundary
with a short analytic argument would improve the result further.

## Comparison, costs and application boundary

There is no need to solve irrational maximum-entropy equations. Enumerating
the15 matchings, counting their class conflicts, and drawing a uniform
integer among tied minima is an exact constant-size operation. Five uniform
excluded-address draws and six cheap class evaluations are charged. Source
sampling uses O(log M) bits per draw, in addition to original-address
materialization/unranking and the cost of the classifier. It uses exactly
two expensive G evaluations, retaining the originally paid first one.
Compared with two independent addresses there are four extra cheap states;
a learned proxy also has preparation/storage/update costs. None are free.

For a time-independent dLLM denoiser, the known count-NELBO source in A41
maps uniform original addresses to count-uniform token masks. Holding the
CFG-valid JSON/DSL candidate, parameters and a past-trained structural
classifier fixed, take G to be its score or full stochastic gradient at
that corrupted input. The theorem gives unbiasedness and covariance safety
for this original finite noising law, conditional on the past. It does not
prove reduced error compared with two different data examples, semantic
generation quality, likelihood correctness of a changed law, training
convergence, superiority to EPIC, or a physical wall-time gain.

A41's576 observations show that the existing proxy is weak for the full
output-bias gradient and that retained ranked-set/analytic controls are
stronger for its scalar score. They remain in the report. This theorem alone
does not justify a new large model campaign or protagonist promotion. The
next scientific obligations are closest classical-law/priority reduction,
a CFG-specific useful operation, and complete-cost comparison with competent
controls. Those are necessary to meet the user's publication goal.
