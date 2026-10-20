# A79 — Written guarantees and their limits

These are written mathematical derivations, reviewed by independent agents and
checked on finite rational oracles. They are not Lean verification, human academic
approval, evidence of scientific priority, or measurements of a decoder.

## Contract

Let a finite acyclic positive binary sum-product circuit have exactly one
derivation for every admissible original-ID sequence x. Its weight is
`W(x) = 1_G(x) product_i w_i(x_i)`. Each position is assigned exactly once;
no rounded gate occurs twice in a derivation. Z is positive. Zero values and
constants with empty position scope remain exact.

Rounded gates are partitioned into globally ordered groups. A derivation visits
at most one gate in each group. The inputs of every gate in group g depend only
on the original inputs and earlier groups. In particular, contracting the groups
must leave an acyclic dependency graph; exclusivity alone is insufficient.

Each group has its own independent uniform variable, shared monotonically among
its gates. The p-bit format has explicit exponents and strictly positive neighbors
for every positive operation. Underflow, overflow and saturation are excluded.
The reconstruction uses an independent stream and chooses at each sum between
its **stored operands**, normalized exactly. Products visit both children.

## Executed law

For fixed arithmetic randomness define alpha_v as the stored result at v divided
by the exact operation on v's stored operands. Induction gives

\[
\widehat Z=\sum_x W(x)R_x,
\qquad R_x=\prod_{v\in\pi_x}\alpha_v.
\]

At a sum the reconstruction divides child values by their exact sum, rather
than by the rounded parent. At a product it multiplies the two conditional laws.
Another induction therefore gives precisely

\[
Q_R(x)=\frac{W(x)R_x}{\sum_y W(y)R_y}.
\]

Recomputing an exactly multiplied alternative after rounding that product during
evaluation need not have this law. Its stored rounded result must be retained or
replayed with identical arithmetic randomness. Sharing a gate across different
derivations is permitted; visiting it twice within one derivation is excluded.

## Bilateral envelope

Set u = 2^(1-p) and c = u²/[4(1+u)]. For SR between positive neighbors a <= z <= b,
with alpha = SR(z)/z,

\[
E\alpha=1,\qquad
E\alpha^{-1}=1+\frac{(z-a)(b-z)}{ab}\leq1+c.
\]

Indeed b/a <= 1+u and the numerator is at most (b-a)²/4. Conditional on earlier
groups, the thresholds in the current group are fixed. The alpha factors are
monotone in the same uniform; alpha_a and 1/alpha_b have nonpositive covariance.
Consequently E(alpha_a/alpha_b | earlier groups) <= 1+c. A factor only in the
numerator has conditional mean one; a shared identical gate cancels.

Let d(x,y) count groups where y visits a gate and x does not visit that same gate.
Reverse integration over the globally ordered groups yields

\[
E(R_x/R_y)\leq(1+c)^{d(x,y)}.
\]

If D = max d(x,y) and C = (1+c)^D, Jensen gives

\[
E\frac{R_x}{\sum_y Q(y)R_y}
\geq\frac1{\sum_y Q(y)E(R_y/R_x)}\geq C^{-1},
\]
\[
E\frac{R_x}{\sum_y Q(y)R_y}
\leq\sum_y Q(y)E(R_x/R_y)\leq C.
\]

For a normalized density in [C^-1,C], maximizing its mean absolute deviation
from one gives

\[
C^{-1}Q(x)\leq\bar Q(x)\leq CQ(x),\qquad
\operatorname{TV}(\bar Q,Q)\leq\frac{C-1}{C+1},
\quad \bar Q=E Q_R.
\]

D can conservatively be replaced by the maximum number K of rounded gates per
derivation. Common gates, including the root, need not be charged. This is
O(K u²) for small K u², without a factor 1/Z. It is a statement about the
**mean output law**, not the TV of every random table.

## A competent generic stochastic control

Second-order normalized bias does not by itself establish a substantial own
method. Suppose positive R_x satisfy E R_x = 1 and put

\[
v=\sup_x\operatorname{Var}(R_x),\qquad
w=\sup_x E R_x^{-2}-1,\qquad T=\sum_x Q(x)R_x.
\]

Centering the numerator gives
`E(R_x/T)-1 = E[(R_x-T)(T^-1-1)]`. Cauchy–Schwarz, first in the noise and then
over x, gives

\[
\operatorname{TV}(E Q_R,Q)
\leq\frac12\sqrt{
\left[\sum_xQ(x)E(R_x-T)^2\right]E(T^{-1}-1)^2}.
\]

The bracket equals `sum_x Q(x) E R_x² - E T²` and is at most v. Jensen implies
`E(T^-1-1)² <= E T^-2 - 1 <= w`. Thus

\[
\operatorname{TV}(E Q_R,Q)\leq\tfrac12\sqrt{vw}.
\]

For SR the conditional bounds
`E alpha² <= 1+u²/4` and
`E alpha^-2 <= 1+3(1+u)^4 u²/4` give

