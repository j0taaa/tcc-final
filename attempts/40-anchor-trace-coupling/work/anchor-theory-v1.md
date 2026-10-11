# A40 — independent retained anchor and immutable neural trace

2026-10-11. Written BEFORE prototype or new model observations. Cache reuse,
antithetic empirical transport and conditioning are KNOWN principles.
A39's frontier is copied as a separately delimited antecedent, not re-proved
or renamed as novel theory here. Specific priority/publication remains OPEN.

## Operation and information

Fix an unchanged finite-horizon CFG-constrained dLLM decoder, deterministic
model inference and all CPU/GPU/Python/NumPy randomness from a uniform finite
source s in[M]. Let its full original result (including failure) be Z(s).
Draw an independent original anchor s0, finish it and RETAIN its output.
Record exact model inputs and original logits; freeze this trace C BEFORE
querying any subsequent helper. C may depend on the complete anchor and may
be truncated by a predeclared memory budget. It is READ-ONLY afterwards.
All anchor forwards, copies, lookup, memory and output costs are charged.

A helper generator, with its own original random tape, follows native flow
only while its next model input is present in C. At the last yield before
a miss, stop WITHOUT calling an uncached predictor. Terminal/failure events
remain outcomes. The original generator/control locals are kept unchanged.
The key k_C(s) is fixed before helpers, gold-free, from that frontier state.
For selected sources, continue the SAME generator; cache hits return clones
of the EXACT original head, misses use the unchanged actual model. Misses
are NOT inserted into C, including misses of the first selected trajectory.

Assumption: re-evaluating a model input under declared deterministic inference
has the same head; caching is semantically transparent. If this fails, refuse
the equivalence claim. A resume snapshot must include RNG and native control
state, not only the visible partial canvas. Deadlines must not change the map
according to other trajectories; native finite retry budgets are unchanged.

## Three-output corollary, conditional on any anchor trace

Apply A39's C4 equality-only kernel to FOUR distinct uniform source indices,
using k_C and adaptive three/four queries; retain its first and second chosen
original states, then finish only those two. Return Z(s0),Z(X),Z(Y).

Conditional on s0,C, both X and Y are uniform on[M] for EVERY map k_C.
The covariance theorem gives Cov(f(Z(X)),f(Z(Y)) | s0,C)<=0 for EVERY
finite real terminal score f, even if future logits differ arbitrarily.
Thus each output has the ORIGINAL decoder marginal. Moreover, X and Y
individually are independent of s0,C; the PAIR need not be.

For any Boolean terminal verifier f with original success probability p,
let c(C) be that conditional pair covariance (nonpositive). Then

  P(all three fail) = (1-p)^3 + E[1_(anchor fails)*c(C)] <= (1-p)^3.

So pass@3 is never inferior to THREE iid runs of the SAME decoder, for
EVERY verifier. Applying each score threshold proves best-score first-order
dominance. With V=Var(f(Z(s))), the mean of the three scores has variance

  V/3 + (2/9)*E[c(C)] <= V/3.

Cross-covariances with the anchor vanish by the conditional uniform marginals.
These statements do not require the prefix key to predict success or a gold
to be known. Strictness/useful magnitude depend on actual conditional classes.
The anchor is an output, not an omitted expense or an extra unnamed sample.

## Neural work, physical work and competent cache control

Let H0(s0) be the anchor's complete neural work, and H_C(s) the work to finish
original source s using the same immutable C. Helpers use ZERO uncached model
work, by construction and runtime audit. Conditional marginal linearity gives

  E total neural work = E H0(s0) + 2*E_(s0)[M^-1*sum_s H_C(s)].

This is EXACTLY an anchor plus two iid original paths with the SAME frozen
trace, assuming an identical model-input cost function. It is not equality
of physical time, observed work in one random batch, memory or dynamic-cache
work. Helper lookups, uploads, copies, dense noise/softmax and CFG checks are
extra. Same-law full-four/early/adaptive kernels have equal retained-pair law
conditional C, so omitting a helper saves its ACTUAL prefix work on a common
virtual source tape, rather than skipped probability times an iid mean.

A standard accumulating cache may compute FEWER forwards than a frozen one.
It is a mandatory strong comparator; freezing must not handicap all controls.
Uniform THREE-source sampling without replacement has only three queries,
all original marginals, and lower variance than iid for every score. Include
it; the candidate does NOT universally dominate it. Extra iid outputs, biased
novelty search, direct seed couplings and learned/informed class samplers are
also legitimate when their different output-law guarantees are declared.

The anchor already reveals information about one source's label. Therefore
A39's NO-FREE-unqueried-label query minimax theorem is NOT a lower bound for
all native algorithms using this trace. Only its universal C4 LAW is reused.
Do not claim optimal native query count or new caching/conditional-probability
principles. Before a large implementation, find a useful informative frontier
with honest all-cost controls and complete the specific literature reduction.

## JSON/DSL link and limits

Z(s) is the original native recursive-JSON output consumed by an interpreter
or verifier. The frontier can expose already fixed operator/argument choices
without evaluating more neural heads. Thus strict pass@3 or lower unbiased
score variance can help multiple attempts at tool execution/configuration.
This is a SAMPLE-SET guarantee; no pass1 improvement, automatic semantic
correctness, posterior-softmax equality, or universal latency victory follows.
If cached frontiers expose only syntax, reject this application.
