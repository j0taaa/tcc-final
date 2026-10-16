# V7 — Prefix-aware anchor, written BEFORE code or neural campaign

2026-10-16. V5 remains CLOSED NEGATIVE; V6 is only an old-head contract
diagnostic. This is a new policy, not retroactive V3/V5 evidence. Forcing,
weighted automata, latent scores, conditional means and suffix stopping are
CLASSICAL. Own sufficient originality/usefulness remain OPEN. Only a minimal
independent rational oracle is justified next.

## Eight criteria

1. Operation: stopped structured responses whose original committed IDs all
   remain in the returned prefix. Release decisions should concern that prefix,
   not suffix garbage. This is an internal grammar-conditioned dLLM canvas
   operation; validity alone and stopping semantics are not the contribution.
2. Difference: the anchor's eligible set depends on latent prefix length. Its
   normalizer enters visible-action probability through a terminal-edge
   potential. Elimination is classical; a useful own consequence is unconfirmed.
3. Choice: integrating hidden prefix/length may reduce gradient noise without
   another model/reward query. Cheap anchor-only, length-only, within-class
   and combined controls below are mandatory, not just the noisy full triple.
4. Proof: law, original-ID preservation, finite progress and score identities
   below. Conditional covariance is standard. No native rounded-RNG law,
   semantic dominance or physical latency is proved.
5. First validation: independent rational full prefix/anchor/mask enumeration,
   variable eligible sets, all aliases/fixed IDs/EOT, scores and adaptive toy
   paths. No new neural head/label/update/timing campaign is authorized here.
6. Cost: full-V normalization/gates/derivatives, grammar compilation, terminal
   potentials, proposals, queries, next heads, baselines, updates, memory,
   output and batch reuse. Compact moments are not a new compiler. Every
   eventual empirical claim needs its own complete-cost source-frozen protocol.
7. Objections: ordinary evidence, small exact enumeration/conditional rewards,
   cheap partial conditional means, native confidence/PL/position-only/fixed
   anchor policies and direct SFT may win. Confidence need not mean correctness.
   The current proposal law is not the native final decoder distribution.
8. Gap: enough own originality, useful complete-cost effect, real useful
   updates and independent confirmation. Passing oracles/resources alone does
   not meet the scientific goal; V5's failed gate must not be relaxed/reopened.

## State, proposal and progress

Slots are1,...,n. State contains fixed ORIGINAL IDs F and EXPLICIT active
bits. Every fixed position must be in the eventual output prefix, including
true EOT. A valid completion's first EOT position T therefore has T>=max(F)
and literally matches every fixed ID. A fixed EOT forces T to its position.
All bytes before it satisfy the declared grammar. Unused suffix rows integrate
to1 instead of contributing model PAD probabilities. All original vocabulary
IDs/empty aliases retain their declared emissions.

If an EOT and every preceding position are fixed, return the independently
verified prefix and stop. Otherwise let P_s(X_1:T)=W(X_1:T)/Z_s be the current
normalized independent-head VALID-prefix law with those fixed-ID constraints.
Active rows use full original probabilities c; fixed factors are singleton
weights1 (their common model factors cancel). This is a current-step law,
not the native iterative model's final law.

Let I(T) be active positions<=T. It is nonempty on every feasible completion
of a nonterminal state: otherwise that prefix would already satisfy the
terminal predicate. Given X and its stop T, choose

    P(A=i|X)=u_i/H_T on I(T),
    u_i=exp(r_i)>0, H_T=sum_(j in I(T))u_j.

Force A retained, independently retain other i in I(T) with g_i(X_i) in(0,1),
and NEVER release after T. Observe only a=(B,t_B), nonempty. Discard hidden
prefix IDs, T and A. Newly fixed IDs all belong to this proposal prefix;
the same prefix remains a feasible completion after restricting
T_new>=max(F union B). Thus no fixed ID changes or can be truncated by an
earlier EOT. At least one active position becomes fixed; at most n such
transitions suffice. This is canvas progress, not a useful speed guarantee.
Drawing X first preserves the CURRENT proposal marginal; anchor independence
from X from V3 no longer holds. Future attention/temperature/release budgets
must be declared before a neural consumer, not inferred from this proof.

## Visible action partition

