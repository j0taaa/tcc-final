# V4 proof obligations, before certificate expansion

Same law/source/classes/eight criteria as v2/v3. No measured model benefit.
The B=6 polynomial has been derived and checked independently; those finite
checks do not prove its covariance sign. Set A=M^2-S2, d=15M-30,
T=sum n_i^2(M-n_i)^2, B0=A^2+T-dA, c0=30M^2-126M+120.
For centered class scores put a_i=n_i f_i, h=sum n_i a_i,
t_i=n_i(2M-n_i), b_i=a_i+(h/A)n_i. Algebra suggests

  D6*f^T C*f = -sum (B0+A*t_i)b_i^2
                +(B0+A*M^2)/M^2*(sum n_i*b_i)^2
                -c0*sum a_i^2/n_i.

When B0>=0, weighted Cauchy and
 B0+A*t_i >= (B0+A*M^2)*n_i/M
prove nonpositivity. This is a written sufficient-condition proof, not yet
all-population safety. The degenerate one-class case is separate.

For M>=28, no majority has A>=M^2/2>=d. For a majority n_h=M-r
with r>=8, prove B0>=0 using A>=2(M-r)r and
T>=(M-r)^2*r(r+1); account the monotonicity of A(A-d) explicitly.
Thus remaining infinite families are majority complements r=1..7; r<=3
is the fixed star law. There are38 integer partitions of r=4..7.

Next produce exact symbolic principal-minor polynomials for these38 families,
after grouping equal-count classes; inspect coefficients in M-(2r+1) and
factor signs, not eigenvalue frequencies. Any failed identity/nonnegative
claim remains OPEN. Repeated small classes have nonpositive contrast modes;
remove the majority using C1=0. The small boundary M=6..27 still requires a
separate algebraic/finite exact certificate; ordinary floating checks will
not be treated as a proof. A finite rational certificate is computer-assisted
verification, with its boundary declared, not Lean/software verification.

No claim of all-B covariance, novel sampling principles, publication, training
or speed follows even if this B=6 theorem closes. Priority, sharper competent
classical comparison and a useful full-cost CFG/dLLM application remain open.
