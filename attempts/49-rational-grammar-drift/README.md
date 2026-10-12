# A49 — Rational certificates for drift of a grammatical posterior

2026-10-12. Contract BEFORE code or observations. This is an investigation,
not confirmed novelty, publication sufficiency, or a faster decoder.

## Eight scientific questions

1. **Use.** Compare two frozen dLLM heads on the SAME finite original-token
   domains, canvas and unambiguous CFG. Software needs an upper/lower certificate
   for total variation (TV) of their valid-completion laws, for auditing a
   quantized/draft head or a proposed reuse. This does not save the forward
   needed to obtain a new head. A low TV certificate bounds every bounded
   downstream verifier under a common continuation policy, not semantic accuracy.
2. **Difference.** TV, zonotopes, geometric normalization, relative approximation
   and domain compression are OLD. Fu2609.24235 already provides the general
   admissible-gate FPTAS in an extended real-arithmetic model; applying it to
   derivations is a corollary, not a new principle. The candidate difference is
   a small, entirely RATIONAL two-dimensional compressor, complete bit costs,
   and a word-faithful variable-shape packed-forest reduction. Bhattacharyya
   et al.2609.18707v2 has a common-v-tree PC theorem, including fixed-tree WTAs.
   It must remain a control. The distinction may still be too small.
3. **Choice.** Intended guarantee: deterministic rational [L,U] with
   L<=TV<=U<=(1+epsilon)L, in polynomial input-bit cost, without enumerating
   completions, a fixed parse tree, a minimum valid mass or a minimum positive
   TV. Exact TV is #P-hard already for products. Compare Fu's actual framework,
   existing product/Markov FPTASs, PC domain reduction, exact enumeration and
   exact Hellinger/KL upper bounds. No claim to dominate these on easy inputs.
4. **Without code.** Prove the planar normalization/compression lemma, signed
   generator composition, error accumulation, unique-word representation and
   integer bit bounds. A pure admissible-gate instantiation does not establish
   novelty; the claimed arithmetic/representation distinction must survive.
5. **Experiments.** Initially adversarial small vector/forest enumeration with
   independent rational expected norms, zero TV, rare events, zero supports,
   near-collinearity and incompatible decompositions. These are correctness
   checks, not scientific superiority benchmarks. No neural/timing campaign
   until the theorem and closest-prior comparison survive.
6. **Costs.** Charge grammar/token/lattice preparation, normalizers, geometric
   reduction, all exact integer/rational operations and output. Declare maximal
   expanded derivation size, not only DAG size: repeated squaring can have
   exponential bit growth. A shared graph or original-token lifting is not free.
   A one-step drift certificate is not global neural quality or native EPIC law.
7. **Objection.** Fu's framework may already make this a direct specialization;
   standard planar geometry may supply the rational compressor. Sum alternatives
   MUST denote disjoint word events, or the result measures derivation TV.
   A proof over a fixed tree is insufficient for a CFG forest. General
   stochastic/ambiguous grammars and changed support need an explicit contract.
8. **Article.** Need the exact nearest primary theorem, a complete comparative
   result with bit costs, a real operation and minimum implementation. No human
   review, priority, useful timing, EPIC win or acceptance has occurred. Preserve
   this attempt if it reduces to prior work; do not promote on finite checks.

## Initial boundaries

Work is isolated in `work/`; no mutable imports from another attempt, main API
changes, model forwards, dependencies or tests restored. Integer/rational inputs
only. Two weightings share the unambiguous event forest; neither normalization
constant may be zero. Zeros are allowed using the union of both declared supports.
The maintained LL(1)/EOS-free contract is not enlarged by this investigation.

Current primary sources actually inspected: Fu2609.24235v1 sections1,3.3--3.4
and4.1 (general framework, real-arithmetic boundary); Bhattacharyya et al.
2609.18707v2 sections1,4 (common-v-tree condition and product propagation).
The ICML2024 inference reduction has only been downloaded/abstract read so far;
its full reduction remains a mandatory elimination check.

The next deliverable is a proof/obstruction, not a performance campaign.

V1 producer8f19b2f:3,100 planar cases,57,769 exact norm-breakpoint queries,
1,004 independent exhaustive sign-domain queries, all pass;2,799 cases actually
shorten. These are correctness checks only. V2's bit proof admits a scoped,
disjoint-sum forest and keeps source preparation/word-faithfulness as separate
obligations. A small compiled-forest adapter/oracle is frozen BEFORE observations;
it checks original aliases and macro tokens against separate stack/JSON parsing.
No neural capture, performance protocol, main API or article has changed.