Set S_a=sum_(i in B)u_i/g_i(t_i). To define Q_a, sum over valid prefixes with
T>=max(F union B) matching retained IDs. Multiply W by g_i(t_i) on retained
active rows and (1-g_i(X_i)) on unretained active rows UP TO T, with an
additional terminal potential1/H_T. No gate/factor is multiplied after T.
Then

    P_s(a) = S_a * Q_a / Z_s.

Indeed a compatible anchor j contributes u_j/H_T and omits just its retained
gate; factoring the common filtered word weight and summing j gives S_a.
Impossible/nonempty-domain violations have mass0, never a finite log score.

H_t is known at each layer from the CURRENT active bits/r. Thus an ordinary
weighted grammar calculation supplies Q_a by adding1/H_t to its EOT edge and
enforcing the minimum stop layer. An accepting tail contributes identity
weight1. Before it, factors depend on active/retained status. One MUST NOT
apply filtered rows to the accepting tail. This is classical state-dependent
edge weighting/mixture elimination, not an invented parsing theorem.

## Scores

Write nu_iv=P(i<=T,X_i=v|a), an OCCUPANCY marginal whose row sum can be<1,
q_t=P(T=t|a), pi_i(t)=1[i in I(t)]u_i/H_t, and

    rho_i=1[i in B]*(u_i/g_i(t_i))/S_a.

The conditional anchor depends only on retained IDs: A is independent of
hidden X/T given a. Cheap integration of ONLY A therefore gives gate score

    1[i<=T,X_i=v]*(1-rho_i)*(1[i in B]-g_i(v))

and anchor-logit score rho_i-pi_i(T), at O(n+|B|) cost after the paid sample
and sampled-token gates. Integrating hidden prefix/T too gives

    d log P(a)/d h_iv = nu_iv*(1-rho_i)*(1[i in B]-g_i(v)),
    d log P(a)/d r_i  = rho_i-sum_t q_t*pi_i(t),

for h_iv=logit(g_iv), on active rows only. A retained row necessarily has
occupancy1 at its retained ID. Fixed-row derivatives are0. Project to alpha_i
and beta for h_iv=alpha_i+beta*log(c_iv)-log(tau). Updating model parameters
also requires TRUE confidence-softmax and proposal-normalizer derivatives;
no detached shortcut inherits these scores.

Unlike V3, pi_i(T) is random even after cheaply integrating A. This is not
permission to ignore the following still stronger controls.

## Mandatory competent partial controls

1. **Length only:** a single filtered inside pass computes q_t. Use exact
   rho_i-sum_t q_t*pi_i(t) for anchor coordinates, keep other coordinates
   sampled. This unbiased coordinatewise estimator is cheaper than a full
   outside pass and can erase the apparent anchor-block advantage.
2. **Original IDs within classes:** retain the proposal's unique full lexical
   CLASS/state path and length as auxiliary information, integrate ID aliases
   within each class. At an unretained active row/class C, conditional IDs have
   weights c_iv*(1-g_iv); alpha's mean is the prepared sum of
   -c*g*(1-g) divided by sum c*(1-g), with log(c) for beta. Retained IDs are
   already known. This is a cheap lookup after batch preparation, not a full
   outside pass. Classical class sufficiency/conditional expectation apply.
3. **Combined:** use class-conditional gate means and length-only integrated
   anchor means together. Both blocks remain unbiased, though their joint
   covariance needs its own analysis. Do not beat only a weaker full triple.
4. **Known mechanisms:** ordinary evidence computes the SAME full collapse;
   exact enumeration/continuation means, optimized scalar/zero/RLOO baselines,
   iid batching and competent behavioral policies/SFT remain controls whenever
   their contracts apply. Different policies need actual quality/cost tests.

The full collapsed score is the conditional mean of the complete score given
a. With action/fresh-future measurable rewards and a common independent
state-only baseline, the usual covariance reduction applies. It extends to
finite adaptive paths with fresh kernels and sufficient explicit state.
Mixing different coordinatewise controls or baselines does NOT automatically
give a Loewner-order claim. Only a declared metric/full-cost comparison can
establish a practical benefit.

## Small next step only

Minimal independent rational complete laws/scores, variable T/eligibility,
original IDs and the cheap class/length controls precede any further work.
Then reassess sufficient own distinction and a real stopped consumer BEFORE
large implementation/heads. A future neural protocol needs attention to
unused positions, release budget, temperature, terminal rule, all costs,
semantic controls, raw evidence and independent confirmation. No V7 code,
neural result or achieved scientific goal is established by this note.
