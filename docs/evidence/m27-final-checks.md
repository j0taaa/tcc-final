# M27 final execution record — 1 October 2026

The machine-readable record is `m27-final-checks.json`; source hashes bind the
new code, Lean definitions, portable mathematical example and paper sources.
These are correctness/formal/build checks, not model-performance measurements.

| Gate | Executed result |
| --- | --- |
| Full `python -m pytest -q` | **1,360 passed**, 73.49 seconds |
| Ruff and strict MyPy | PASS; 98 source files type-checked |
| Pinned Lean 4.34.0 formal gate | PASS: 17 audited universal theorems, 16 concrete claims across five profiles; forged upper bound rejected |
| Production Rust tests, format, Clippy and binding lint | PASS: 21 unit + 3 randomized tests |
| Upstream Python | 406 passed, 8 existing skips, 2 upstream deprecation warnings |
| Upstream Rust | 63 passed, 1 upstream ignored test |
| Upstream provenance | Exact pinned `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, no tracked changes |
| Publication/statistical/final artifact rebuild checks | PASS; archived raw hashes and derived bytes unchanged |
| All current manuscript data derivatives | PASS through `make paper` |
| Final article build | 16 pages, no overflow or unresolved references; all final pages rendered and visually inspected |
| Isolated wheel/sdist rehearsal | PASS, no source-tree leakage; installed library generates/verifies v2 proof and exports Lean; formal sources included, build caches excluded |
| `git diff --check` | PASS |

The additional upstream `cargo fmt --all -- --check` **fails** on existing
formatting in three read-only files, as documented in `m27-simplification.md`.
It was not silently reported as passing or fixed by modifying the baseline.
All production formatting gates pass.

An early full suite hit the existing deadline-sensitive JSON repair timeout
(1 failed / 1,339 passed); the isolated repair suite passed 33 tests, followed
by successful full suites. Concurrent formal checking was present, but the
cause is not established. No timeout or baseline test was weakened. Article
compression temporarily removed required exact caution phrases (2 failed /
1,350 passed); the cautions were restored and all tests retained. A 17-page PDF
was rejected by the unchanged 16-page gate and reduced through prose edits.
Eight new regression cases reject Boolean/float aliases of integer result IDs.

The formal boundary is explicit in `formal/README.md`: the kernel checks
specified resource-CFG/bound statements and exported instances; an independent
Python checker binds original inputs to graphs/tokens. Whole Python/Rust
source refinement, model execution, semantic accuracy, written DP completeness
and infinite-language separation constructions have not been silently declared
formally verified.

Local commands used the installed pinned toolchain through
`--lake "$HOME/.elan/bin/lake"`. The mandatory CI formal job is configured;
remote CI was not run or represented as passing. No slides, model runs,
remote publication, branch changes or pushes were performed.
