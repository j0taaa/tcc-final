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

At V1, primary sources inspected were Fu2609.24235v1 sections1,3.3--3.4
and4.1 (general framework, real-arithmetic boundary); Bhattacharyya et al.
2609.18707v2 sections1,4 (common-v-tree condition and product propagation).
The ICML2024 inference reduction's definitions2.7--2.11 and technical
overview3.1 had been read; its full reduction remained a mandatory elimination
check. V10 below records the subsequent complete section4 reading.

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

V9 producerbb1be02 completes ALL6 public cases, full50,258 original IDs;
source/evidence are preserved in `work/evidence/public-v9`. Independently
checked masses and original assignment count109,026,321,152. For probability
table FP16 at epsilon0.1, U=4.095231914338327e-5 against the certified
Hellinger upper0.0027838314673018887 (about67.98 times larger). The inexpensive
controls are FASTER, and the complete six-case table/costs are generated from
immutable rationals by `work/build_report.py`. This confirms a concrete
certificate-strength use, not a new quantized model or latency improvement.

V10 re-evaluates all eight questions: (1) a numerical table audit with a
bounded-verifier budget is now materialized on a real head; (2--4) the
distinction is a quantitative deterministic product/forest bound and full
integer bit analysis, rather than merely combining a parser and diffusion;
(5) all prospective cases and prior failures remain; (6) full audit costs
and cheaper controls are explicit; (7) the ICML2024 inference reduction is
now read IN FULL section4 and admits a competent derivation encoding.
Generic approximation feasibility, geometry, parsing and TV consequences
are OLD. `work/primary-comparison-v10.md` locates the specific improved upper
bounds and a trimmed-source qualification. Novelty beyond those inspected
primaries and human/venue judgement remain open (8); absolute acceptance or
priority is not implied. The mathematical draft `work/manuscript-v10.tex`
contains three complete written theorems, the faster product corollary,
application and ALL6 generated numerical rows. It does not replace the main
article or silently claim verification of its compiler.

The direct product recurrence/protocol were frozen at476ace7 BEFORE checks:
all1,167 cases pass (six undefined-zero-mass refusals and eight invalid-input
refusals). Its independent enumerator is in `work/verify_product.py` and
evidence in `work/evidence/product-v10`. The proof, not this finite gate,
establishes the precision exponent. No new model forward or competitive
timing campaign was run. The next useful step is adversarial full-proof/
priority checking, not another decoder benchmark chosen to favor this audit.

V11 preserves the V10 draft/data and adds a ROUTINE exact shortcut: m<=k
returns the input core, otherwise the V8 query algorithm runs. This gives
O(m log(m+2)) compression arithmetic work, without changing the64k guarantee.
The proof/prospective gate preceded code (782e9a2,3a9416b). ALL1,860 geometry
cases/30,741 norm queries/117,376 independent projections and75 original-ID
forests pass; ALL1,167 original product checks pass again. The added389
cases at epsilon2^-1024 are exact, with two zero-mass refusals and six signed
checks. Three independent small regressions are in CI through `make test`;
source67b5f92 passes them. The previous164-test suite passed70.471s.
Geometric-priors-v11 reinforces that planar compression/bit models are OLD;
only the explicit quantitative TV bound is the candidate scientific advance.
No reattribution of V9 timings, new neural capture or semantic benchmark.

V12 re-evaluates BEFORE code all eight questions: (1) the operation remains a
numerical probability-table audit; (2--4) the candidate is ONLY a sharper
deterministic TV precision bound, because a strengthened classical angular
control already has integer polynomial bit costs without minimum mass/TV.
(5) `strong-angular-control-v12.md` freezes all old correctness families and
ALL18 public functional rows, not a new performance benchmark. (6) matched
error budgets, CPU/wall and complete preparation are charged. (7) the linear-
work angular control may beat endpoint projection; no control is omitted.
A calibrated endpoint and routine hybrid are separately named and do not
inherit V9 timings. (8) geometric novelty, human review, complete priority,
editorial sufficiency and generation superiority remain unconfirmed. The
specific quantitative TV bound must survive this stronger comparison.

V12's independent gate passes5,580 geometry cases/80,898 norm queries,
225 original-ID forests and3,501 products (18 zero-mass refusals). Public
producer81c6c5b completes ALL18 rows:12 certificates, six angular product
materialization refusals, no errors. These refusals are NOT a scientific
win. V13 will stream the classical control's products rather than cap its
Cartesian tables. Endpoint/hybrid timings are developmental single runs,
and their faster calibrated constants are not attributed to older sources.

