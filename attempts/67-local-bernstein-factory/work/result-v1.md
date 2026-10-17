# A67 coefficient audit — PASS; full useful construction still under review

2026-10-17. Contract/proof9a22308 before frozen producer
14b2b7a3f58684b300ef60e0418660aa573b6cb7 and the ONLY execution, direct exit0.
No complete sampler, fast-bit implementation, input p-coin sampling, model,
tokenizer, dataset/gold, head/forward/update or timing benchmark was executed.

All six predeclared functions and every coefficient at16,64,256 were kept:
constant, affine, quadratic, cubic, nonanalytic C2 spline and its reflection.

| Independent obligation | Exact checks |
|---|---:|
| Coefficient boxes and valid three-point stencils |2,034|
| Finite difference against independent analytic second derivative |2,034|
| Common-denominator premise |2,034|
| Hypergeometric elevation versus independent power-basis conversion |1,932|
| Normalized positive-mixture coefficients in[0,1] |1,356|
| Rational-p approximation/bracket/truncation comparisons |126|
| Invalid degree/metadata refusals |9|
| Raw/analytic-derivative/Boolean coefficient controls |36|

Every degree-elevation inequality passed; no coefficient was clipped. Both
stencil directions and points crossing the spline knot were included. The
independent power-basis computation uses a different exact representation
from the reference's combinatorial hypergeometric sum. The geometric-mixture
weight/tail/input-count identities also pass. In the spline example the
WRITTEN expected count is91/4; this is not a sampled empirical mean.

Cold coefficient calls are3 for the candidate versus17/65 f-values for the
ordinary Boolean sum at the checked interior degree16/64 queries. Analytic
correction uses one f-value plus one second-derivative value and is kept.
These are narrow deterministic query counts, not full generation latency or
a comparison with all other local methods/cached implementations.

Retain stronger unfavorable facts: for known polynomial formulas, a direct
classical mixture computes the quadratic link with expected p-coins
(1+p)/4<=1/2, and the cubic with(1+p+p^2)/4<=3/4. Those are far cheaper than
the candidate's17.5/25 bound. Constant/affine inputs also prefer their direct
classical factories. The candidate targets an effective GENERAL value-only
interface, not faster simulation of such known closed forms. HNP already
provides the smooth finite-mean existence result for the nonanalytic spline.

The separate AFTER-audit `cold-value-cost-v2.md` derives an expected value-
query bound and a restricted cold oracle-class comparison. It adds no
experimental gate or measured timing, and is not retroactively attributed to
the V1 producer. It explicitly leaves derivative/caching/other local controls,
input-coin work and whole-operation usefulness unresolved.

Scientific decision: the coefficient/proof obligations survive this bounded
audit. They justify completing the closest quasi-interpolant/implicit-reduction
audit next. They do NOT trigger a neural campaign, article promotion or a
full sampler/performance claim. The fast binary-split bit theorem is written
and the reference uses naive Fraction elevation; that code cannot inherit
the theorem's expected-runtime bound. Specific priority and a substantial
own useful consequence remain OPEN, as does the user's full objective.

Raw summary, full stdout and AFTER-run execution receipt are in
`docs/artifacts/raw/a67_local_bernstein_v1_initial`. Focused Ruff/format2 files
passed before source freeze. The maintained345-test suite was not rerun for
these isolated coefficient checks. Preservation checks follow separately.
