# V1 primary audit: eliminate the immediate generic proposals

2026-10-12. Read original sources before implementation; distinguish actual
read sections from titles/abstracts. These are reductions, not a new theorem.

* Bertoni/Goldwurm/Santini, *Random generation for finitely ambiguous
  context-free languages*, RAIRO35(6):499--512,2001, DOI10.1051/ITA:2001128.
  Original <https://www.numdam.org/item/ITA_2001__35_6_499_0.pdf>, introduction
  and section2/procedure Generate and ambiguity-correction proof actually read.
  They sample derivations with word mass proportional to d_S(x), count the
  derivations of the sampled word, then reject with reciprocal multiplicity
  (plus a common dyadic factor). Bounded/polynomial ambiguity yields their
  stated efficient generator; arbitrary exponential ambiguity does not.
  Thus our proposed1/d correction is OLD. Rational frozen-product weights
  multiply every derivation of the same original event by the same weight,
  so the same cancellation applies. That specialization is not a new principle.
* Meel/deColnet, *#CFG and #DNNF admit FPRAS*, original arXiv:2406.18224v3,
  2026-05-14, SODA2026 camera-ready corrections explicitly noted by authors.
  <https://arxiv.org/pdf/2406.18224>. Actually read introduction, definitions,
  Theorems1/2/4, Corollaries1/2 and section1.3 technical overview. Arbitrary
  CFG UNIQUE-WORD counting has an FPRAS; almost-uniform sampling follows.
  The printed technical bound O(n^15 |P|^14 eps^-4 log(1/delta)) is an
  existence bound, not practical evidence. Full42-page dependency analysis
  has NOT been reviewed here; don't claim validation of their entire proof.
* Chakraborty/Fried/Meel/Vardi, *From Weighted to Unweighted Model Counting*,
  IJCAI2015, <https://www.cs.rice.edu/~vardi/papers/ijcai15.pdf>. Actually read
  abstract, literal-weight definitions, related-work/chain-formula rationale
  and Section4's representative-formula/reduction statements. Dyadic weights
  are encoded by polynomial bit-sized gadgets with specified model counts.
  This broad weighted-to-unweighted principle cannot be renamed as our method.
* Amarilli/vanBremen/Meel, *Conjunctive Queries on Probabilistic Graphs: The
  Limits of Approximability*, ICDT2024, DOI10.4230/LIPIcs.ICDT.2024.15,
  original <https://drops.dagstuhl.de/storage/00lipics/lipics-vol290-icdt2024/LIPIcs.ICDT.2024.15/LIPIcs.ICDT.2024.15.pdf>.
  Actually read Section2 weighted-nOBDD result and AppendixA comparator-
  gadget proof. General rational probabilities p/q use binary comparators
  with p and q-p assignments; normalization is product q. Bit-length costs
  and zero/one-weight handling are already explicit.

For positional original-token weights a_i(v)/D_i, a standard auxiliary-bit
encoding supplies a_i(v) different auxiliary strings to token v. Membership
tests the ORIGINAL IDs/rendered bytes while ignoring those auxiliary bits.
The resulting unique encoded-event count would be

    sum_valid_original_y product_i a_i(y_i),

and projection of uniform auxiliary-weighted events gives the desired weighted
distribution. Fixed slot/auxiliary widths and inverse-homomorphism/finite-state
intersection constructions are classical. A full polynomial-size CFG proof
has NOT been written here. It should be treated as a plausible standard
reduction, not as a publication result or an implemented algorithm.

**Decision:** close reciprocal-ambiguity correction and generic weighted
FPRAS lifting as independent novelty claims. Don't develop a large decoder
for these already established operations. General ambiguity can be a useful
capability extension later, but requires a distinct guarantee/cost advance
before becoming the user's protagonist. No new forwards/benchmarks/software.
This audit also corrects any temptation to use exact #P-hardness to deny
competitive approximate conditioning on arbitrary CFGs.
