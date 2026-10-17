# A70 V1 — Closest original sources and reading limits

Written before implementation/execution,2026-10-17.

- GS-Scale ASPLOS2026 original Section4.3/5.5 and pinned host-source portions
  were read in M95. Hashes/scopes and immutable source manifest remain at
  docs/research/next-operation-audit-2026-10-17-v5.md and
  docs/artifacts/raw/structural-operation-audit-v5/gs-scale-manifest.json.
  Its epsilon approximation, lazy updates/cap and real consumer are prior
  work, not A70 inventions. More of host sparse_adam was read this turn; no
  original source was compiled/executed. A70 does NOT claim native equality
  to that whole compiler/library/flush-to-zero implementation.
- Miahi/Belilovsky, ORIGINAL PULSE2602.03839v1:
  https://arxiv.org/html/2602.03839v1 . Read abstract/introduction, Section3.1,
  3.3 and4/Algorithm1, A.1 and startA.2. It already exploits weight-update
  absorption for bitwise-lossless synchronization. BF16-visible sparsity
  under dense gradients is not a zero-gradient FP32-master certificate.
  No complete experimental/theorem/code audit, source/checkpoint download,
  claimed bound endorsement or reproduction. Their empirical numbers are
  not ours. In particular neither absorption nor lossless bit transmission
  is a new A70 principle.
- Lauter/Lefevre, ORIGINAL RR2007-36 *An efficient rounding boundary test
  for pow(x,y) in double precision*:
  https://www.vinc17.net/research/papers/rr_power-cr.pdf . Read introduction,
  Section2.1 and displayed Section2.2 interval/rounding-boundary/Ziv account,
  not the complete proposed pow algorithm/proofs/worst-case search. The
  interval endpoint uniqueness principle is CLASSICAL. This report is2007;
  do not relabel it as the later IEEE journal PDF/version2009.
- Cattaruzza/Abate/Schrammel/Kroening's abstract-acceleration article was
  inspected as a PRIMARY lead:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7900086/ . Only the algorithm-
  overview search excerpt was inspected, not the full concrete-rounding
  semantics/proofs. No claim that it already proves A70, or that its error
  model is the same as repeated native rounding. Sound loop summaries and
  interval arithmetic are obligatory antecedents/controls.

Focused searches for exact/lossless/bitwise lazy Adam and native zero-gradient
skipping found these leads, but cannot certify absence of earlier optimizers
or compiler transformations. Sufficient specific novelty and useful effect
remain OPEN. Do not infer priority from the absence of a search hit.
