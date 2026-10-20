# A79 — Offline development result V1

2026-10-20. **Nonpositive development application; not a qualified TCC topic.**
The written arithmetic theorem survives. No operational advantage over the
competent controls was demonstrated. The campaign is complete and will not be
expanded to obtain a favorable gate.

## Frozen operation and evidence

The protocol was frozen in `fb184931`, with prospective clarifications in
`958a8278` and `821031ed`. The executable producer is
`821031ed28c75716ae901288051b8ecda1920778`. It predates every performance
measurement. Full source hashes are in
[metadata.json](work/evidence/offline-v1/metadata.json).

The operation is one numerical evaluation, original-ID sample, original-head
confidence and deterministic commitment mask per supplied finite dyadic head.
EOS is absent. The symbolic structure is cached. All inputs are synthetic;
there are no model forwards, model downloads, training or GPU measurements.
Uniform profiles intentionally repeat heads; exact services may exploit that
or amortize preparation across many outputs, unlike this cold-numeric contract.

All 27 preparations and all **2,160 timed queries** completed. Every query passed
the independent byte recognizer and original-ID validation. No refusals,
timeouts, correctness failures or interruptions were omitted. The interval
control needed no exact fallback in the timed queries; its fallback was tested
separately, including preservation of the existing uniform prefix.

## Frozen gate

The primary candidate was `sr_shared`. The controls were `exact_plan`,
`sr_singleton`, `nearest`, and `interval64`. The exact control performs no outside
or marginal calculation. All four controls remain in the comparison.

For each case, divide the candidate's median query time by the smallest control
median; for each family, take the median of all nine case ratios:

| Family | Candidate / best control | Time gate |
| --- | ---: | --- |
| All binary words | 1.9044 | Failed |
| Two constant-word modes | 1.6384 | Failed |
| Typed Dyck, including an alias ID | 6.1540 | Failed |

The exact integer control was fastest in **27/27 cases**. Individual ratios range
from 1.2715 to 9.7384. No family met the required 20% reduction; two families were
required. These are CPU implementation measurements, not lower bounds on every
possible implementation and not neural decoder speed ratios.

The actual total resident-memory gate is **inconclusive**. Recorded Python
object sizes and ideal packed payloads are diagnostics, not isolated RSS/peak
measurements. The runner retains the original forest for comparison and
validation; it is not a measurement of a minimal deployed consumer. The original
control also retains vectors for all compiled cells while evaluating only the
reachable order. Compacting it could further change memory and cost comparisons.
Neither diagnostic supports a memory-win claim.

The [decision.json](work/evidence/offline-v1/decision.json) records
`nonpositive_development`, with zero approved time-gate families and no TCC,
neural-speedup or GPU-speedup claim.

## What did improve, and why it is insufficient

SR used 6–8 significant bits under its sufficient TV certificate. The nearest
certificate used 11–16. Against the improved generic stochastic moment control,
the candidate used the **same precision in 15/27 cases** and one fewer bit in
12/27. Thus the broad comparison against nearest does not describe the entire
own contribution.

Shared rounding used 114,088 arithmetic random bits versus 178,468 for singleton
groups: a **36.07% observed reduction** over all specified trials. This is a PRNG
program observation, distinct from the theorem's expected random-bit bound.
It did not provide a competitive complete-query time. As proved separately,
sharing can also increase actual bias on some inputs; no accuracy dominance is
claimed.

Circuit sizes ranged from 63 to 2,044 stored gates; conservative path budgets K
ranged from 30 to 767. Across all preparations, original compilation took
2.0988 seconds and binary construction/verification 0.1916 seconds. Cold
preparation and input generation are recorded separately from query timing.
Recursive object-size instrumentation and output validation were outside the
timers for every method. Backbone, dense neural head and transfer costs were
absent and cannot receive a saving claim.

## Mathematical status and decision

[theory.md](theory.md) preserves the executed-law identity, bilateral error
envelope, generic stochastic comparator, order-matching lower bound for this SR
strategy, and counterexample to universal accuracy improvement from sharing.
These statements concern fresh-noise mean output laws under explicit circuit
hypotheses. They do not cover arbitrary random tables, adaptive reuse, rounded
marginal selectors, native neural trajectories or semantic correctness.

Independent agent audits accepted the numerical theorem conditionally. They
did not establish specific scientific priority or sufficient novelty for a strong
TCC; the generic moment argument already attains the same asymptotic order.
There is no human academic approval or Lean verification. Correct implementation
and lower precision did not settle useful own-method improvement here.

**Decision:** preserve the mathematical result and this complete negative time
comparison; do not select A79 as one of the three positive topics requested.
Do not broaden cases, lengths, seeds, controls or hardware campaigns to rescue
this frozen development gate. A71 and the earlier closed applications remain
untouched. The original research objective remains open.

## Reproduction and integrity

At the producer commit, with the existing development environment:

```bash
.venv/bin/python -m attempts.79-stochastic-circuit-sampling.run --check
.venv/bin/python -m attempts.79-stochastic-circuit-sampling.run --output /tmp/a79-new-output
```

The output directory must not already exist. The runner writes all rows and a
derived decision. The preserved archive contains the same row bytes compressed
losslessly, without keeping a second large plain copy. It has 2,322 records:
27 preparations, 135 initializations and 2,160 timed queries. Compression was
verified byte-for-byte and the decision recomputed before removing the plain
unversioned copy.

- Uncompressed rows SHA-256:
  `ea08cd69695c856eeee76e7fc4183feaf2d0f47075bb3cfd83ffdd7dba39288d`.
- Gzip SHA-256:
  `dcccdbfd4a254e103918259890d111e49e2ef8f89c0b1526562ee8ae4dcb5c00`.
- Compressed size: 250,574 bytes.

To recompute the preserved decision without executing measurements:

```python
import gzip, importlib, json
from pathlib import Path
p = Path("attempts/79-stochastic-circuit-sampling/work/evidence/offline-v1")
run = importlib.import_module("attempts.79-stochastic-circuit-sampling.run")
rows = [json.loads(line) for line in gzip.decompress((p / "rows.jsonl.gz").read_bytes()).splitlines()]
assert run.summarize(rows) == json.loads((p / "decision.json").read_text())
```

Before measurements, 31 A79 correctness tests passed, along with `make check`
(baseline integrity, lint, format, types and 345 maintained tests). These checks
are distinct from the scientific comparison above.
