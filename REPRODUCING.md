# Reproducing the reduced project

The user requested removal of the old test suite and excess implementation.
There is no replacement suite yet. The commands below check builds, actual
mathematical proofs and original-input certificates; they do not prove universal
implementation correctness or scientific relevance.

## Setup

```bash
make bootstrap
make check
make bootstrap-rust-parser
make build-rust
```

Python 3.11 is the reproducibility baseline; dependencies remain pinned in
`pyproject.toml` and `requirements/`. The core wheel has no model dependencies.
EPIC is now a versioned snapshot of upstream `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`,
with only test files and `cfg(test)` source sections removed. It needs no
submodule initialization. `make bootstrap-epic` installs the existing pinned CPU
model environment/binding; `scripts/verify_upstream.sh` checks retained hashes.

## Current mathematical and artifact checks

```bash
.venv/bin/python scripts/exact_commit/budget_math_example.py --verify docs/artifacts/math/m27-budget-proof.json
.venv/bin/python -m mwpc_exact.mass_cli --verify docs/artifacts/raw/m30_probability_v1/probes/proofs/json_schema_type-2-top8_plus_catalog-finite_language_coverage-64.json.gz --sample --max-tv 1/20
make check-formal LAKE="$HOME/.elan/bin/lake"
make article-results-check
make paper
```

`check-formal` verifies the unchanged universal Lean library/axiom audit and
canonical resource example. The former generated regression-fixture campaign
was removed with the suite. Historical 16-claim/forged-bound results remain
attributed to their original source revisions, not claimed as a current suite.
Lean does not refine the whole Python/Rust/model source.

`article-results-check` verifies the pre-cleanup SHA-256 inventory of 3,683
scientific files and independently rechecks all 35 returned M31 probability
certificates against exact counter inference and their original rational inputs.
`article-results` regenerates only the maintained M31 products. Earlier generated
products remain frozen; their original generators live at the historical commit.

## Offline audit and archived experiment producers

Read the [frozen M31 protocol](docs/research/m31-relevance-audit.md) and the
[complete outcomes](docs/artifacts/processed/m31_probability_v1/report.md).
Only offline certificate/control checking and table regeneration remain in
the maintained scripts. The fresh-model campaign drivers and hardware metadata
layer are retired; recover them at `9deb3df` and follow that revision's commands.
The immutable campaign config remains at its original path for provenance.

The existing full logits remain ignored locally at
`results/raw/m31_probability_v1/capture`; large traces are not distributed.
To additionally bind archived retained values to original full softmax and
original token bytes:

```bash
.venv/bin/python -m scripts.exact_commit.build_probability_audit_results   --check --capture results/raw/m31_probability_v1/capture
```

The default check reproduces mathematics/tables from Git rational inputs,
tokenizer semantics and proofs. Source hashes cannot reconstruct unavailable
logit matrices. No semantic benchmark, full denoising trajectory or bitwise GPU
equivalence is claimed. The counter is an independent standard exact control,
not execution of FactorDLM, Dang--Ermon or CARS.

## Historical source and tests

All old scientific outputs remain in the current tree; retired configs remain in Git history. The complete implementation,
suite and campaign generators before cleanup are at
`a98ae8e09f2066157ebf6df05f8873b8600e00fb`. Recover them in an isolated checkout:

```bash
git worktree add --detach /tmp/tcc-before-cleanup a98ae8e09f2066157ebf6df05f8873b8600e00fb
git -C /tmp/tcc-before-cleanup submodule update --init --recursive
```

Follow `REPRODUCING.md` in that checkout for the historical commands/environments.
The old suite is intentionally absent from the maintained branch. No archived
measurement was rerun, overwritten or relabeled during cleanup.

For the last fresh-model probability campaign and the pre-M33 comparison/byte
APIs, use a separate checkout (EPIC is already versioned there):

```bash
git worktree add --detach /tmp/tcc-campaign-source 9deb3df
```

Current version 0.4 uses `mwpc_exact.solver.solve_state` for finite-state
oracles and `mwpc_exact.serde` for private strict JSON helpers. The unused
`evaluation`, `experiments`, byte-only and enumeration APIs are retired.
Serial/EPIC generation and the exact LLaDA adapter remain available.

Bulk raw research evidence is excluded from the library sdist/wheel and retained
in Git. Full manuscript reproduction uses the Git evidence checkout. Build an
installed package with `.venv/bin/python -m build --no-isolation`.
