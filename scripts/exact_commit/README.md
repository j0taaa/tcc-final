# Maintained mathematical/artifact tools

The old suites and experiment drivers are retired. This directory maintains:

- `budget_math_example.py`: the canonical resource example, portable budget
  proof verification and optional Lean export/check.
- `check_formal_project.py`: pinned Lean specifications/axiom audit and the
  canonical resource example; no implementation regression suite.
- `build_probability_audit_results.py`: independent original-input checks for
  all returned M31 certificates, exact-control comparison and generated tables.
- `probability_audit_controls.py`: independent exact forward/backward counting
  for the two declared recursive array schemas, retaining original token IDs.
- `io_utils.py`: strict offline JSON/gzip reading and streaming file hashes.

Run from the repository root:

```bash
make article-results-check
make check-formal LAKE="$HOME/.elan/bin/lake"
.venv/bin/python scripts/exact_commit/budget_math_example.py --verify docs/artifacts/math/m27-budget-proof.json
```

No new model prediction is needed for these commands. All old inputs, results
and generated article products retain their scientific provenance. Verification
can optionally bind the retained probabilities to locally available full logits
with `build_probability_audit_results --check --capture <local-capture-path>`.
Full logits are not distributed; rational input mathematics remains reproducible.

Recover the final probability campaign capture/runner/CPU model code at
`9deb3df`. Earlier suites/campaigns are at `a98ae8e`; follow `REPRODUCING.md` in
that checkout. Current recovery commands and exact availability boundaries are
in the root [REPRODUCING.md](../../REPRODUCING.md). Archived tests/results do not
constitute a current suite pass. No new scientific outcome follows from cleanup.
