# EPIC baseline smoke path

Measured on 2026-08-23 during T003. No model inference was run.

## Successful model-free path

Command:

```bash
source .venv/bin/activate
python scripts/smoke_epic_baseline.py
```

Output:

```json
{"invalid_path_completable": false, "model_free": true, "normalized_before_graph_check": true, "path": "EPIC rustformlang CFG-on-TerminalGraph", "valid_path_completable": true}
```

This exercises the compiled PyO3 binding, CFG normalization, a terminal graph,
and EPIC's Rust CFG-on-graph feasibility checker. The fixture accepts the path
`a b` and rejects `a a` under `S -> A B`, `A -> a`, `B -> b`.

## Pre-existing raw-CFG deadlock

Calling `CFG.is_graph_intersection_empty()` on a CFG returned directly by
`CFG.from_text()` did not return within an external five-second limit, even
with the API timeout set to one second (`timeout` exit 124). The same call
returns immediately after `to_normal_form()`.

The cause is in the pinned read-only baseline:
`rustformlang/src/cfg/cfg.rs::is_graph_intersection_empty()` initializes
`_in_normal_form` with a closure that calls `is_normal_form()`, which accesses
the same `OnceCell`. The parent adapter therefore normalizes before invoking
the boolean baseline API. The regression is
`tests/integration/test_epic_baseline.py`.

This baseline API also returns a bare boolean and maps its internal timeout to
"empty". It is acceptable only for reproducing the existing heuristic
baseline. The exact MWPC implementation must use its own explicit status type
and never map `TIMEOUT` to `INFEASIBLE_ON_SUPPORT`.

## Later exact-strategy hook

The LLaDA loop constructs per-position argmax proposals and confidence before
`_try_regular_cover_batch_commit_llada()` in
`constrained_diffusion/eval/dllm/models/llada/generate_constrained.py`; DREAM
has the analogous `_try_regular_cover_batch_commit_dream()` path. The new
strategy should be selected from a parent-side adapter at this boundary,
leaving the submodule and its serial/regular-cover behavior unchanged.

Large-model smoke inference was not attempted: this checkout has no local
model checkpoint, and the M0 CPU environment intentionally uses a CPU-only
PyTorch wheel.
