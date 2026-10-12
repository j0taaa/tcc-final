# A46 — Ambiguity-aware conditioning: primary reduction before code

2026-10-12. This direction starts with a read-only scientific audit. No
prototype/model observations. A45's conjecture and all negative applications
remain preserved; the maintained LL(1) API/article are unchanged.

1. **Use:** frozen-product dLLM token completions constrained by an ambiguous
   recursive CFG, counting ORIGINAL token events once rather than parse trees.
   SQL/expression DSLs with overlapping alternatives can benefit from accepting
   existing grammars without silently changing their language/distribution.
2. **Difference:** initially investigate exact multiplicity correction or
   approximate weighted word counting. Both broad principles already have
   primary predecessors. Merely inserting token IDs/dLLM weights is NOT enough
   novelty; locate an additional mathematical/operational gap BEFORE code.
3. **Choice:** broader grammar admission and error-controlled conditioning,
   if complete preparation/counting/sampling costs are usable. Compare with
   grammar disambiguation, exact rejection/multiplicity correction, #CFG
   FPRAS, deterministic parsing and factor/circuit inference as appropriate.
   EPIC feasibility already admits grammar ambiguity; do not claim otherwise.
4. **Without code:** define rational position weights, byte rendering, aliases,
   valid original events, fixed slots and zero valid mass. Any reduction to
   unweighted counting must be polynomial in BIT size and preserve distinct
   original events despite equal byte strings. A classical reduction is a
   corollary, not our invention. Randomized relative estimates do not become
   deterministic intervals or exact sampling automatically.
5. **Experiments:** NONE before a distinct plausible theorem/use. If it merely
   reproduces known rejection/FPRAS constructions, close as a protagonist
   without an expensive artificial grammar benchmark or implementation.
6. **Cost:** grammar normalization, token/lattice representation, rational
   denominators, precision, approximation parameter and actual high polynomial
   exponents. A polynomial existence theorem does not imply practical decoding
   speed, or make a14th-power circuit-size bound a deployable algorithm.
7. **Objection:** Bertoni/Goldwurm/Santini already correct ambiguity by1/d(x),
   and Meel/deColnet already provide arbitrary-CFG counting/sampling FPRAS.
   Weighted-to-unweighted bit gadgets are established. These reductions may
   eliminate the candidate before implementation, which is the purpose here.
8. **Publication:** need a NEW guarantee/algorithmic operation beyond those
   predecessors and a meaningful dLLM/CFG benefit. No novelty, use, acceptance
   or superiority is asserted by this file or by a passing prototype.

See work/primary-reduction-v1.md. No implementation has started.
