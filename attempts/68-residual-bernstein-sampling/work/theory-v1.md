# Constant callback queries for a conditional Bernstein increment — written proof

2026-10-17, BEFORE new code/execution. f:[0,1]->[epsilon,1-epsilon] is C2,
|f''|<=M, Lip(f'')<=H, with supplied rational bounds. For H=0, f is quadratic
and a finite polynomial/direct factory is preferable. Below H>0. A function
query means one exact value f at a known rational argument, not a free neural
forward or an arbitrary exact real oracle implemented by machine arithmetic.

## 1. Classical operator and the enlarged constant gap

For d=4^j>=16, x in[0,1], h=1/sqrt(d), let sigma be+1 if x<=1-2h,
otherwise-1. Put f_i=f(x+i*sigma*h),

    D_d f(x)=d*(f_0-2f_1+f_2),
    S_d f(x)=sigma*(-3f_0+4f_1-f_2)/(2h),
    b_d(x)=f(x)-q(x)D_d f(x)/[2(d-1)], q(x)=x(1-x).

The n-1 quasi-interpolant and finite-difference replacement are CLASSICAL.
By quadratic Taylor remainders, |D_d f-f''|<=H/sqrt(d) and
|S_d f-f'|<=H/d. The latter follows from
(4*H*h^3/6+8*H*h^3/6)/(2h)=H*h^2.

The classical-control analysis from A67 is restated here as a mathematical
dependency, with no runtime import: binomial approximation error is at most
11H/(30d^1.5); for n=4m and K~Hypergeom(4m,k,m),
|b_n(k/n)-E b_m(K/m)|<=241H/(630m^1.5). The proof cancels the quadratic
term using E q(K/m)=4(m-1)q(k/n)/(4m-1) and Var(K/m)=3q(k/n)/(4m-1),
then adds Taylor and finite-difference errors. These elementary moment bounds
suffice: E|K/m-k/n|<=1/(2sqrt(m)), E|K/m-k/n|^3<=m^-1.5.

Choose delta_d=2H/d^1.5, l_d=b_d-delta_d, u_d=b_d+delta_d and the first
power of4 d0>=16 such that

    M/[8(d0-1)]+32H/[15d0^1.5]<=epsilon.

The displayed approximation/elevation bounds and
|b_d-f|<=M/[8(d-1)]+2H/[15d^1.5] give coefficient boxes and consistency.
As for the classical positive-series factory, let d_j=d0*4^j,

    w_0=1-2delta_d0, w_j=2(delta_(d_(j-1))-delta_dj), j>=1.

Preselect J with these weights independently of the input coins. Generate
d_J p-coins, k successes. At J=0 use Bernoulli(l_d0(k/d0)/w_0), needing
three f-values. At J>=1 let m=d_J/4, n=4m, x=k/n and target

    r=[b_n(x)-E b_m(K/m)+delta_m-delta_n]/w,
    w=2(delta_m-delta_n)=7H/[2m^1.5].                    (1)

The law proof telescopes to f(p), with
P(N>d_j)=4H/d_j^1.5 and E N=d0+24H/sqrt(d0). This count is independent
of the p-coin outcomes. It is larger than the tighter H-gap control; the
callback reduction is not free in input flips.

## 2. Explicit residual envelope independent of function values

At x use the m-scale stencil, set s=S_m f(x), t=D_m f(x), and f0=f(x).
Let Y=K/m, Z=Y-x, and

    R(Y)=f(Y)-f0-sZ-tZ^2/2,
    g(Y)=-R(Y)+q(Y)[D_m f(Y)-t]/[2(m-1)],
    T=q(x)[t-D_n f(x)]/[2(4m-1)].

EXACT cancellation of the quadratic moment gives

    b_n(x)-E b_m(Y)=T+E g(Y).                           (2)

Moreover Taylor plus the derivative errors gives

    |R(Y)|<=H[|Z|/m+Z^2/(2sqrt(m))+|Z|^3/6],
    |D_m f(Y)-t|<=H[|Z|+2/sqrt(m)].

Thus |g(Y)|<=H W_m(Z), where the KNOWN positive function is

    W_m(z)=|z|/m+z^2/(2sqrt(m))+|z|^3/6
                         +(|z|+2/sqrt(m))/[8(m-1)].     (3)

With nu_i=P(K=i), B=H*sum_i nu_i W_m(i/m-x) is known WITHOUT any f-values.
The first/second/third absolute moment bounds imply

    B <= [1/2+1/8+1/6+1/3]H/m^1.5=9H/[8m^1.5].        (4)

