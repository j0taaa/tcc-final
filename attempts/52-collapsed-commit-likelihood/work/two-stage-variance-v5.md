# V5 — Strong reverse-collapse control and bounded real-return screen

2026-10-16. Written BEFORE V5 code, new heads, labels or variance measurements.
V4 passed resources only. Its9 real forwards/32 draws remain independent
historical evidence. This note does not claim that forcing/Bernoulli/weighted
counting/conditional means are new. It authorizes a bounded necessary-condition
screen, not broad training or independent confirmation.

## Eight criteria, reassessed

1. Operation: optimize the first release of a TWO-STAGE grammatical numeric
   answer decoder. Stage1 uses V3; stage2 recomputes the frozen dLLM on the
   actually committed canvas and samples a complete grammar-conditioned word
   preserving every fixed original ID. Consumers receive complete numeric JSON.
   The training target is expected terminal numerical correctness, not validity.
2. Difference: exact visible-transition likelihood integrates the hidden word
   and anchor under a token-dependent release law. These are classical evidence
   operations. Whether this specific dLLM use is sufficiently original and
   useful is OPEN; generic RL/planners and conditional means receive no credit.
3. Choice: conditional scores can reduce variance without another reward/model
   call. A stronger cheap control integrates ONLY the anchor, BEFORE integrating
   the hidden word. Its anchor score already equals the candidate's. Beating
   the full triple on anchor noise alone therefore cannot establish useful gain.
4. Proof: V3 gives the law/gradient/covariance; reverse control is proved below.
   Terminal reward depends on the exposed action and fresh continuation noise,
   never the hidden proposal/anchor. The covariance identity still applies.
5. Experiment: ALL8 known development V4 states,16 pilot+64 evaluation draws
   each, one config. Actual next heads/continuations; labels only after the
   capture is closed. The necessary variance gate is frozen below. No input,
   seed, correctness or method selection from outcomes; no independent claim.
6. Cost: no speed claim from this screen. A zero-additional-score-cost variance
   screen is necessary for a20% cost-times-variance win against a cheaper
   control. Only if it passes may a separately frozen complete-cost comparison
   (shared/cold preparation, original-V reductions, model, continuation, scoring,
   transfers, caching and output) proceed. Its passing remains insufficient
   for training. No cached initial head is credited as a free future neural run.
7. Objections: cheaper anchor collapse, position-only/fixed-anchor policies,
   deterministic confidence/PL/native decoding, one-shot completion, conditional
   MC/ordinary evidence compilers, better baselines, ARM/relaxations, larger iid
   batches and direct supervised fine-tuning may erase the benefit. Policy
   changes require behavioral comparisons, not a same-target variance label.
8. Article gap: enough own originality, complete-cost effect, actual useful
   updates and independent confirmation. Passing this small development screen
   is not any of those claims and does not fulfill the user's scientific goal.

## Reverse collapse: a mandatory cheap classical control

Use V3 notation. Given a full word x and observed action a=(B,t_B), every
compatible anchor j in B has conditional weight

    pi_j * product_(i in B except j)g_i(t_i)
         * product_(i not in B)(1-g_i(x_i)).

The common product cancels, leaving

    rho_j = (pi_j/g_j(t_j)) / sum_(k in B)(pi_k/g_k(t_k)).

It depends ONLY on retained IDs. Thus the anchor is conditionally independent
of the hidden word given a. Let d_i(x)=1[i in B]-g_i(x_i), and let mu denote
the proposal token marginals. The conditional score given (x,a), integrating
only A, is

    weight-coordinate: 1[x_i=v]-mu_i(v)
    gate-logodds:      1[x_i=v]*(1-rho_i)*d_i(x)
    anchor-softmax:    rho_i-pi_i.

This costs O(number of active positions+|B|) AFTER the already paid sample and
sampled-token gates; it needs no filtered grammar query. Model confidence
chain rules remain required if model parameters change. Conditional averaging
this control over hidden x gives V3's fully collapsed score. For any bounded
action/fresh-continuation reward and independent state-only baseline, covariance
cannot increase at either step (ordinary conditional-variance decomposition).
The anchor block is IDENTICAL in the cheap control and full collapse, so there
is no additional anchor-gradient benefit to credit to grammar inference.

This argument strengthens the comparator; it is not a new scientific theorem.
Full-triple and the other intermediate (hidden word integrated, A retained)
remain correct, but neither replaces this cheaper control.

## Compact planner readout: classical batch preparation, not a new compiler

For fixed model c, w and planner parameters, group original IDs by their
complete DFA effect. Precompute, for each position i/class C,

    U_iC = sum_(v in C) w_iv*(1-g_iv)
    A_iC = -sum_(v in C) w_iv*g_iv*(1-g_iv)
    D_iC = -sum_(v in C) w_iv*g_iv*(1-g_iv)*log(c_iv).

For an unretained row, the filtered grammar uses U. Its class posterior nu_iC
contributes sum_C nu_iC*A_iC/U_iC to alpha_i and
sum_C nu_iC*D_iC/U_iC to beta. Zero-mass classes contribute zero. For a
retained singleton v, contributions are (1-rho_i)*(1-g_iv) and that times
log(c_iv), including the scalar-anchor derivative. Anchor score is rho-pi.
This follows by differentiating positive class sums and the ordinary partition.
The preparation remains O(nV), repeated when c or planner parameters change;
per-action readout can use compact class tables. There is no memory/head-free
training claim and no invention of expectation semirings/class sufficiency.
Generic compiled evidence inference implements the SAME arithmetic/law and
must be acknowledged, not treated as a weaker competing algorithm.

