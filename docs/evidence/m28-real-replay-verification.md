# M28 real-state replay: final verification

Date: 2 October 2026. Scope: execute the new rational budgeted optimizer on
authentic saved LLaDA states and update the project/article from actual evidence.
No new model generation, network request, slides or remote publication occurred.

## Immutable experiment provenance

- Protocol/input freeze: commit `7b4d7ce` and
  `configs/experiments/m28_budgeted_real_replay_v1.json`, SHA-256
  `aa6ad04b72feb28438d8ec9a9d56734f4cfbfbced5cdafef8d414000d2a22413`.
- Corrected producing code: `ac0e5da9300db83adbacf2fee312bcca082d7aec`.
- Command (thread environment also recorded in raw metadata):

  ```bash
  PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 .venv/bin/python \
    scripts/exact_commit/run_budgeted_real_replay.py \
    --config configs/experiments/m28_budgeted_real_replay_v1.json \
    --output results/raw/m28_budgeted_real_replay_v2
  ```

- Byte-preserved archive: `docs/artifacts/raw/m28_budgeted_real_v1/completed/`.
  Manifest SHA-256:
  `3ce2dc3d170a394f68fa904973a84b98a203c649e00f8b54e4c878468a6e30b9`.
- All 24 recursive snapshots and 12 geographic-query steps retained, with
  two reward profiles and caps 0--2. Model/tokenizer revision remains
  `08b83a6feb34df1a6011b80c3c00c7563e963b07`.
- The interrupted first attempt remains under `interrupted/` with 124 recorded
  rows. Its failures were harness defects: unrestricted rows were passed for
  newly fixed positions, and an empty infeasible witness was indexed. Both have
  minimal regressions. The complete cohort was rerun with identical parameters;
  interrupted rows supply no final scores or timings.

## Observed results and limits

All 252 corrected method jobs completed. Independent verification accepts 216
budget certificates: 192 optimal and 24 infeasible on the represented support.
These are repeated budget/profile measurements, not 216 independent tasks.

For ordinary rewards, exact improves over confidence preselection in 2/64
feasible paired budget cases; post-filtered MWPC ties in all 64, and the native
EPIC byte-selector/cap ties in all 50 eligible pairs. Seven EPIC states requesting
serial fallback are excluded from scored comparisons. The complete EPIC decoder
was not rerun, and no semantic superiority is inferred from these rewards.

Median geocoding frontier cost is 48.491 CPU seconds, including the internal
certificate checks and shared caps 0--2. This is a costly reference computation,
not an interactive-latency or GPU speed claim. The first geographic witness is
semantically wrong despite a correct optimality certificate; every step remains
visible in the report.

Post-hoc application of the existing M27 relaxation certifies 114/128 feasible
post-filtered batches directly. The report separates all-token and ordinary
profiles, zero rewards and positive tight bounds. This demonstrates a use of
the bound; the latency of a hybrid strategy was not measured. Existing Lean
coverage remains explicitly scoped; these 216 concrete certificates are checked
by the independent Python checker, not claimed as new Lean kernel checks.

## Executed verification

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  **1,373 passed**, 136.75 seconds.
- Final replay/artifact suite after the report's profile/zero-reward clarification:
  `python -m pytest -q tests/exact_commit/test_budgeted_real_replay.py`:
  **13 passed**, 56.95 seconds. The archive/derivative test forbids calling either
  optimizer and still checks every certificate and regenerated file.
- Ruff on `src`, `tests` and both new scripts: PASS. MyPy on `src`: PASS,
  98 source files.
- `make test-rust-parser`: 21 unit + 3 randomized tests, formatting and Clippy
  for parser and bindings: PASS. No Rust source/API change was needed.
- Existing upstream `test_constrain_utils.py` and `test_bindings.py`:
  **19 passed, 4 pre-existing skips**. `verify_upstream.sh`: unchanged
  `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`.
- `run_budgeted_real_replay.py --verify <completed archive>`: PASS for all
  source hashes, mapped inputs, statuses, proofs, batches and physical updates.
- `make paper`: all old/new artifact gates PASS. Final `make -C paper`:
  **16 pages**, no overflow or unresolved references. Final rendered pages
  10--16 (all changed/repaginated content) visually inspected: no clipping,
  overlap or broken equations/tables. Earlier pages' content was unchanged.
- Source-distribution size guard PASS. Only the duplicated interrupted audit
  archive is omitted from the sdist; it remains in Git. Final replay inputs and
  certificates remain included for offline verification. No test was weakened.

An initial full-suite run exposed the source-distribution size cap and required
historical-caution wording. Packaging was narrowed as above and original caution
text restored. No data, baseline test, theorem or page-size rule was relaxed.
Prose was shortened to preserve the original 16-page limit and template.

The accompanying JSON records final source and artifact hashes. No remote CI
execution, fresh GPU experiment or universal Python/Rust source proof is claimed.