The last1/3 bounds5m/[16(m-1)] for m>=16. Also

    |T|<=3H/[16(4m-1)sqrt(m)]<=H/[21m^1.5].            (5)

Let a=delta_m-delta_n+T. Since delta_m-delta_n=7H/(4m^1.5), equations
(4)--(5) imply 0<B<min(a,w-a), uniformly over every k. No clipped or
negative probabilities are accepted. The envelope is a piecewise cubic in
i with known rational coefficients, independent of the callback values.

## 3. Sample the target coin without evaluating E b_m

Use the following standard importance/mixture identity, specialized by(2)--(5):

- With probability 2B/w, sample I with probabilities nu_i*H*W_m(i/m-x)/B,
  and return Bernoulli(1/2+g(I/m)/[2H W_m(I/m-x)]).
- Otherwise return Bernoulli((a-B)/(w-2B)).

All probabilities lie in[0,1]. Its probability of returning1 is exactly

    (a-B)/w + sum_i nu_i H W_i/w + sum_i nu_i g(i/m)/w
      =(a+E g)/w=r.

This importance/positive-envelope mechanism is CLASSICAL, not invented here.
The candidate claim is its explicit uniformly safe specialization with(3).
The six setup value calls determine s,t,D_n f(x); only the optional branch
needs three more, to determine f(Y),D_m f(Y). No query of all m+1 values is
needed. Every complete output therefore has at most NINE callback calls.
This is a deterministic cap, not a cap on source coins, auxiliary bits or
arithmetic. Endpoints can take cheaper exact shortcuts; retain those controls.

By(4), 2B/w<=9/14. A refined written expected-call bound is

    E callback calls <=3+138H/[7d0^1.5],                 (6)

because higher-level conditional expected calls are at most6+3*(9/14)=111/14,
and P(J>=1)=4H/d0^1.5. No sharing/caching discount is needed in this bound.

## 4. Comparative scope: computing a coefficient is a different operation

For m>=64 a power of4 and m<=k<=3m, the HG support is all0..m. Write
E b_m(K/m) as a linear combination of f(t/m), t=0..m, collecting repeated
stencil arguments. For every integer0<=t<sqrt(m), its coefficient is

    nu_t*[1-m*q(t/m)/(2(m-1))]>0.                       (7)

No other forward stencil reaches below sqrt(m), and backward stencils begin
above m-4sqrt(m)>=sqrt(m). For those t, the newer b_n stencil is also
disjoint: its arguments are at least1/4 in the stated k range. Consequently
an EXACT value-oracle computation of (1) must inspect at least sqrt(m)
distinct old values in the worst case. The standard indistinguishability
argument uses a sufficiently small C2,1 bump at any unread grid point, with
strict range/curvature/Lipschitz slack. This is a lower bound over the
unrestricted oracle class, NOT for a particular known spline formula, every
sampler, cached grid, derivative oracle, or every algorithm for f(p).

Our SAMPLING operation never requires the exact scalar r and has the <=9
cap instead. This is the scoped comparative consequence to audit. Direct
importance/signed-estimation methods, exact retrospective integration and
equally clever coefficient-free samplers remain mandatory strong controls.

## 5. Full arithmetic, and the limit of the current theorem

For the exact-machine specialization assume fixed D,d with rational values
f(j/n) of denominator dividing D*n^d, O(log n) bits, evaluated in polynomial
log(n) bit work. Rational fixed piecewise polynomials are examples, not the
only application or a lower bound against their analytic implementations.
The proposed arguments all have denominator dividing n=4m. W has rational
piecewise-polynomial coefficients in i with O(log m) bit sizes. Its weighted
prefix sums use C(m,i)C(3m,k-i), with consecutive rational ratio
(m-i)(k-i)/[(i+1)(3m-k+i+1)]. Classical binary splitting and fast integer
multiplication compute B and exact prefix sums in O(m polylog m) bit work.
Binary-search unranking adds logarithmic factors, using recomputation rather
than storing m separate O(m)-bit weights. Rational Bernoulli/integer rejection
charges its O(m polylog m) expected auxiliary work as well. Thus the SAME
conditional asymptotic bit-work route remains integrable against w_j=O(d_j^-1.5),
while the number of f-value calls is bounded by9.

This is a written route using quasi-linear multiplication, NOT a bound proved
for a naive Fraction prototype or Python's asymptotic multiplication. A timing
comparison must also include the tighter H-gap factory, input coins, all
preparation/unranking, callback work, RNG and memory. Unknown f values cannot
be assumed infinitely precise or free. No full-cost superiority, existing
consumer deployment, specific priority, human review or achieved goal follows
from(6)--(7) alone. First audit the finite identities and closest alternatives.
