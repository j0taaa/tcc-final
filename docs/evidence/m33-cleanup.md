# M33: additional reduction of owned code

Removed another **3,026 physical lines (14.6%)** of owned code, without editing
external EPIC. Relative to the source before both cleanups, the reduction is
**78.1%**. No replacement test suite was created.

| Owned source | Before M33 | After M33 |
|---|---:|---:|
| Implementation (`src`, `crates`) | 17,798 | 15,623 |
| Experiment/maintenance scripts | 1,892 | 1,041 |
| Lean proof sources | 818 | 818 |
| Build files | 197 | 197 |
| **Total** | **20,705** | **17,679** |

The same explicit scope counts comments/blanks and excludes documents, data,
artifacts, other declarative configs, caches and compiled files. Every remaining
counted file/hash is recorded in [m33-line-count.json](m33-line-count.json).
EPIC is excluded from these counts and its source diff is empty.

## Simplification

- Retired the old `evaluation` result/selector hierarchy. Current conflict and
  probability oracles use `solve_state`, returning the existing typed
  `ExactCommitResult` and retaining its live independent certificate validator.
  The external serial/EPIC decoders and exact LLaDA adapter remain intact.
- Removed the unused byte-only lattice and `TokenArc`. The existing production
  EOS lattice already handles ordinary byte expansion with `EOSMode.ABSENT`,
  alongside optional/required EOS and finite PAD slots; no tokenizer path was
  replaced or weakened.
- Removed old language/path enumerators, unused reference-graph indices and
  unused exact-control sampling. Kept independent Python/Rust parsers, original
  input checkers and exact forward/backward controls.
- Retired the last fresh-model campaign drivers/CPU model wrapper and their
  metadata package. Kept offline certificate/control verification and table
  generation. All original outcomes/configs/proofs remain available.
- Kept strict JSON helpers in `mwpc_exact.serde`; shared the offline script
  reader/hash helper. Version 0.4 documents the retired API surface.

The complete pre-M33 code is recoverable at
`9deb3df`; [REPRODUCING.md](../../REPRODUCING.md) gives an isolated-checkout route.
Earlier complete suites/generators remain at `a98ae8e`.

## Verification and boundaries

`make check`, locked Rust formatting/Clippy, pinned Lean build/axiom audit,
editable installation, wheel/sdist build and isolated wheel execution pass.
All 54 retained modules and installed baseline/bindings import. The isolated
wheel verifies/samples a real archived certificate without importing optimizers;
the removed packages are absent. All 158 external files are included in the
source archive with unchanged hashes.

The real saved geocoding state returns equal ordinary objective/status on Python
and Rust. Its budget-2 portable certificate is **identical** to the pre-cleanup
certificate and independently verifies. A zero work limit remains `TIMEOUT`.
The probability API produced an independently verified partition on an original
saved MDLM input at eight queries; its status is **incomplete**, not a posterior
tolerance success. These are operational checks, not new model/benchmark results.

`make article-results-check` verifies all **3,683 frozen scientific files** and
all 35 returned M31 certificates against independent exact counting. Lean checks
the unchanged 35 universal statements/canonical example; no whole-source
refinement or historical regression-fixture pass is claimed. No article values,
formal sources, baseline source or archived results changed. `git diff --check`
passes. Tests remain absent by explicit request.

Exact commands/log hashes, package measurements, returned values and limitations:
[m33-cleanup.json](m33-cleanup.json), [runtime record](m33-runtime.json),
[formal record](m33-formal.json), [package record](m33-package.json). Build logs
and the temporary probability proof remain ignored locally under
`results/processed/m33-*`. Cleanup establishes no scientific novelty,
performance/quality superiority or universal implementation correctness.
