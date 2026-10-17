# V1 — Native numerical quantile enclosures and the complete classical control

2026-10-17. Written BEFORE a quantile solver or source-audit producer. No neural
head, runtime measurement or theorem priority claimed. This is an AR-prefix
operation, not A60's fixed finite product/DAG operation or A61's training score.

## 1. Declare the law and numerical meaning

Let a finite-depth prefix tree describe ORIGINAL allowed token sequences.
For each internal prefix p, an oracle supplies a normalized conditional law
q(a|p). It depends on the entire token history p and the fixed encoder input.
Let w(p)=product of those probabilities on its root path. Leaf z has numerical
meaning f(z). In the checkpoint candidate, f is the actual deterministic
binary64 conversion in source-audit-v1.md; mathematical decimal meaning is a
DIFFERENT operation. Signs/leading-zero/exponent-zero aliases remain paths.

Exact statements here use rational conditional weights. A runtime can declare
normalized binary32/64 weights as rationals and compute these certificates
exactly, or use outward bounds and explicit mass-conservation guards. Neither
choice by itself proves equality to a native finite-RNG categorical sampler.
Temperature, mask/top-p ordering, EOS/length and failure semantics must freeze
before runtime. An unavailable/invalid conditional law is a refusal, not zero
probability or an silently repaired distribution.

## 2. Classical frontier enclosures

A frontier F is a finite prefix antichain covering every leaf exactly once.
For each p in F, compute valid bounds

    l(p) <= f(z) <= u(p)    for every leaf z extending p.

The root is a frontier; replacing a prefix by ALL its allowed children preserves
the antichain and total mass. Parallel/original paths are not deduplicated by
f. Define endpoint distributions

    P_lo = sum_p w(p) delta_l(p),  P_hi = sum_p w(p) delta_u(p).

For the lower tau-quantile Q(tau)=inf{t:P(Y<=t)>=tau}, with tau in(0,1],

    Q_lo(tau) <= Q(tau) <= Q_hi(tau).                    (1)

Proof: couple the true leaf and its covering prefix on the same probability
space. Its lower endpoint is <=Y and its upper endpoint >=Y pointwise. Their
CDFs satisfy F_hi<=F_Y<=F_lo; invert. Refinement shrinks each interval, so
Q_lo can only increase and Q_hi can only decrease. If both equal one value,
that value is the exact lower quantile, including atoms/aliases/ties.

For a threshold t, the same frontier gives

    sum_(u(p)<=t) w(p) <= P(Y<=t) <= sum_(l(p)<=t) w(p). (2)

Use strict endpoints consistently for P(Y<t). These inequalities also allow
binary/decimal CDF searches, not just one endpoint-quantile implementation.
Outward bounds for weights give corresponding conservative sums; do not use
rounded sums as exact unit mass without proving their direction.

If a<=Q(1/2)<=b and a>0,b/a<=1+epsilon, choosing any c in[a,b] controls relative
error to the MODEL median by epsilon. If values have finite first moment,

    E|Y-c| - min_d E|Y-d| <= b-a.                      (3)

Proof: any median minimizes absolute risk; absolute loss is1-Lipschitz in its
prediction, and |c-Q|<=b-a. This is classical decision theory. It is NOT a
bound on true-label error or a calibration theorem for a misspecified model.
For nonpositive/cross-zero brackets declare an absolute criterion or refuse;
never silently use a meaningless relative ratio. Resolving a narrow bracket
does not certify that a sampled empirical median lies within it.

## 3. Complete native ranges, without assuming canonical mantissas

The candidate's fixed layout is sign, exponent-sign, r exponent digits, m
mantissa digits. A positional prefix specifies intervals of possible integer
exponents and mantissas. Once exponent sign is fixed, reverse its integer
endpoints when negative. Once output sign is fixed, reverse value endpoints
when negative. Missing sign alternatives are unions, whose min/max are taken.
Leading-zero mantissas are allowed, so the minimum can be0 even for a huge
positive exponent. Both exponent-sign spellings of0 remain separate histories.

