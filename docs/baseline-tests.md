# Baseline test record

Recorded on 2026-08-23 during T002, before any MWPC solver behavior was
implemented. The pinned EPIC submodule was clean at commit
`5b1b31098f34ed3691d2a9f4aae14fdf5839d072`.

## Root contract and bootstrap tests

```bash
/usr/bin/time -p python -m pytest -q
```

Final M0 result: **13 passed** in 0.10 s (0.23 s wall time). This includes
eight initial data-contract cases, four deterministic bootstrap regressions,
and the parent-side EPIC graph-adapter integration regression.

## Complete upstream Python suite

```bash
/usr/bin/time -p make test-upstream
```

Final M0 result: **406 passed, 8 skipped, 2 warnings** in 53.97 s (54.55 s
wall time). The existing skips were not changed:

- two unconditional C++ CFG fixture skips;
- two unconditional JSON-mode fixture skips;
- one `not implemented` constrain-utils case;
- three additional unconditional constrain-utils skips.

Warnings were two upstream `pytest.parametrize(enumerate(...))` deprecations.
They are pre-existing baseline behavior, not MWPC results.

## Upstream Rust library

```bash
/usr/bin/time -p cargo test \
  --manifest-path vendor/EPIC-Decoding/rustformlang/Cargo.toml
```

Final M0 result: **63 passed, 1 ignored, 0 failed** in 0.55 s wall time from
the warm build cache. The initial measured run took 7.41 s. Cargo also emitted
pre-existing compiler warnings from the read-only EPIC and `regex-dfa`
sources; no warning was suppressed and no submodule source was edited.

One chained non-interactive invocation initially could not locate `cargo`.
The rustup binaries were then exposed through the already configured
`~/.local/bin`; the documented bare `cargo test` command subsequently passed.

## Scope

These are software baseline results only. They do not establish MWPC
correctness, oracle agreement, tokenizer semantics, performance, GPU behavior,
or end-to-end model quality.
