# Repository review hardening

This working record covers the post-v0.1.1 code review. The existing publication
artifacts remain historical evidence produced by their recorded commits.

## Contract

Preserve exact-on-support, per-step optimization, all positive proposal matches,
fixed slots, explicit EOS/PAD semantics, complete witnesses, independent parser
implementations, and distinct non-optimal statuses. Public scores remain
Python float/Rust f64. Repeated validation of immutable internal objects may be
consolidated, but the final independent witness validator remains mandatory.

## Findings and validation

All seven concrete findings from the review are addressed, together with an
additional evidence-overwrite bug exposed by the final verification run.

| Finding | Change | Regression coverage |
| --- | --- | --- |
| Stale validated result could be applied to different proposals | Bind commit authority to the frozen canvas and complete proposal tuple, before consuming generators | `test_review_boundaries.py`: changed, added, deleted unmatched proposals; remasked canvas; both solve APIs |
| Rust build outputs contaminated the source archive | Explicit sdist source selection and nested build exclusions; inspect both source archive and wheel | `test_release_hardening.py` and isolated release rehearsal |
| Floating-point grouping changed the optimal witness | Exact internal score ordering; preserve individual terms through duplicate aggregation, token expansion and epsilon closure | `test_exact_scores.py`, Rust score tests, independent exhaustive campaigns |
| Optional/absent EOS never completed a full canvas | Completion accepts fully committed canvases when EOS is not required | `test_llada_adapter.py` |
| Missing support check appeared fully validated | Record omitted support checks and supply a real support predicate in the token-aligned reference | `test_validator.py`, `test_token_aligned_certificate.py` |
| RSS sampler leaked threads after boundary failures | Join on every measurement exit; propagate background-reader failures | `test_robust_timing.py`: setup, clock, RSS and accelerator errors |
| Development and CPU environment could drift | Exact dev pins, transitive CPython 3.11/Linux constraints, build constraints, Rust 1.98.0 and locked Rust resolutions | Resolver checks, CI/Makefile checks and Rust gates |
| Differential runners overwrote historical evidence | Fresh output directories, explicit destination option, exclusive creation and dirty-worktree metadata | `test_campaign_output.py`; original evidence files restored byte-for-byte |

### Numerical contract

The objective is the exact real sum of the finite, non-negative binary64 input
weights. Public input and output scores remain Python `float`/Rust `f64`.
Python's comparison keys use `Fraction`; Rust independently sums the same
binary64 values as integers in units of 2^-1074. The public objective is rounded
once, with ties to even. Distinct exact objectives can have the same rounded
public float; the witness is nevertheless chosen using the exact ordering.

Original `weight_terms` survive duplicate-proposal aggregation and epsilon
normalization. Their rounded sum must equal the existing public `weight`.
Backtracking checks exact child sums as well as recorded float scores. The new
Rust dependencies, `num-bigint` and `num-traits`, avoid implementing custom
large-integer arithmetic; both versions and transitive checksums are locked.
Scores outside the finite public range still cannot produce an `OPTIMAL`
public result. This is per-step exactness on represented support, not a
full-vocabulary or future-trajectory claim.

### Simplification and skipped-work justification

- Replaced five copies of JSON freeze/thaw code with one small private module.
  Reference parsing algorithms remain independently implemented.
- Removed the unused logit-matrix adapter helper, repeated successful-canvas
  application, and duplicated Python profiling branches.
- Batched tensor ranking and witness-probability gathering. Compact results
  cross the CPU boundary once per operation instead of once per row. Tie and
  infinity behavior is checked against the dense reference; no GPU speedup is
  claimed without new measurements.
- Epsilon-free normalization returns the original graph with identity edge
  provenance. With no epsilon edges, no closure can add a path or reward.
- Rust visits only split states having a left chart entry, and retains only the
  best candidate per head for a span. A missing child cannot derive a binary
  production; a lower-scoring derivation with identical endpoints and head is
  interchangeable in every surrounding grammar context. Stable traversal order
  still determines equal-score ties. No represented support is pruned.
- Reconstruct and check normalized path/proposal provenance internally, then
  run the final independent grammar recognizer once. A regression counts that
  final call; public standalone DAG validation still checks grammar itself.
- Removed the arbitrary active-task line-count/progress-prose test. Historical
  evidence assertions, package-boundary checks and baseline tests remain.

The frozen ordinary-token reference bridge and large research drivers were
not replaced wholesale: their historical/reference roles do not justify
merging independent algorithms or introducing a general workflow framework.

## Verification

