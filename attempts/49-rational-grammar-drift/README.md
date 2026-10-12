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
The ICML2024 inference reduction's definitions2.7--2.11 and technical
overview3.1 have been read; its full reduction remains a mandatory elimination
check. Do not claim to have audited its full proof.

The next deliverable is a proof/obstruction, not a performance campaign.

V1 producer8f19b2f:3,100 planar cases,57,769 exact norm-breakpoint queries,
1,004 independent exhaustive sign-domain queries, all pass;2,799 cases actually
shorten. These are correctness checks only. V2's bit proof admits a scoped,
disjoint-sum forest and keeps source preparation/word-faithfulness as separate
obligations. A small compiled-forest adapter/oracle is frozen BEFORE observations;
it checks original aliases and macro tokens against separate stack/JSON parsing.
No neural capture, performance protocol, main API or article has changed.

V2 producer51245fc passes all75 predeclared compiled-forest cases:48
certificates and27 zero-mass refusals, compared to independent original-ID
enumeration. All outputs are preserved. These are correctness observations.

V3 re-evaluates the eight criteria BEFORE implementation: operation/application
and hypotheses are unchanged (1,5,6); the candidate difference and reason to
choose are now a quantitative integer core improvement, O(sqrt(d/epsilon))
stored generators versus Fu's stated O((d/epsilon)^2), with a full bit bound
(2--4). Classical convex approximation is explicitly credited; a strengthened
planar control can share the benefit, so no exclusivity or physical speed is
claimed (7). `work/optimal-planar-proof-v3.md` states the algorithm, proof,
complete costs, comparison boundaries and falsification gate. Specific TV
priority, real application and publication relevance remain OPEN (8).

V3 producer2e3b4a7 passes2,480 integer cases/40,035 exact norm-breakpoint
queries and ALL75 original-ID forest cases under BOTH cores (150 checks,
96 certificates/54 zero-mass refusals). No original family was excluded;
1,896 geometry cases shorten. Classical projection geometry is not new.
No model data, physical timing or publication gate has been validated.

V4, BEFORE application code: criteria1/3 now specify a software consumer
auditing numerical storage of a REAL frozen full-head probability table,
with guaranteed bounded-verifier drift. Criteria2/4 retain the quantitative
integer-core theorem, explicitly crediting classical geometry/parsing.
`word-admission-v4.md` separates the admitted-CNF word lemma from the source
normalizer obligation and an independent classical JSON-stack bridge.
Criteria5/6 freeze ALL3 rounding formats x BOTH tolerances on the one already
public packet, full original IDs, strong Hellinger/range controls and charged
preparation. This is a functional numerical audit, NOT a competitive benchmark
or quantized-neural-model execution. Explicit stacks can explode; controls
can be faster or sufficient, and all outcomes remain (7). Specific TV priority,
useful certificate improvement on this input, article and human review remain
open (8). Validate the bridge independently before the public-head audit.

V4 source038a404 failed while constructing the first fixed-slot oracle:
the fixture supplied extra IDs at a newly fixed position; the maintained API
correctly refused it. Partial checks/failure are preserved, and the public
audit was NOT run. V5 corrects only that fixture to the required singleton
support, preserving the exact scientific gate/controls/rounding protocol.
Producer7ae7641 passes all60 bridge cases: independent original-ID counts,
both exact masses, TV, both competent controls and fixed-slot behavior.
IEEE rounding ties/subnormal behavior are checked. This triggers only the
already frozen functional public-packet audit, not a competitive campaign.
The first public command (producer5d91beb) was refused during input setup:
FULL support also requires an explicit input source in the maintained API.
No head-rounding/core measurements ran; metadata/failure are preserved.
V6 supplies every original ID at every free position and the singleton at
fixed positions. No support reduction or scientific protocol change occurs.

V8 prospective refinement re-evaluates2--4/6/7 BEFORE code: exact logarithmic
nearest-edge queries sharpen the core cost to O(H*(d/epsilon)*log(d/epsilon)),
and the product-head corollary to O(n*q*sqrt(n/epsilon)*log(q*n/epsilon)).
Guarantees, original IDs, real use and ALL public cases are unchanged (1/5).
Convex approximation/query geometry is classical; Fu already removes the
log(1/TV) dependence. The candidate advancement is the sharper deterministic
TV bound/full integer implementation, not those principles. Source admission
is now constructive/polynomial in a WRITTEN algorithm, not verification of the
current compiler (`polynomial-source-admission-v7.md`). Exact exhaustive edge
queries must agree before another public run. Specific priority, performance,
publication and human review remain open (8). V6 outputs remain separate.
Producer45903f3 passes all1,860 geometry cases/30,846 norm breakpoints,
117,376 nearest queries against independently computed exhaustive segment
projections, and all75 original-ID forest cases. V6 was interrupted after
one completed row (371.95s core), with all partial metadata/output retained;
it is NOT a six-case campaign. V9 repeats ALL six original public cases with
the proved/validated exact query implementation, preserving both controls.
No favorable-case selection, neural quantization or generation-speed claim.
