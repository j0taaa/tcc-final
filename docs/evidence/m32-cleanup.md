# M32: reduced implementation and clean test restart

The explicit request of 2026-10-05 removed all previous tests and reduced the
maintained implementation/experiments. No replacement suite was created.
Historical source, tests, configs and campaign generators are recoverable at
`a98ae8e09f2066157ebf6df05f8873b8600e00fb`; see [recovery instructions](../../REPRODUCING.md).

## Actual reduction

Physical lines include comments and blank lines. Counted files are versioned
source, including Python/Python interfaces, Rust, Lean, scripts and build files.
Document prose, configs/data, scientific artifacts, dependencies/caches and
compiled outputs are excluded. Before/after use the same scope.

| Source | Before | After |
|---|---:|---:|
| Own implementation (`src`, `crates`) | 38,911 | 17,798 |
| Experiment/maintenance scripts | 17,118 | 1,892 |
| Owned Python tests | 23,588 | 0 |
| Lean proof sources | 818 | 818 |
| Build files | 317 | 197 |
| **Own total** | **80,752** | **20,705** |
| EPIC source | 33,172 | 24,291 |
| **Total including EPIC** | **113,924** | **44,996** |

Own code falls **74.4%**. The maintained tree contains one Python package,
13 tool scripts and one experiment configuration, instead of 88 configs.
The [machine-readable count](m32-line-count.json) records nonblank lines and
every counted source file/hash. This final count uses the same eight explicit
build files on both revisions, superseding preliminary working-tree totals.

## Removed and retained

Removed the 154 owned Python test files, owned Rust test modules/randomized
integration file, obsolete differential/oracle infrastructure, `mwpc_research`,
historical campaign generators, repair experiment, duplicate toy solvers and
their old configs/CLI/CI routes. Archived experiment inputs and outputs remain.

Retained the finite-token support/tokenizer/EOS path, independent Python and
Rust CFG parsers, serial/EPIC/exact integration, rational budget/conflict APIs,
probability bounds/admission, independently checked portable certificates,
Lean proof library and one larger-canvas probability campaign with its exact
counter control. These are the current inference/certificate dependencies.
Simplified shared state/serialization, metadata, exports, packaging and tools.
Version 0.3 removes old research APIs and root algorithm reexports: import
algorithms from their explicit modules as documented in the README.

EPIC is a versioned production snapshot of unchanged upstream commit
`5b1b31098f34ed3691d2a9f4aae14fdf5839d072`. Twelve test files and ten test-only
Rust sections are removed. Its production algorithms and license notices are
preserved; the [manifest](../../vendor/EPIC-Decoding/.upstream-manifest.json)
records original/retained hashes and each removal. No unpublished local
submodule commit is required to reproduce it. The production/test-only diff
was also checked against all 170 original upstream Git blobs; see the
[source comparison record](m32-upstream-checks.json).
Root download-directory ignore rules now use `/models/` and `/datasets/`, so
EPIC's legitimate Python packages with those names are tracked/distributed.

## Completed verification

- `make check`: pinned baseline hashes, Ruff and MyPy pass (61 package modules).
- `make build-rust`: owned parser/binding formatting and locked Clippy pass.
  Locked upstream `cargo check` passes with existing upstream warnings.
- All retained modules and installed bindings import. Serial/EPIC/exact CLI
  configuration works; exact configuration still requires explicit support.
- A real archived geocoding state solves with budget 2 and returns an optimal
  certificate, independently rechecked without optimization. The
  [returned certificate](m32-geocoding-proof.json.gz) is operational evidence.
- `make article-results-check`: all **3,683 frozen scientific files** keep
  their pre-cleanup hashes; all 35 returned M31 probability certificates pass
  the retained original-input/exact-counter check. All measured failures and
  unfavorable comparisons are preserved.
- Pinned Lean build and axiom audit pass for **35 universal statements** and
  the canonical resource example. Mathematical sources remain unchanged.
  [Current formal record](m32-formal-checks.json).
- Original-input resource/probability certificates verify; a real probability
  certificate admits sampling with requested total-variation tolerance 1/20.
- Editable install, wheel and sdist build pass. An isolated dependency-free
  wheel contains 61 package modules, excludes removed research modules and
  verifies/samples the real certificate without importing optimizers. The
  sdist measured before final package evidence metadata is 9,059,035 bytes
  unpacked, below the unchanged 50 MB gate; all 158 canonical upstream files
  are included with verified hashes. [Package record](m32-package-checks.json).
- The revised manuscript builds to 16 pages, with no unresolved references or
  overflow; every rendered page was visually inspected. Scientific values and
  generated result tables remain unchanged.
- `git diff --cached --check -- . ':!vendor/EPIC-Decoding'` passes for owned
  changes. Whitespace inherited from the pinned upstream snapshot is retained
  to preserve its hashes/licenses. `make test` intentionally fails with the
  explicit statement that no replacement suite exists.

Exact commands, returned values and artifact/log hashes are recorded in
[m32-cleanup.json](m32-cleanup.json). Large build logs and rendered pages remain
ignored locally under `results/processed/m32-*`; they are not distributed as
scientific measurements. Updated GitHub CI has not been executed remotely.

## Boundaries

Builds and checked witnesses are operational evidence, not a replacement
regression/oracle suite. Lean checks specifications and the canonical example;
it does not verify every Python/Rust/model instruction. The historical
16-claim/forged-bound regression campaign belongs to its original revision,
and is not reported as a current suite pass. No new full LLaDA trajectory or
model benchmark was run. Removing code/tests changes neither measured outcomes
nor the conclusions about novelty, practical superiority or semantic quality.
