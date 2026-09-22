# M16: scientific evidence beyond fixed literal tasks

## Contribution and a falsifiable motivation

The central subset-to-completion equivalence is a short reduction. Weighted
CKY and CFG/automaton intersection are established, not new discoveries of this
project. Its substantive contribution is the precise commitment objective,
finite-token construction, certificate and exact reference for heuristic loss.
No claim of exhaustive literature priority is added by this maintenance work.

There is a simple worst-case reason to study an exact reference. Consider the
constant-size regular grammar `S -> a B | b A`, `A -> a A | epsilon`,
`B -> b B | epsilon`, a length-n canvas, full `{a,b}` support at every slot,
and unit proposals for `a` at all positions. Give the first proposal strictly
higher model confidence than the others. For n >= 3:

- A confidence-ordered feasibility-preserving greedy selector accepts the
  first proposal, leaving only `a b^(n-1)` feasible. Its utility is 1.
- The other completion, `b a^(n-1)`, has utility n-1 and is optimal: these are
  the only two permitted words of length n.
- The greedy/exact ratio is 1/(n-1), so this policy has no positive constant
  approximation guarantee across unbounded n, even for this regular subset of
  CFGs. This is a worst-case construction, not an estimate of real-model loss.

`tests/exact_commit/test_greedy_worst_case.py` exercises n=3,4,8,16,32 through
both independent backends. This statement concerns the explicitly named
finite-support greedy selector, not EPIC's full decoder or its approximation
ratio. It is an elementary supporting observation, not a priority claim.

## Evidence policy

The prospective protocol is
[`ADR 0023`](decisions/0023-nontrivial-evidence.md). Generated conditions,
real-model capture, and end-to-end tasks must remain separate evidence tiers.
The new family grammars accept recursively nested, multiple-output languages;
task answers are checked independently and do not change grammar productions.

The development campaign uses
`configs/experiments/m16_branching_v1.toml`. Raw inputs, outputs and source
hashes are saved under
`results/raw/m16_branching_v1/20260905T164909861792Z/`.
Its generating command was
`.venv/bin/python scripts/exact_commit/run_branching_study.py`.
The generator's seeds are 160100--160199 per family. There are 300 family/seed
states but only 100 shared seed clusters across families. Four support/weight
conditions per state are repeated measurements, not independent samples.
The run is explicitly dirty-tree development evidence; it cannot replace the
article's committed-source measurements.

The first execution, `20260905T163430145325Z`, is retained separately. Its
summary called family/seed states independent; that label was corrected before
any inferential claim. The v2 summary explicitly records shared seed clusters.
Repeating the same configured study after that reporting correction does not
add independent samples. The initial generated v1 report is superseded by v2.

Quantitative summaries and the complete source/metadata record are generated
from the raw JSONL, not hand-entered into the manuscript. The results must not
be described as measured EPIC speedups or representative model improvements.

The [generated report](evidence/m16-branching-development-v2/report.md) records
all 1,200 conditions, zero correctness failures and all selector status counts.
Both exact backends return independently checked optima on every condition.
Greedy loses in only a few strata; branching is common but does not itself imply
a heuristic gap. The observed support-width improvements motivate support
sensitivity experiments, not a claim about typical real-model behavior.

## Reproduction and verification

```bash
.venv/bin/python scripts/exact_commit/run_branching_study.py
.venv/bin/python scripts/exact_commit/analyze_branching_study.py \
  --run-directory results/raw/m16_branching_v1/20260905T164909861792Z \
  --output-directory docs/evidence/m16-branching-development-v2
```

Use fresh destinations for repeated executions; neither command overwrites an
existing run/report directory. The raw SHA-256 verified by the analysis is
`5e8cd203cca175ef911e14125b2d3acee9e3b5d4bd82ec1e4474a94c05808642`.

- `.venv/bin/python -m pytest -q`: 817 passed.
- `.venv/bin/python -m ruff check src tests scripts`: passed.
- `.venv/bin/python -m mypy src`: passed, 75 files.
- `make test-rust-parser`: 22 tests; both crates passed format and Clippy.
- `.venv/bin/python scripts/rehearse_release_wheel.py`: archive inventories,
  isolated imports, Q3 and artifact smokes passed.
- `make final-artifacts-check article-results-check`: passed unchanged.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=vendor/EPIC-Decoding .venv/bin/python -m
  pytest -q vendor/EPIC-Decoding/tests/test_constrain_utils.py
  vendor/EPIC-Decoding/tests/test_bindings.py`: 19 passed, four upstream skips.
- `./scripts/verify_upstream.sh`: passed after relocating the one generated
  Python import-cache file from the environment preflight; vendor source and
  license provenance are unchanged.

## Remaining gates

The real-model and end-to-end evidence remains incomplete until a free GPU,
the frozen code/config checkpoint, captured genuinely competing model states,
and independent quality/cost measurements are available. An idle singleton
support, a literal grammar, or repeated timing of the same answer cannot meet
this gate. Pilot failures will be retained; the confirmatory task set and
sample size must be frozen before its runs begin.
