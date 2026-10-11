# Primary-source scope, 2026-10-11

These readings do not establish priority or usefulness.

- Gerber, Chopin, Whiteley, *Negative association, ordering and convergence of
  resampling methods*, v3 2020-01-17, https://arxiv.org/pdf/1707.01845.
  Actually read introduction/setup and §§3.4.2--3.4.3, Algorithm1, Corollary3,
  pp8--10, and Theorem2 in §4.1. SSP is classical pivotal/randomized rounding;
  its conditional offspring counts are negatively associated. The paper
  explicitly leaves general variance domination over multinomial open.
  This is not a theorem about averaging a uniformly sampled unknown-label
  source pool, and negative association of counts alone is not the requested
  arbitrary-score Loewner comparison. No claim about unseen appendix proofs.
- Shu Yang and Peng Ding, *Two-phase rejective sampling and its asymptotic
  properties*, https://arxiv.org/abs/2403.01477 and published
  https://academic.oup.com/jrsssb/article/87/4/957/8006592.
  Actually read abstract, review §2.1, Definition1 §§3.1--3.3 and extracted
  large-sample discussion. Their phase-II acceptance is Mahalanobis balancing
  against phase-I auxiliary means. Its asymptotic result does not directly
  assert the exact finite two-output empirical conditional-Poisson claim here.
  The generic idea of two-phase use of auxiliary variables is already known.
- Qualite, *A comparison of conditional Poisson sampling versus unequal
  probability sampling with replacement*,2008,
  https://www.sciencedirect.com/science/article/pii/S0378375807002728.
  Read publisher abstract/intro only, not its full proof. The variance
  comparison concerns the HT estimator for a single fixed population/design.
  Its principle must not be claimed new; our nonlinear random-pool step
  still needs its own proof or a verified reduction to this result.

The numerical probe completed16824 populations/budgets (M<=20, <=5 labels)
without a positive eigenvalue above1e-9. This finite floating observation is
NOT the missing theorem, an exact sampler or a model experiment. It does not
justify a neural campaign. Earlier exploratory outputs are also preserved;
only the registered rerun has a frozen producer commit.
