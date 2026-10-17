# V4: executable GMP/bit factory preflight PASS

2026-10-17. Contract67bafcf BEFORE source
5775a89efa21def9e6ca891ec6ba50620e8561b6 and ONE execution/direct exit0.
Pre-freeze lint complaints were corrected before source/run. Runtime uses an
isolated Python3.11.16 environment, gmpy2 2.2.1 / GMP6.3.0, with pinned wheel
hash. The maintained .venv was unchanged. Diagnostic2.634s is not a speed
comparison. No prior V1/V2/V3 file or data was modified.

| Obligation | Exact/actual checks |
|---|---:|
| Balanced GMP binomials versus independent integers |8385 small +15 larger|
| Balanced weighted sums with varying denominators |103|
| Exhaustive bit prefixes: Bernoulli / geometric / uniform integer |30576 /13104 /26208|
| Repeated comparisons against one shared lazy uniform |1076|
| GMP proposal normalizers/plans versus Fraction |1347|
| Additional GMP proposal point weights |4041|
| Native dense/sparse conditional kernel pairs |966|
| Complete factory calls, all6 functions/3 p/32 seeds/2 methods |1152|
| Matched J,N,k/source-tape pairs |576|
| Actual calls to external input p-coins |24480|
| Base / higher cache replays |12 /18|
| Explicit over-limit refusal BEFORE any input coin |1|
| Invalid input refusals |8|

All1152 ordinary calls COMPLETE; no random resource failure or hidden rerun.
The separate deliberately over-limit call raises RESOURCE_FAIL, as required.
No output is credited from that call. Conditional native executions exercise
12 endpoint,270 fair,624 residual and60 deterministic-correction branches;
these observed counts are coverage, not probability or speed estimates.

The executable sampler now includes J selection, actual sampling-only input
coin calls, exact-bit scalar decisions, shared-uniform geometric inversion,
rational rejection proposals and terminal votes. Dense controls receive
balanced product trees and weighted sums, exact rational denominators and
value/scalar caching. Sparse methods have <=6 callback requests per output.
Fresh bits are drawn on cache replays; random outcomes are never cached.

Exact prefix checks preserve unresolved mass, rather than inferring a law
from output frequencies. Seeded demonstrations are not proof of iid physical
entropy or universal software correctness. The mathematical theorem assumes
iid fair supplied bits and valid supplied function/range/curvature contracts.
Source-count laws match, while different valid couplings need not return the
same literal output bit. P is only inside the external coin callable.

This is a full numerical FACTORY runtime preflight, not a complete genealogy,
biological validation, dLLM application, training or competitive benchmark.
The positive query/preparation theorem has an executable implementation, but
useful total wall/bit/memory superiority and sufficient own novelty remain
OPEN. Formula-aware spline/truncated-moment integration, analytic derivatives,
direct cheap polynomial factories, coefficient-free alternatives and global
cache reuse are still required BEFORE competitive timings. Do not benchmark
only a naive Fraction comparator or manufacture slow callbacks.

Raw summary, all1152 draws/input tapes and576 pair identifiers, stderr/stdout
and direct-exit receipt: docs/artifacts/raw/a68_exact_runtime_v4_initial.
Own Ruff/format2 passed before freeze; maintained345 tests were NOT rerun.
