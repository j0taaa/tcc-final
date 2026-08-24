# Review-fix validation record

This document records the validation of the support-scope, CI, and agent-handoff corrections introduced after the M3 review.

## Corrected contracts

1. `SupportKind.FULL` cannot be paired with caller-supplied pruned rows.
2. A token-aligned `FULL` claim requires the terminal/token mapping to cover the complete declared vocabulary.
3. Explicit support cannot omit an already committed token.
4. Explicit support cannot contain a token without a token-aligned terminal mapping.
5. Result diagnostics contain canonical represented rows, row sizes, and a deterministic SHA-256 support fingerprint.
6. `make check` and the default GitHub workflow execute the complete lightweight `tests/exact_commit` suite in addition to unit tests.
7. The permanent `m3-extended-correctness` workflow reruns the configured 2,000-case differential campaign on relevant pull requests and on manual dispatch.
8. `README.md`, `START_HERE.md`, and `TASKS.md` direct the next agent to M4/T400 rather than repeating completed milestones.

## Validated code tree

- Commit: `8d25dcdbb9837295c13166bc43fc062a306b6ac3`
- Tree: `449072f4bd20cbd8c49722359aa36f8955e8c294`
- Validation PRs: [#1](https://github.com/j0taaa/tcc-final/pull/1) and [#2](https://github.com/j0taaa/tcc-final/pull/2)

The pull-request synthetic merge used by the final validation was
`98cb763f7a3bdf776b2168628517425592227760`; its tree is identical to the
squash-merged commit above.

## Repository checks

GitHub Actions run [`32678215375`](https://github.com/j0taaa/tcc-final/actions/runs/32678215375) completed successfully:

- pinned EPIC provenance: passed;
- Ruff over `src` and `tests`: passed;
- strict MyPy: passed with 16 source files checked;
- unit and exact-commit tests: **148 passed, 1 skipped**.

The single skip is expected in the lightweight environment: the optional pinned EPIC Rust binding is not built there. EPIC binding and upstream tests remain part of the heavier baseline environment rather than being silently treated as passed.

Bootstrap-integrity run [`32678215370`](https://github.com/j0taaa/tcc-final/actions/runs/32678215370) also completed successfully.

## Extended M3 campaign

GitHub Actions run [`32678215360`](https://github.com/j0taaa/tcc-final/actions/runs/32678215360) completed successfully using the versioned configuration `configs/exact_commit/m3_differential.toml`:

- cases: **2,000 / 2,000 passed**;
- failures: **0**;
- base statuses: 1,500 `OPTIMAL`, 500 `INFEASIBLE_ON_SUPPORT`;
- three-way CKY/completion/subset comparisons: 10,000;
- independent certificate validations: 23,538;
- support-monotonicity checks: 2,000;
- proposal-removal checks: 2,000;
- fixed-position checks: 2,000;
- Python: 3.11.16;
- configuration SHA-256: `d68e8e8890890d0f18604a12351e2a05ff40dd90b106f501206c07c960db3d86`.

Machine-readable evidence is stored in
[`docs/evidence/post-review-support-scope-validation.json`](evidence/post-review-support-scope-validation.json).

## Scope of the evidence

These checks validate the executable repository contracts and the configured tiny finite M3 instance families. They do not replace the formal proof, establish correctness for every possible CFG or tokenizer, or claim tokenizer-aware, Rust-production, performance, or end-to-end model results that have not yet been implemented. The next required milestone remains M4/T400.
