# V12 — A competent rational angular control and matched error budgets

2026-10-12. Written BEFORE code or new measurements. Classical angular
aggregation is a control, not a claimed invention. V1--V11 and their timings
remain immutable. The operation, original-ID supports, hypotheses and
application are unchanged.

## Linear-work integer normalization

Let Z=sum_j[-a_j,a_j], for integer planar generators. Zero/rank-one cases
are exact. Let u_x=sum_j sign(a_j.x)*a_j and u_y=sum_j sign(a_j.y)*a_j,
choosing +1 for zero signs. Choose u among these two points with maximal
squared Euclidean norm. For every x in Z, |x_i|<=h_Z(e_i)<=||u||, hence
||x||<=2||u||. Set v=sum_j sign(det(u,a_j))*a_j. In rank two,
D=det(u,v)=sum_j |det(u,a_j)|>0. Both u,v belong to Z.

In coordinates x=alpha*u+beta*v, |beta|=|det(u,x)|/D<=1. Also
|alpha|*||u||<=||x||+||v||<=4||u||. Therefore for T=[u v]^-1,
diamond conv{+/-e1,+/-e2} is contained in K=T Z, and
K is contained in [-4,4]x[-1,1]. In particular
h_K(w)>=||w||_infinity and h_K(e1)+h_K(e2)<=5.

All comparisons use integer determinants, squared norms and cofactors.
No input polygon, sorting, matrix square root or real oracle is required.
Computing the two support points and v costs O(m) integer operations.

## Uniform angular aggregation, with its complete guarantee

Map each a_j by T, write h_j=r_j z_j with r_j=||h_j||_infinity and z_j
on the boundary of the unit square. Divide each of its four sides into
intervals of length 1/N, using half-open intervals and a consistent corner
rule. There are at most 8N+4 candidate buckets. Sum the ORIGINAL integer
generators in each bucket; call the output B. No generator coordinate is
rounded and original probability events are not merged by this representation.

For one bucket choose its lower endpoint z0. Each ||z_j-z0||_infinity<=1/N.
The triangle inequality gives, for every real w,

    0 <= sum_j |h_j dot w| - |sum_j h_j dot w|
       <= 2/N * sum_j r_j * ||w||_1.

Summing, sum r_j<=h_K(e1)+h_K(e2)<=5, so the loss is at most
10||w||_1/N<=20 h_K(w)/N. Consequently, for every original-coordinate
query x,

    (1-20/N) F_A(x) <= F_B(x) <= F_A(x).

Use integer cofactors (D cancels from bucket keys). Floor division determines
the bucket, in O(m) arithmetic work and O(min(m,N)) stored rows, with
polynomial bit costs. If m<=N, return the original rows EXACTLY. No N-sized
array is allocated. This classical control is competent even at extreme
precision and may beat endpoint projection on real inputs.

## Matched accumulation and routine hybrid

For the same epsilon in (0,1] and derivation compression count d>=1, set

    N = ceil(20*d*(1+epsilon)/epsilon),
    k = ceil(sqrt(d*(1+epsilon)/(16*epsilon))).

The angular loss is at most epsilon/[d*(1+epsilon)]; the endpoint loss
1/(16k^2) is bounded by the SAME number. Bernoulli gives retained factor
at least 1/(1+epsilon) after at most d compressions. Both issue the same
[L,min(1,(1+epsilon)L)] certificate. This calibrates V8's existing theorem;
the old k=ceil(sqrt(d/epsilon)) oversamples and remains valid historically.

A routine hybrid first computes the angular core with N=320k^2. If it has
at most 64k rows, return it. Otherwise apply endpoint compression to the
ORIGINAL input, not the angular result. Either branch has the endpoint's
1-1/(16k^2) guarantee and 64k-row bound. There is no double error. The hybrid
has O(m log(m+2)) worst-case arithmetic work, including a failed shortcut.
Rank zero/one and m<=k remain exact before any grid. This is an engineering
shortcut, not additional scientific novelty.

## Fair quantitative comparison

For products with n original positions and q alternatives per position,
sequential diagonal images imply angular O(n^2*q/epsilon) arithmetic work
versus endpoint O(n*q*sqrt(n/epsilon)*log(q*n/epsilon+2)). For bounded-fan-in
event forests the conservative bounds are O(H*(d/epsilon)^2) and
O(H*(d/epsilon)*log(d/epsilon+2)). Add complete input, preparation,
normalization, bit arithmetic and output costs as in V10. These are UPPER
bounds of specified algorithms, not lower bounds for all TV algorithms.
Angular already gives rational polynomial-time approximation without a
minimum mass or TV: do not claim that capability as endpoint novelty.
The candidate distinction is the sharper precision exponent, if not already
present in a closer TV antecedent. Dudley/Matousek geometry remains known.

## Prospective correctness and public functional protocol

Before the real packet: check BOTH angular and hybrid on all existing planar
families at N=21/40/80 or k=1/2/4, with all original AND retained norm
breakpoints. Check rank zero/one, near-collinearity, signs and corner ties.
Run every original-ID forest fixture/mode/tolerance and every existing product
fixture/tolerance under angular, calibrated endpoint and hybrid. Independent
enumerators provide answers. Any unexplained violation blocks the public run.

Then repeat ALL three numerical formats x BOTH tolerances of the SAME public
packet under ALL three controls, with the full original vocabulary and same
forest. Charge input/grammar/normalizer/control/core costs for every output;
record CPU and wall times, budgets and all refusals/errors. Retain inexpensive
Hellinger/range controls. No new forward, synthetic performance family,
favorable-case selection or competitive gate. These 18 rows are development
of a previously used functional audit, NOT independent performance confirmation
or native execution of Fu/Feng/ICML algorithms. Faster controls are reported.

The protocol cannot establish publication acceptance, exhaustive priority,
semantic improvement, EPIC superiority, or quantized neural-model speed.
