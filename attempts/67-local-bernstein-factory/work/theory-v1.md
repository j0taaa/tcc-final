# Explicit local value-only Bernstein envelopes — candidate proof

2026-10-17, BEFORE code or new calculations. Classical ingredients are named
in primary-v1.md. This is a written candidate, not priority or human review.

## 1. Interface and coefficient

Let f:[0,1]->[epsilon,1-epsilon], 0<epsilon<=1/2, have continuous second
derivative with |f''|<=M and Lipschitz constant of f'' at most H. Given
nonnegative rational upper bounds M,H and rational epsilon, set c=M+H.
For n=4^j>=16, h=1/sqrt(n), x=k/n, define

    D_n f(x) = [f(x+2h)-2f(x+h)+f(x)]/h^2,  x<=1-2h;
               [f(x)-2f(x-h)+f(x-2h)]/h^2,  otherwise.
    a_n(k) = f(x) - x(1-x) D_n f(x)/(2n).
    delta_n = c/n^(3/2),
    l_n(k)=a_n(k)-delta_n,  u_n(k)=a_n(k)+delta_n.

Both stencils stay in[0,1]: h<=1/4, and the backward case has x>1-2h>=2h.
Each coefficient requires THREE f-values at points with denominator n.
Forward/backward second differences are averages of f'' over a square of
side h. The mean distance from x is h, so

    |D_n f(x)-f''(x)|<=H h.                                      (1)

Let n0 be the first power of4 at least16 satisfying

    M/(8n0) + 9c/(8 n0^(3/2)) <= epsilon.                       (2)

This is an exact rational comparison because sqrt(n0) is an integer. For
c=0, f is affine; direct interpolation using f(0),f(1) is a cheaper classical
factory. The following construction concerns c>0. Its constants are explicit,
not asserted optimal.

## 2. Elementary moments, including sampling without replacement

For X=Bin(n,x)/n, or X=K/m with K hypergeometric from a population of4m
bits with k ones and m draws (x=k/(4m)), put Z=X-x. Then

    E Z=0, E|Z|<=1/(2sqrt(m)), E|Z|^3<=m^(-3/2),               (3)

using m=n in the binomial case. Binomial variance is x(1-x)/n. The
hypergeometric variance is 3x(1-x)/(4m-1)<=1/(4m).

For completeness, the third-moment bound follows from
P(|Z|>t)<=2 exp(-2mt^2), with no new concentration principle. In the
without-replacement case reveal the m sampled bits; the Doob martingale
of their final mean has conditional increment range3/(4m-i)<=1/m at
reveal i<=m. For the binomial case the range is1/m. A centered variable
of range r has log-mgf at most t^2*r^2/8: its tilted variance is at most
r^2/4, so integrate the second derivative of its log-mgf twice. Applying
this conditionally and Chernoff's inequality gives the displayed tail.
Integrate 3t^2 times that tail: the resulting constant is
3sqrt(pi)/(2*2^(3/2))<1, proving(3). No asymptotic approximation is used.

## 3. Approximation and coefficient consistency

Write g(x)=x(1-x)f''(x), and A_n(k)=f(k/n)-g(k/n)/(2n), the ordinary
derivative-corrected local coefficient used only as an ANALYTICAL control.
The Lipschitz constant of g is at most L=M+H/4. Taylor's remainder after
the quadratic term is at most H|t-x|^3/6. From(3),

    |B_n A_n(x)-f(x)| <= [M/4+11H/48]/n^(3/2).

By(1), |a_n(k)-A_n(k)|<=H/(8n^(3/2)). Positivity of Bernstein weights gives

    |B_n a_n(x)-f(x)| <= [M/4+17H/48]/n^(3/2) <=delta_n.      (4)

Now n=4m and K~Hypergeom(4m,k,m), x=k/(4m). Taylor and the EXACT variance give

    A_(4m)(k)-E A_m(K)
      = -3g(x)/[8m(4m-1)] + [E g(K/m)-g(x)]/(2m) - R,
    |R|<=H/(6m^(3/2)).

The first term has absolute value at most M/(32m^2), and the middle term
at most L/(4m^(3/2)). Adding the two finite-difference errors gives

    |a_(4m)(k)-E a_m(K)|
       <=[9M/32+71H/192]/m^(3/2) <=c/(2m^(3/2)).             (5)

But delta_m-delta_(4m)=7c/(8m^(3/2)), larger than the bound in(5). Thus

    l_(4m)(k)>=E l_m(K),    u_(4m)(k)<=E u_m(K).              (6)

These are coefficientwise inequalities under ordinary degree elevation,
not merely pointwise approximation inequalities. Also(1) implies

    |a_n(k)-f(k/n)|<=M/(8n)+H/(8n^(3/2)).

Condition(2), decreasing with n, proves0<=l_n<=u_n<=1 for every n>=n0
in the power-of4 sequence. Equations(4)--(6) give all envelope conditions.
This effective special case does not assert a general converse from
approximation error to coefficient consistency.

## 4. Exact positive mixture with a preselected input count

Let n_j=n0*4^j. Define weights

    w0=1-2delta_(n0)>0,
    wj=2[delta_(n_(j-1))-delta_(n_j)] for j>=1.

