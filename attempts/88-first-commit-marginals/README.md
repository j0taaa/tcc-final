# A88 — Integrating the first commitment of one output position

2026-10-21. Operation, antecedents, proof and objections BEFORE a prototype.
This is a small candidate investigation, not a selected thesis or a reopened
A52/A65 application. No model measurement or worldwide-priority claim.

## Scientific contract

1. **Operation.** Estimate the complete categorical marginal of a designated
   output position of a positive-temperature masked decoder, allowing all
   other output positions to vary. This measures what the configured sampler
   would write, integrating its free text and reveal order. It is not the
   probability that an answer is factually correct. A fixed answer slot can
   represent classification alternatives; the full original vocabulary and
   its mass outside those alternatives must remain visible.
2. **Possible own distinction.** In sampled-token-confidence top-k decoding,
   all proposals at the observed slot that leave it masked lead to the SAME
   next canvas, conditional on proposals at the other positions. Exploit
   this coalescence to integrate all token values AND first-commit times
   using one auxiliary canvas with changing model heads. Ordinary implicit
   capture, conditional Monte Carlo and covariance identities are classical.
   Whether this specific capability is a sufficient contribution is OPEN.
3. **Benefit to verify.** A normalized unbiased vector, covariance no larger
   than sampled counts or the correct selection-aware first-commit readout.
   Strong controls can stop earlier. Therefore the necessary practical
   criterion is lower complete cost times variance, not fewer noisy samples
   at an arbitrarily equal number of full trajectories.
4. **Hypotheses/proof.** Sections below concern an explicitly configured
   monotone clean-token sampler, arbitrary changing heads and exact arithmetic.
   They need neither ideal Bayesian conditionals nor a trained extra model.
5. **Competent controls.** Counts stopped when the observed slot commits;
   selection-aware conditional readout stopped at that same first commit;
   exact small-state enumeration; root/head shortcuts, with their bias shown
   when they target another distribution. Recognize analytic special cases.
6. **Full cost.** All model calls, head projection, proposal RNG, ranking,
   full-V vector updates, copies, preparation/load, output memory and numerical
   arithmetic count. The auxiliary continuation after a hypothetical native
   commitment is extra work relative to early-stopped controls. No wall-time
   dominance follows from the covariance theorem.
7. **Fatal objections.** Known survival biasing may make the remaining
   distinction too small; the strong control may be cheaper; native heads may
   have little removable stopping-time noise. A fixed slot does not cover
   arbitrary parsed multi-token answers, EOS trimming or revisable sampling.
   Do not rescue a negative gate by changing the sampler or choosing prompts.
8. **What remains.** Independent finite oracle, specific priority audit,
   frozen complete-cost native screen and a useful general application.
   No accuracy gain, calibrated correctness, central selection or admission
   guarantee is established by this note.

## Configured sampler, not an unqualified upstream claim

The state is a token canvas and public time. Model heads and confidence scores
are deterministic functions of that state. Conditional on it, proposals at
currently eligible masked positions are independent categorical laws q_i.
The sampler selects the public number k_t of largest proposal confidences,
writes those proposals, and never revises a committed position. Unselected
proposals cannot enter self-conditioning, caches or another hidden state.

The observed position f starts masked. A public finite schedule eventually
forces every eligible position. k_t=0 is allowed. Blocks before f's block run
normally; only eligible positions compete. The statement concerns the full
canvas slot, without early EOS truncation or parsing a variable answer location.

The proposal law explicitly excludes MASK, q_i(MASK)=0, at ALL positions.
All other IDs, including EOS/PAD under the declared canvas semantics, remain.
LLaDA's upstream generate.py does not explicitly suppress MASK; therefore this
configuration is a disclosed shared policy for candidate and controls, not
literal preservation of the unmodified upstream bit-level sampler. Positive
temperature determines q; the confidence score may use the untempered head p.

Use a fixed total rank of (confidence, position priority). It resolves ties
between positions. The mathematical contract does not assume torch.topk has
that tie convention. Exact categorical laws on supplied rational heads and
ideal real-valued logits are distinct from finite CUDA/Gumbel/RNG laws. A
floating implementation must disclose numerical error and cannot call its
whole distribution bit-exact merely because the formula is exact.

## Algorithm and proof

Initialize an auxiliary canvas identical to the native initial canvas,
Y=0 in R^V and W=1. Keep f masked in that auxiliary canvas.

At an eligible step, obtain the current heads and sample proposals Z only
at the other masked positions. If 0<k_t<=number of those free positions,
let h be their k_t-th largest rank. Define, for every original token v,

    a_t(v) = q_f(v) * 1[rank_f(v) > h],
    A_t = sum_v a_t(v),
    b_t = 1-A_t.

Add W*a_t to Y, multiply W by b_t and commit the top k_t FREE proposals
in the auxiliary canvas, leaving f masked. With k_t=0, set a_t=0,b_t=1
and take the ordinary zero-progress step. If k_t exceeds the number of free
positions, f must be selected: add W*q_f to Y and stop. If W=0, stop.

For a fixed set of free proposals, a native draw at f either commits v
with probability a_t(v), or fails to select f with probability b_t. In
the latter event, its particular proposal has NO effect on the next state:
exactly the top k_t free proposals are committed. If H_v(s) denotes the
native probability of eventually writing v at f, this gives the recursion

    H_v(s) = E_Z[a_t(v) + b_t H_v(s_free(Z))].             (1)

