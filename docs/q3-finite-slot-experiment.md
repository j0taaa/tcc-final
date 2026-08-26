# Q3 finite-slot experiment

Q3 asks whether an abstract ordered-anchor `Sigma*` representation can accept
a proposal combination that no completion on the physical token canvas can
realize. The experiment deliberately compares two different decision models:

- the relaxed abstract side checks a concrete grammar-valid token witness with
  unbounded gaps and does not allocate EOS or canvas slots;
- the finite side constructs the explicit per-position token lattice, composes
  the required-EOS policy, solves the CFG exactly on that represented support,
  and independently enumerates every finite token path.

The abstract side is a false-positive baseline only. It is not an exact solver.
The finite result is always scoped as `exact_on_support`; an
`INFEASIBLE_ON_SUPPORT` result says nothing about tokens outside the explicit
fixture rows. A replay error or deadline failure is recorded as an experiment
failure with no finite decision, never as infeasibility.

## Configured corpus

`configs/experiments/q3_finite_slots_v1.toml` freezes the two curated T703
one-slot counterexamples. Both contain an abstract one-token witness plus a
required EOS, so the witness needs two physical tokens while the canvas has
one slot:

- one finite instance has no grammar-valid represented path;
- one admits a lower-scoring EOS-only completion, whose full token/edge witness
  and objective are recorded.

Real decoder-state mining is explicitly disabled in this version. These cases
are synthetic claim witnesses, not an estimate of how frequently the mismatch
occurs in a model workload.

## Reproduction and artifacts

Run:

```bash
source .venv/bin/activate
python scripts/exact_commit/run_q3_finite_slots.py
```

The ignored run directory contains:

- `resolved-config.json`, including the normalized configuration hash;
- `q3-finite-slot-rows.jsonl`, one immutable row per counterexample;
- `q3-finite-slot-summary.json`, computed only from those rows' in-memory
  records.

Every successful row records available slots, the minimum physical tokens for
the abstract witness, its concrete token witness, the abstract decision, the
finite status, the finite witness or explicit reason, represented-support hash,
EOS policy, and independent enumeration checks. Single-run timings are smoke
diagnostics and are not publication benchmark measurements.
