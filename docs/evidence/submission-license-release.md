# Institutional submission license and v0.1.1 release evidence

Verification date: 2026-09-01 (America/Sao_Paulo)

## Decision and scope

Gabriel Jota Lizardo selected the MIT License for his original parent-repository
software and versioned research artifacts. The canonical notice is `LICENSE`;
`LICENSES.md` records the scope and preserves these boundaries:

- the scholarly manuscript's publication rights remain separate;
- `vendor/EPIC-Decoding` remains under its own MIT and third-party notices;
- external model weights, tokenizers, datasets, and trademarks are not granted
  rights by the parent license; and
- a file-specific third-party notice takes precedence for that file.

Python and Rust package manifests declare `MIT`. The release-wheel rehearsal
also requires `License-Expression: MIT` and one packaged canonical `LICENSE`
file, in addition to both Python package trees.

## Immutable release

- Release: [`v0.1.1`](https://github.com/j0taaa/tcc-final/releases/tag/v0.1.1)
- Payload commit: `3db85bb0ec7e4416352b74832e8a6750af8bcaf2`
- GitHub Actions:
  [`33584766533`](https://github.com/j0taaa/tcc-final/actions/runs/33584766533)
- Evidence archive: 136 entries
- Evidence archive SHA-256:
  `26195f5129bcfb9a09f4c8f892aa4c1708f3f405c78a7d9e3a57858f76ecd1be`
- 16-page PDF SHA-256:
  `f1bb235b40f17ad5f3fd2840fd6511f6fe4ba819fa43c5c1f9d5d90594d86037`

The local digests and GitHub asset digests agree. The annotated tag resolves to
the payload commit. Historical `v0.1.0`, its pending-license statement, and all
raw experiment rows remain unchanged.

## Verification

| Gate | Result |
| --- | --- |
| Required pre-change `make check` | 11 unit and 676 exact tests passed |
| Required pre-change `make paper` | 16 A4 pages |
| Focused license/release regressions | 14 passed |
| `make release-wheel-smoke` | MIT expression/license file, both packages, isolated import, Q3 experiment, and artifact generator passed |
| Final `make check` | Ruff and strict MyPy passed; 11 unit and 680 exact tests passed |
| Full `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q` | 701 passed |
| Rust/parser gate | Formatting and Clippy passed; 17 unit and 3 randomized oracle tests passed |
| Focused Rust/finite-slot Python gate | 25 passed |
| `make final-artifacts-check` | T1203 outputs matched; manifest SHA-256 `28a17dcd3e054d9ab4d676793caf081bbba75eafd6513d1f751fa38436c46acb` |
| `make article-results-check` | All M13 outputs matched their pinned hashes |
| Clean-clone `artifact-rebuild` | All processed and paper outputs matched byte-for-byte |
| Clean-clone `source-experiment-rerun` | 249/249 agreement; 334 certificate validations; semantic comparison passed |
| Final `make paper` and Poppler inspection | 16 A4 pages, 357,555 bytes; all 16 pages inspected with no visual defect |
| GitHub Actions | `verify`, `rust-correctness`, and `epic-integration` passed |

One optional focused pytest command named two obsolete test paths and exited
before collecting tests. The actual inventory was inspected immediately, and
the corrected four-file Rust/finite-slot command passed 25 tests. The Rust
formatting, Clippy, and 20 Rust tests preceding that typo had already passed;
the full 701-test Python run and CI independently cover the same code.

The institutional checklist now records the parent release license as complete.
Advisor review remains deliberately unchecked because the author chose to skip
that separate workflow step for now.
