# V9 — Supervised visible-transition objective, BEFORE its prototype

2026-10-16, AFTER V8 closes negative. This does not reopen V5/V8 or authorize
training either failed Tiny-A2D initialization. PAPL already marginalizes
discarded proposals and derives planner-aware ELBOs. Jensen/teacher-forcing/
random-time estimation are CLASSICAL. No new ELBO principle is claimed.

## Eight criteria and restricted next step

1. Operation: learn a reveal policy for structured dLLM responses from correct
   original-ID serialized targets. The consumer needs a valid gradient before
   an untrained decoder happens to obtain a correct terminal reward. It does
   not substitute JSON validity or a toy task for actual semantic evaluation.
2. Difference under investigation: use the ACTUAL grammar-conditioned,
   batch-release, stopped-prefix transition likelihood in a supervised path
   bound. PAPL supplies the general antecedent; classical weighted inference
   supplies the computation. Own sufficient distinction is OPEN. Merely
   implementing this composition is not assumed to meet the scientific goal.
3. Possible benefit: one current-state head can give a supervised policy loss
   and exact policy gradient, integrating all discarded grammar proposals.
   This avoids requiring another full semantic rollout FOR THAT LOSS SAMPLE.
   It is NOT automatically a better estimator of the downstream reward gradient
   or a better learning objective than cheap supervised policy adaptation.
4. Proof: finite-path lower bound, policy-only derivative and random-time
   identity below. Differentiation does not pass through a parameter-dependent
   reference sampler. The downstream likelihood gradient is NOT identified
   with the gradient of this potentially loose bound.
5. First experiment: ONLY a minimal independent rational oracle. Enumerate
   all actual decoder paths on tiny original-ID grammars; check bound, subset
   reference support, gradients, random-time identity and EOS/aliases/fixed-ID
   progress. No pretrained forward/update or competitive timing next.
6. Full eventual cost: current and initial-feature heads, every original-V
   normalization, grammar inference, reference-mask preparation, policy and
   gradients, dataset/tokenizer preparation, updates, evaluation/I/O and
   setup/amortization. Do not call model-gradient or teacher-head work free.
7. Strong objections: plain SFT, supervised CE-trained policies (Adaptive
   Order Policies), grammar-conditioned CE/marginal policies, practical PAPL,
   position/PL/Bernoulli controls and native confidence/greedy decoders can win.
   A narrow reference path family may severely bias learning toward serial
   release. A fixed random batching reference may also impose the wrong budget.
   The policy cannot supply reasoning capacity missing from its denoiser.
8. Gaps: own meaningful distinction, useful full-cost updates, competent
   behavioral/training comparisons and independent confirmation. Any real
   consumer needs ANOTHER written frozen protocol after this small audit.
   Prior LLaDA native results20/32 are known evidence under another decoder,
   not results for this proposed consumer or a promise that it will work.

## Target law and reference paths

Use the V7 declared ideal prefix kernel K_phi(a|s), with positive proposal
weights/gates/anchor weights on its declared domain and finite progress.
Its sufficient state includes every committed original ID, explicit fixed bits
and the complete neural input configuration. In this first objective the
denoiser is FROZEN. Any precomputed root feature is a fixed exogenous feature.
Learnable parameters phi belong only to the release policy. There is no
claim that the floating implementation already supports neural-weight training.

Fix a valid target y including its true final EOS, in one declared ORIGINAL-ID
serialization. The final returned-prefix probability is

    p_phi(y) = sum_{h: terminal(h)=y} prod_t K_phi(a_t|s_t).

Other valid serializations/semantically equivalent numbers remain separate
outputs of this law. Training one serialization is not semantic-class MLE.

Define a cheap reference R(h|y), INDEPENDENT of phi and the denoiser outputs:
at state F containing only target IDs, let E be unfilled positions of y.
Select A uniformly from E; force it and independently include every other
position with gamma_m=min(1/2,1/(m-1)) for m=|E|>1. At m=1 release that
one ID. Commit only y's IDs. For a nonempty B subset E, m>1,

    R(B|F,y) = |B|/m * gamma_m^(|B|-1) * (1-gamma_m)^(m-|B|).

Every such path is compatible with y, preserves fixed IDs and ends in at
most L_y steps. Even when its EOS is revealed early, all other target IDs
are before it; the active suffix is integrated. The reference does NOT use
the target length at inference; it is a supervised/variational sampler.
No early-EOS truncation of a previously committed ID is permitted.

The reference covers multi-position releases instead of only permutations of
singletons. It still need not equal the policy posterior over target paths.
Absolute continuity R(h|y)>0 => P_phi(h,y)>0 is REQUIRED. A zero model/support
probability cannot be silently replaced with a finite training loss.

## Bound, derivative and single-state evaluation

Write P_phi(h,y)=prod_t K_phi(a_t|s_t). By Jensen and support inclusion,

    L_phi(y) := E_{h~R(.|y)}[log P_phi(h,y) - log R(h|y)]
        <= log sum_{h:R(h|y)>0} P_phi(h,y) <= log p_phi(y).

With the declared positive domain this is a finite path sum. Holding R and
the denoiser/root features fixed gives

    grad_phi L_phi(y) = E_R[sum_t grad_phi log K_phi(a_t|s_t)].

It is an unbiased gradient of THIS BOUND, not of log p_phi(y) or semantic
reward. No REINFORCE term for the fixed reference is missing. If a learned
reference is introduced later, detaching it is a different contract and must
not be justified by this statement.

Pad each reference path to L_y steps with absorbing probability1 transitions,
whose log-ratio/gradient is0. Independently choose J uniformly from0..L_y-1.
Then L_y times its J-th log-ratio (or gradient) has the above expectation.
Preparing the reference state/action uses target IDs and cheap reference draws;
it does NOT require querying the denoiser at the earlier reference states.
The current-state head is still required; a separately needed root feature
must also be computed/charged. Absorbing samples have zero contribution and
must not be discarded without the correct sampling/weighting change.

For equal reference states/actions, the visible gradient also equals the
conditional mean of the complete latent gradient under the ACTUAL policy's
posterior given that action, NOT under unconditional auxiliary proposals.
That conditional posterior may itself be costly to sample. It is a classical
identity, not evidence of a speed/variance victory over another objective.

## Interpretation and decision boundary

The variational gap can be substantial. Optimizing this loss may prefer the
reference's batching style, and accuracy alone does not establish efficiency.
The next small audit must show the mathematics is consistent before deciding
whether a distinct real consumer is worth implementing. No Tiny-A2D rescue,
new seed/temperature search, full model training or publication claim follows.
