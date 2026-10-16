# V14 — Stronger control contract, written before variance code/data

2026-10-16, while V13's CPU functionality replay is running. No new neural
sampling, variance campaign, parameter update or performance result is defined
by this note. The mathematical identities are classical. A52's sufficient
originality, useful magnitude and complete cost remain OPEN.

## A cheap zero-mean control is available to EVERY estimator

At a fixed visible state, frozen proposal X and full policy score F, V11 gives
E[b(X)F|s]=0 for any fixed bounded semantic verifier b. This vector can be
subtracted from ANY unbiased partial or fully collapsed gradient estimator:

    G_partial = (R-v(s))*S_partial - lambda(s)*b(X)*F.

Unconditional/statewise zero mean is enough for this subtraction; it does NOT
require multiplying b(X) by S_partial. The latter is generally biased, as V11
demonstrates. The anchor-integrated score F_A retaining X also satisfies
E[F_A|s,X]=0, so b(X)*F_A is another legitimate cheap control for EVERY method.
All full/cheap/class/length/combined/known-anchor/visible methods must receive
both options, with independent coefficient fitting and verifier/score costs.
These sampled controls can reintroduce hidden noise. No blanket RB/Loewner
comparison holds between arbitrarily fitted combinations. The exact regular
proxy control C is also available to ALL methods, at its measured query cost.
Do not attribute a gain to withholding these controls from a comparator.

For finite paths, sum these statewise controls. Fixed coefficients may depend
on visible state/head/horizon and independent fit data. Martingale/tower
identities preserve zero mean. Coefficients must not depend on the current
discarded X/action/future R without another correction. Same-evaluation-batch
coefficient fitting is not an unbiased gradient estimator.

## One actual policy parameterization, before looking at variances

Avoid choosing arbitrary score coordinates after measurements. Consider this
nine-parameter actor at theta=0, conditional on a frozen head at visible s.
For original slot i on the64-slot canvas put

    x_i=(2*i+1)/64-1,
    h_i=log(max_v c_i(v))/10  (fixed slots may use0),
    m=(number of active slots in the current prefix extent)/64,
    e=1 iff the visible fixed IDs already contain true EOS.

Use the SAME frozen per-question V10 root feature a0, no re-calibration through
theta. The confidence c_i is the ORIGINAL full-V neural softmax, not the
grammar/proxy posterior. Define

    alpha_i=theta0+theta1*x_i+theta2*h_i+theta3*m+theta4*e,
    r_i=theta5*x_i+theta6*h_i+theta7*m*x_i,
    beta=exp(theta8),
    g_i(v)=sigmoid(a0+alpha_i+beta*log(c_i(v))-log(.01)),
    u_i=exp(r_i).

At zero this is EXACTLY V10's current policy. Conditional on s, features and
proposal are theta-independent, so the chain rule maps each stored alpha_i,
beta,anchor_i score to these9 actor coordinates:

    [sum alpha, sum x*alpha, sum h*alpha, m*sum alpha, e*sum alpha,
     sum x*anchor, sum h*anchor, m*sum x*anchor, beta_score].

The SAME linear map applies to projected/sampled control vectors. It changes
neither trajectories nor the target gradient. This is a written model/score
contract, not an implemented trainable actor or a claim about nonzero-theta
native logits. Any future update implementation needs independent checks and
floating-domain refusals. Learned planners/linear policies are antecedents.

## Necessary future variance protocol requirements (NOT yet a frozen campaign)

Use fresh independently seeded development rollouts from ALL eight known
questions, separate pilot fitting/evaluation, and preserve all failed paths.
Candidate versus EVERY complete control, including zero/state/horizon/RLOO,
raw semantic proposal controls above, exact regular proxy and partial means.
State features should include progress, active horizon, EOS, actual head
confidence and pre-action proxy mass. Fit the trajectory gradient's variance,
including cross-time covariances, not merely each score coordinate's variance.
RLOO groups introduce within-group dependence; compare independent group means.

Use a predeclared common actor metric, reporting gate/anchor/confidence blocks;
pilot-only fixed preconditioning may be considered but is not chosen here.
No coordinate weighting, baseline choice, question omission or threshold is
selected after evaluation. A cheap pilot-selected combination of score controls
is mandatory; do not assume one partial representation is always best.

Charge full native head/projection, grammar normalizers, verifier calls, all
query/gradient/compiler/copy/I/O work, baseline fitting and cache preparation.
A variance-only pass is a necessity screen, not a complete-cost training win.
Behavioral native/position-only/PL/one-shot/supervised alternatives and external
confirmation remain required before an application or publication claim.

DTM2604.18739v1 Sections3.1--3.2/A.3--A.4 independently confirms that conditional
control variates are already a dLLM training antecedent. It has another objective;
it neither proves this implementation's benefit nor removes its comparisons.
No human review, priority confirmation or accomplished scientific goal.