V13 is a correction of the comparison under the SAME eight answers. Before
code, `streamed-control-v13.md` removes the control's product materialization
cap via three replayable scans, with unchanged all-query/error proof. This
classical optimization is not novelty. All old oracle families and ALL18
public rows will be repeated; controls get more permissive resources, and
their losses/longer costs remain recorded. No table-cap win is accepted.

V14 writes BEFORE finite checks a positive original-probability family with
strict stored-core separation: the streamed angular control needs Omega(1/epsilon)
rows while endpoints need O(1/sqrt(epsilon)), at matched all-query tolerance.
`positive-core-separation-v14.md` answers all eight criteria and credits the
exact O(M)-time/O(1)-space scalar control for this one-position example. This
is a mathematical intermediate-representation result, NOT a favorable
generation benchmark or a lower bound against all TV solvers.

V13 producer9111102 passesALL5,580 geometry/83,054 norm checks,225 forests,
3,501 products and300 streamed/materialized Cartesian checks. Its ALL18
public rows finish without refusals/errors, including44,867,550 streamed
candidates in the largest control product. Shared preparation/full costs and
CPU/wall are preserved. Single-run speed differences against this specified
control are descriptive, not independent/statistical/general superiority.
V14 producer8cae148 passes ALLfive positive-family formula checks, with no
performance measurement or forward. Exact scalar TV remains the better
one-position operation; the theorem concerns retained intermediate cores.

V15 re-evaluates all eight criteria BEFORE code in `adaptive-control-v15.md`:
strong angular aggregation chooses a coarser grid only after EXACT all-query
norm certification. ALL methods receive exact unary/singleton passthrough
and its tighter structural error count. All old correctness/public families
remain, with full costs and no capped-product success credit. The control may
erase the observed speed advantage. These classic optimizations are NOT the
candidate novelty; the sharper theoretical TV precision bound remains so.

V15 correctness producer748fc16 passesALL5,580 geometry/80,016 norm queries
(including independent exact sorted-prefix/ratio checks),225 forests,
3,501 products and300 Cartesian checks. Producer9d7aab9 completes ALL18
public rows without refusals/errors. The adaptive angular control beats
BOTH candidates in the BF16/epsilon0.5 core timing; this loss is preserved.
Other rows favor the candidates, but no independent speed gate was frozen.
No universal superiority follows. Next strengthen the inexpensive scalar
bounds to separate support loss before using Hellinger/chi-square.

V16 BEFORE code: `mass-aware-controls-v16.md` re-evaluates all eight criteria
and strengthens inexpensive scalar controls using common-support coupling,
certified Hellinger, both chi-square directions and likelihood ranges.
All75 oracle cases and ALL18 unchanged public rows are required. Old67.98x
is not attributed to these stronger controls. No favorable budget or corpus
selection; if a cheap bound suffices, the core certificate may be unnecessary.

V16 producerb969c64 is BLOCKED at the first independent forest: the imported
public-bridge scalar helper assumed node IDs were topologically ordered.
That bridge has this property; general CfgSampler.order need not match IDs.
Zero new scalar bounds were certified and the public run was NOT triggered.
All failure/metadata are preserved. V17 corrects the new control's scalar
evaluation to the declared plan.order; theory, cases/budgets and all eight
criteria stay unchanged. Do not reattribute the failure to corrected code.

V17 producer87a3b52 passesALL75 original-ID scalar-bound cases (27 undefined
mass cases) and ALL18 public rows, no errors/refusals. The stronger mass-aware
FP16 upper is0.0007602747856462345, against the endpoint0.1 upper
4.0946010443571345e-5. Thus the old67.98x comparison overstates the advantage
against the NOW strongest cheap control; report the strengthened curve.
The adaptive BF16/0.5 core win persists. Scalar chi-square's absolute64-bit
atom rounding can be unnecessarily loose under denominator imbalance; V18
will give it scale-aware relative precision before any consolidated claim.

V18 BEFORE code references the same eight answers and fixes only control
precision: `scale-aware-controls-v18.md` gives EVERY nonzero chi-square atom
64 bits of certified relative rounding precision, with polynomial bit costs.
Both directions get it, all75 oracles/18 public cases repeat, and prior
outputs remain true historical records. No new contribution is claimed here.
