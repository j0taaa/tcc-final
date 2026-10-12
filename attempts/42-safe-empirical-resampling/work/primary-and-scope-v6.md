# V6 primary-source and scope audit

2026-10-11. This is a reading/contract audit, not a priority certificate.
The producer and pure IID proof were frozen at a300a2e. Earlier finite-source
and all-six-bank negative comparisons remain unchanged.

## Closest confirmed antecedents

* Chauvet and Ruiz-Gazen, arXiv:1609.02688v2, 2016-09-13,
  <https://arxiv.org/pdf/1609.02688>: actually read the fixed-population setup
  in section2, Algorithm1 and Proposition1, Proposition2/Theorem1 in section4,
  the independent random-order extension, and the eigenvalue criterion in
  section5. The proof of Proposition2 is not printed (available from authors).
  Their variance domination is for a fixed population and inclusion
  probabilities. It cannot simply be averaged over an IID pilot pool and
  called domination of two original IID draws: the pilot mean also fluctuates.
  A conditional bound of Var(pool)/(2) alone would yield
  (1+1/B)*Var(P)/2 after averaging, which is too weak. V6's unconditional
  polynomial/square identity addresses that extra term. This observation
  does not prove that their other results or the sampling literature lack a
  stronger two-phase theorem. Pivotal6 shares our balanced query frontier.
* Ridout, *On Ranked Set Sampling for Multiple Characteristics*, author PDF,
  <https://www.kent.ac.uk/IMS/personal/msr/webfiles/rankss/multiple.pdf>:
  actually read introduction, methods in sections2/3 and simulation setup
  in section4. Multivariate ranking and balancing auxiliary characteristics
  are established. Its balancing selection and precision examples do not
  assert the specific six-IID, two-output, arbitrary-function guarantee here.
  This is a distinction from the examined result, not exhaustive priority.
* Hashemi/Luo/Makur's September2026 preprint is listed at the authors' sites,
  but its full49-page text has not been obtained. The linked group-meeting
  slides are dated2025-11-18, not that2026 manuscript. Actually read those
  slides' assumptions and theorems on known-CDF, monotone/strongly isotonic
  functions. Do NOT infer that the unavailable2026 manuscript excludes V6.
  <https://zhankunluo.com/publication/antithetic/>
* Olofsson/Grafstrom/Lundstrom, <https://arxiv.org/html/2305.02446v1>:
  large cheap pilot pools, thinning and few expensive evaluations are already
  explicit. See A41's recorded reading of section2/Algorithm1. Those principles
  and classical pivotal allocation are not our proposed originality.

## Lower-bound information model: important clarification

The directional frontier in `iid-theorem-v6.md` is a **score-oblivious
coupling** bound. One fixed joint law is evaluated on all linear projections;
it is not a lower bound against a different scalar-score-aware selection
policy chosen for each projection. Already paid first scores may be kept,
but the specified selector does not consult them. Analytical estimates,
control variates, known class masses/inverses, non-IID sampling and policies
which exploit other source information are outside that lower-bound model
and remain competent practical alternatives. Universal unknown-mass validity
is essential; a promise of known balanced masses admits stronger designs.

The adversary can choose a source with one canonical raw state per class, so
the Bernstein argument does not depend on hiding useful raw metadata. This
is a worst-direction theorem for an explicitly defined oracle contract,
not a claim that opaque sampling is optimal for every real JSON application.

## What is and is not established

The written square proof covers ANY IID original law and arbitrary finite
fixed class map, without numerical certificates or monotonicity of G.
The frozen exact oracle checks two identities and8,256 weighted raw tapes,
including aliases, repeated raw states, four classes and a useless proxy.
These checks validate the reference on those cases, not novelty or model use.

The distinct candidate result is simultaneous unconditional covariance safety
and a sharp bounded-proposal directional frontier, rather than matching,
sampling without replacement, a known objective, or a new dLLM decoder.
The old proxy's practical promotion remains rejected. No complete-gradient
training, independent generation improvement, EPIC superiority, human review
or publication priority has been established.
