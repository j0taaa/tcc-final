# Candidate positive separation: adaptive finite work versus every preselected batch

2026-10-17, BEFORE code or measurements. WRITTEN mathematics, not mechanized
or independently reviewed. All A68 stopping decisions remain intact.

## 1. Contract and theorem

A source returns iid Bernoulli(p) bits, p unknown in[0,1]. Independent iid
fair bits are allowed. A *preselected batch* first chooses an integer N using
only auxiliary randomness and the known response f, consumes N source bits,
then produces a bit with any randomized rule. Computation of that rule is
unrestricted. In particular it may inspect ordering, not only the count.
Its law for N is independent of p AND of the entire source sequence. An
adaptive pilot followed by a random budget is NOT within this restricted
class. A sampler which preselects a maximum but skips unneeded source calls
is adaptive for purposes of consumed work.

Candidate theorem. There is an explicit computable f:[0,1]->(0,1) such that:

* an exact adaptive factory terminates with sup_p E_p T finite;
* its expected complete internal bit work is finite for EACH p;
* f is locally C1,1 but is not C2 in any neighbourhood of p0=1/2;
* EVERY exact preselected-batch factory for f has E N=infinity.

The last statement is NOT a lower bound for all samplers. The first two
give a positive capability, not merely an obstruction. The constructed f
is a proof object, not an independently established useful application.

## 2. Explicit finite predicates and the factory

For n>=1 set

    p_n=1/2+2^(-n-2),  L_n=n^2+4,
    M_n=4^L_n,          q_n=1/M_n.

Given a source sequence, let S_t count its first t ones. Predicate G_n is1
exactly when BOTH conditions hold:

    |S_(4^j)-4^j p_n| <= 2(j+1)2^j, 0<=j<L_n;
    |S_(M_n)-M_n p_n| <= sqrt(M_n).

Define g_n(p)=P_p(G_n=1), a finite polynomial, and

    f(p)=1/4 + (1/4) sum_(n>=1) q_n g_n(p).                 (1)

The series is uniformly convergent, with range in[1/4,1/2). To simulate it:
draw two auxiliary bits. Ticket00 returns1; tickets10/11 return0. On01,
draw n>=1 with probability2^-n by a geometric fair-bit scan. Require the
next 2L_n-n bits all to be0, stopping this ticket at its first1; a failed
ticket returns0. A passed ticket evaluates G_n, revealing source bits in
order and returning0 at the FIRST failed checkpoint. If every checkpoint
and the final test pass, return1. The weight of a reached predicate is
(1/4)2^-n 2^(-(2L_n-n))=q_n/4, proving (1) exactly. No p, floating arithmetic,
estimated probability, resampling or truncation is used.

Each selected n is finite almost surely and its predicate is finite, hence
termination is sure under the fair-bit contract. Generating the geometric
n has finite expected work. The all-zero ticket has expected inspected
length at most2 regardless of its huge potential length. Computing n^2
and its integer thresholds costs polynomially many bits in n; weighted by
2^-n this is integrable. No random real/exponential primitive is assumed.

## 3. Uniform input-call bound

Let T_n be the number of source calls for the sequential predicate. Always
T_n<=M_n. For d=|p-p_n|>0, write u=ceil(log2(1/d))>=0 and choose j*=2u+10.
Since d>=2^-u,

    2(j*+1)2^(-j*) <= d/2,
    t*=4^j* <= 2^24 d^-4.

The first inequality follows from 4u+22<=2^(u+9); the second from2^u<2/d,
with d=1 handled directly. Thresholds decrease with j. If a check at j>=j*
passes, |S_(4^j)/4^j-p|>=d/2. Hoeffding therefore bounds the survival
probability by2 exp(-4^j d^2/2). For j*>=L_n, T_n<=M_n<=t*. Otherwise the
tail-sum formula and4^(j*+s)=t*4^s give

    E_p T_n <= t* + 6 t* sum_(s>=0)4^s exp(-t*d^2*4^s/2)
             <= 10 t* <= 2^28 d^-4.                       (2)

Here t*d^2>=2; sum4^s exp(-4^s)<1 follows from4^s>=1+3s and the resulting
geometric series. The loose constant is intentional, not a timing estimate.
Together, E_p T_n<=min(M_n,2^28 d^-4).

Use disjoint open intervals I_n=(p_n-r_n,p_n+r_n), r_n=2^(-n-5). Their
adjacent radii sum is smaller than the distance between centres. For any p,
at most ONE interval contains p. Its contribution q_n E_p T_n is at most1.
For all other n, d>=r_n, so

    sum_n q_n E_p T_n
      <=1+2^28 sum_n 4^(-n^2-4) 2^(4n+20) < infinity.      (3)

This is uniform over p. Multiply by1/4 for the reached-predicate probability
in the actual factory. The bound is large but explicit; it establishes
finite versus infinite expectation, not acceptable practical constants.

## 4. Full bit work: pointwise, not uniform

Only integer counters, shifts and comparisons with the dyadic p_n are needed.
At a checkpoint compare integer-scaled counts; never evaluate a huge power
as a stored vector of M_n bits. M_n itself has2L_n+1 bits. A straightforward
implementation needs at most poly(n)(1+T_n) internal bit operations for a
reached predicate, including metadata and counters; memory is polynomial
in n plus any supplied source state. The level/ticket stage was charged above.

