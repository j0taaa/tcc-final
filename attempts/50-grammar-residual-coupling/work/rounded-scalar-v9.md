# V9 — Exact residual outputs with bounded-precision scalar common mass

2026-10-13. Written BEFORE changing code. V8 producer2dba8da passes1,780
original word cases,90 complete channel laws,18 residual laws,432 valid
samples and12 undefined refusals. No timing or model campaign.

The2023 original [Feng/Guo/Jerrum/Wang, Section3/Lemmas3.1,3.3,3.5 and
their complete proofs](https://arxiv.org/html/2208.00740v3) already constructs
the product first-divergence proposal and precisely the acceptance function
used by V8. Turning that bounded estimator into rejection is immediate.
Neither the product sampler nor this acceptance identity is a novelty claim.
The candidate extension is the compact recursive-forest operation, its full
bit/conditional costs and a useful grammar/dLLM consumer; significance OPEN.

## 1. Why finite precision here does not change the target law

V8 exact common totals can have denominators involving many different local
normalizers. Instead round the common mass at EACH node downward to grid1/S,
and interpret the rounding as a genuine scaled submeasure, not just a root
certificate. Exact rejection uses that submeasure's actual point density.
Rounding only a root total while sampling the old common law is incorrect.

Let p_(v,t),q_(v,t) be the exact normalized alternative kernels, and let
m_t=min(p_t,q_t). Suppose each child already has a common submeasure
C_child<=min(P_child,Q_child) with mass c_child=Cint_child/S. Compute

    c_raw = sum_t m_t*product_child c_child,
    Cint_v = floor(S*c_raw), c_v=Cint_v/S,
    alpha_v = c_v/c_raw when c_raw>0, otherwise0,
    beta_(v,t)=alpha_v*m_t.

Define C_v on the alternative events by beta_t*product C_child. Its total
is EXACTLY c_v and its point density stays below both P_v and Q_v, by
induction. Common-channel conditional sampling weights are m_t*product
c_child: alpha_v cancels on normalization. The subtraction-free difference
channels use beta_t in V8's identity. Thus the actual proposal is EXACTLY
(P-C_root)/(1-c_root), and final acceptance still gives EXACT (P-Q)_+/delta.
There is no approximation of the returned law on successful unlimited runs.

## 2. Select S from an available positive lower bound, including equality

Compute BOTH exact ORIGINAL-token marginal tables with ordinary inside/outside
inference. Define ell=max_(i,v)|mu_P(i,v)-mu_Q(i,v)|. Data processing gives
ell<=delta. On the present shared-support product-conditioned family,

    ell=0  if and only if  P=Q.

Proof: if supports differ, a positive word in one and zero in the other has
a token with a zero weight in the other head; its marginal differs. On common
positive support, log(P(y)/Q(y)) is a sum of unary log ratios plus a constant.
If all marginals agree, sum_y (P(y)-Q(y))*log(P(y)/Q(y))=0. Every term is
nonnegative and strictly positive when P(y)!=Q(y); hence P=Q. This is the
classical exponential-family/Gibbs identity, not an invented identifiability
principle. The support/word-faithfulness hypotheses are essential.

For ell>0, choose a power of two S>=2D/ell, where D bounds EXPANDED selected
nodes, including empty-scope syntax, not merely compressed-DAG height.
For ell=0 the residual is undefined and the decoder's draft is retained.
Do not silently substitute a numerical near-equality test for exact zero.

The unrounded scalar overlap loses at most D/S after node rounding. Proof:
the new loss at a node is less than1/S; product loss is bounded by the sum of
child losses since common masses lie in[0,1]; sum kernels have total<=1.
Induction along expanded derivations gives that bound, independently of
sharing. Consequently, for delta>0,

    delta <= r_hat=1-c_root <= (2D+1/2)*delta,
    E[correction attempts] = r_hat/delta <= 2D+1/2.

Both zero detection and precision are polynomial-bit: a nonzero marginal
difference has denominator dividing Z_A*Z_B under integer head scaling, so
ell>=1/(Z_A*Z_B). Thus b=log2(S)=O(W+log(D+2)), not1/delta bits. All marginals,
two normalizers and that precision calculation count toward preparation.

## 3. Integer CDF construction: no growing common-total denominators

At node v let a_t,b_t be its integer A/B term masses, with totals A_v,B_v.
For a jointly positive node put M_t=min(a_t*B_v,b_t*A_v), so m_t=M_t/(A_v*B_v).
For a binary term let child grid masses be L,R. For a choice/unit leaf use
the empty product S^2. Set

    U_t=M_t*L*R  (binary),   U_t=M_t*S^2  (leaf),
    U=sum_t U_t,   Cint_v=floor(U/(A_v*B_v*S)).

Common-channel CDF weights are the nonnegative integers U_t. P-channel CDF
weights are the original a_t. If U>0, beta_t=Cint_v*S*M_t/U. Under common
denominator A_v*U*S, the difference-channel integer weights are

    branch failure: a_t*U*S - A_v*Cint_v*S^2*M_t;
    left failure:   A_v*Cint_v*S*M_t*(S-L);
    right failure:  A_v*Cint_v*M_t*L*(S-R).

The last two components apply only to binary terms. They are nonnegative
because beta_t<=m_t<=p_t. Their sum is A_v*U*(S-Cint_v), exactly the declared
difference mass times the common denominator. If U=0, C_v=0 and the difference
sampler uses P directly; it must not divide by zero. If either inside head
mass is zero, common mass is zero and unavailable P channels stay empty.

For a sampled derivation its submeasure point density is product beta_(v,t).
Its P/Q densities can instead use the original token products/root totals,
which telescope the local-kernel denominators. The final Bernoulli compares
(P(y)-Q(y))_+ with P(y)-C(y) exactly. Original IDs/aliases remain unchanged.

All stored Cint values use b bits. CDF weights use O(W+b+log(H+2)) bits,
without a factor from every preceding node's normalizer. Preparation/storage
requires O(H+nq) such operations/entries plus both exact marginal passes and
source/tokenizer/head work. Per-proposal reconstruction/product densities
cost O(D log(H+2)) arithmetic steps on polynomial-bit operands; expected
conditional correction cost is O(D^2 log(H+2)) steps, with charged RNG bits.
This is a concrete bit-cost refinement, not merely counting scalar gates.

## 4. Remaining objections and validation

Ordinary DP, local coupling, downward rounding, exponential-family identity
and rejection are antecedents. A competent combined algorithm may already
contain this result; no priority/publication claim is made. The2025 circuit
transport paper restricts couplings to a structured circuit family and
optimizes a Wasserstein-style contract; its full relevant conditions must
be compared before claiming optimal original-word agreement as a difference.

Validate each stored CDF's channel law, the actual scaled C(y), all pointwise
domination, the polynomial attempt bound, equal/tiny/singular cases, aliases,
prefixes and fixed slots using independently recognized words. Constant
small grids must be tested too: they may fail the2D+1/2 guarantee, but still
return the EXACT law if they terminate. Such losses stay recorded. Do not
choose a grid after observing timings or pretend cheaper preparation implies
a faster native EPIC/dJev. The user's complete objective stays OPEN.
