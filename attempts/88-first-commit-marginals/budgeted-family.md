# A88 — Budgeted exact feedback, before native data

2026-10-21. Addendum to the unchanged 6452120e proof. No A88 neural head has
been obtained. The family is defined NOW, rather than selecting a rescue
after observing which integration budget wins. Full integration is an
endpoint, not a requirement to waste work on a negligible remaining mass.

Stop analytic integration at a public step budget d or a stopping rule
measurable from the auxiliary prefix, for example the first W<=eta. Write
S_d for mass already deposited. From that auxiliary state, run the correct
selection-aware first-commit readout R_tail, and return

    Z_d = S_d + W_d R_tail.

For W_d=0, return S_d without another call. Public time, eligibility, full
proposal support and the clean-token/irreversible contracts are unchanged.
Conditionally on the complete auxiliary trajectory, E[Z_d]=Y. Also Z_d is
a probability vector on every execution. Iterated expectation proves the
same native terminal marginal as in the original note.

The original readout R_0, conditional on the auxiliary path, is a mixture
of first commitments before d and the conditional tail, whose mass is W_d.
Consequently its conditional covariance contains W_d Cov(R_tail), whereas
Z_d has conditional covariance W_d^2 Cov(R_tail). Total covariance gives

    Cov(Y) <= Cov(Z_d) <= Cov(R_0) <= Cov(one-hot).

For nested budgets on the same auxiliary path, repeat this mixture argument
to obtain monotone covariance reduction. No fictitious nested sigma-field
on unrelated sampled trajectories is needed. Since W_d<=1, this remains
valid for prefix-observable adaptive d. The principles are classical partial
implicit capture; the potentially own component remains the top-k
coalescence that makes the operation available for this dLLM sampler.

## Stronger finite gain and honest loss

Two positions, k=1, root q_f=(.9,.1), other position uniform in two tokens.
After the other position is written, let q_f(A)=.2 or .8 equiprobably. Then
mu_A=.95, integrated Y_A is .92 or .98, and Var(Y_A)=.0009. The early
selection-aware readout is 1 with probability .9 and .2/.8 with probability
.05 each: variance .0315. Costs without root reuse are 2 and 1.1 calls,
respectively. This demonstrates a possible variance-times-cost improvement;
arbitrary state-dependent heads are permitted, but Bayesian coherence is
not claimed for this particular table.

Root reuse must also be counted: many independent replicas share identical
initial heads. Charge one root preparation, not one per replica. As replicas
grow, incremental model-call costs in this example approach 1 and .1, so
the corresponding products become .0009 and .00315. This is still a gain,
but smaller. Actual RNG, cache and readout work are additional costs.

A coherent counterexample has joint probabilities, rows f=A/B and columns
free=0/1/2,

    ((1/2, 1/200, 1/200), (0, 49/200, 49/200)).

The integrated and early readout have exactly the same distribution:
(1,0) with probability 1/2 and (.51,.49) with probability 1/2. Expected
model-call counts without cache are 1.5 and 1.245. Thus efficiency can be
strictly worse even for coherent conditionals. Both gain and loss are
included in the independent oracle; neither selects favorable native cases.

## Additional primary precedents and consumer

[ASC-D, 2609.38931](https://arxiv.org/html/2609.38931), Sections 3-4, already
formalizes distribution-valued feedback for modal-answer identification.
Soft voting, adaptive stopping and the general statistical guarantee are
not A88 inventions. Its feedback is a conditional answer distribution; the
unfiltered head at a sampled-token-confidence commitment is generally NOT
that conditional distribution. A88 supplies candidate feedback for the
explicit post-selection sampler. Applying the existing ASC-D algorithm
would be an application, not an additional original stopping theorem.

[Answer First, Reason Later, 2608.05687](https://arxiv.org/html/2608.05687),
Section D, already uses a one-token answer slot with free reasoning and fixed
delimiters. Its 280+1-slot experiments and mostly zero-temperature setting
are NOT reproduced by a small stochastic resource qualifier. The slot
commits early in that paper, which strengthens the early-stopped controls.

## First exact oracle result

Source 6985bf05 was committed BEFORE executing

    .venv-live/bin/python attempts/88-first-commit-marginals/oracle.py --audit

All 11 fixed rational cases passed: 904 complete native leaves and 53
auxiliary leaves, two explicit unsupported-contract refusals. The oracle
checks means, per-path simplex, complete first-commit readout/cost laws,
conditional covariance identity and every principal minor of both covariance
differences. It includes changing heads, q!=p, ties in both positional orders,
zero-step and forced-all schedules, zero probabilities, quantitative gain
and coherent efficiency loss. This is finite correctness evidence, not
Lean verification, a model measurement or sufficient originality.
