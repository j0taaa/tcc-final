# V11 — Strongest known residual construction and the remaining difference

2026-10-13. Primary reading, not a model experiment or human review. V1–V10
remain unchanged. This audit deliberately strengthens the comparator before
any measurement. Tests do not answer this anteriority question.

## 1. The product case is already an immediate sampling consequence

[Feng, Guo, Jerrum and Wang2023](https://arxiv.org/html/2208.00740v3), entire
Section3 and all its proofs, constructs C(w)=product_i min(P_i(w_i),Q_i(w_i)),
r=1-sum C, and samples pi=(P-C)/r. Its exact bounded estimator is
f(w)=(P(w)-Q(w))_+/(P(w)-C(w)). Sampling pi and accepting a Bernoulli f is
therefore EXACT residual sampling, with conditional mean attempts at most n.
No product-residual priority or invention of this acceptance identity is
defensible for A50. The operation follows immediately even though the paper
uses f for TV estimation instead of returning residual samples.

## 2. Dependence and the factor2D argument also have a direct antecedent

[Bhattacharyya et al., ICML2024](https://proceedings.mlr.press/v235/bhattacharyya24a.html),
full Section4 and Appendices A.2–A.7, defines a local partial coupling of
same-DAG Bayes nets. It computes the same product of minima of conditional
kernels, the same proposal and the same f. Lemma4.7 bounds r<=2n*TV using
conditional differences, triangle inequality and data processing. The
complete proof was read. A50 V8's trace argument is this principle for a
bounded derivation process;2D is not an independently new coupling bound.

Their Claim4.4 samples pi by O(n*q) inference calls; changing bounded f into
Bernoulli rejection immediately gives polynomial exact conditional residual
sampling whenever those calls are efficient. Their stated TV-estimation
runtime is a different operation and must not be quoted as the cost of one
residual output. No artificial epsilon-estimation factor is charged to them.

For a word-faithful forest, a sequential derivation process can be represented
by a state (pending nodes, current marks) and normalized local kernels. This
state space may be large if materialized. A50's useful implementation property
is that common/difference inference is performed directly on the compact
forest, with subtraction-free channels; the pending stack is traced only for
an actual output. Ordinary weighted-circuit sampling and the positive product
difference identity already furnish those channels. Thus the scalar operation
is a compact specialization of a competent combined classical construction,
not a new way to overcome the TV rarity factor. No asymptotic separation from
that equally compact combined control has been established.

## 3. Bounded-bit rounding and equality do not rescue priority by themselves

Dyer2003, sum-approximation calculus2018 and the actual Rizzi/Tomescu2019
sampling original already supply rounding, retained sampling information and
exact rejection. V9's dyadic scaled common submeasure remains a correct useful
engineering construction, but a claim of substantial own novelty requires
more than these standard operations plus the2024 coupling principle.

[Wainwright and Jordan2008](https://www.cs.princeton.edu/courses/archive/fall11/cos597C/reading/WainwrightJordan2008.pdf),
Section3.5.1 Proposition3, complete proof and the following overcomplete
parameter discussion, identifies the standard mean/parameter correspondence.
V9 uses its elementary distribution-level Jeffreys argument, including zero
supports separately. Equal marginals determining this conditioned unary
family is not claimed as a new statistical theorem.

## 4. Other competent contracts

[Anand, Benford and Guo2026](https://arxiv.org/html/2607.27088v1), entire
Sections2–4 and their proofs, gives linear-input-time RANDOMIZED relative TV
estimation for products, via a filtered martingale estimator with constant
relative variance. This supersedes comparisons that treat the2023 estimator
as the strongest current product estimator. It does not directly generate
exact positive residuals or give deterministic TV intervals. Its real-RAM
contract is declared; neither hardware superiority nor exact-bit costs were
inferred from its arithmetic expression. This paper cannot be ignored merely
because A50 does not currently estimate TV.

[Ciotinga and Choi2025](https://proceedings.mlr.press/v286/ciotinga25a.html),
full Sections3.1/3.2, Definitions2–4, Proposition1 and Algorithm1, optimizes a
restricted coupling-circuit Wasserstein objective on compatible hierarchical
partitions. Internal marginal constraints are stronger than whole-output
marginals. Its contract is not exact TV or whole-word coalescence; that is a
scope difference, not a claim that A50 dominates its transport algorithm.
Appendix proofs were not read completely and are not described as verified.

## 5. Current decision

The verified residual operation, finite bit bounds and compact references
are retained. The proposed scalar mathematical advantage is now explicitly
accounted for by a stronger known construction. The profile reference can
trade more preparation for fewer conditional attempts, but has no demonstrated
paid benefit over the scalar control. A50 is NOT promoted as a substantial
novel theorem or a publication-ready decoder. Neither A49's negative storage
results nor A24's separate wins are transferred to it.

The next permissible work is a small, prospective operational investigation
with this strong control, or an explicitly new result that survives this
reduction. Both must identify their actual dLLM/CFG consumer and full costs
before implementation or observing performance. Counting more finite law
checks is not the user's scientific objective.
