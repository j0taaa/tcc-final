# V1 — finite executed proposal and exact scalar correction

Written2026-10-16 before code/timings. These are elementary/classical rejection,
max-product and interval constructions specialized to an original-token DAG.
They are not claimed as new mathematical principles.

## Target and unique traces

A finite layered deterministic graph has root s0, physical positions0..n-1,
original token ID labels and accepting terminal states. Deterministic means each
state and original ID has at most one successor; acceptance and the original-ID
word therefore determine a UNIQUE state trace. Arc labels may group token classes,
blocks and IDs using disjoint partitions. No token alias is merged as an outcome.
Fixed slots allow only their original ID, with weight1. The true language includes
JSON EOT PAD*, not surrogate whitespace. Set W(x)=product_p w[p,x_p], with finite
nonnegative binary64 input bits interpreted as rational numbers, Z=sum_valid W>0.
The target is P(x)=W(x)/Z. Row normalization cancels; ideal exp(logit) and native
Torch multinomial are different contracts.

## Fixed integer proposals: the law actually executed

For EACH categorical choice install a positive integer count vector a, totals
A=sum a, cumulative endpoints s_i. Require A<=2^41 and at most2^18 categories.
One implementation can round an approximate probability vector with B=2^40,
a_i=max(1,ceil(B*p_i)); verify bounds BEFORE sampling. Invalid/bad vectors can
use positive uniform counts or refuse. Their numerical accuracy is not trusted.
A category can be absent only if structural support proves it irrelevant; zero
original weight may retain positive proposal mass and be rejected.

Let R be uniform on integers0..2^64-1. Compute T=high64(R*A), i.e.
floor(R*A/2^64), and select the unique i with s_(i-1)<=T<s_i. Prefix sums,
comparison and high multiplication must be EXACT integers. For H=2^64:

 b_i = ceil(H*s_i/A) - ceil(H*s_(i-1)/A),   q_i=b_i/H.

Proof: preimages are the integers R in [H*s_(i-1)/A,H*s_i/A). They partition
all H source integers. This is generally NOT a_i/A (multiply-high bias).
Since each endpoint ceiling differs from its operand by a number in[0,1),
q_i >= a_i/A - 1/H >= (a_i/A)(1-A/H) >= (a_i/A)(1-2^-23)>0.
Consequently 1/q_i <= (A/a_i)/(1-2^-23). Record A and BOTH integer endpoints
for every actual draw. These suffice to reconstruct its exact density on CPU,
without an integer128 division at EVERY GPU category. A singleton choice can
be deterministic with q=1 and no random word. All draws are independent under
the fair-bit model. Real PRNGs approximate that model, as in other samplers.

## Independent max-ratio audit

For each node, outgoing edges, classes and original IDs form a deterministic
choice tree. Let q_e, q_c, q_b, q_t be its categorical laws. A class/block may
have only one child. Define its local token bound

 h_e = max_{c,b,t in e} w[p,t]/(q_c q_b q_t).

Then, backward from accepting leaves R=1 (nonaccepting R=0),

 R_s = max_{e:s->v} (h_e/q_e)*R_v.

By induction R_root=max_valid_x W(x)/Q(x), where Q is the normalized executed
proposal over accepting traces. This uses UNIQUE traces. If proposals can end
at nonaccepting leaves, assign them an explicit rejection outcome; their target
weight is0 and the same proof holds, provided target support remains covered.
No independence between different categorical tables is needed: tables are
fixed before random draws, and trace density uses the selected conditional law.

Directed rounding of nonnegative multiplies/divides/conversions yields an
upper M>=R_root. In place of exact q, use the above upper inverse bound with
g>=1/(1-2^-23). Note: the binary32 value1+2^-23 is BELOW that reciprocal;
use a genuinely upward-rounded value (e.g.1+2^-22). Integer A/a_i conversions
must round numerator UP, denominator DOWN, then divide UP. Omit factors for
singletons. Maxima are exact comparisons; no exp/log/trigonometric guarantee
is needed for the auditor. Overflow/NaN or uncovered positive support is a
refusal, never a finite certificate. Subnormals require declared non-FTZ
arithmetic; a rounded-down zero is legal for a LOWER bound only.

Separately compute L<=Z by directed-down nonnegative sum-product on original
weights. Common powers-of-two scales per layer avoid range loss and are tracked
as exact exponent integers. The SAME total scale is applied to both root bounds;
rescaling itself must be directed or exact, never assumed safe near subnormals.
No requirement says L>0 for every query; L=0 cannot certify admission. The design
may refine precision or refuse before drawing, with all preparation charged.

## Exact correction, rate, budgets and trajectory

Hold head, graph, tables and M fixed. Sample x~Q and accept with exact rational
probability a(x)=W(x)/(M Q(x)). Evaluate Q from b_i/H and W from ORIGINAL binary64
bits, not approximate class masses. The auditor ensures0<=a<=1; an observed a>1
is ERROR, not a clamp. A rational Bernoulli may use uniform integer randrange
of its denominator. Summing Q(x)a(x)=W(x)/M gives acceptance Z/M and the
accepted law W/Z. Expected trials M/Z<=M/L when L>0. The max-ratio M is the
smallest universal rejection constant for THIS fixed Q, a classical observation.
Batching is permitted only with the first accepted trial in a fixed order.

With a fixed deterministic K trials, return FAIL if none accepts. The output
subprobability is [1-(1-Z/M)^K]P and FAIL probability (1-Z/M)^K <=(1-L/M)^K.
Conditioned on successful completion of THIS frozen query the law is P. A wall
clock cutoff can depend on x/trial cost and need not preserve that conditional
law. Across adaptive dLLM queries, state-dependent failures change the success
conditioned trajectory. Under a common decoder policy and explicit ideal
coupling, the augmented execution differs with probability at most the sum of
per-query failure bounds; do not assert unconditional equality or silently retry
a new head after a finite-budget failure.

## Comparative resource consequence and open practical question

For an admitted graph, preparation/audit can use fixed-precision machine work
linear in original n*V reduction size and in the expanded graph/choice circuit
size. Exact rational weight/density evaluation touches O(n*r) selected choices
per trial (r<=4 for edge/class/block/ID), not all graph states. Finite binary64
weight products have O(n*1074) fractional bits plus bounded integer exponent
bits for finite inputs; ticket densities add at most64nr denominator bits.
Scalar products and exact Bernoulli must still pay big-integer multiplication,
GCD/division/RNG costs. No word-RAM assumption hides them.

This avoids full-graph exact rational messages. It is NOT a universal speed or
bit lower bound: lazy certified intervals, dynamic exact categorical methods,
stronger envelopes or competent GPU multiprecision may be cheaper. Independence
from small Z only follows if M/L is certified small; it is not automatic for a
poor proposal. Actual useful throughput, sufficiently specific systems novelty
and full neural benefit remain unproved/unmeasured.
