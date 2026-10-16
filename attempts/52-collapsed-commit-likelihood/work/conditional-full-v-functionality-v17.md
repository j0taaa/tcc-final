# V17 — Full-V conditional sampler functionality, BEFORE code/auxiliary data

2026-10-16, after V16's small rational oracles. V15 is still unfavorable/
exploratory, not relabeled or statistically refuted. No own sufficient novelty
or useful training/cost result has been established.

## Eight criteria and bounded operation

1. On ALL70 OLD V10 transitions, sample conditional discarded proposals X|B
   using the SAME original weights/gates/fixed IDs/root feature, terminal1/H_T
   and observed release. No pretrained head/model/decoder trajectory/update/
   label. These ARE new AUXILIARY words from old heads, not new forwards.
2. Standard weighted backward sampling/categorical integer CDFs/stratification.
   Exact categorical input-float tickets are classical and not new theory.
   The tractability of this particular reveal kernel is the candidate-specific
   ingredient; sufficient difference from A17/PAPL/GRAS remains unconfirmed.
3. Test functional/resource availability of preserving the FULL semantic
   proposal baseline. No measured variance, cost advantage or training yet.
4. V16 proves the ideal posterior q_B/(H_T Q_B). Small complete original-word
   laws must compare the numerical sampler with that rational reference,
   including nonuniform probabilities, aliases/EOS/fixed IDs and rare tokens.
5. First minimal offline categorical/prefix/conditional-law oracles, including
   competent correlated prefix-history sampling. Freeze runner/runtime/source/
   all old input hashes before any new real-head-derived auxiliary word.
6. Count query/backwards, original-V filtering, token CDF construction/cache,
   big-integer bits/memory/randomness, all draws/verifiers/scores/copies/I/O.
   No forward is not free. No competitive timing from this CPU functionality.
7. Classical exact/partial enumeration, class/anchor means, semantic baselines,
   regular conditional controls, iid and correlated replicas all remain
   required in a later cost study. Do not win by assuming iid is necessary.
8. Gaps remain useful full-cost variance, independent fitting/confirmation,
   actual learning/application and sufficient originality/publication. A
   functional pass never launches such a campaign automatically.

## Numerical contract, before implementation

CPU binary64 class factors/matrices/scaled backwards reuse V7's frozen
PrefixPlanner. Build retained singleton c*g and unretained c*(1-g) with the
original full-V confidence, no renormalization on observed/gold tokens. Fixed
rows remain original-ID singletons. Reject a positive native factor whose
product underflows; preserve all errors/refusals and do not censor successes.
Sampling class probabilities uses those positive binary64 backward products.

Within EACH categorical draw, convert every positive binary64 weight to an
exact dyadic integer at a common power-of-two denominator, and sample a Python
randbelow ticket with rejection. Preserve tiny positive original IDs instead
of losing them in a binary64 cumulative sum. Cache ONLY visited position/class
original-ID CDFs; inaccessible all-dead classes need no token-CDF preparation.
The outer class factors/backwards remain floating approximations. Thus exact
categorical tickets DO NOT certify the ideal whole posterior, native NumPy/
CUDA RNG law or an exactly unbiased finite-precision gradient. Compare small
complete numerical laws with Fraction and clearly retain that boundary.

Do NOT unrank a whole high-entropy word from one53-bit floating uniform:
that silently limits its support. Use fresh integer tickets per class/token
decision. The correlated control stratifies repeated decisions ONLY within
identical complete conditional-prefix histories; never merge divergent original
word prefixes merely because their lexer states agree. Split groups again by
selected class before token selection, then continue with the original word
prefix. All randomness is separate from the decoder's streams.

For a group of size k, integer categorical counts n_v and total N, use expanded
tickets[0,kN): k equal strata of width N. Draw jN+UniformInteger(0,N-1) in each,
randomly permute strata among group members, and map ticket to its category via
the cumulative counts scaled by k. Each member marginal is exactly n_v/N;
this implements ordinary stratification for ANY k, including k not dividing N.
It is not systematic sampling with one common random offset. The classical
prefix-history induction gives no larger variance than iid for any square-
integrable whole-word score under the DECLARED categorical kernels. Small
rational pair laws/negative-covariance checks must test this before real draws.

## Functionality replay to freeze after preflight

Use4 fresh iid conditional proposals plus4 prefix-history-stratified proposals
at EACH of the70 states: EXACTLY560 new auxiliary words, zero decoder words/
forwards/updates. For this first correlated test do not condition a stratum on
the old proposal; its original-word reuse optimization is not implemented.
Both methods get fresh draws, all costs retained. Separate deterministic
random.Random streams seeded by first8 SHA256 bytes little-endian of
`52170:{case}:{replica}:{step}:{method}`. Do not mutate Python/NumPy globals or
model/native future RNG. Inputs/golds were already known development data.

Preserve every word/first EOS/original ID, trace/fixed/retained IDs, semantic
verifier result, cheap/full/class/length/combined/known-anchor scores and actor
projection when available, query log mass and all preparation/CDF/bit/cache/
memory/status data. Check against frozen original action likelihood1e-7,
independent official tokenizer/json/Decimal; no statistical goodness-of-fit
claim from four samples. Each sampled prefix MUST preserve B and fixed IDs.

Caps: CPU four threads/no CUDA/no model;1200s whole/60s numeric operation;
2GiB entire-process peak RSS. ALL70*8 words must be valid with no error/refusal
for functionality. A resource failure does not trigger more questions/seeds or
relaxed criteria. All560 attempts including NOT_RUN/refusals stay. Diagnostic
time under shared host load is not competitive performance. Next after a pass
would require a separate complete-cost/variance design, not automatic training.
