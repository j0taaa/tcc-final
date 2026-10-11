# A37: a distribution-free canonical-event guarantee

Written 2026-10-11 BEFORE implementation or new model measurements.
All probabilities here describe the COMPLETE original decoder, not one head.

## 1. Operation

Let D be an iid sampling oracle on finite original payloads with law P. It may
be a fixed-budget dLLM/CFG decoder, including its token IDs, recovery transcript
and failure statuses. Let k map each payload to a finite canonical byte string.
Equal keys MUST mean the same outcome required by the application; no gold
answer is passed to k. Every failure remains an outcome and is never filtered.

Draw a random binary hash h independently of all oracle randomness, with

    Pr_h[h(u) != h(v)] = 1/2   for every u != v.

No higher independence is required for the main bound. Freeze this hash for
one pair. Classify a full payload by h(k(payload)). Apply the barrier-three
coupling below to independent COMPLETE oracle draws. Return the literal first
payload and the literal selected second payload, never a modified answer.

Barrier-three: draw first and original-second. If their bits differ, return
them. Otherwise start height two relative to the first class. A subsequent
draw in that class increases height by one, and another decreases it by one.
Stop at zero or three; return the last draw. At an even deterministic draw
cap, return the ORIGINAL second draw instead if neither boundary was reached.

The hash can be genuinely pairwise independent, without treating a
cryptographic hash as an exact ideal random function. Inject a key u of length
l into the positive integer e(u)=2^(8l)+int_be(u). Choose independent fair
coefficients r_j and set h(u)=sum_j r_j e(u)_j mod2. Distinct encodings have
nonzero XOR, proving the displayed probability. Reveal higher coefficients
lazily, retaining all previous coefficients. Their RNG is independent of D.
Cost is linear in the largest key bit length; no global distribution is built.

## 2. Fixed-hash law and cost

Write p=P(class1), q=1-p, z=pq. For p=0 or1 three draws reach height three;
the algorithm does not know or branch on these probabilities. The formulas
below remain valid at both endpoints. For 0<p<1, after
initial bits11, repair to class0 has probability

    q^2 + q^2*z + ... = q^2/(1-z).

The only continuing two-step path from height two is a down/up pair. For00
exchange p and q. Consequently the joint bit law is

    J11=p^2-delta, J00=q^2-delta,
    J10=J01=pq+delta, delta=z^2/(1-z).

Thus BOTH marginals are original. Conditional on a class transcript, all
payloads have the independent original within-class laws; decisions inspect
only classes. Summing transcripts proves the full payload law

    Law(X,Y|h) = sum_ab J_ab (P|class a) tensor (P|class b).

Terms for empty classes have zero coefficient. This proves full marginals,
including aliases and failures, not merely rendered-text marginals. First is
retained literally. For every common square-integrable score f,

    Cov(f(X),f(Y)|h) = -delta*(E[f|1]-E[f|0])^2 <=0.

Conditional means of each returned f are always E_P f, independent of h;
therefore averaging h does not add a positive covariance term. Every verifier
has pass@2 at least iid2. This standard antithetic identity is not a new claim.

Expected full draws are3 for all p. At cap2L, L>=2,

    delta_(2L) = delta*(1-z^(L-1)),
    E N_(2L)  = 3-z^(L-1) <=3.

The same within-class argument applies to the original-second fallback.
For cap12 the relative loss is at most4^-5=1/1024. A count cap is NOT a
wall-time deadline fallback. The written guarantee assumes iid D; dependence
through shared mutable caches, other requests or adaptive wall deadlines must
not be silently admitted.

## 3. Main canonical-event bound

Suppose success is exactly k(payload)=u*, for a fixed canonical outcome u*.
Let a=P(success) in(0,1), b=1-a. This outcome is used ONLY in the proof.
For fixed h let s be the mass of the class containing u*, and t=1-s.
The success probabilities within the two classes are a/s and zero. Hence
the EXACT improvement over iid2 is

    Delta_h = delta*(a/s)^2 = a^2 F(t),
    F(t)=t^2/(1-t+t^2).

This also holds at t=0, when the fixed partition offers no gain. Balanced
differences of the random hash give E_h t=b/2 by summing all wrong-key mass.

F is NOT convex everywhere. The valid convex minorant is

    H(t)=F(t),       0<=t<=1/2;
         (4t-1)/3,  1/2<=t<=1.

Indeed F''(t)=2*(1-3t^2+t^3)/(1-t+t^2)^3>=0 on[0,1/2];
F'(1/2)=4/3, and for t>=1/2,

    F(t)-(4t-1)/3 = (1-t)*(1-2t)^2/[3*(1-t+t^2)] >=0.

Therefore H is convex and H<=F. Jensen, now applied ONLY to H, yields

    E Delta_h >= a^2 H(b/2) = a^2 b^2/(3+a^2).             (1)

