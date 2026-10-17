# After A68: a new primary lead is not yet a new contribution

2026-10-17, after the complete negative A68 V7 gate. This note does not
reopen its numerical application, change the stopping rule or select a new
prototype. Earlier closed directions keep their own decisions.

Original Zhang/Li/Di/Gu, *Query-Efficient Rejection Sampling for Parallel
Masked Diffusion*, arXiv2610.22238v1, posted15October2026:
https://arxiv.org/html/2610.22238v1
Read abstract/introduction/related work, Sections3--4 including Algorithms1--2
and Proposition4.1, and the displayed Theorem5.1/definitions in Section5.1.
Later proofs/experiments were not audited. Their SIRS uses clipped log-ratio
increments and a Poissonized factory; Rao--Blackwellizing over remaining
positions is already their method. No missing-feature or priority claim.

The relevant real operation is correcting dependence in parallel masked
generation, rather than merely making syntax valid. This is distinct from
A68's generic smooth numerical factory and has an original recent comparator.
The following tempting grammar extension is nevertheless only a CLASSICAL
composition, not presently a sufficient own consequence:

If a proposal q has positive mass outside grammar G, finite clipped weights
a(x) in[e^(-2B),1] cannot enforce G. Exact rejection of invalid x would yield
Q_G=Q(.|G), where Q(x) is proportional to q(x)a(x). If P(G)=1, elementary
conditioning gives KL(P||Q_G)=KL(P||Q)+log Q(G)<=KL(P||Q). Sampling directly
from q(.|G) and using the SAME a(x) gives the same Q_G. The scalar proposal
normalizer cancels. This identity is derived here as a standard conditioning
calculation, not attributed as an unmentioned theorem of their paper.

Thus simply adding CFG filtering/product-conditioned proposals, known
Poisson thinning, stopping a Bernoulli product early, caching identical
queries or batching forwards would not establish adequate own novelty.
Neural costs, changed laws under inconsistent learned scores, grammar
normalization and strong existing conditioned-proposal controls all remain.
No SIRS code/model/head/dataset/quality/timing was executed. No new attempt,
theorem priority, useful measured benefit or fulfilled positive goal follows.
Next substantive work must identify a sharper useful consequence or another
real operation and answer the eight criteria before implementing it.