For this checkpoint r=2,m=5; all conversions stay finite. For a fixed output
sign, native multiplication/division is monotone in nonnegative mantissa and
in exponent over[-99,99]. The range endpoints therefore occur at the extrema
of these integer intervals. Evaluate the SAME binary64 arithmetic at those
endpoints; do not round an exact-decimal minimum once and assume equivalence.
The two equal mathematical values3/10 in source-audit-v1 may be different
native float atoms. A general larger codec needs explicit overflow/underflow/
NaN status semantics and cannot inherit the r=2 finiteness argument.

## 4. Complete costs and controls

After K expanded prefixes, with token branching at mostB, there are at most
1+K(B-1)frontier entries. Computing child masses uses K conditional-row queries
(possibly batched, but charge every row), plus all endpoint work and caches.
Naively sorting endpoint masses each expansion costs O(K^2 B log(KB))total;
balanced weighted order structures or batched rebuilds are standard controls.
Binary rational weights of b bits per row and depthD give O(Db+D log B)path
mass bits before sums, up to polynomially more in the explicit explored tree.
This is an explored-tree bound, not polynomial in D for every AR model.
Charge encoder once, actual padded batch work, decoder prefixes/KV caches,
probability conversion, exact/outward arithmetic, scheduling and output.

The strongest baseline must receive the SAME endpoint computation and cache
interfaces. Best-first mass refinement, a CDF midpoint variant, exponent-first
enumeration and shared prefix batches are classical complete alternatives.
If their law/work is identical to the candidate, record equality, not a win.
A fair sampling comparator caches the encoder and batches/merges common sampled
prefixes where it actually preserves the sampler. Count independent histories,
not fictitious repeated encoders or nominal API calls. Confidence-sequence/
binomial/DKW CDF bounds are legitimate stochastic controls with explicit failure
probabilities. Their statistical guarantee differs from a deterministic bound.

## 5. Why token inverse CDF is insufficient, and a worst-case obstruction

For canonical numerals whose token-prefix cylinders are ordered, standard
arithmetic inverse CDF at one ticket tau computes the numerical quantile with
one conditional query per token. This control is mandatory when applicable.
When cylinders overlap in numerical values, token-space ticket order need not
be numerical order. Restricting the codec to canonical sequences changes P;
canonicalizing AFTER sampling preserves mathematical meaning only if the
mapping really matches the declared original f, including float differences.

A black-box obstruction prevents promising a uniformly cheap exact answer.
In a mathematical decimal codec with r exponent digits, positive exponent,
one mantissa digit0/1, choose the exponent uniformly from M=10^r values.
For every complete exponent history e set P(mantissa0|e)=1/2. Its lower
numerical median is0. If any such history is unqueried, an indistinguishable
oracle may instead assign probability0 to mantissa0 there. Then mass at0 is
1/2-1/(2M), and the lower median is strictly positive. All earlier conditionals
are unchanged. Therefore certifying the exact median0 on the first oracle
requires all M queries, even though its individual exponent prefixes are
simple. This is an elementary oracle indistinguishability argument, not a
new lower-bound principle, a bound on neural-parameter-aware algorithms or an
exponential claim for this fixed r=2 checkpoint. It uses exact compact decimal
values, not an unchecked large-exponent binary64 decoder.

## 6. Decision boundary before a solver

These proofs give correctness of a classical endpoint readout and expose
invalid shortcuts. They do not demonstrate an own new generic algorithm.
The remaining candidate is a specific complete native scientific-codec binding
with useful complete cost/certification behavior; priority and sufficient
scientific distinction need investigation. A source-derived audit is justified
to establish the actual contract. More kernels, larger trees or neural captures
are NOT triggered merely by these propositions. The positive user goal remains
OPEN, and no A60/A61 numerical/model evidence is inherited.