Every pair of Bernoulli(a) success indicators has maximum possible pass@2
improvement over iid2 equal to min(a^2,b^2), by the Fréchet bound. Thus

    (E Delta_h)/min(a^2,b^2) >= 1/13.                       (2)

For a<=1/2, the lower ratio b^2/(3+a^2) decreases to1/13; for a>=1/2,
a^2/(3+a^2) increases from1/13. This is a guaranteed fraction of the maximum
PRESERVED-MARGINAL improvement, NOT1/13 absolute accuracy or relative speed.
At cap12, (1) is multiplied by at least1023/1024, giving fraction1023/13312.
No claim that this last conservative finite-cap constant is sharp.

## 4. Sharpness of (2) for THIS construction

Set a=1/2. Put wrong mass1/(2m) on each of m distinct keys whose hash
differences from u* are independent fair bits. An independent-label hash
supplies such keys; the linear construction also does so using zero-byte
strings of distinct lengths, whose encodings are distinct basis vectors.
Conditional on the correct bit, t=(1/(2m))*Binomial(m,1/2), so t converges
to1/4. Since F is bounded and continuous,

    E Delta_h -> (1/4)*F(1/4) =1/52.

The maximum improvement is1/4, giving ratio1/13. These are objects of proof,
not model observations or selected performance benchmarks. This proves the
uniform constant cannot be improved for this algorithm/hash family. It does
NOT establish optimality among all oracle-only couplers.

## 5. Competent theoretical controls and full cost

With the same hash, the classical bounded-four factory has delta=z^2 and
expected draws3-z (its early-stop version, not an artificially charged4).
Its canonical-event gain is a^2 E[t^2]>=a^2 b^2/4, giving uniform fraction
1/16, sharp on the same diffuse-wrong-tail limit. The ideal bound (2) is16/13
times that lower fraction, but our expected cost3 is higher than3-z. This
is not a pointwise cost domination or a23% improvement in observed accuracy.

Categorical Barker collision repair has per-wrong-key contribution
a^2 r_j^2/(a+r_j) and expected draws2.5+sum_i p_i^2/2<=3. At a=1/2 with
m equal wrong keys its gain tends tozero; its cost tends to2.625, not3.
The distinction is a nonvanishing guarantee for a canonical atom with diffuse
wrong outcomes, not a proof that a slower pair beats Barker in all uses.

If one full native draw costs c and one downstream evaluation costs v,
mean pair cost is3c+2v plus canonicalization/hash/coordination. iid2 costs
2c+2v; iid3 costs3c+3v and can achieve greater coverage if a verifier is
cheap. Probability-aware CDF coupling or no-replacement sampling can win;
no-replacement changes marginals and may be preferable anyway. A consumer
needing only correct answers is not obliged to preserve marginals.

In fact iid3 ALWAYS has higher pass coverage for the unique-outcome event,
at the same expected number of complete generations. For 0<=t<=b,
F(t)<=t*F(b)/b since F(t)/t increases up to1. Consequently

    E Delta_h <= a^2 b^2/[2*(1-a+a^2)] <= (1/2)*a*b^2,

whereas iid3 improves over iid2 by a*b^2. Thus this direction cannot be
sold as a generation-budget improvement. Evaluating only two outputs must
be a real consumer constraint, not a restriction invented for a victory.

For unbiased evaluation of the single decoder's correctness, two returned
labels have mean variance [a(1-a)-E Delta_h]/2, strictly below iid2. Large v
can make this worthwhile, but that is a FULL-cost condition to establish,
not a fabricated delay or a measured native speed gain. PPI/stratified survey
methods remain stronger controls when extra informative labels/proxies exist.

For illustration of the exact condition, put beta=a*b/(3+a^2). Ignoring NO
generation draws, but separately denoting coordination cost by d, the ideal
sampler has variance-times-cost at most

    (a*b/2)*(1-beta)*(3c+2v+d).

All fixed-count iid assessed-output means have variance-times-cost a*b*(c+v).
The bound beats them only when

    2*beta*v > (1-3*beta)*c + (1-beta)*d.

At a=1/2 and d=0 this requires v>5c, not just v>c. This is a mathematical
cost condition, NOT an observed ratio. If a known canonical gold key makes
checking cheap, this application is inappropriate; do not charge a human
label per duplicate when one query-level answer would label all duplicates.

The corollary for dLLM/CFG generation is direct: D is the complete original
decoder and k is the application-required canonical outcome. Neither its
transition probabilities nor stable next logits are needed. Grammar, original
tokens and each trajectory are preserved because outputs are original draws.
This is not an improvement to parsing, per-sample semantics, pass@1 or EPIC
latency. Novelty specific to (1)/(2) and a useful full-cost application remain
open gates; correctness alone does not complete the research goal.
