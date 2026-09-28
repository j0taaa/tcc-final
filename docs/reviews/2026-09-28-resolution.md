# Audit resolution and scientific direction — 2026-09-28

This record concerns fixes and a research plan, not new performance measurements.
Base source: `a43e1cf904eceff8bbcc802b5c0b2abb1c10c059` plus the delivered review patch.
Historical experiment rows, configs, licenses and tags remain unchanged.

## Changes

- The witness-reusing greedy selector now checks the whole-call deadline after
  final certificate accounting. Late results are TIMEOUT without score/witness.
  Thirty injected-clock regression cases cover both backends, five execution paths
  and before/at/after deadline. In-budget choices remain identical.
- `build_selection_audit.py` reconstructs and checks all three M19 derivatives,
  including a table of absolute times and paired ratios. `make article-results-check`
  and CI include it. Six corruption/missing-file cases reject drift; raw manifests
  are validated by the existing analyzer. No archived measurements were changed.
- The article adds Nederhof/Satta, Hanneforth, Pasti et al. and CLAD, distinguishing
  established weighted intersection and exact subset selection from this application.
  Background and repeated pseudocode were shortened; detailed historical methods
  and results moved to the existing supplement. Main results retain all negative
  findings. Three tables cover correctness, current selection and live confirmation.
- `make paper` now checks the actual PDF's 10–16 pages, overflow and references.
  Fonts and margins are unchanged. Five regression cases check this gate.
- README/REPRODUCING distinguish the current snapshot from historical v0.2.0.
  The snapshot uses a base bundle plus patch so delivery does not require an
  unsolicited commit, tag, branch change or push.
- The [four-week plan](../research/2026-09-28-json-repair-plan.md) prioritizes
  certified bounded JSON repair with protected fields, strong baselines, separate
  controlled/real-output cohorts, a first-week decision and held-out confirmation.
  Minimal substitution cost on represented support is the intended guarantee;
  unrestricted minimum edit distance and superior task quality are not claimed.

## Executed verification

| Command / check | Observed result |
|---|---|
| `.venv/bin/python -m pytest -q tests/exact_commit/test_selection.py` | 42 passed; new deadline regression failed before the fix |
| `.venv/bin/python docs/reviews/repro_greedy_total_deadline.py` | Both backends now TIMEOUT at simulated 2 seconds for a 1-second budget; no certificate |
| `.venv/bin/python -m pytest -q` | 885 passed |
| `make check` | Upstream verified; Ruff/MyPy (78 source files), 14 unit and 851 exact tests passed |
| `make test-rust-parser` | 21 unit and 3 randomized tests passed; both crates format/Clippy clean |
| `make test-upstream` | 406 passed, 8 upstream skips, 2 upstream pytest deprecation warnings |
| `make article-results-check` | M13, M17 and M19 artifacts reproduce from archived evidence |
| `make release-wheel-smoke` | Wheel/sdist build, isolated wheel imports, Q3 and artifact smoke pass; no source-tree leakage |
| `make paper` | 16 pages; final pass has no undefined references or overfull boxes |
| Visual PDF review | All 16 pages inspected; changed final pages re-rendered and checked |
| `git diff --check` | Clean |

The wheel smoke correctly warned that this is a dirty review worktree; it is a
packaging test, not a new publication experiment. The TeX log has an underfull
line in related work; visual review found no clipping or overlap. No new GPU/model
campaign was run. Rust logic/API and EPIC source were not changed.

Delivery rehearsal is recorded below once completed. Intermediate command logs
and page renders are temporary QA files; source, tests and evidence here are the
maintained record.

## Completed delivery rehearsal

The base bundle was cloned into a fresh temporary checkout; `git apply --check`
and `git apply` accepted the review patch. All 26 changed/new source files matched
the delivered manifest's SHA-256 values. From that checkout, using the existing
CPU environment with its Python path pointing at the reconstructed source:

- `make article-results-check VENV_PY=<existing CPU Python>` passed;
- selection, audit-artifact and compiled-paper-gate tests: 54 passed.

This verifies source reconstruction and offline artifact regeneration; it is
not a claim of reinstalling every dependency in a fresh operating system.
The final delivery retains the same base commit and records its complete patch
and file hashes. Use `sha256sum -c SHA256SUMS` inside the snapshot directory.
