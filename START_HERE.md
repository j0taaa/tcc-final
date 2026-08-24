# Start here - AI agent handoff

You are implementing a correctness-critical research artifact. A passing demo is insufficient unless the mathematical contract, exactness scope, and independent certificate checks remain valid.

## First session

```bash
git submodule update --init --recursive
make bootstrap
source .venv/bin/activate
make check
```

Build the Rust binding only when the current task depends on it:

```bash
make bootstrap-rust-parser
make test-rust-parser
```

## Read in this order

1. `AGENTS.md` in full;
2. `UPSTREAM.md`;
3. `TASKS.md`, beginning with the first incomplete required task;
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`;
5. the affected source, ADRs, tests, and evidence files.

`TASKS.md` is the sole source of the current milestone. This file intentionally does not repeat a task number, so it cannot become stale after a gate closes.

## Non-negotiable rules

- Keep `vendor/EPIC-Decoding` read-only and integrate through adapters.
- Preserve serial and EPIC baseline behavior.
- Never return or report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` or explicit support globally exact.
- Never treat `TIMEOUT` as `INFEASIBLE_ON_SUPPORT`.
- Keep represented-support validation distinct from EOS/PAD-policy validation.
- Any disagreement with an exhaustive oracle blocks later optimization and model integration.
- Preserve deterministic seeds and save every discovered counterexample as a regression fixture.
- Do not enter measured values in the article until their raw artifacts, configuration, generation script, and commit are versioned.

When blocked, record:

```text
BLOCKED:
Cause:
Evidence:
Smallest next experiment:
```
