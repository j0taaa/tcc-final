# Primary readings and scope — 2026-10-16

These are read-only antecedent checks, not evidence of a new method's benefit.

- Li and Zheng, *A note on alpha-permanent and loop soup*, 2022,
  https://arxiv.org/html/2212.06095v1 . Read Introduction/Theorems1.2/1.3 and
  §3.1 definitions/Poisson law. Occupations already have a permanental law.
  MacMahon/Vere-Jones and Le Jan are explicitly credited there. The binary
  occupation restriction in our derivation is a consequence, not new theory.
- Armendáriz, Ferrari and Frevenza, *Gibbs measures over permutations of
  point processes with low density*, 2019,
  https://arxiv.org/pdf/1904.03952 . Read §3's independent simple-cycle Poisson
  conditioning and loss-network/clan construction (pages8–11), plus the
  introduction. This is a direct and strong antecedent, not merely a paper
  with the word "permutation". Its perfect-simulation route must be considered.
- Kuck et al., *Approximating the Permanent by Sampling from Adaptive
  Partitions*, NeurIPS2019,
  https://proceedings.neurips.cc/paper_files/paper/2019/file/d914a6c6d93c8df063b9099a076a488c-Paper.pdf .
  Read abstract, bounds around Eq3, §6.3/application and conclusion. Exact
  weighted-assignment sampling already serves particle filtering. Their
  tracking example uses simulated Gaussian motion; do not call it real
  recorded tracking data. A new sampler must compete with adaptive bounds.
- Harviainen, Röyskö and Koivisto, *Approximating the Permanent with Deep
  Rejection Sampling*, NeurIPS2021,
  https://proceedings.neurips.cc/paper_files/paper/2021/file/01d8bae291b1e4724443375634ccfa0e-Paper.pdf .
  Read introduction and §5's code/evaluation description; full algorithm and
  supplement comparison remain pending. Not an implemented control yet.
- Harviainen/Koivisto, *A Faster Practical Approximation Scheme for the
  Permanent*, AAAI2023,
  https://ojs.aaai.org/index.php/AAAI/article/download/26440/26212 . Read the
  nesting-product bounds and code pointer, not full performance replication.
  Author code: https://github.com/hjuha/nesting . Newer nesting bounds are a
  required control, not an excuse to compare only Huber2003.
- Blanca, Cannon and Perkins, *Fast and Perfect Sampling of Subgraphs and
  Polymer Systems*, RANDOM2022/TALG2024,
  https://drops.dagstuhl.de/storage/00lipics/lipics-vol245-approx-random2022/LIPIcs.APPROX-RANDOM.2022.4/LIPIcs.APPROX-RANDOM.2022.4.pdf .
  Read abstract/§1.2/Theorem4 in this version. Exact near-linear polymer
  sampling is known with explicit oracle/weight conditions; no generic claim
  that all known cycle methods require exponential enumeration is permitted.
- Liu et al., *DiffuRank*, 2026,
  https://arxiv.org/html/2602.12528v1 . Read §4.3.1's permutation inference.
  The model supplies a matrix of per-rank identifier probabilities. Its native
  greedy unique-assignment and one-pass assignment methods are different
  operations; users needing only a deterministic ranking do not need our law.

Further checks before any novelty claim: original Boltzmann samplers
(Duchon/Flajolet/Louchard/Schaeffer2004), original Le Jan/loop-soup algorithms,
the loss-network algorithm's feasible cycle oracles, current weighted-matching
samplers and actual consumers of posterior permutations. Search absence is
not priority confirmation. No human review is claimed.
