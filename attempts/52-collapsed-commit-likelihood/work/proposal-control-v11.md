# V11 — Proposal-dependent baseline and its correct projection, BEFORE code

2026-10-16, after V10's known-data feasibility/signal passes. This is not yet
a cost/variance protocol or training authorization. Baselines, conditional
expectation, grammar intersection and score identities are CLASSICAL.
Own sufficient distinction and useful full-cost benefit remain OPEN.

## Eight criteria

1. Operation: estimate a reward gradient for a reveal policy on a FROZEN
   dLLM. The proposal word X is drawn from the current grammar posterior
   BEFORE the policy's anchor/mask. Supervised labels may define training
   baselines; they must never constrain proposal generation or inference.
2. Candidate: project a legitimate proposal-dependent baseline through the
   visible-action kernel, together with the policy score. This is a structured
   application of known control variates, NOT a new baseline/RB principle.
   PAPL's discarded-proposal marginalization remains a direct antecedent.
3. Possible benefit: use a current proposal's correctness proxy without a
   further model call, while avoiding an incorrect baseline multiplication
   after partial/full collapse. All score controls receive the same exact
   projected proxy when it is available; do not handicap them deliberately.
4. Proof: zero-mean full control, projected correction and finite-path
   identity below. They apply to policy parameters only, with frozen head/root
   features and a proposal marginal independent of those parameters. They do
   not automatically apply when training denoiser weights or V2's changed
   proposal marginal. No global numerical/native-RNG exactness claim.
5. First validation: ONLY small independent rational joint/action/path
   oracles, including a counterexample to naive multiplication after collapse,
   original-ID aliases/EOS, impossible proxy events and the covariance identity.
   No new pretrained forwards, parameter updates or favorable variance gate.
6. Costs: proxy compiler/query/gradients, original-V normalizers, all baseline
   preparation/fitting, sampling/head work, data retention, cache/I/O and
   deployment use count. A proposal reward uses an extra verifier evaluation;
   it is not free merely because it avoids a neural forward. Both fast original
   lexical/class controls and vectorized GPU implementations must be considered.
7. Objections: good state-only baselines, horizon-aware features, RLOO,
   semantic-proposal baselines and class/length partial means can remove most
   noise already. Ordinary evidence inference gives the SAME exact projection,
   not a separate variance victory. A proxy may poorly predict the future.
   Fitting baselines on the evaluation batch biases the purported gradient.
8. Gaps: useful magnitude/cost against ALL competent controls, actual updates,
   behavioral/native/supervised comparisons, own adequate originality and
   independent confirmation. No large training campaign follows from algebra
   or V10's6/16 outputs. V5/V8 remain closed and V9 remains a limited control.

## Full proposal control

At visible state s let P_s(X) be independent of learnable policy parameters
phi, and let q_phi(A,a|X,s) be the anchor/forced-mask law. Put

    L_phi(X,A,a|s)=P_s(X)q_phi(A,a|X,s),
    F=grad_phi log q_phi(A,a|X,s),
    K_phi(a|s)=sum_{X,A} L_phi(X,A,a|s),
    S=grad_phi log K_phi(a|s).

For ANY bounded proxy b_s(X) independent of phi, E[F|s,X]=0 gives

    E[b_s(X)F|s]=0.

Thus a sampled baseline using proposal correctness is legitimate for the
full score (and for the anchor-integrated score, whose conditioning retains X).
This is an input-dependent baseline, not an invented action-baseline trick.
After further collapsing X, b_s(X) times the collapsed score generally does
NOT have zero mean. Its correct projection is the VECTOR

    C(s,a)=E[b_s(X)F|s,a].

For b_s=1_{D_s}, a grammar-recognizable proxy event which is a subset of the
proposal language, define J_D(a|s)=sum_{X in D_s,A}L_phi(X,A,a|s). Then

    C(s,a)=grad_phi J_D(a|s) / K_phi(a|s).

Equivalently, if z=P(D_s|s,a),

    C = z*grad log J_D = z*S + grad z.

Subtracting ONLY z*S omits the correction and is generally biased. If J_D=0,
C=0: never divide by its logarithmic score or replace impossible events with
a fabricated positive mass. If the proxy recognizer is not known to be a
subset, use intersection with the actual grammar; a proxy-only partition
outside the proposal support is incorrect.

## Weighted-query form for V7

Use the SAME native confidences/gates/anchor weights in the base and proxy
queries; do not renormalize the head on the proxy. V7 gives K=S_ret Q/Z_s.
The retained-only anchor scalar S_ret is unchanged by restricting X, hence

    J_D=S_ret Q_D/Z_s,
    z=Q_D/Q,
    grad log J_D=grad log S_ret + grad log Q_D.

The frozen-model Z_s has no phi derivative. A deterministic proxy DFA can be
intersected with the existing grammar, or used alone when its language has
been verified to be a subset. Weighted automata/intersection are prior art.
Original IDs, tokenization aliases, empty emissions and physical EOS positions
are preserved in both queries. This is not sampling from a gold-only decoder.

For the numeric consumer, a possible cheap proxy is a REGULAR SUBSET of
equivalent spellings of its fixed integer target: arbitrary JSON whitespace,
canonical integer digits, optional zero fractional digits and zero exponent,
then closing brace/whitespace/EOS. This does not cover every correct scientific
notation (e.g.27e1 versus270). Raw semantic-proposal correctness remains a
stronger cheap full-score control. All tokenizations of a proxy byte string
and every declared empty original ID remain included; do not pick one token
segmentation and call it the whole event.

## Visible reward and finite paths

Let R be a bounded visible-action/fresh-future measurable reward, and use a
common state baseline v(s) and coefficient lambda(s), fitted independently
of evaluation trajectories. Both may use visible state/horizon/head features,
but not the current discarded proposal, current action or future reward as
an uncorrected coefficient. Stop gradients through fitted coefficients.

    G_full=(R-v(s))*F-lambda(s)*b_s(X)*F,
    G_vis =(R-v(s))*S-lambda(s)*C(s,a).

E[G_full|s,a,fresh future]=G_vis and their means agree. The standard conditional
covariance identity proves nonincrease for this MATCHED comparison. It does
not order arbitrary independently chosen baselines. The sufficient-state path
factorization in path-control-clarification-v8.md extends the same identity
to the sums on finite complete trajectories. Never discard resource failures
and claim an unconditional ideal gradient from the censored successes.

## Strong controls and next decision

Every partial-score method may subtract the SAME exact visible C, not only
the full-collapse method. Also retain raw semantic-proposal controls for the
full/anchor scores, correct conditional projections when comparing them,
zero/fitted state baselines and group-aware RLOO. State baselines should have
real head/horizon information, such as proxy mass before action, completion
progress/EOS and a greedy valid proposal reward when applicable. Include
their costs and independent fitting. Do not treat unconditional unbiasedness
alone as permission to multiply a proxy into a partially collapsed score.

The minimal rational audit comes first. If it passes, a separately frozen
ALL-old-head functionality replay can precede any larger cost/variance design.
No numerical variance win or newly trained model is asserted here.
