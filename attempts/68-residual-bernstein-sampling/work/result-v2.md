# A68 V2: same source-count law, at most nine callback queries

2026-10-17. V2 proof/prospective addendum b7acbb0 BEFORE new source
13e5aa14072473fe60db0c9232f6f1f7b17e39de and ONE scientific execution,
direct exit0. Initial lint complaint about an assigned lambda was fixed
before source freeze/execution. V1's source/raw result remain unchanged.
Diagnostic elapsed5.958s is not a speed comparison.

All V1 finite cases were retained. The new exact audit passes:

| Obligation | Checks |
|---|---:|
| Complete conditional-law equality with the tighter H-gap classical operator |966|
| Every residual/branch probability/callback count |40134|
| Envelope mass, deterministic term, setup calls |966 each|
| Sharper first-difference slope bound against analytic derivatives |41100|
| Strict safe mixture margin |966|
| Zero-H exact polynomial points / invalid refusals |21 /9|
| Collected nonzero coefficients for the restricted exact-evaluation bound |1032|

The WRITTEN V2 theorem uses the classical Peano slope bound H/(3m) to
reduce the known envelope mass to19H/(24m^1.5). Its margin is at least
H/(28m^1.5). The same importance mixture therefore uses the SAME tighter
H-gap source-count law as the classical dense coefficient sampler:

    E N=n0+12H/sqrt(n0), total callback calls<=9.

For the original spline, both written input means are41/2, and the proposed
callback expectation is bounded by183/56. The nine-query cap is deterministic
for each output of the written construction; the reference enumerates
conditional paths and does not implement the complete outer sampler or a
fast bit engine. Finite cases validate identities, not the universal theorem.

This is a DIFFERENT V2 law/envelope from V1's enlarged2H implementation.
V1 paid a source-count penalty and remains preserved literally. No V1 data
is attributed to source13e5aa1 or the later sharper derivation.

The comparative lower bound is only for EXACTLY EVALUATING the old scalar
coefficient in a smooth value-oracle class with strict slack. It is not a
lower bound against all samplers, formula-aware integration, derivatives,+caching or other coefficient-free algorithms. Classical importance/sign/
Peano/quasi-interpolant principles are credited. A sufficient own novelty,
practical complete-cost advantage and the user's goal remain OPEN.

Next justified work is closest coefficient-free/importance/lazy-integration
comparison and a charged cost argument for an independently identified
callback use. Do not manufacture a slow callback or promote query counts to
latency. No automatic production sampler/neural/performance campaign follows.

Zero full samplers, p-coin simulation, model/tokenizer/dataset/gold loads,
forwards, updates or performance tests. Source/hash/raw receipt and all
enumerated results: docs/artifacts/raw/a68_residual_bernstein_v2_initial.
Own Ruff/format2 passed before freeze; maintained345 tests were NOT rerun.
