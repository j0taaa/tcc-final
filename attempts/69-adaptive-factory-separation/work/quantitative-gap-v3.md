# V3 written candidate: sharp order of batch cost and a full-work separation

2026-10-17, AFTER V1/V2, BEFORE V3 code or checks. This independently
quantifies V2's qualitative claim using classical scores and differences.
Earlier finite oracles do NOT validate this new proof. No human review.

## 1. Operation, exact input contract and claim

Retain V1's G_n,g_n,p_n,L_n=n^2+4,M_n=4^L_n and q_n=1/M_n. Define

    f_R(p)=1/4+(1/4)sum_(n=1)^R q_n g_n(p), R>=1.

R is supplied in binary, together with the common fixed predicate program,
NOT an expanded coefficient table of degree M_R. ALL comparators know this
same representation and can compute arbitrarily. A preselected/full batch
chooses N with a p-independent law before inspecting any source bits and
consumes all N. Its output kernel is unrestricted. Adaptive pilots and
partial evaluation are outside that comparison class, as inV1/V2.

For R>=4, the candidate bounds for the optimum batch mean A_R are

    (R-3)/2048 <= A_R <= R/4,
    sup_(R,p) E_p T_R <2.                                 (1)

Thus A_R=Theta(R), while a single adaptive implementation family has constant
expected INPUT work. The constants are not claimed optimal. The lower bound
uses only the target values at5(R-3) points inside[1/4,3/4]. Exact target
equality is essential; this does not establish the same gap under a fixed
absolute approximation tolerance or machine rounding.

In the ordinary bit model, the compact finite-family implementation also
has, for each FIXED p,

    E_p internal_bit_work <= C_p+C log(R+1).                (2)

If each iid source call has finite positive mean work c(p), charged
additively, then its full expected work is at most

    2c(p)+C_p+C log(R+1),

whereas every preselected/full batch needs at least c(p)(R-3)/2048.
This gives an Omega_p(R/log(R+1)) ratio in the DECLARED oracle/bit model,
not measured wall-clock speed. Source costs may correlate with their own
output bit; iid pairs and predictability suffice for Wald. A known-p or
aggregate Binomial(N,p) oracle, shared-head batch primitive, or outcome-
dependent budget is a different contract and is NOT lower-bounded here.

The f_R are still constructed proof objects. Sufficient priority and a
natural useful application remain OPEN; no positive user-goal claim follows
from a correct mathematical separation alone.

## 2. Classical fourth-derivative bound for EVERY batch output kernel

For a batch of size m, let h_m(p) have arbitrary Bernstein coefficients
b_(m,k) in[0,1]. On I=[1/4,3/4],

    |h_m^(4)(p)| <=160 m^2.                               (3)

Self-contained score proof: on m independent p-coins put
Z_i=(X_i-p)/[p(1-p)]. The r-th derivative score of their joint probability is

    S_r=r! sum_(A subset[m],|A|=r) product_(i in A)Z_i.

Distinct products are orthogonal, since a variable appearing just once has
mean0. Hence E S_r^2=r!(m)_r/[p(1-p)]^r. For r=4, Cauchy--Schwarz and
0<=b<=1 give

    |E[b S_4]| <=sqrt(24(m)_4)/[p(1-p)]^2
               <=5m^2(16/3)^2 <160m^2.

For m<4 the derivative is0. This is a CLASSICAL score/orthogonality estimate,
not an invented Fisher-information principle. It applies to kernels which
inspect the entire word/order by averaging over orders conditional on count.

## 3. A multiscale functional charged by the batch mean

Let h_n=4/sqrt(M_n) and write

    D_n F=[F(p_n-2h_n)-4F(p_n-h_n)+6F(p_n)
                         -4F(p_n+h_n)+F(p_n+2h_n)]/h_n^2.

For n>=4 all evaluation segments lie in I. The integral representation of
the fourth difference and3, or the sum16 of the absolute stencil weights,
give, respectively,

    |D_n h_m| <=min(160 m^2 h_n^2,16/h_n^2)
               =min(2560m^2/M_n,M_n).                     (4)

The scales M_(n+1)/M_n=4^(2n+1) are at least64. Split scales at64m.
The small scales have sum M_n <=(64/63)64m. The reciprocal sum of large
scales is at most(64/63)/(64m). Therefore, for m>0,

    sum_(n>=4)|D_n h_m|
       <=(64/63)(64+40)m <128m.                          (5)

For m=0 every difference vanishes. For any preselected/full batch, averaging
over N and using a FINITE set of n thus yields

    sum_(n=4)^R |D_n f_R| <=128 E N.                      (6)

No assumption on the chosen N support, runtime of its output rule or
knowledge of f_R was made. Infinite E N makes the bound trivial, not a win
obtained by excluding an expensive complete comparator.

## 4. Separate every own peak from EVERY other polynomial term

Put F_j=q_j g_j/4. V1's elementary probability inequalities give

    g_n(p_n)>=37/50,
    g_n(p_n+-h_n)<=1/100.

The terms at p_n+-2h_n have positive coefficients and are nonnegative.
Since q_n/(4h_n^2)=1/64,

    D_n F_n >=[6(37/50)-8/100]/64=109/1600.              (7)

