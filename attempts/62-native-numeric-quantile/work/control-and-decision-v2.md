# V2 — A complete BEAVER/quantile control matches the basic enclosure

2026-10-17. AFTER the source-derived codec audit, before any query solver,
weights, data rows, neural forward or competitive timing. V1 proofs are retained.

## Original antecedents read, beyond search metadata

[BEAVER2512.05439v1](https://arxiv.org/html/2512.05439v1), Definition2.2,
the explicit completion-based prefix closure in Section2.2, and Sections4.1--4.3
through Algorithm2 were read directly. The opening of4.4 was also inspected;
not every proof/experiment was reverified. It already computes deterministic
LLM satisfaction-probability bounds with prefix tries, frontiers and Max-mu/
Sample-mu refinement. Do not claim those principles as new or weaken this
control by making it rerun the encoder. Its released code has NOT been executed.
Author-hosted PDF was cached,1312426 bytes/SHA256
2bbf2e0e70f4f106e3283ae55e9ec75f3b554707a7c20820858186deec61dd09;
methods above were read in the versioned HTML, not asserted identical by hash.

[Yiu/Mamoulis/Tao2006](https://www.cs.uoi.gr/~nikos/edbt06.pdf), Section3's
node ranges and Section4.3's branch-and-bound description, Lemmas1/2 and Figure8
pseudocode read directly in extracted PDF text. It already selects quantiles
from hierarchical nodes with lower/upper value bounds and additive counts,
including pruning/rank-component heuristics. Our probability-weighted AR
frontend is different, but the generic interval/rank structure is established.
PDF444054 bytes/SHA256
2fc81dd14279217d3de765fa89a35df9739d72b26cfaa023a4fcba04bd8bb9a1.
Not a read/audit of its full experimental campaign or every extension.

## A complete analytical control for exactly the V1 CDF bounds

Use the same finite original-token tree, same conditional-row oracle, same
frontier F and SAME exact native numerical endpoint callback as V1. For t define
two predicates on valid prefixes, including the deterministic completion marker:

    H_t(p): some completed extension has f(z)<=t,
    J_t(p): some completed extension has f(z)>t.

Both are prefix-closed, exactly the completion construction BEAVER already
describes. With tight extrema they are l(p)<=t and u(p)>t respectively.
The endpoint implementation in V1 supplies those extrema, including zero and
float distinctions. Looser sound ranges can be intersected with ancestor
ranges first to preserve the required monotone/prefix-closed rejection rule;
the identical-bound calculation below uses V1's tight extrema.
Complete a fixed nine-token field with a deterministic EOS marker of weight1;
this is a mathematical encoding, not an extra model forward or native PAD edit.

Apply BEAVER's upper-bound invariant to both predicates on a SHARED original-
prefix cache/frontier. Its two upper bounds are

    UB(H_t)=sum_(l(p)<=t) w(p), UB(J_t)=sum_(u(p)>t) w(p).

By complementing the second bound, the SAME native CDF satisfies

    1-UB(J_t) = sum_(u(p)<=t)w(p) <= F_Y(t) <= UB(H_t).

These are IDENTICAL to V1 Equation2. Do not compare only with BEAVER's weaker
completed-safe-leaf lower bound: the second upper bound and complement are
available to a competent complete control. Sharing a queried prefix means one
conditional neural row, not two; its children can update both predicates.
Full-history caching preserves AR laws, whereas merging by value does not.
Use the same exploration policy if comparing certificates. The construction
does not assert that the released BEAVER API already has this numeric callback,
automatic complement or identical batching. No code/timing comparison was run.

The threshold-independent pair of weighted endpoint distributions retains all
these bounds for every t. Inverting them is ordinary weighted order statistics;
Yiu et al.'s interval/count structure is an additional direct antecedent.
Replacing normalized additive counts by additive probability masses changes
the source/frontend, not this generic pruning theorem. V1's alias-zero oracle
obstruction likewise uses standard indistinguishability, not a new principle.

## Actual codec audit result and versioned runtime findings

Producer885c61471428969aebf933d164c99c8c827eee1d was committed BEFORE execution.
It validates six pinned text/JSON hashes and selected AST/config facts WITHOUT
importing or executing the third-party source. Six independently evaluated
literal-arithmetic pairs pass: two sign variants of3/10 differ by one ULP,
while two other nonzero pairs and both signed-zero pairs remain equal. Twelve
finite corner calculations pass, and the nonzero corners do not underflow.
Original token IDs and literal float hex encodings are retained. This is NOT
a native tokenizer-call/forward test, quantile implementation, or exhaustive
enumeration of every codec value. No repaired scientific failure is hidden.

Local metadata reports Transformers4.52.2, with no t5gemma entry in either local
AutoConfig/AutoModel mapping. The checkpoint card recommends4.53.2; a native
binding must use a separately pinned compatible environment, not mutate the
maintained environment silently. No new dependency environment was installed.

The OFFICIAL Transformersv4.53.2 generation/utils.py was fetched/read at
_get_logits_processor's minimum-token and sampling-warper paragraphs:
290241 bytes/SHA256
d81c40d6be84bfba3c3b242ca9dfe0c03c7380e544fcdf76bfb0259cfba7a0f6,
https://raw.githubusercontent.com/huggingface/transformers/v4.53.2/src/transformers/generation/utils.py.
Superclass top-p processing precedes return; this model appends its numeric
mask AFTER that return. Therefore card-style top-p0.95 is applied before this
numeric mask. Conditioning first would be a different law. On arbitrary
logits, pre-mask top-p could leave no allowed token; this is a THEORETICAL
possibility, not a measured checkpoint failure. Any native run needs explicit
support/FAIL semantics and must not silently swap the order. Versioned official
T5Gemma docs were also checked; that is availability, not runtime validation.

## Eight-criterion reassessment and decision

1. Real frozen numerical-model consumer identified, with original binary64
   semantics now explicit; no AR/dLLM equivalence claimed.
2. The basic deterministic prefix/CDF and interval-quantile structure has direct
   antecedents. A substantial specific own contribution has not survived yet.
3. No complete-cost advantage over shared-cache BEAVER/endpoint controls is
   proved or measured. Sampling alone is not the strongest complete control.
4. Keep V1 as a bounded correctness/contract derivation. Its same CDF certificate
   is reproduced by the analytical control, not an exclusive new guarantee.
5. Source audit PASS; no model quality/resource/cost experiment was run.
6. Native binary64/processor/cache versions require explicit binding. Neither
   a compatible module nor fewer theoretical calls establishes physical speed.
7. Complete classical control, canonical inverse CDF when allowed, cached/batched
   sampling and direct heads remain. No artificial restriction may remove them.
8. Preserve the codec audit and written bounds. Do NOT implement/promote the
   simple endpoint algorithm or initiate a neural campaign merely from them.
   A new useful difference must survive this control before expansion.

This does not prove that every native numerical readout is already solved or
that the specific integration can never help. It removes the current generic
algorithmic novelty justification. The original positive scientific goal,
substantial practical benefit, specific priority and publication remain OPEN.
