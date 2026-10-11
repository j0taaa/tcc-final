# Primary antecedent audit — 2026-10-11, no priority certificate

This is a targeted difference matrix, not proof that no similar theorem exists.
Read sources supporting the operation, rather than counting paper titles.

| Claim | Primary source checked | Assessment |
|---|---|---|
| Polynomial representation of bounded p-coin factories | Niazadeh/Paes Leme/Schneider, [Combinatorial Bernoulli Factories](https://arxiv.org/html/2011.03865v2), Section2.2, Definition2.3/Lemma2.4 and Section2.1 decision tree | KNOWN machinery; do not call Bernstein uniqueness new. Our bound additionally fixes B1 and optimizes its disagreement with Y. Whether the precise bound was published elsewhere is OPEN. |
| Negative covariance from a stationary class transition | Classical reversible/Barker/Dirichlet; internal A29 frozen reference | KNOWN principle. Four-draw adaptive realization is a specialization. It becomes a contribution candidate only with sharp oracle budget and useful integration, not alone. |
| Categorical antithetics from CDF and Gumbel copulas | Dimitriev/Zhou, [CARMS2021](https://proceedings.neurips.cc/paper/2021/file/6e16656a6ee1de7232164767ccfa7920-Paper.pdf), Algorithms1/2, Sections3.2.1/3.2.2, Theorem2 (PDF locally read) | KNOWN. CDF requires category probabilities and their estimator includes pair-PMF importance correction. It is a competent known-p comparator; no claim its gradient theorem fails. Coordinatewise antithetics do not automatically give our unknown terminal-verifier theorem. |
| Conditional retained-particle resampling | Chopin/Singh, [Particle Gibbs](https://arxiv.org/html/1304.1887v2), Section5 conditional resampling, conferred during31 | KNOWN. First-visitor anchoring is not invented here. Our sampler requires neither measured class probabilities nor a retained particle's weight. |
| Ranking/Gumbel conditional laws | Kool/van Hoof/Welling, [Ancestral Gumbel-Top-k2020](https://www.jmlr.org/papers/volume21/19-985/19-985.pdf), Sections2.3/2.4/3.2 | KNOWN. Complete ranking must be retained for EPIC recovery. Our implementation returns a complete original native row instead of forcing a winner with an iid tail. |
| Finite precision changes diffusion categorical laws | Zheng et al., [Masked Diffusion Models...](https://arxiv.org/html/2409.02908v2), Section5.2/5.3, Proposition5.2 | KNOWN. Their truncated-continuous Gumbel formula is not equality with every Torch53-bit grid/tie kernel. Our native oracle target avoids silently switching to ideal PL. This distinction alone is not novelty. |
| Exact sampling using interval refinement | Haney et al., [Precision-based attacks...](https://tpdp.journalprivacyconfidentiality.org/2022/papers/HaneyDHSH22.pdf), introduction/framework | KNOWN alternative principle. Do not invent exact sampling/interval refinement or claim that finite-law conditioning is impossible for all algorithms. |
| Exact CFG generation with optimized recovery | [EPIC source](https://github.com/hyundong98/EPIC-Decoding), latest public commit5b1b31098f34ed3691d2a9f4aae14fdf5839d072 checked; [paper](https://arxiv.org/html/2606.00722v2) | KNOWN/main comparator. Entire unmodified decoder, regular cover/exact/DFA-free settings and recovery must remain enabled. Our pair coupling is not new parsing. |

The primary paper [Strong Antithetic Variates](https://www.cs.purdue.edu/homes/amakur/docs/AntitheticVariates.pdf)
is indexed with strong-monotonicity/anti-Lipschitz assumptions, but fetching
the actual PDF returned404. [Author page](https://www.cs.purdue.edu/homes/amakur/publications.html)
also lists a2026 multivariate representation/optimal-transport preprint with
no direct link. FULL text is unresolved; do NOT conclude from its title that
it does/does not subsume this proposal. No human review has occurred.

## Candidate contribution versus known consequence

Known: Bernoulli factories, class projection, stationary covariance reduction,
conditioning, native replay and Markov martingales. Candidate: the SHARP
finite sample-budget curve B_n(p), minimum four p-blind oracle draws, bounded
adaptive realization attaining B4 with expected auxiliary<=1, and its exact
finite-native full-recovery use. This is an incremental recut, not priority
confirmed. If a matching published oracle-budget theorem is found, reclassify
it as known and retain only a genuinely useful application/implementation if
competitive; otherwise reject this direction.

Oracle-only optimality must never be sold as superior to density-aware CDF,
arbitrary diffusion decoders, four full independent generations or hardware
speed. Applying the proof to dLLMs/CFGs preserves the entire adaptive law but
does not prove large semantic gain or that the cost is paid back.
