# Exact reduction of the anonymous family to two moment directions

This is algebra toward the OPEN sufficiency proof, not that proof. The V9
screen has37,200 endpoint checks, largest eigenvalue8.89e-16 and no >1e-10
obstruction. This floating observation does not prove safety or originality.

Let x=pi,y=pj, Rk=Sk-x^k-y^k for k>=2 and R1=1-x-y. Changing the
(2,2,1,1) small/small probability from1/30 to t changes off-diagonal J by

    (t-1/30)*90*x*y *
       [xy*(R1^2-R2)+R2^2-R4-(x+y)*(R1*R2-R3)].

The diagonals stay g6(pi). The three terms count respectively i,j as the
two big classes, as the two small classes, and as one big/one small; the
multinomial coefficient of the profile is180. Marginals do not change.

For centered class f, use V6's a_i=pi*f_i, h=sum pi*a_i,
A=1-S2, T=S2-2*S3+S4, B=A^2+T and b_i=a_i+(h/A)*pi. Put

    q=sum pi*b_i=h/A, H2=sum pi^2*b_i,
    E=S2^2-S4, D=S2-S3, F=A+2*S3+E,
    e_i=E-2*D*pi+A*pi^2,
    d_i=B+A*pi*(2-pi), K=B+A, lambda=90*t-3.

Since sum a_i=0, the exact class covariance form is

    f^T(J_t-pp^T)f = -sum_i (d_i+lambda*e_i)*b_i^2
                    +2*lambda*H2^2
                    -2*lambda*(1+S2)*q*H2
                    +(K+lambda*F)*q^2.                    (1)

At lambda=0 this is V6's proved square identity. The prospective boundary
t=4/45 has lambda=5; t=0 has lambda=-3. The legitimate b also satisfies
sum_i(1-pi)*b_i=0. Ignoring that constraint in a coarse Jensen bound does
NOT close the argument: its pointwise slack is

    (1-pi)*[B+A*pi+lambda*(E-(1+S2)*pi+2*pi^2)],

which is negative for a middle class in e.g. p=(1/5,7/10,1/10), lambda=5.
This is failure of that sufficient proof tactic, not a sampler counterexample.
Do not certify the interval from this calculation or the numerical screen.

Next mathematical obligation: prove or refute nonpositivity of(1) under
sum_i(1-pi)b_i=0 for lambda=-3 and5 and arbitrary class masses. Convexity
in lambda would then cover the interval. Prior significance and CFG/native
complete-cost application would still remain separate obligations.