Only small independent reverse/compact-control oracles are next. Their source
and the real-screen runner/runtime/protocol must be committed BEFORE V5 heads.

## Frozen development design and necessary decision

Inputs: ALL8 consumer-inputs-v4.json questions, cached initial heads from the
complete V4 packet produced by854a733, verified by its immutable manifests.
They are KNOWN development, not independent inputs. Keep checkpoint/tokenizer,
prompt,32slots, temperature1, full original V151936, uniform anchor and
g=c/(c+.01). No tuning or parameter update. Only first-transition planner
derivatives are evaluated: alpha32, beta1, anchor logits32; backbone is frozen.

For each question, generate16 pilot and64 evaluation independent first-stage
joint draws, then a fresh continuation draw. Use root52050; SHA256 integer
seeds derived from case/phase/draw and documented before runner freeze. Sample
X, then A, then all32 gate uniforms and force A; commit the original IDs in B.
If B already covers all32 slots, the word is terminal without another head.
Otherwise make ONE model call on prompt+that canvas (the other IDs are MASK),
then complete all remaining positions using the grammatical product of that
new head with original fixed IDs clamped. Never reuse the hidden draft as the
continuation. Every fixed ID must match, including EOS/PAD/epsilon IDs.

Exact duplicate canvases may share a cached head, with full sufficient cache
keys (prompt IDs, complete canvas, model/runtime/config) and explicit hit/miss
counts. All methods receive that reuse. Different draws still use fresh suffix
sampling randomness. The head projects ALL original IDs at active positions;
fixed-position factors cancel and are set to their single original ID with
weight1. Verify tensor-index head cropping with a tiny random model first.

Cap:641 NEW pretrained forwards, including at most one warmup; at most640
continuation calls, possibly fewer by complete first actions/caching. Save ALL
projected original BF16 bits including warmup and cache misses, prompt/canvas/
active IDs, initial/full/final words, actions, anchors, seeds, statuses and
checks. No successful-only deletion or replacement. Same resource caps2GiB,
60s/query,1200s screen,2M symbolic arcs; a refusal/timeout/error remains a case
and disqualifies a passing gate. Resource-censored successes are not asserted
to preserve the ideal unconditional law. No simultaneous tests/installations.

Primary reward is exact numerical equality to the external question's answer,
not correctness of one preferred tokenization. The language remains unrestricted
JSON numbers; the verifier may NOT constrain the sampler by the label. Only
AFTER every capture record is closed, read the matching8 labels from pinned
GSM8Ktrain3101c7d5072418e28b9008a6636bde82a006892c, checking question hashes.
Record labels/provenance separately. Huge exponents/negative zero are compared
as numeric lexemes without float range/expansion caps or rejecting legal JSON.

On the SAME draws compute: full triple; cheap anchor-integrated control;
known-anchor/hidden-word-integrated control; fully collapsed score. The compact
class readout and ordinary evidence implementation must agree; no new method
claim from their equal laws. For each method, fit its own optimal scalar
state-only baseline on16 PILOT draws:

    b = sum R*||S||^2 / sum ||S||^2  (zero denominator =>0).

Evaluate64 independent draws with this fixed baseline. Also include zero
baseline and RLOO on disjoint groups of8 for EVERY control. No fitted baseline
uses its evaluated draw. Candidate uses its pilot-fitted scalar; report its
RLOO/zero variants too, without switching the primary after results.

Primary variance metric is trace of covariance of independent8-draw mean
gradients, concatenating the declared65 coordinates in their natural logit/
beta units. Compute sample covariance across the8 groups, separately per
question, then sum/64 for the equal-weight8-question mean. Do not mix raw
score variance with reward-weighted gradient variance. Report alpha/beta/
anchor blocks and all baseline variants as diagnostics. RLOO group means
include within-group dependencies; do NOT pretend each contribution is iid.

Necessary gate: all8 cases complete/correct, nonzero reward variation in at
least6/8, and candidate primary variance<=.8 times EVERY fully concluded
control/baseline aggregate, with favorable sign in at least6/8 individual
questions against the cheap anchor-integrated pilot-baseline control.
If either is zero, no strict improvement is credited. Fixed stratified
bootstrap of groups (2000 resamples, seed52051) is diagnostic uncertainty,
not an independent significance or publication gate. Do not relax any threshold
after observing labels. A negative decision ends THIS application; it does not
refute the general conditional-variance identity.

Even a pass triggers ONLY a separately frozen complete-cost comparison with
competent full/cheap-anchor/known-anchor/ordinary-evidence implementations,
state-only optimal/pilot/RLOO baselines, caching, batch preparation and first/
amortized head costs. It does not trigger training automatically. Behavioral
position-only/fixed-anchor/one-shot/native/PL/SFT controls and independent
quality assessment remain mandatory before a useful learning claim.

## New primary scopes, no broad priority claim

PUMBA (arXiv2609.37974v1), Section3.2/Table1 and AppendixC.2 setting: continuous
carries and truncated BPTT already provide temporal credit, compared with
REINFORCE/RLOO and relaxed bridges. We read those scopes plus Section3.1's
teacher-forcing/local-overfitting discussion. This is a strong alternative,
not evidence that exact discrete scores improve learning.

x-Prediction Flow (arXiv2606.29066v1), Sections3--4: continuous decoding and a
confidence/progress-conditioned Beta step policy trained with GRPO are prior.
Our visible discrete-action likelihood has another contract; generic learned
step scheduling cannot be called a contribution. Learning Unmasking Policies
2512.09106v3 Section3.2 also explicitly warns about forced-release reward
hacking. That risk remains a behavioral objection to our auxiliary-anchor law.
These readings do not establish sufficient originality for A52.