Run on Linux x86_64, CPython 3.11.16, Rust 1.98.0. These are local maintenance
checks against uncommitted changes based on `feabbfda8ff4266388926bc8a8fee1f0f9882e2d`,
not newly published benchmark results. New campaign summaries explicitly mark
the worktree dirty and live under `docs/evidence/review-hardening/`.

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q --cov=mwpc_exact --cov=mwpc_research --cov-report=term:skip-covered` | 767 passed; 85% statement coverage of the two Python packages; scripts/Rust excluded from this coverage percentage |
| `.venv/bin/python -m ruff check src tests scripts` | Passed |
| `.venv/bin/python -m mypy src` | Passed, 73 source files |
| `.venv/bin/maturin develop --release --locked --manifest-path crates/mwpc_parser_py/Cargo.toml` | Rebuilt and installed the production binding |
| `make test-rust-parser` | 19 unit and 3 randomized Rust tests; format and Clippy checks for both crates passed |
| `.venv/bin/python scripts/rehearse_release_wheel.py` | Source archive and wheel passed; isolated installed-wheel imports, Q3 experiment and artifact generation passed |
| `make final-artifacts-check article-results-check` | Existing publication artifacts and source hashes verified unchanged |
| `./scripts/verify_upstream.sh` | EPIC and license provenance unchanged at `5b1b31098f34ed3691d2a9f4aae14fdf5839d072` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=vendor/EPIC-Decoding .venv/bin/python -m pytest -q vendor/EPIC-Decoding/tests/test_constrain_utils.py vendor/EPIC-Decoding/tests/test_bindings.py` | 19 passed, 4 existing upstream skips |

The inspected source archive was 16,144,835 bytes unpacked and 3,179,255 bytes
compressed before the final documentation-only update. The previous selection
included 779,829,025 bytes of Rust targets alone. Tests enforce exclusion of
nested `target` directories and a 50 MB unpacked source budget.

The adversarial numerical test also checks 100 recorded seeds per backend
against exhaustive homogeneous completions using independently recomputed
rational objectives. Normal M5/M6/M7 campaigns each passed 500 cases:

```bash
.venv/bin/python scripts/exact_commit/run_m5_rust_differential.py --campaign normal --output-directory docs/evidence/review-hardening
.venv/bin/python scripts/exact_commit/run_m6_finite_lattice_differential.py --campaign normal --output-directory docs/evidence/review-hardening
.venv/bin/python scripts/exact_commit/run_m7_eos_finite_slot_differential.py --campaign normal --output-directory docs/evidence/review-hardening
```

Use a different, empty destination to repeat these commands. Reusing the
recorded destination now correctly refuses to overwrite the summaries.

Development dependency resolution was checked without relying on installed
packages; the existing CPU/EPIC environment also satisfies the new constraints:

```bash
.venv/bin/python -m pip install --dry-run --ignore-installed --build-constraint requirements/constraints-py311-linux.txt -c requirements/constraints-py311-linux.txt -e '.[dev]'
.venv/bin/python -m pip install --dry-run -c requirements/constraints-py311-linux.txt -e '.[dev]' -r requirements/epic-baseline-cpu.txt
```

## Follow-up simplification (M15)

This follow-up removes 192 net implementation lines across nine Python files
relative to the completed M14 working tree, not relative to Git HEAD. It adds
86 test lines and four regression cases; no dependencies or frameworks were
introduced.

- Use the existing disabled, clock-free profiler in one execution path instead
  of maintaining profiled/unprofiled copies of every operation. Retain enabled
  component boundaries, counters and Rust's separate internal timing values.
- Inline the single-use proposal/support builder wrappers and remove an unused
  normalized-certificate argument. Public builder signatures are unchanged.
- Replace field-by-field immutable result and attempt copies with
  `dataclasses.replace`, and merge identical adaptive-support exit paths.
- Share identical canonical JSON encoding through the existing private JSON
  module. Serialized artifact bytes and fingerprints remain unchanged.

New regressions compare complete pipeline outputs with absent, disabled and
enabled profiling for optimal and infeasible instances, enforce epsilon-only
measurement boundaries, and reject corrupted certificates in both profiling
modes. The independent Python/Rust algorithms, final witness validation,
ordinary-token reference bridge and baseline decoders remain intact.

Validation against this uncommitted working tree:

- `.venv/bin/python -m pytest -q`: **771 passed**.
- `.venv/bin/python -m ruff check src tests scripts`: passed;
  `.venv/bin/python -m mypy src`: passed, 73 source files.
- `make test-rust-parser`: 22 tests passed; both crates passed format/Clippy.
- `.venv/bin/python scripts/rehearse_release_wheel.py`: source archive, wheel,
  isolated imports, experiment and artifact smokes passed. The diagnostic
  experiment reports the expected dirty-worktree metadata warning.
- `make final-artifacts-check article-results-check` and
  `./scripts/verify_upstream.sh`: passed; historical artifacts are unchanged.
- The EPIC regression command listed above: 19 passed, 4 existing upstream skips.

No performance improvement is inferred from the line-count reduction, and no
model/GPU experiments or publication numbers were changed by this follow-up.

## Remaining research limitations

The release's singleton-support saved-logit cases and two literal end-to-end
tasks are still limited evidence. This maintenance pass does not expand their
empirical scope, rerun model/GPU experiments, claim measured speedups, create a
new CUDA dependency lock, or alter paper numbers. The clean-Git CPU rehearsal
requires a committed clean checkout; it was not represented as run against
this dirty worktree. The isolated wheel rehearsal above did run successfully.
