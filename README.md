# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Research and implementation workspace for the TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

The project implements an exact, certificate-producing optimizer for selecting the maximum-weight compatible set of token proposals at one denoising step. EPIC's serial and heuristic decoders remain read-only baselines. Results over pruned alternatives are reported as exact on the represented support, never as full-vocabulary or future-trajectory optimality.

## Sources of truth

- [`AGENTS.md`](AGENTS.md): scientific and engineering invariants;
- [`TASKS.md`](TASKS.md): authoritative current milestone, completed evidence, and remaining work;
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md): supersession index for
  the archived legacy plan and maintained English sources;
- [`UPSTREAM.md`](UPSTREAM.md): immutable EPIC provenance;
- [`docs/decisions/`](docs/decisions/): accepted architecture and scientific decisions;
- [`paper/`](paper/): SBC LaTeX article.

Do not duplicate the current task in this README. Locate the first incomplete required task in `TASKS.md`.

## Setup

The immutable reproducibility release is
[`v0.1.1`](https://github.com/j0taaa/tcc-final/releases/tag/v0.1.1). Check it
out explicitly so the source, configs, paper, and evidence paths stay aligned:

```bash
git clone --branch v0.1.1 --recurse-submodules \
  https://github.com/j0taaa/tcc-final.git
cd tcc-final
make bootstrap
source .venv/bin/activate
make check
```

Omit `--branch v0.1.1` only when intentionally following development on
`main`.

Artifact regeneration, clean CPU rehearsal, parser-binding, and optional CUDA
model instructions are in [`REPRODUCING.md`](REPRODUCING.md).

Build and verify the independent Rust production parser when the current task requires it:

```bash
make bootstrap-rust-parser
make test-rust-parser
make test-m6-differential
```

## Decoder strategy configuration

The reusable integration boundary validates `serial`, `epic`, and `exact`
commitment before model loading:

```bash
mwpc-commit-config --help
mwpc-commit-config \
  --commit-strategy exact \
  --exact-support-top-k 8 \
  --exact-eos-policy absent
```

Omitting `--commit-strategy` preserves EPIC's existing
`CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH` switch. Exact top-`K` decoding is
reported as `exact_on_support`; it is not a full-vocabulary or future-trajectory
optimality claim.

The first parent-side model hook is
`mwpc_exact.epic_adapter.llada.run_llada_exact_step`. It consumes the pinned
LLaDA loop's single-batch token, logit, prediction, and confidence rows after
the existing `k_s` schedule is known. It excludes prompt tokens from the CFG
canvas, restricts ordinary commits to the active block, applies only a live
independently validated optimum, and records canonical EOS/PAD suffix updates.
The vendor LLaDA implementation remains unchanged. A configured serial or EPIC
failure fallback must be supplied by its baseline adapter; selecting
`--exact-fallback none` requires no such callback.

Install the heavier pinned EPIC environment only for baseline or model-integration work:

```bash
make bootstrap-epic
```

Model weights, datasets, caches, credentials, and generated raw results are not committed.

## Agent handoff

```text
Read START_HERE.md, AGENTS.md, UPSTREAM.md, and TASKS.md. Locate the first
incomplete required task and continue in dependency order. Do not repeat
completed milestones or bypass correctness gates. Update a task's Evidence
field only after every acceptance criterion and required command passes.
Never invent measurements or replace article placeholders without versioned,
reproducible artifacts. Keep vendor/EPIC-Decoding read-only.
```

## Repository map

```text
src/mwpc_exact/            Runtime contracts, reference solvers, validation, and orchestration
crates/                    Independent Rust parser and thin PyO3 binding
vendor/EPIC-Decoding/      Read-only pinned EPIC baseline
configs/                   Immutable correctness and experiment configurations
scripts/exact_commit/      Reproduction and campaign entry points
tests/                     Unit, oracle, differential, regression, and integration tests
docs/                      ADRs, evidence, history, and reproducibility records
paper/                     SBC LaTeX article
```

## Attribution

Gabriel Jota Lizardo's original parent-repository software and research
artifacts are MIT-licensed; the manuscript's publication rights remain
separate. EPIC remains governed by its own license and third-party notices
inside the submodule. See `LICENSE`, `LICENSES.md`, and `UPSTREAM.md` for the
exact scopes and pinned upstream commit.
