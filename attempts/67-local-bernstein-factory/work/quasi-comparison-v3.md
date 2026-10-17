# Closest classical control: quadratic reproduction removes the separation

2026-10-17. Written BEFORE implementing or executing this comparison. V1 and
its raw data remain unchanged. This is a classical-control derivation, not an
own new factory or a claim that the cited survey printed our factory proof.

## Source and exact operator

Sablonniere's ORIGINAL 2004 survey, Section2.2, defines the right Bernstein
quasi-interpolants B_n composed with the differential partial inverse A_n^(r),
and states reproduction of P_r. Its order-two inverse is determined already
by 1,x,x^2. Since B_n x^2=x^2+x(1-x)/n and
B_n[x(1-x)]=x(1-x)(n-1)/n, that inverse is

    A_n^(2) f(x)=f(x)-x(1-x)f''(x)/[2(n-1)].

Thus the right quasi-interpolant has coefficients
C_n(k)=f(k/n)-x(1-x)f''(x)/[2(n-1)], x=k/n. This FORMULA is independently
derived here from the classical definition/reproduction, not attributed to an
unread 1992 original or to a different triangular operator. Replacing expensive
derivatives by finite differences is also a classical quasi-interpolation
operation; it is not our invention. See primary-v3.md for actual reading scope.

Give this control the SAME V1 three-point stencil D_n, h=1/sqrt(n), including
the same forward/backward switch. It uses the SAME three value-oracle calls:

    b_n(k)=f(x)-x(1-x)D_n f(x)/[2(n-1)].

Keep V1's assumptions f in C2, |f''|<=M, Lip(f'')<=H, and
epsilon<=f<=1-epsilon. All degrees below are powers of4, at least16. The
following bounds show that neither local value access nor the effective
finite-mean capability separates V1 from this competent classical control.

## Explicit approximation and elevation constants

Use V1 Section2's elementary bounds E|X-x|<=1/(2sqrt(m)) and
E|X-x|^3<=m^(-3/2), with the binomial case m=n or hypergeometric case
X=K/m, K~Hypergeom(4m,k,m), x=k/(4m). Let q(t)=t(1-t), and write

    f(X)=f(x)+f'(x)(X-x)+f''(x)(X-x)^2/2+R_X,
    |E R_X|<=H/(6m^(3/2)).

For a binomial mean E q(X)=q(x)(n-1)/n. This identity cancels the ENTIRE
quadratic Taylor term against C_n's correction. The remaining correction is
bounded by

    H E[q(X)|X-x|]/[2(n-1)]
       <=H/[16(n-1)sqrt(n)]<=H/[15 n^(3/2)].

Consequently |B_n C_n(x)-f(x)|<=7H/[30 n^(3/2)]. V1's finite difference
error is at most H/sqrt(n), so uniformly in k,

    |b_n(k)-C_n(k)|<=H/[8(n-1)sqrt(n)]
                       <=2H/[15 n^(3/2)],
    |B_n b_n(x)-f(x)|<=11H/[30 n^(3/2)].                 (1)

For the degree-elevation law, E q(X)=4(m-1)q(x)/(4m-1) and
Var(X)=3q(x)/(4m-1). Substitution cancels ALL terms proportional to f''(x):

    C_(4m)(k)-E C_m(K)
      =-E R_X+E[q(X)(f''(X)-f''(x))]/[2(m-1)].

The same calculation gives absolute bound 7H/(30m^(3/2)). Add the old
finite-difference error <=2H/(15m^(3/2)) and the new error
<=H/[16(4m-1)sqrt(m)]<=H/(63m^(3/2)), to obtain

    |b_(4m)(k)-E b_m(K)|<=241H/[630 m^(3/2)]
                            <H/[2m^(3/2)].             (2)

This is coefficientwise consistency, not only an approximation bound. The
constants use no derivative oracle or information unavailable to V1.

## Certified envelopes and the same full-cost route

Set delta_n=H/n^(3/2), l_n=b_n-delta_n, u_n=b_n+delta_n. The gap between
successive deltas is 7H/(8m^(3/2)), larger than (2). Together with (1),
this establishes the same lower/upper approximation and elevation conditions.
Choose the first power of4 n0>=16 satisfying

    M/[8(n0-1)]+17H/[15 n0^(3/2)]<=epsilon.              (3)

Indeed |b_n-f|<=M/[8(n-1)]+2H/[15 n^(3/2)], so (3) puts every
coefficient l_n,u_n in[0,1]. For H>0, delta_n0<1/2 follows from (3).
Apply the SAME classical positive-mixture proof as V1 Section4, with H
in place of M+H. It yields a preselected count independent of the p-coins,

    P(N>n_j)=2H/n_j^(3/2),
    E N=n0+12H/sqrt(n0).                                (4)

For H=0, f is quadratic and b_n=C_n reproduces it exactly: once (3) holds,
one finite Bernstein polynomial already suffices. Do not divide by a zero
mixture weight. Specific known polynomials can still use MUCH cheaper direct
factories; these remain mandatory and no generic implementation win follows.

In V1's exact rational specialization, a safe common denominator is
2D(n-1)n^(d+2). The added (n-1) has O(log n) bits. The SAME classical
binary-splitting/fast-multiplication argument applies, giving the same
O(n polylog n) conditional bit work and finite expected work. This is a
written bound, not an implemented fast arithmetic engine; naive Fraction
loops/Python multiplication still cannot inherit it.

For the prescribed nonanalytic spline M=3/4,H=3/2,epsilon=1/4, both
constructions have n0=16. The classical control has E N=41/2, versus V1's
91/4, with identical three-query locality and asymptotic bit-work route.
These are analytical bounds, not measured latency or sampled costs. Equation
(3) can choose a different n0 on other inputs; no universal pointwise cost
dominance claim is needed or made.

## Decision, before the small confirmation audit

V1 remains a valid coefficient construction if its proof is correct, but its
proposed locality/finite-mean/effective-cost distinction does not survive this
control. The restricted comparison against the dense Boolean sum remains
true as stated and is insufficient to justify an own useful advance. Do not
implement the full V1 sampler, start performance/neural campaigns, or promote
either classical correction to the article on this rationale. A bounded exact
coefficient comparison may check this derivation; it will not establish
priority, full software correctness or a positive scientific contribution.

The user's scientific goal remains OPEN. Before substantial new work, identify
a useful consequence that the equally informed local classical control does
not already provide. No cap, metadata restriction or removal of derivatives,
caching or direct polynomial controls may be introduced just to force a win.
