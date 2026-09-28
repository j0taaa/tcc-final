# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Research and implementation workspace for the TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

The project implements an exact, certificate-producing optimizer for selecting the maximum-weight compatible set of token proposals at one denoising step. EPIC's serial and heuristic decoders remain read-only baselines. Results over pruned alternatives are reported as exact on the represented support, never as full-vocabulary or future-trajectory optimality.

The current research focus is **selection during actual dLLM generation**.
[M22 live results](docs/research/generated/m22-results.md) compare the validated
Rust optimizer with confidence-greedy feasibility during LLaDA generation of
operand-preserving tool calls. The held-out cohort and reversed-order timing
repeat are archived; the comparison is not against EPIC or all decoding methods.
JSON repair without model inference remains an auxiliary experiment.

## Sources of truth

Post-release fixes and their verification record:
[`Repository review hardening`](docs/review-hardening.md).

Audit of batch-selection timing and practical-benefit claims:
[`Selection audit`](docs/reviews/2026-09-22-selection-audit.md).

- [`AGENTS.md`](AGENTS.md): scientific and engineering invariants;
- [`TASKS.md`](TASKS.md): authoritative current milestone, completed evidence, and remaining work;
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md): supersession index for
  the archived legacy plan and maintained English sources;
- [`UPSTREAM.md`](UPSTREAM.md): immutable EPIC provenance;
- [`docs/decisions/`](docs/decisions/): accepted architecture and scientific decisions;
- [`paper/`](paper/): SBC LaTeX article.

Do not duplicate the current task in this README. Locate the first incomplete required task in `TASKS.md`.

## Setup

The archived **M21 2026-09-28 source snapshot** includes certified JSON repair and
4,992 controlled comparison calls (M21). Its local bundle, PDF and checksums are
described in [`docs/releases/repair-2026-09-28.md`](docs/releases/repair-2026-09-28.md).
That bundle/PDF predates the new M22 live results; use the current checkout for M22.
The historical v0.2.0 and M20 bundle/patch remain unchanged. No remote publication
was performed. From the new delivery directory:

```bash
git clone ./source.bundle tcc-final
cd tcc-final
git submodule update --init --recursive
make bootstrap
source .venv/bin/activate
make bootstrap-rust-parser
make check
```

Try the implemented repair without a model:

```bash
python -m mwpc_exact.repair --profile records '{"id":7,"payload":[["a":1,"b":2}]}'
```

[Usage and boundaries](docs/research/json-repair.md) ·
[Complete controlled results](paper/generated/m21_repair_v1/report.md) ·
[Scientific interpretation](docs/research/m21-findings.md) ·
[Novelty and practical-use review](docs/research/2026-09-28-novelty-and-usefulness-review.md).
The original [four-week plan](docs/research/2026-09-28-json-repair-plan.md)
remains broader: real-model error collection and model retries are still future work.

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

Model weights, private datasets, caches and credentials are not committed. Small, checksummed research outputs are archived under `docs/artifacts/raw/`.

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