For p!=p0, d=|p-p_n| is bounded below for all sufficiently large n. Equation2
then bounds E_p T_n uniformly over that tail, and sum q_n poly(n) converges.
For p=p0, d=2^(-n-2), giving E_p T_n<=2^28 2^(4n+8); multiplying by q_n
and any polynomial in n remains summable. The finitely many remaining
indices have finite costs. Thus expected full bit work is finite at EVERY
p. Its bound may grow near individual p_n; a uniform bit-cost claim does
not follow. Physical cost per source call remains an explicit interface
cost, not a delay introduced to create a benchmark advantage.

## 5. A non-C2 interior response

Under p=p_n the probability of any failed preliminary checkpoint is at most

    sum_(j>=0)2 exp(-8(j+1)^2)<1/100.

Chebyshev bounds the final failure probability by1/4. Consequently
g_n(p_n)>=3/4-1/100=37/50. For h_n=4/sqrt(M_n), either side p_n+-h_n can
pass the final test only by a sample-mean deviation of at least3/sqrt(M_n).
Hoeffding gives g_n(p_n+-h_n)<=2exp(-18)<1/100. All three parameters are
in(0,1). Hence

    [q_n g_n(p_n+h_n)-2q_n g_n(p_n)+q_n g_n(p_n-h_n)]/h_n^2
       <=-1/16.                                         (4)

The actual term in f includes the additional factor1/4, so its curvature
offset is at most-1/64. We must control every OTHER term, not ignore it.

On the compact[1/4,3/4], each length-M word weight has second derivative
in absolute value at most C M^2 times that weight, for an absolute C. This
follows by differentiating p^s(1-p)^(M-s) twice and bounding each score
factor by C M. Summing only accepted words yields

    |q_j g_j''(p)| <= C M_j g_j(p).

If d_j=|p-p_j|>=2/sqrt(M_j), the final band and Hoeffding imply
g_j(p)<=2exp(-M_j d_j^2/2). Outside I_j, for all sufficiently large j,

    |q_j g_j''(p)| <= a_j
      :=2C M_j exp(-M_j r_j^2/2),      sum_j a_j<infinity. (5)

The finitely many excluded j have finite continuous polynomial derivatives
and may be bounded separately. On[1/4,p0] every term lies outside its I_j.
Thus the second-derivative series converges uniformly there and the left
second derivative of f at p0 is

    C0=(1/4)sum_j q_j g_j''(p0).

For large n the WHOLE segment[p_n-h_n,p_n+h_n] lies in I_n and outside
every I_j,j!=n. Dominated convergence using5, with fixed finite terms
handled by continuity, shows that the second divided difference of the
sum of all terms j!=n converges to C0 along these segments. Equation4
therefore gives a limsup for the divided difference of f of at most
C0-1/64. If f were C2 near p0, continuity of f'' would force those divided
differences to converge to f''(p0)=C0. Contradiction. This proves non-C2
in EVERY neighbourhood of the interior point p0.

## 6. Local C1,1, with classical stopped scores

Let H be the output bit of the adaptive algorithm and T its stopping time.
For finite m put f_m(p)=E_p[H 1_(T<=m)]. These are polynomials. Write
W_T=S_T-pT. Stopped L2/Wald identities give

    E_p W_T^2=p(1-p)E_p T,  E_p S_T=pE_p T.

Differentiation of the FINITE polynomial and positivity then bound
|f_m''(p)|<=2 E_p T/[p(1-p)], uniformly in m. On every interior compact
this is uniformly bounded by3. Also |f-f_m|<=P(T>m)<=sup_p E_p T/m.
Uniform limits of functions with uniformly bounded second derivatives
have locally Lipschitz first derivatives (integrate against test functions,
or use equicontinuity of first derivatives and the mean-value theorem).
Thus f is locally C1,1. This is the classical score/compactness argument,
not a new general differentiation principle or a claim of C2 regularity.

## 7. Obstruction for ALL fully preselected factories

Suppose a preselected factory uses N with E N<infinity. Conditional on
N=m and on exactly k ones, all input orderings have a p-independent uniform
law. Averaging the arbitrary randomized output rule over order/auxiliary
randomness gives numbers b_(m,k) in[0,1], independent of p. Its conditional
mean h_m(p)=sum_k b_(m,k) binom(m,k)p^k(1-p)^(m-k) is a Bernstein polynomial.

Differentiating the finite experiment exactly, with S~Binomial(m,p), gives

    h_m''(p)=E[b_(m,S) ((S-mp)^2/[p^2(1-p)^2]
                             - S/p^2 -(m-S)/(1-p)^2)].

Consequently |h_m''(p)|<=2m/[p(1-p)]. The first derivatives are bounded
by a compact-dependent constant times m as well. On any interior compact,
sum_m P(N=m)h_m, its first derivatives and second derivatives converge
uniformly by E N<infinity. Therefore its response is C2 there. Section5
excludes this for f. Every preselected factory for the SAME f must have
E N=infinity, irrespective of its output computation or knowledge of f.

This is a classical Bernstein derivative estimate applied to a candidate
explicit separation. Known-p access, adaptive classical controllers and
other contracts are NOT ruled out. No inference about A68's C3 functions,
general superiority over existing samplers, neural latency, specific priority,
natural application or achieved user goal is made.