To control interference without asymptotic unspecified constants, use the
same disjoint I_j=(p_j-r_j,p_j+r_j),r_j=2^(-j-5). For n>=4, the WHOLE
segment[p_n-2h_n,p_n+2h_n] lies in I_n and outside every other I_j.

For j=1,2, the global bound3 gives |F_j^(4)|<=40M_j. For j>=3 outside I_j,
the final band can pass only if the empirical mean deviates from p by at
least |p-p_j|/2, because r_j sqrt(M_j)>=2. Hoeffding gives

    g_j(p)<=2 exp(-M_j r_j^2/2).

The absolute fourth derivative of any length-M word weight is at most
(4M)^4 times its weight on I: expand by Leibniz, bound falling powers by
ordinary powers and use (k/p+(M-k)/(1-p))^4<=(4M)^4. Summing accepted words,

    |F_j^(4)(p)|<=128 M_j^3 exp(-M_j r_j^2/2)
                  <=2^(6j^2+31-2^(2j^2-2j-3)) <=2^-j.    (8)

For the last inequality, at j=3 the exponential exponent512 exceeds
6j^2+j+31=88. Its successive ratio is2^(4j)>=4, whereas that quadratic
increases by a factor at most4. This proves the bound inductively for ALL
j>=3. We only used e>2 to obtain the rational power-of2 upper bound.

Consequently the sum of the absolute fourth derivatives of ALL j!=n terms
on that segment, including arbitrarily large R, is less than

    D=40(2^10+2^16)+sum_(j>=3)2^-j <2^22.

The fourth-difference integral formula therefore bounds the interference by
D h_n^2 <2^26/M_n. Since M_n>=M_4=2^40 for n>=4, this is at most2^-14.
Combining7 with109/1600-2^-14>1/16 gives

    D_n f_R >=1/16, all R>=n>=4.                         (9)

Equations6 and9 prove E N>=(R-3)/2048. The explicit fully consumed batch
fromV2 has meanR/4, giving the matching linear order. This quantitative
proof does not rely on compactness or on assuming a hypothetical limiting
factory is computable.

## 5. A constant adaptive bound, rather than V1's very loose constant

The V1 tail-sum proof actually gives E_p T_n<=min(M_n,10*4^j) whenever
the checkpoint j has relative radius2(j+1)2^-j<=|p-p_n|/2. Outside I_n choose
j=2n+20. The inequality holds even at the smallest distance r_n, since
4n+42<=2^(n+14). If that checkpoint exceeds the terminal horizon, T_n<=M_n
already implies the same upper bound. Thus outside I_n,

    q_n E_p T_n <=10*4^(-n^2+2n+16).

The first five n contribute at most5 using q_n M_n=1. Among n>=6 at most
one p lies in I_n, contributing at most1. For all remaining indices,

    sum_(n>=6)10*4^(-n^2+2n+16)
      <=(10/4^8)/(1-4^-11)<1.

The ratio bound follows from the exponent difference -2n+1<=-11. The whole
factory reaches predicate n with probability q_n/4, so its expected source
work is less than(5+1+1)/4=7/4<2, uniformly over R,p. No computation of p,
estimated stopping criterion or tailored expensive callback was used.

## 6. Complete bit work and the parameter description

Implement the finite sampler by sampling the same geometric n, then
comparing n with R BEFORE computing a huge horizon or any source query.
If n>R return0 on that ticket. Otherwise run the exact existing predicate.
All costs other than reading/comparing R are bounded by those of the
infinite algorithm, whose expected bit work is finite for each p by V1's
explicit dyadic tail argument. Reading a binary R costs O(log(R+1)); the
single comparison costs O(log(R+1)+log(n+1)), and the geometric n makes
the latter term integrable. This proves2, including parameter preparation.
No expanded degree-M_R table, source-dependent learned preprocessing or
unread unary metadata is silently provided free.

For a source with iid output/cost pairs (X_i,C_i), let c(p)=E_p C_i be finite
and positive. The event that source call i is requested depends only on
earlier pairs and auxiliary bits, so Tonelli/independence give

    E_p sum_(i<=T_R) C_i=c(p) E_p T_R.

The same identity for an independent preselected N gives c(p)E N. Source
work plus internal bit work therefore give the stated pointwise full-work
ratio. There is NO uniform-in-p constant for internal work; no fixed-R
practical crossover or physical CPU/GPU latency is inferred from big-O.

## 7. Relevance and novelty boundaries

This is a quantitative positive resource result against ALL kernels within
an explicit competing execution interface, not a timing victory over a
naive implementation. The construction uses very small high-resolution
features; ordinary finite tolerances may erase the distinction. A fair
application must justify exactness/parameter precision and an ordinary
sampling-only oracle. Stronger known-p/aggregate/batched interfaces cannot
be excluded where actually available. Other adaptive algorithms can match
or beat this program; the theorem is not superiority over all decoders.

Orthogonal scores, high-order differences, lacunary-scale sums, concentration
and early stopping are classical. HNP2011 already links positive Bernstein
series, smoothness and moment/Besov questions, and uses lacunary constructions
elsewhere; do not claim these principles or that a historical question is
still open. Specific priority of the finite all-kernel separation and a
natural external useful consequence remain to be established. The user's
goal remains OPEN; this proof alone does not license a large campaign.
