# Conditional matching safety: written theorem for all even pool sizes

This is a CONDITIONAL result obtained using classical stability preservation.
It is not a proof of safety after a randomly selected pool, novelty, or neural
utility. Unlike finite eigenvalue checks it does cover arbitrary pool size.

Let B=2m known distinct sources have positive class counts r_i and uniform
first source. Uniformly choose a perfect matching minimizing equal-class
edges; return the literal first source and its matching partner. Count each
original source/alias separately. Let J denote the joint class law and p=r/B.

**Theorem.** Conditional original-source marginals are uniform, each class
atom has J_ii=max(0,2p_i-1), and Cov(G(X),G(Y)) is negative semidefinite for
EVERY finite-vector function G on these sources. Consequently the covariance
of their average is no greater than two iid evaluations of the SAME pool.
This does not assert comparison to iid draws of the full original population.

**Proof of marginals/diagonals.** A perfect matching partners each original
source with exactly one other source. Uniform first choice and symmetry give
both uniform marginals. A largest class can force exactly max(0,r_h-m)
same-class edges. This classical complete-multipartite matching bound is
attained, and no other class has same-class edges in an optimal matching.
Dividing twice those edges by B gives the stated diagonal.

**Majority case.** If p_h>=1/2, every non-h source is paired with an h source;
J_hj=J_jh=p_j for j!=h and J_hh=2p_h-1. For centered class scores p.f=0,
f^T(J-pp^T)f=-f_h^2. Within h, original matching excludes the identical
source, so centered within-class scores have nonpositive covariance. For
other classes their residual covariance is zero. Orthogonal decomposition
into class means and within-class residuals proves the vector statement.

**No-majority case.** Put e2(z)=sum_{i<j}z_i z_j. Let H(r) be the number of
perfect matchings having no equal-class edges on r individually labeled
sources. The classical exponential generating function gives

  coefficient[z^r] e2(z)^m = m! H(r) / product_i r_i!.

H(r)>0 because max r_i<=m. The monomial z^r is real stable, and so is e2.
By Borcea--Branden Theorem1.3, the constant-coefficient operator e2(partial)
preserves real stability (its symbol e2(-w)=e2(w) is stable). Therefore

  Q(z)=e2(partial)^(m-1) z^r

is a nonzero real stable quadratic with nonnegative coefficients. Its Hessian
A has at most one positive eigenvalue: for positive e and any real x, the
univariate quadratic Q(e t+x) has real roots, so its discriminant yields
(x^T A e)^2 >= (x^T A x)(e^T A e). Since e^T A e>0, the quadratic form is
nonpositive on the codimension-one space x^T A e=0. This proves the inertia
claim directly; no new Lorentzian-polynomial theorem is being claimed.

For i!=j the Hessian coefficient is

  A_ij=(m-1)! r_i r_j H(r-e_i-e_j).

For i=j it is (m-1)! r_i(r_i-1)H(r-2e_i), nonnegative. Subtracting this
nonnegative diagonal cannot increase the number of positive eigenvalues.
The remaining matrix, divided by (m-1)! B H(r), is exactly J: each possible
original i--j edge is present in H(r-e_i-e_j) completions and the uniformly
chosen first source accounts for division by B. Thus J has at most one
positive eigenvalue. Since J1=p, conjugating by diag(p)^(-1/2) has unit
positive eigenvector sqrt(p), eigenvalue1. Subtracting sqrt(p)sqrt(p)^T
leaves a negative-semidefinite matrix, proving J-pp^T<=0. Within-class
residual covariance is zero because no same-class pair occurs. This also
proves the arbitrary-vector lift by checking every linear projection.

**Costs and missing step.** This proof does not turn the small count-vector
oracle into a polynomial-time implementation. Classical rook-polynomial
inclusion/exclusion can count multipartite matchings with integer arithmetic;
that algorithm and its bit costs still need to be audited before promotion.
For a uniform RANDOM pool, the matrix to control is E[J]-p_global p_global^T,
not E[J-pp^T]. Pool-mean fluctuations remain. Nothing here proves this matrix
negative semidefinite, or any end-to-end dLLM performance improvement.

## Actually checked primary source

Borcea and Branden, *Multivariate Polya-Schur classification problems in the
Weyl algebra*, arXiv math/0606360v6 (2009-11-06),
https://arxiv.org/pdf/math/0606360, Definition1.1 and Theorem1.3, pp2--3.
Read the actual symbol/sign convention, not only a secondary description.
Theorem1.3 supplies operator preservation; the matching argument and spectral
reduction above are written consequences. No claim its31-page proof was all
read, or that absence of this application there establishes priority.
