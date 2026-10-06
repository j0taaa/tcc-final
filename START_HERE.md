# Start here

Read `AGENTS.md`, then the current milestone in `TASKS.md`. The user removed
all previous tests to start a new suite; do not silently restore them.

```bash
make bootstrap
make check
make bootstrap-rust-parser
make build-rust
make check-formal LAKE="$HOME/.elan/bin/lake"
make article-results-check
```

The checks compile/lint, verify Lean declarations and recheck recorded artifacts.
They are not a replacement regression suite. `make test` explicitly fails until
new tests are implemented. EPIC is now a versioned production snapshot of the
same pinned upstream commit, with its test-only files/sections removed.
`UPSTREAM.md` documents the original and retained SHA-256 inventories.

Use `REPRODUCING.md` for current commands and historical-source recovery. Keep
scientific objectives, support scope, original probabilities, status separation
and independent certificate validation intact. Do not replace negative results.
