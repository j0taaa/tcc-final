# The strongest declared scalar controls need not give a near-relative audit

Written proof BEFORE its finite verification. This is an asymptotic proof
object, NOT a benchmark, model observation, replacement V25 gate or proof of
exclusive capability. The V25 independent 2x gate FAILED. No threshold is
changed, and the application remains a proposed fidelity audit, not a faster
EPIC decoder. All geometric/inequality/sampler principles are classical.

## Statement, precisely named competitors

For the SAME positive-support product law, compare ideal infinite-precision
upper bounds: Hellinger U_H=sqrt(1-BC(P,Q)^2), both chi-square bounds
U_QP=min(1,sqrt(chi^2(Q||P))/2) and U_PQ, the sharp normalized likelihood-range
upper, and sequential maximal categorical-coupling upper. Common-support and
full-support variants coincide here. Certified numerical implementations of
these bounds can only have higher uppers. These are the eight declared upper
controls of V25, NOT every conceivable scalar formula or algorithm.

For each integer m>=4, let n=m^2, delta=m^-4 and a=m^-3. There are n+1 binary
positions. At the first, P(1)=a and Q(1)=2a. At every remaining position,
P(1)=1/2 and Q(1)=1/2+delta. Every coordinate and joint event has strictly
positive rational probability. Both distributions are normalized.

Then

    a <= TV(P,Q) <= 3a,
    min(U_H,U_QP,U_PQ,U_range,U_coupling) >= 1/(2m^2).

Thus the best of these classical upper bounds divided by the actual TV is
at least m/6 = Omega(sqrt(n)). In contrast the admitted A49 theorem returns
U<= (1+epsilon)TV for EVERY input, including this family, while explicitly
paying its higher computational cost. This separates guarantees; it does
not establish universal physical acceleration.

## Proof of the TV bound

Projection onto the first coordinate gives TV>=a. Product coupling/triangle
inequality gives TV<=a+TV(P_dense,Q_dense). For the n balanced coordinates,

    chi^2(Q_dense||P_dense) = (1+4delta^2)^n-1.

The binomial expansion and binom(n,k)<=n^k imply (1+x)^n<=1/(1-nx) for
0<=nx<1. Since 4n delta^2=4/m^6<=1/2, this chi-square is at most8/m^6.
Cauchy--Schwarz therefore gives TV_dense<=sqrt(2)/m^3<2a. This proves TV<=3a.

## Proof for all declared competitors, including exact ideal controls

1. Sequential independent-coordinate coupling has upper
   1-(1-a)(1-delta)^n >= 1-(1-delta)^n. The two-term Bonferroni bound is
   n delta-binom(n,2)delta^2 >= (1/m^2)(1-1/(2m^2)) >=1/(2m^2).

2. Chi-square tensorization shows the forward chi-square is at least the
   first-coordinate value a/(1-a)>=a. The reverse is at least
   a/[2(1-2a)]>=a/2. Therefore both capped square-root upper bounds exceed
   1/(2m^2) for m>=4. Capping at1 does not violate that inequality.

3. Hellinger affinity tensorizes. Its total upper is at least the binary
   first-coordinate upper, exactly

       sqrt(a)*(sqrt(2(1-a))-sqrt(1-2a))
       = sqrt(a)/(sqrt(2(1-a))+sqrt(1-2a))
       > sqrt(a)/3 >= 1/(2m^2).

4. Let l,h be exact extrema of Q/P. Here
   l=[(1-2a)/(1-a)](1-2delta)^n and h=2(1+2delta)^n.
   In particular h>=2 and 0<l<=1. The sharp range upper is
   (1-l)(h-1)/(h-l) >= (1-l)/2. Also
   1-l>=1-(1-2delta)^n >=2/m^2-2/m^4 >=1/m^2.
   Hence the range upper is at least1/(2m^2).

All supports coincide, so support-loss corrections vanish. No approximation
of a control or resource refusal is responsible for the separation.

## Original-token JSON corollary and objections

Use a fixed recursive JSON grammar, fixed array punctuation and n+1 slots
whose distinct original tokens emit `true` and `false`. Every supported
assignment is an accepted JSON array; the valid mass is1. The byte/ID mapping
is injective, so conditioning has no effect and the same separation holds
for structured original-token head laws. These are abstract rational heads,
NOT logits obtained from a model or a claim about typical quantization.

This family is exchangeable in its last n bits: a competent binomial counter
computes its TV EXACTLY in O(n) arithmetic operations. Include that fact;
do not benchmark the general core against enumerating its 2^(n+1) words or
claim the core is the best algorithm FOR THIS FAMILY. The family only
disproves a near-relative guarantee for the explicitly named cheap bounds.
Feng/Liu/Liu2024 and Fu2026 already give general near-relative algorithms;
the comparative claim against them remains A49's quantitative upper bound.

The use is an a priori guarantee when an application requires a tight audit,
not that every dLLM needs this precision or that the added cost pays off on
V25's heads. Budgeted two-sided decisions are elementary consequences,
and require the competent lower controls described in decision-operation-v27.
This lemma may sharpen the manuscript's motivation. It does not settle
exhaustive literature priority, human review or publication acceptance.