\[
v\leq(1+u^2/4)^K-1,\qquad
w\leq[1+3(1+u)^4u^2/4]^K-1.
\]

This already has order K u². Its leading constant is sqrt(3)/8; the bilateral
envelope has leading constant 1/8. The corresponding continuous precision gap is
only about 0.396 bit. At K=4096 and epsilon=1/100, the sufficient integer
precisions are 10 and 9 bits respectively. Neither statement demonstrates a
speedup, total memory reduction, or necessity against every specialized control.

## Order is sharp for this SR strategy

The following construction concerns the specified arithmetic program; it is not
a lower bound for every possible sampler. Fix p>=2, u=2^(1-p), gamma=1+u/2,
m=floor(log2(gamma^n)), N=n+m. The fixed LL(1) grammar

```text
S -> 0 A | 1 B
A -> 0 A | epsilon
B -> 1 B | epsilon
```

accepts only 0^N and 1^N at length N. Original IDs emit `0`, `1`, `#`, with `#`
rejected by the grammar. The first m rows are (1/4,1/2,1/4); the remaining n are
(gamma/4,1/4,1/2-u/8). Every row sums to one; all entries are finite dyadics.
The odds of the zero word are r=2^-m gamma^n in [1,2), so its probability q is
in [1/2,2/3). Input precision is at most p+1 significant bits.

Use a binary product tree for each word and add their roots. All conversions and
products actually receive SR. The zero word's n inexact conversions have
independent relative factors 1 +/- delta, delta=u/(2+u), equiprobably. Write their
product as L. The other word and the compensating positions use exact powers of
two. If R is the zero word's factor after the rounded products, conditional
unbiasedness and independent product subtrees imply `E(R | leaves) = L`.

For f(z)=qz/(1-q+qz), concavity yields E f(R) <= E f(L) <= q. Put s=delta²,
t=ns. Exact moments give

\[
v_L=E(L-1)^2=(1+s)^n-1\geq t,
\]
\[
h_L=E[L(L-1)^2]=(1+3s)^n-2(1+s)^n+1.
\]

The normalization identity and Cauchy–Schwarz give

\[
q-E f(R)\geq q^2(1-q)
\frac{v_L^2}{(1-q)v_L+q h_L}
\geq\frac{t}{24e^{3t}}.
\]

Here v_L,h_L <= 3t exp(3t) and q²(1-q)>=1/8. Counting the root, K=2N<=3n;
delta²>=4u²/25. If K u²<=1/4, then t<=1/32 and consequently

\[
\operatorname{TV}(\bar Q,Q)\geq K u^2/600.
\]

This and the upper bound establish worst-case order Theta(K u²) for this SR
strategy. An exact control can exploit the two-word grammar directly; the family
is not evidence of an operational advantage or natural model behavior.

## Sharing is not an accuracy dominance theorem

At p=2 take one slot, grammar `S -> a | b`, weights (5/64,7/64), and the remaining
mass on a rejected third ID. Q(a)=5/12. SR rounds the weights to (4 or 6)/64 and
(6 or 8)/64, each equiprobably. Independent uniforms give

\[
\bar Q_{ind}(a)=349/840,\quad \operatorname{TV}=1/840.
\]

One shared monotone uniform gives

\[
\bar Q_{shared}(a)=29/70,\quad \operatorname{TV}=1/420.
\]

The shared group is valid. The root's factor cancels. Thus sharing can increase
actual bias while preserving the approved envelope. Its potential gain concerns
RNG work, not uniform improvement in accuracy.

## Bit cost, scope and antecedents

A group of m thresholds needs at most ceil(log2 m)+2 uniform bits on average:
the chance a k-bit prefix leaves any threshold unresolved is at most m*2^-k.
This saves random bits, not all m threshold computations. A two-way Bernoulli
race with envelope max(a,b) realizes a/(a+b) with at most two attempts on average.
Compressed exponent shifts and lazy threshold digits avoid constructing huge
aligned integers. These are classical mechanisms, not isolated novelty claims.

For S_a additions, S_m products and J reconstruction decisions, a suitable
implementation can have expected bit cost
`O(B_input + S_a(p+E) + S_m(M(p)+E) + J(p+E))`, plus graph preparation,
group verification and output. Memory includes all rounded intermediate values,
exponents, original inputs, graph, groups and RNG state. The bound is expected;
resource limits may censor execution and must not be silently conditioned away.

Relevant primary antecedents include [Castro et al.](https://arxiv.org/html/2411.13601v2)
for SR sum-product martingales, [Agapiou et al.](https://arxiv.org/pdf/1511.06196)
for normalized-estimator bias, [ProbLP](https://arxiv.org/pdf/2103.00216) for
conditional precision, [Moniqua, supplement C](https://proceedings.mlr.press/v119/lu20a/lu20a-supp.pdf)
for shared SR, and [Saad et al.](https://people.csail.mit.edu/rinard/paper/popl20.sampling.pdf)
for random-bit-efficient sampling. The specific derivations above are not claimed
to be absent from all prior literature. Novelty and sufficient practical benefit
remain open.
