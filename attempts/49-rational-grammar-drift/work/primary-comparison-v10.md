# Quantitative distinction after the adversarial primary audit

2026-10-12. Written mathematical comparison, not peer review, a priority
certificate or an experimental latency ranking. V1 remains preserved.

## Exact nearest antecedents

| Primary result actually read | Already known | Remaining quantitative distinction |
| --- | --- | --- |
| Feng/Liu/Liu, SODA2024, Theorems1/2, sections4/5, arXiv2309.14696v1 | Deterministic relative TV approximation for arbitrary products/Markov trajectories; likelihood-ratio sparsification | Our product recurrence has arithmetic bound O(nq sqrt(n/epsilon) log(qn/epsilon+2)), rather than their stated O(qn² epsilon^-1 log q log(n/(epsilon TV))). These are upper bounds, not an implementation lower bound. For the same multiplicative convention use their error epsilon/(1+epsilon). |
| Fu2609.24235v1, computational model, Lemma3.5, Definition3.6/Theorem3.8, Corollaries1.4/1.5 and section4.1 | General admissible-gate composition; paired product bound O-tilde(nq(n/epsilon)^4); arithmetic bound independent of positive TV; arbitrary acyclic admissible gates | Dimension2 has an integer endpoint core of size O(sqrt(d/epsilon)), built in O((m+k) log(m+2)) operations. The complete bit proof needs neither ideal real primitives nor a numeric probability floor. Generic CFG feasibility is NOT new. |
| Bhattacharyya/Cormode/Fu/Meel2609.18707v2, Theorem4.1 and Lemma4.1 | Domain compression for smooth decomposable PCs on a common v-tree; determinism is NOT required in v2 | Different splits in a word parse forest need not share a v-tree. This scope observation is not a lower bound against all possible encodings; Fu's generic framework already covers admissible forest gates. |
| Bhattacharyya et al., ICML2024, Theorem1.1 and ENTIRE section4 (Algorithm1, Claims4.2--4.6, Lemma4.7 and its proof) | Randomized relative approximation via partial coupling and derived probabilistic inference; local-CPT overlap removes rare-event rejection | An appropriate derivation encoding can supply a competent randomized alternative. Do not claim that grammatical conditioning first becomes approximately computable here. Our certificate is deterministic and has a different precision exponent. |
| Har-Peled/Jones, complete three-page proof of Dudley's approximation, Theorem1.1 | Outside-point projection and quadratic support error; optimal planar polygon order | Classical geometric ingredient. Our construction keeps ORIGINAL integer endpoints, giving integer generators and the TV bit-cost/recurrence bound. The square/projection principle is not invented here. |
| Lützow/Kochdumper/Althoff2025, published sections2--4 | Underapproximate zonotopes by aggregating generators, including heuristic clustering | The read clustering passages do not state our all-query relative tolerance/runtime. This is not a claim to have audited every proof in that paper. |
| Anand/Benford/Guo2607.27088, Algorithm1 and Lemmas2--4 | Linear-time randomized relative TV approximation of product distributions | A competent stronger alternative when random failure is acceptable; no physical speed dominance over it is claimed. |

Primary URLs: <https://arxiv.org/abs/2309.14696>,
<https://arxiv.org/abs/2609.24235>, <https://arxiv.org/abs/2609.18707>,
<https://proceedings.mlr.press/v235/bhattacharyya24a.html>,
<https://sarielhp.org/p/17/dudley_approx/dudley_approx.pdf>,
<https://mediatum.ub.tum.de/doc/1791694/ha1wphfu5k9dd3qnom2gjfy8m.2025-07-18_PublishedVersion.pdf>,
<https://arxiv.org/abs/2607.27088>.

## The ICML objection, rather than an artificially weak adversary

A normalized unambiguous event forest admits a generative derivation encoding.
For every reachable nonempty node, use its exact inside mass to normalize
the probabilities of its local alternatives. Activate children selected by
their parents; unused nodes take a canonical inactive value. Decomposability
prevents a nonempty node appearing twice in a derivation. Original assignments
and complete choice/activation vectors are bijective. Thus TV is unchanged.
Deterministic activation can be encoded with polynomially many Boolean gates;
do NOT write an exponential CPT for a node with many possible parents.

The local overlap h is the minimum of the two normalized alternative
probabilities (inactive/deterministic factors are1). The particular diagonal
and topological-prefix queries in ICML Algorithm1 are weighted inside queries:
replace local alternative weights by h and clamp the already known active
choices. A topological prefix determines activation of every visited node;
it does not impose arbitrary future activation constraints. This is the
reason that generic BN inference need not be presumed tractable. Zero-inside
states are never reached in the corresponding head and receive an arbitrary
canonical CPT. Both root normalizers must be positive.

This reduction is a classical specialization, not a new claimed FPRAS.
Its exact construction/implementation has NOT been benchmarked here. It is
enough to reject the claim that only our method can approximate grammatical
drift. The published ICML bound has epsilon^-2 and a random failure parameter;
it does not provide this deterministic integer-core precision bound.

## Novelty matrix and what is actually worth writing

**Known:** TV as a support query, admissible-gate error propagation, planar
convex approximation, nearest-point queries, LL(1) parsing, token lifting,
TV data processing, trajectory coupling and probability-table rounding.

**Written comparative result:** the integer endpoint/query construction gives
the product bound above and O(H(d/epsilon) log(d/epsilon+2)) core operations
for bounded-fan-in forests with bounded leaf lists, with polynomial bit cost.
It improves the stated deterministic upper bounds just identified. No new
geometric exponent or optimality lower bound for TV is claimed.

**Concrete useful operation:** certify the drift of the FULL original-token
grammatical posterior after probability-table rounding. All six predeclared
cases completed. Strong inexpensive Hellinger/range controls are retained;
they are faster, but their guarantees can be substantially looser. The
FP16/epsilon0.1 upper certificate is about4.095e-5 against2.784e-3 from
Hellinger. This is certificate precision, not semantic quality/EPIC speed.

**Open external judgement:** exhaustive literature priority, independent human
proof review, venue-specific significance and editorial acceptance. Neither
finite tests nor AI confidence resolves these. The defensible submission
claim is a quantitative deterministic algorithm and its integer/grammar
corollary, not discovery of a new inference principle. This warrants a full
mathematical draft and adversarial checking; it does not warrant claiming
that publication is guaranteed or promoting the whole decoder as faster.

## Source-admission qualification found during review

Trim unreachable and unproductive nonterminals before the LL(1) source theorem.
Unambiguity of the start language alone need not certify an unused chart cell.
For a trimmed grammar, ambiguity of a productive cell can be embedded in a
start derivation and is therefore excluded. Interior token-trie paths without
a closure edge are unique, so an empty original-slot scope is unit/zero.
This is an explicit mathematical hypothesis/standard preprocessing step, not
a claim that the existing Python source normalizer was formally verified.

Literature search repeated2026-10-12 for deterministic/product TV,
zonotope/Dudley/integer planar compression and grammar TV; primary versions
above were checked. Absence from these searches is not absolute priority.
