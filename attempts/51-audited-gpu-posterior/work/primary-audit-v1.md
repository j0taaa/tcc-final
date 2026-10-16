# Primary antecedents and limits — 2026-10-16

Read scopes below refer to original sources, not search snippets. No absence of
a matching result in these readings establishes priority.

- Dymetman/Bouchard/Carter, OS*2012, original https://aclanthology.org/W12-6106.pdf,
  refreshed sections2.1–2.4 (rejection, normalized/unnormalized envelope and
  refinement). Its exact-envelope principle already subsumes the proposed
  scalar correction. The previous A25 audit also recognizes this antecedent.
- Lemire2019, https://arxiv.org/pdf/1805.10941, sections1–4 and Algorithm5:
  multiply-high range reduction has bias, corrected there by a small rejection.
  We deliberately ACCOUNT for its finite preimages instead of calling it
  unbiased; that counting identity and integer CDFs are elementary, not inventions.
- Saad/Freer/Rinard/Mansinghka2020, author original
  https://people.csail.mit.edu/rinard/paper/popl20.sampling.pdf, portions1.1–1.2,
  section2 finite inversion and sections3–4 precision/approximation problems
  read in the preceding investigation. Exact categorical and limited-precision
  sampling, entropy/precision tradeoffs and finite inversion error are known.
  This is not a full reading of all31 pages.
- Hafner/Meligrana2025 EBUS, original https://arxiv.org/html/2506.14062v1,
  sections1–3 including the integer-level Algorithm1, exact intra-level sampling,
  and global-shift adjustment. Bit-level mantissa/exponent grouping, approximate
  upper weights and exact rejection already yield exact floating-weight samples.
  This is a mandatory strong local categorical control; its fixed binary64 input
  contract does not itself compute exact inside messages of a large grammar.
  No novelty is claimed for upper-rounded integer categorical proposals.
- Sainudiin/York2009, original institutional manuscript
  https://ir.canterbury.ac.nz/server/api/core/bitstreams/f1867726-17a9-482e-812b-494cfe9f46ca/content,
  background, rejection sampler, interval arithmetic and Moore rejection sampler
  sections read. Certified directed envelopes, including lower/upper integral
  acceptance bounds, are established. Their phylogenetic application is not
  claimed as our system; neither does that make a grammar specialization novel.
- Duchon2011 and Brassard/Devroye/Gravel2019 primary sections are already scoped
  in47/work/primary-reduction-v1.md. Exact recursive interval decisions are a
  mandatory control, NOT a novelty opportunity simply because they use GPUs.
- NVIDIA PTX ISA, https://docs.nvidia.com/cuda/parallel-thread-execution/,
  floating div section9.7.3.8: explicit .rnd modes IEEE-compliant; .rp/.rm,
  and support for subnormals by default on sm_20+. .ftz would break a claimed
  positive upper conversion of tiny inputs. The auditor must use explicit
  correctly rounded basic operations, not empirical nonexhaustive error bounds
  for an arbitrary CUDA/Torch log/exp implementation. Documentation is a hardware
  contract; it does not formally verify our future compiled program.

Published consumer inspected from unchanged local Git tree:
Mosaic https://github.com/MhDang/mosaic, pin36945e4b3c64913e23962e0924a8b40a84c58807,
`mosaic/dlm/llada2.py` lines1–16,29,79: default commit_by=model and return_marginal
only when constrained confidence requested. A51 would provide the joint sample,
not exact conditional confidences. Whole-token decode and true EOT/PAD need the
explicit adapter semantics, not a claim of identical upstream tokenizer language.
FactorDLM https://arxiv.org/html/2609.32900v1, introduction/section3/Proposition2,
is prior for graph-based exact mathematical inference and quotient laws. No claim
that this is the first GPU, graph, class or joint grammar sampler.

## Main unresolved objection before extensive implementation

A certified recursive interval GPU sampler may retain its random threshold and
refine only ambiguous choices. It can avoid MOST exact scalar CPU corrections,
whereas A51 pays a selected-word correction every time. Interval passes, GPU
integer/EBUS local disintegration and precision/refinement must be compared under
the SAME original rational law, with complete transfer/output costs. One cannot
claim speed merely against full Fraction messages, nor claim practical usefulness
by banning the already accurate ordinary FP64 implementation. First small
rational oracles only; no substantial implementation/campaign is authorized by
an inference of novelty from the above search.
