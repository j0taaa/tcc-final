# Primary comparison: keep the counting claim narrow

2026-10-11. Read BEFORE code. No claim of publication priority from absence
in search. No private/paywalled access was bypassed.

- Istvan Miklos, *Computational complexity of counting and sampling*, author
  manuscript, [Renyi institute copy](https://www.renyi.hu/~miklosi/CCC/ComputationalComplexityOfCountingAndSampling.pdf):
  Sections4.2.1/4.2.2, printed188--190 actually read. Local original PDF2020837
  bytes/SHA256 `e13e00e519e664ede395d9cc36c618864140fb806ebd4d7b611ad847f1d15a66`.
  Theorems47/48 give #DNF/#3DNF hardness by negating CNF and subtracting.
  Section4.2.2 ALREADY constructs the union-of-terms regular grammar with
  O(mn) size and explains the difference from unambiguous word counting.
  That is the exact underlying counting mechanism of A35. Our explicit
  witness makes the syntax LL(1); its existentially delayed selection projects
  away the witness, recovering the old union. Witness lifting/projection is
  not itself a new complexity principle. The manuscript cites Kannan,
  Sweedyk and Mahaney for the original regular-language counting result;
  that original has not yet been fully read.
- Hazan/Jaakkola2012, [original](https://arxiv.org/pdf/1206.6410), Sections3--5
  and7--8 actually read: a local random perturbation followed by argmax
  induces its OWN distribution (Section5/Theorem3). They explicitly separate
  low-order random MAP output probabilities from Gibbs/partition inference.
  Thus 'solver pushforward differs from a tractable product posterior' is a
  precedent, not our invention. Their Section4.2 exact construction still
  alternates expectation and maximization with exponential work. A35 uses
  confidence-weighted TOP-PROPOSAL matching, not their continuous perturbed
  objective, so their formulas cannot silently replace this kernel's law.
- Karp/Luby/Madras1989, DOI10.1016/0196-6774(89)90038-2, original publisher
  abstract/preview read, full original not yet retrieved. #DNF has an FPRAS.
  A35 must NOT use exact hardness to deny competitive approximate masses.
- A13 already rejected generic event/ranking counting as a protagonist.
  This companion distinguishes a native greedy/MWPC accepted tag from the
  CFG posterior, but is not a resurrection of generic counting as novelty.

The plausible own observation is an EXPLICIT confidence/alias construction
for ideal grammatical commitment: polynomial commitment + LL(1) witnessed
product inference versus hard accepted-tag probability. It may be a direct
specialization of these precedents. Keep it as a small bridge for A34, not a
claimed new hardness theory or neural win. It does not show that every good
coupler needs a tag probability, nor that finite-CUDA EPIC equals ideal PL.
