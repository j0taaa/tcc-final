# Primary comparisons BEFORE implementing A38

2026-10-11. These are ACTUAL reading scopes, not claims of reading whole books.
Conditional empirical coupling, rotations and binary Bernstein clipping are
antecedents. Neither search silence nor a proof certifies publication priority.

## Ordered overrelaxation: unknown-law rank coupling is already known

Neal, [Suppressing Random Walks in Markov Chain Monte Carlo Using Ordered
Overrelaxation](https://arxiv.org/abs/bayes-an/9506004), original1995 report,
Sections4.1--4.2 and the concluding ordered-underrelaxation paragraph READ.
Local original PDF SHA256
`80587d2018aa25aaf22e3f376e0e1adbe9d756ddc9bf4acd884a2ae12f69a37e`.
It samples K auxiliaries, retains the old value's rank, reflects that rank,
and breaks equal-value ties randomly. Exchangeability proves reversibility.
It explicitly discusses replacing the rank map with another valid update.
Thus unknown density, retained first and rank/pool coupling are NOT new.
The reflected rank can leave a size-two class paired with itself when it
occupies the middle ranks; a half-rotation of grouped ranks avoids that.
This observation alone does not establish a new algorithmic principle.

Andrieu/Lee/Livingstone, [A general perspective on the Metropolis--Hastings
kernel](https://arxiv.org/abs/2012.14881), original2020 Example4, surrounding
Proposition1 interpretation and Remark6 READ. Original SHA256
`019aae631cb32ce00136a55cf5b23d2650dc4ffe167c01e25c29d884a9a90770`.
Example4 restates unknown-CDF empirical/order-statistic coupling and its
exchangeability proof; Remark6 permits avoiding unnecessary simulation/storage
of auxiliary variables. Do NOT claim that early auxiliary simulation is a
new principle. A specific SHARP categorical expected-cost bound still needs
comparison; those passages do not state that bound.

## Bootstrap and antithetics: expensive evaluation is already motivation

Craiu, [Efficient Bootstrap Resampling](https://utstat.utoronto.ca/craiu/Papers/rom.pdf),
Sections1--3 and conclusion READ; original SHA256
`0c1faa9209289ea7be7fd4cf3a49214f00b4509b7767692ec6ba8d576bb5fd95`.
It develops Hall's antithetic permutations for conditional empirical bootstrap
resamples, and optimizes an approximation involving ranked derivative scores.
Its empirical-law and resampling distinction is explicit. This is a competent
precursor; expensive downstream evaluation is NOT an invented new application.
[Hall1989](https://doi.org/10.1093/biomet/76.4.713) itself remains ABSTRACT-only,
not full-text inspected. Do not exclude the original's scope based on this.

## Uniform rotations and nonmonotone scores

Casarin/Craiu/Frattarolo/Robert, [Living on the Edge: An Unified Approach to
Antithetic Sampling](https://arxiv.org/abs/2110.15124), originalv2 Section1,
Definitions1.1--1.3 and Examples1.1--1.2 READ. SHA256
`572313db17d72d7ead61744e7b9aff9fda30fc2e45bdfe4641bc5a2a74a37e5f`.
It credits rotation/systematic sampling, doubly stochastic transports and
nonmonotone-score optimization. A38 cannot claim half-circle quantiles or
arbitrary-score variance reduction as entirely unexplored. Craiu/Meng2005's
arbitrary-L2 asymptotic statement, already read for A37, remains a control.

## Model-checking trajectories

Roohi/Wang/West/Dullerud/Viswanathan, [STMC](https://lagrange.mechse.illinois.edu/pubs/RoWaWeDuVi2020/RoWaWeDuVi2020.pdf),
original2020 Sections1--3, Algorithms1--2, Theorems1--2 READ. SHA256
`9df7cd6a304ebb0900ffde5ab75836051c37c5617810aca04468cdf6635025a0`.
It stratifies stochastic-system transitions and evaluates whole LTL paths;
Theorem1's nonpositive covariance has an explicitly restricted until-formula
hypothesis. Its preceding2018 proof has not been read here. The known
transition-to-trajectory coupling principle is not A38's scientific novelty.

## Remaining gate

Nacu--Peres2005 Proposition24 already realizes binary Bernstein clipping;
A32 records the exact reduction. The unresolved question is the precise
categorical simultaneous-attainment and expected-work characterization, with
competent reflected-rank, half-rotation, binary/RSS and informed controls.
No native EPIC run, timing, priority confirmation or human review was done.
