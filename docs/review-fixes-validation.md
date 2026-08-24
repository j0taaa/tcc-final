# Review-fix validation record

This document records the validation intent for the support-scope and CI corrections introduced after the M3 review.

The pull-request checks must verify, on the corrected tree:

- pinned EPIC provenance;
- Ruff over `src` and `tests`;
- strict MyPy over `src`;
- all lightweight unit tests;
- the complete `tests/exact_commit` suite, including support-scope regressions.

The correction establishes these executable invariants:

1. `SupportKind.FULL` cannot be paired with caller-supplied pruned rows.
2. A token-aligned `FULL` claim requires the terminal/token mapping to cover the declared vocabulary.
3. Explicit support cannot omit an already committed token.
4. Explicit support cannot contain a token without a token-aligned terminal mapping.
5. Result diagnostics contain canonical represented rows, row sizes, and a SHA-256 support fingerprint.
6. `make check` and the default GitHub workflow execute the exact-commit tests.

A passing workflow validates the repository checks available in CI; it does not replace the formal proof or broaden the configured M3 campaign beyond its documented finite instance families.
