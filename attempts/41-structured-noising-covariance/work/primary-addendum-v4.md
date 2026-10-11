# Additional direct primary controls for a score operation

2026-10-11. No new neural noising scores/training have been run.

[Zhu et al., LLaDA1.5/VRPO, current v2,2025-10-12](https://arxiv.org/html/2505.19223v2):
actually read Introduction, Section3.2 and Propositions1/2, with v1 Appendix
B.1.4 for the loss/gradient time-versus-mask decomposition. Not their entire
training/appendix or a reproduction. They already analyze the ELBO preference
score, allocate Monte Carlo budget across distinct times, and reuse the same
noise for policy/reference differences. Their correlation condition matters.
A smaller variance upper bound is not actual nonlinear DPO loss/gradient
dominance. Common noise for candidate/policy differences is NOT our invention.
All matching controls must keep their actual weights and operation.

[Lee et al., parallel balanced sampling, AAAI2022 original](https://matteo.rionda.to/papers/LeeEtAl-AScalableParallelAlgorithmForBalancedSampling-AAAI.pdf):
actually read both pages. Auxiliary vectors are KNOWN on every population
unit; querying the target is expensive. Cube/stratified flight/landing and
parallel balancing are known. This differs from A39's opaque labels at
unqueried source addresses; do not erase their stronger available information.

[Roohi et al., STMC2020 original](https://lagrange.mechse.illinois.edu/pubs/RoWaWeDuVi2020/RoWaWeDuVi2020.pdf):
actually read Sections2.1--2.2/Algorithms1--2 and Theorems1/2, not the entire
experimental study. Coupled/stratified simulation of black-box paths is old;
the nonpositive-path covariance result has a stated temporal-property class.
Neither broad Monte Carlo acceleration nor path simulation is a new claim.

The source-cap frontier's interpolation is a finite-population version of
classical completeness/coefficient arguments. The Catalan increment is an
explicit projectivity calculation, not proof of publication significance.
No inaccessible Makur2026 manuscript is claimed fully audited: the author
page is public, but the2025 linked PDF still returns404, and only the older
slides/sections previously recorded were available. This remains a priority
limitation, not evidence that our result is absent from that work.

## Necessary stronger baseline before any new score experiment

For a TIME-INDEPENDENT denoiser, integrating the uniform Bernoulli mask rate
analytically gives the known mask-count objective:

 ELBO-negative = sum_(k=1)^n (1/k) E_(uniform k-subset S) sum_(i in S) NLL_i(S).

Thus k uniform in1..n and score(n/k)*sum masked NLL is an unbiased estimator
without no-mask calls or the singular uniform-time1/t weight. Beta integration
gives each subset weight1/[k*choose(n,k)]. This is a reduction to existing
discrete/count formulations, NOT a new estimator. Time-dependent denoisers
need their actual t conditional on S and are not covered by that shortcut.
Any A41 score protocol must admit this stronger baseline when applicable,
besides MIRROR, importance, analytical proxy control variates and ranked-set
sampling. Do not manufacture a victory against a uniform-time estimator with
poor or infinite second moment while withholding the known remedy.