They are nonnegative rational numbers summing to1. For j=0, let
r0(k)=l_(n0)(k)/w0. For j>=1 let

    rj(k)=[l_(n_j)(k)-E l_(n_(j-1))(K)]/wj,
    K~Hypergeom(n_j,k,n_(j-1)).

Equation(6) and the constant coefficient gap u_n-l_n=2delta_n prove
0<=rj(k)<=1. Draw J with probabilities wj using known auxiliary randomness,
BEFORE input coins. Draw n_J p-coins, let k be their sum and output1 with
probability rJ(k). Then

    P(output1) = B_(n0)l_(n0)
       + sum_(j>=1)[B_(n_j)l_(n_j)-B_(n_(j-1))l_(n_(j-1))]
       =f(p),

by telescoping and(4). This is the CLASSICAL positive-polynomial-mixture
factory principle, instantiated with explicit coefficients and weights.

The entire input count N=n_J is independent of the p-coins; for every j>=0,

    P(N>n_j)=2delta_(n_j),
    E N = n0 + sum_(j>=0)3n_j*2c/n_j^(3/2)
        = n0+12c/sqrt(n0).                                   (7)

Condition(2) ensures delta_(n0)<=8epsilon/9<=4/9, so w0 is positive.
No empirical-frequency approximation or estimated p is used. Counts other
than p-coin calls, and boundary failures, are not erased by(7).

## 5. Full arithmetic contract, not unit-cost rationals

For an executable exact-bit specialization, require fixed metadata D,d such
that f(k/n) on dyadic grids is exactly evaluable in poly(log n) bit work,
with denominator dividing D*n^d and numerators of O(log n) bits (constants
may depend on metadata). Rational piecewise polynomials of fixed degree
with fixed rational coefficients satisfy this, including C2 cubic splines;
include denominators of c in D. This restriction is EXTRA, not true for an
arbitrary real-valued function oracle or an unbounded-cost derivative oracle.
Then all l_m coefficients have the known common denominator

    L_m=2D*m^(d+2).

The stencil points have denominator m and m^(3/2) is integral, proving the
claim by clearing denominators. The elevation numerator uses
U_i=C(m,i)C(3m,k-i), with nonzero i in[max(0,k-3m),min(m,k)]. Its consecutive
ratio is

    U_(i+1)/U_i=(m-i)(k-i)/[(i+1)(3m-k+i+1)]=a_i/b_i.

An exact weighted sum of these terms can use classical binary splitting.
For a block of coefficient numerators A_i=L_m*l_m(i), maintain P,Q,T such
that P/Q is the product of INTERNAL consecutive ratios and T/Q is their
weighted sum relative to the block's first U. A singleton has P=Q=1,T=A_i.
Join left and right blocks across ratio a/b using

    P=P_left*a*P_right,
    Q=Q_left*b*Q_right,
    T=T_left*b*Q_right+P_left*a*T_right.

Multiply T/Q by the first U, then divide by L_m*C(4m,k) to obtain the
elevated coefficient exactly. Binomials can use balanced products too.
All intermediate integers have O(m log m) bits; with quasi-linear integer
multiplication, the work is O(m polylog m), including O(m) value calls,
and memory O(m polylog m). Summing against wj=O(n_j^(-3/2)) proves FINITE
expected bit work and expected memory. Exact Bernoulli(rJ(k)) generation
from a rational uses ordinary rejection of a random integer; all its bits
and trials are charged and have finite expected cost of the same order.

This is a theoretical implementation bound using known fast arithmetic.
Naive per-term Fraction sums, or a prototype with an unspecified integer
multiplication exponent, do NOT automatically inherit it. In particular an
O(N^2) bound is not integrable under this N distribution. First validate
coefficients independently, then audit an actual implementation's full work.

## 6. Scope of the positive consequence and comparisons

For a known C2 rational cubic link such as

    f(p)=1/4+p/8+(1/4)*max(p-1/2,0)^3,

epsilon=1/4, M=3/4, H=3/2 satisfy the hypotheses. The initial degree is16,
and(7) is91/4. This is a nonanalytic proof object, not a timing benchmark.
Known rational/finite-automaton factories do not by themselves apply to a
nonrational spline, but HNP's smooth-factory EXISTENCE DOES already apply.
Do not claim that finite-mean simulation of splines is new.

An interior coefficient of the ordinary Boolean-sum operator
2f(k/n)-B_n f(k/n) requires n+1 f-values in the unrestricted exact value-
oracle model: each grid weight is nonzero and a sufficiently small C2,1 bump
at an unread grid point changes that coefficient without changing the other
read values. This is a comparison with ONE specified operator for a COLD
query; preparation/caching can amortize it, and other local methods may match
our three-query locality. Derivative-corrected coefficients are also local
if derivatives are available, and remain a mandatory competent control.

The own candidate is the fully effective value-only envelope/cost contract,
not the classical ingredients, finite-mean capability, or a victory over all
known methods. Priority and enough publication significance remain unproved.
There is no new dLLM/CFG execution. A deterministic cap on J or runtime does
not return the exact f(p) law conditional on success in general; that is a
different approximate/FAIL operation requiring its own contract.
