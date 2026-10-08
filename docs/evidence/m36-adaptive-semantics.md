# M36 continuation — delivered semantic-core reference

This records technical delivery, not human-review approval, exclusive priority,
whole-source formal verification or production-decoder promotion.

## Operation and useful guarantees

Generate Boolean JsonLogic rules matching supplied input/output examples, under
the current dLLM's finite original-token product distribution. Fixed positions,
byte aliases, support normalization and absent EOS retain their declared
contracts. Ordinary ASCII field names and shared prefixes are admitted; dotted
paths, non-Boolean values and correctness on unseen records are excluded.

`scripts/exact_commit/adaptive_semantics.py` supplies:

- An exact conditional stream with at most `m` rejected complete rules over the
  entire stream for `m` supplied requirements, when required refinements fit
  resource limits. Zero probability and unresolved resource refusal differ.
- A sufficient-core certificate using positive auxiliary weights on **every**
  supported token. Pointwise equivalence survives arbitrary reweighting,
  support contraction and added commitments; expansion/released commitments
  require recertification. Model-zero tokens cannot hide violating paths.
- Queries whose profile exponent is certified core size `k`, rather than total
  supplied examples `m`. Preparation and integer bit costs are additional.

The supplement contains written proofs R1–R3, Proposition C1's finite-batch
expected-rejection comparison, a scoped exponential zero-rejection prefix
representation gap, all-profile join bounds and total/bit
costs. Classical conditional sampling, CEGIS, example selection, transforms and
compact semantic automata/factor representations remain credited antecedents.
These guarantees do not establish an exclusive new inference principle.

## Frozen complete audit, including losses

Producing source: `30e6ac38aac69ddc0e9ccad6c0ac06d36016fa9c`, clean before
`python -m scripts.exact_commit.audit_adaptive_semantics --output
docs/artifacts/raw/m36_adaptive_semantics_v1`.
Configuration: `configs/experiments/m36_adaptive_semantics_v1.json`.
Raw archive: `docs/artifacts/raw/m36_adaptive_semantics_v1/`.
Generated report: `docs/research/generated/m36-adaptive-summary.md`.
Generated manuscript table: `paper/generated/m36-adaptive-table.tex`.

Every label of the unchanged MDLM canvas is retained: 256 targets, three seeds,
108 original-token programs, 17 positive targets. Each of five methods resolves
51 positive and 717 zero rows with no refusal. Independent enumeration checks
all masses, all returned paths and every core on every represented path.

Enumeration is fastest on this small support. Core median batches are cheaper
than eager-profile batches, but certification makes its total cost worse in this
audit. Prefix control has a perfect enumeration-backed oracle and shares its
preparation; its timing is not native CARS or EPIC. Blind rejection expectations
use the same product law and are derived geometric identities, not measured
decoder performance. This is developmental evidence, not held-out generalization.

## Current verification and source boundaries

- `make check`: pinned upstream, lint, formatting and typing pass.
- `make check test research-note` passes all 25 focused checks, including C1's
  exhaustive decision-tree oracle
  against an independent finite Markov recursion, with uniform and unequal
  weights and a positive-probability worst-case rejection branch. It brings the
  suite to 25. C1's general expectation proof is written, not mechanized.
- The preceding `make test`: 24 focused checks pass. This includes sampling-decision
  laws, independent execution/token enumeration, zero-weight reweighting and
  archived current-code recomputation of the first positive and zero targets.
- A correctness corollary independently enumerates 72 generic AND/OR programs
  over all 64 distinct six-field records: a certified two-example core retains
  exactly the two valid programs, beyond eager admission's twelve-record cap.
  This is not used as a speed benchmark.
- `make build-rust`, `make article-results-check` and `make paper` pass; the
  3,683 historical artifacts and 16-page main manuscript remain preserved.
- `make check-formal LAKE="$HOME/.elan/bin/lake"`: 66 selected statements
  pass the approved-axiom audit. Sixteen new statements cover progress, parity
  prefix exclusions and structural-core implications. The full iid law,
  positive-uniform CFG count construction and Python source remain written or
  independently tested obligations, not Lean source refinement.
- `make research-note`: final eight-page C1 supplement passes layout/reference
  checks; rendered pages are inspected. The main manuscript remains sixteen pages.

Source CI [37723768912](https://github.com/j0taaa/tcc-final/actions/runs/37723768912)
passes the source-stage 22 tests, Rust, historical artifacts and Lean. Subsequent
archive/current-code and identifier checks bring the suite to 24; final CI
confirmation is recorded separately rather than attributed to this older run.
The archive/identifier source `3b983020fa43e1a8e45ebbe460242aa9dc1e6951`
passes [37725286998](https://github.com/j0taaa/tcc-final/actions/runs/37725286998),
including all 24 then-existing tests, Rust, artifacts and Lean. That run does
not include the subsequent C1 oracle.

The optional local pinned JsonLogic consumer additionally passed 144 execution
checks under Node `v24.19.0`: all 16 assignments of four ordinary identifier
fields on their variable/AND rules, and all 32 length-five NOT/identity choices
under both Boolean anchor values. Consumer SHA-256 is
`73a6dc521e8990c2eed330dcfdb35605d7e1065a6e19d26673cb7ad4cd09d881`.
This local consumer check is not attributed to the offline CI path.

No advisor comments, independent human review or publication acceptance have
been invented. The research notebook keeps those open scientific gates separate
from completed implementation/proof/audit obligations.