It is valid for arbitrary heads at later canvases, not only fixed-context
heads. Iterating (1) proves

    E[Y_v] = Pr_native[X_f=v].                            (2)

On every auxiliary path, sum_v a_t(v)=1-b_t. Thus the deposited mass is
W_old-W_new. The forced last step deposits all remaining W, so

    Y_v >= 0,                 sum_v Y_v = 1.              (3)

No omitted tail or post-hoc renormalization is used.

For the stronger covariance statement, presample all free-proposal uniforms
along the auxiliary canvas. Couple a native execution to those uniforms
until f first commits. Its conditional probability of committing at step t
is W_(t-1) A_t, and its conditional token law there is

    R_t(v) = a_t(v)/A_t    when A_t>0.

At a forced step R_t=q_f. Sampling only that first-commit time and returning
R_t is the competent early-stopped selection-aware readout R. It is not the
unfiltered q_f at the selected step. Conditional on the entire auxiliary
free trajectory Z*, both R and a sampled native one-hot vector have mean Y.
The law of total covariance therefore proves

    Cov(Y) <= Cov(R) <= diag(mu)-mu*mu^T,                 (4)
    mu = Pr_native[X_f=·],

in positive-semidefinite order. The second inequality conditions on the
native first-commit information before drawing its token. For N independent
replicas, divide all covariances by N.

In particular, for every token utility g, Y·g is unbiased and has no greater
variance than either control's corresponding readout. For the entire
categorical distribution, the exact reduction in mean squared estimation
error against N sampled one-hot counts is

    (1/N) * E[1-||Y||_2^2].                              (5)

This is precision of a sampler-probability estimate, not improved answer
accuracy or calibrated factual confidence. The covariance reductions are
classical consequences of the specific valid coupling, not new general
Rao-Blackwell theorems. No such guarantee is inferred for termwise sums
that lack this coupling.

## Nontrivial finite possibility, not a model result

Take two independent binary positions, one token committed per step. At f,
q=p=(9/10,1/10). At the other position q=p=(1/2,1/2), unchanged after any
commitment. The native f marginal is (99/100,1/100): the first f proposal A
wins immediately, whereas B loses and f is sampled afresh at the next step.
The root head (9/10,1/10) is a different quantity even with consistent heads.

The candidate returns (99/100,1/100) deterministically in two calls. The
selection-aware early readout returns probability of B equal to 0 with
probability 9/10 or 1/10 with probability 1/10. Its variance is 9/10000
and its expected call count is 11/10. Counts have variance 99/10000.
Thus a useful cost-times-variance gain is POSSIBLE against those controls.
Recognizing the invariant-head special case is a stronger analytic control;
this example is not evidence of superiority to all algorithms or of native
model benefit.

## Antecedents and the actual remaining distinction

- [Who Gets Unmasked?, 2610.24795](https://arxiv.org/html/2610.24795),
  Lemma 1 and its proof, already expose sampled-token selection bias and a
  survival-weighted sum under a fixed-context fork. Its Fork-First method
  changes generation. Discovery of peeking or that identity is not ours.
- [DUEL, 2603.01367](https://arxiv.org/html/2603.01367), Sections 3-4,
  gives likelihoods for deterministic position choices before token draws.
  This is a different policy and estimand, not a failure of DUEL's theorem.
- [PAPL, 2509.23405](https://arxiv.org/html/2509.23405), Sections 3.1-3.4
  and A.4.1, already marginalizes discarded proposals in a transition.
  A52 investigates that operation; neither kernel marginalization nor its
  generic gradient identity is a new A88 claim.
- [Demystifying MaskGIT, 2510.04525](https://arxiv.org/html/2510.04525),
  Section 3 and B.1-B.2/C.3-C.6, analyzes sample-then-choose and a moment
  sampler asymptotically approximating it. The scoped reading did not locate
  the above changing-head finite terminal-slot estimator.
- Implicit capture/survival biasing is established, including the
  [MCNP manual, LA-13709-M](https://mcnp.lanl.gov/pdf_files/TechReport_2000_LANL_LA-13709-M_Briesmeisterothers.pdf).
  Deposit absorbed weight and continue weighted survival is NOT new.
- [Estimating Great Expectations, 2610.11399](https://arxiv.org/html/2610.11399)
  constructs AR expectation estimators and explicitly rejects a generic
  termwise variance claim. [DiSE, 2603.02760](https://arxiv.org/html/2603.02760)
  uses regeneration as a useful confidence signal; that is not necessarily
  the same sampler's terminal marginal. Both are required comparisons within
  their actual estimands.

A88's possible specific contribution is the proof and exploitation of
single-survivor-canvas coalescence for the actual top-k post-selection law,
integrating the observed token's entire commitment time. The existing A65
last-transition numerical readout does not integrate that uncertainty and
its closed application is not being expanded. This directed reading is
evidence of a scoped difference, not proof of worldwide novelty or importance.

## Next bounded verification

First freeze an independent rational oracle before executing it. Enumerate
small COMPLETE native paths with arbitrary state-dependent heads; separately
enumerate auxiliary free paths and the conditional stopping-time readout.
Check equality of means, per-path normalization, both covariance differences,
strict quantitative example, changing heads, k=0 and forced termination,
position ties, zero probabilities and different proposal/confidence laws.
Reject MASK-support and revisable/unsupported inputs explicitly. Only then
consider a separately frozen native complete-cost necessity screen against
early-stopped selection-aware readout. Passing algebraic checks alone does
not authorize calling the user's scientific objective achieved.
