# Prospective minimal V3 audit, before code

2026-10-17. Quantitative-gap-v3.md and README reassessment precede code.
Only exact constructed correctness/certificate checks follow; NO timings,
new model/data/labels or practical benchmark. V1/V2 source/evidence unchanged.

Implement a compact finite-R wrapper using the same immutable predicate,
reading a binary R and comparing the selected n with R before source calls.
Keep independent auxiliary bit counting and malformed-input guards. The
declared binary-parameter cost is charged in the proof, not timed as a win.

Freeze source AND independent auditor before ONE execution, inspecting lint
exit before proceeding. An execution after a failed freeze is not permitted;
any error/source/run must be preserved without rewriting earlier evidence.

1. Independently differentiate binomial word probabilities by Leibniz for
   m0..32, p1/8,..,7/8, r1..4. Check the exact score squared-norm identity,
   Cauchy L1 bound and the constant160 where p belongs to[1/4,3/4]. These
   finite checks do not replace the written orthogonality proof for all m.
2. Check exact fourth differences of bounded Bernstein polynomials against
   both derivative and range bounds, using small degrees/independent integer
   combinations. Confirm the multiscale majorant sum<=128m on a fixed finite
   grid: m0..128 and2^j-1,2^j,2^j+1 for j0..80, scales n4..64. No claimed
   enumeration of all kernels or all m; the universal bound is written.
3. Check rational peak/interference inequalities, the explicit constants and
   base/induction arithmetic for the off-centre sequence and source-cost
   tail. Preserve all finite checks. Do not calculate huge g_n at n>=4 and
   present its analytical bounds as sampled/empirical probabilities.
4. Force finite wrappers R0/1/2/3/30 and a huge binary R: base tickets,
   excluded n (zero input), passed/rejected gates, accepting n1 and rejected
   zero sources at n2/3/30. Match complete result/call/aux counts to a separate
   literal truncated controller. Exhaust small auxiliary words where relevant.
   All are finite deterministic transcripts, not neural/iid observations.
5. Guard invalid bits, binary encodings, limits and source values. Report
   hashes/direct exit and maintained-suite scope. No implementation of a
   nonadaptive optimum, stochastic cost run, external consumer or article
   promotion is triggered by passing this finite audit.
