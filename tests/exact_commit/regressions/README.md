# Exact-commit regression fixtures

Every discovered correctness bug is minimized into one offline JSON fixture in
this directory. Files are loaded in filename order and must use this schema:

```text
schema_version: 1
regression_id: stable unique string
description: what failed before the fix
discovered_in_task: task that exposed the failure
fixed_by_commit: full implementation commit
expected_status: optimal | infeasible_on_support
expected_objective: non-negative number for optimal, otherwise null
expected_selected_proposal_ids: all positive proposal IDs matched by the
  deterministic completion-oracle witness, or [] when infeasible
instance: RandomTokenAlignedInstance schema_version 1 payload
```

The instance payload contains the complete CNF grammar, finite per-position
support, fixed canvas, proposals, terminal/token map, and replay seed. It must
not contain paths, credentials, external datasets, model state, or network
dependencies.

`test_regression_corpus.py` loads every `*.json` file, runs the five-variant
three-way differential checker, then checks the recorded base status,
objective, and selected IDs. Multiple optimum witnesses should be minimized
or encoded so the completion oracle's stable support order has the documented
selected set; theorem-level tests elsewhere never require CKY to choose the
same optimum witness.
