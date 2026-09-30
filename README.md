# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Research and implementation workspace for the TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

The project implements an exact, certificate-producing optimizer for selecting the maximum-weight compatible set of token proposals at one denoising step. EPIC's serial and heuristic decoders remain read-only baselines. Results over pruned alternatives are reported as exact on the represented support, never as full-vocabulary or future-trajectory optimality.

The current research focus is **selection during actual dLLM generation**.
[M24 findings](docs/research/m24-findings.md) preserve 3,856 live generations
and a scoped cost–quality benefit on synthetic tool calls, compared with actual
EPIC and its official recovery. The [M25 external study](docs/research/m25-findings.md)
adds a schema/question-grounded development/confirmation split, strong EPIC,
greedy and canonical-MAP controls, and all failures. Its finite support and
own AST grader are explicitly distinguished from an official BFCL evaluation.
[Novelty boundaries](docs/research/m25-novelty-boundaries.md) identify established
weighted-parsing and exact-dLLM antecedents; no universal superiority is claimed.

Run the archived **real LLaDA geographic query** without a model or network:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/run_query_demo.py --mode replay
make query-demo-check
```

The [live/replay guide](docs/research/m25-query-demo.md) explains both sets of four
recorded policy attempts and the validated read-only API dispatch. The replay
is an archived execution, not new inference. New live generation needs the
pinned CUDA environment and locally cached model. Model-free JSON repair
remains an auxiliary application.

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

The current local source/PDF delivery is described in
[`dLLM study, 2026-09-30`](docs/releases/dllm-2026-09-30.md).
It includes the versioned measurements and their reproduction scripts. The
[2026-09-28 repair snapshot](docs/releases/repair-2026-09-28.md), M20 delivery
and v0.2.0 remain historical; no remote publication was performed.
From the current delivery directory:

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
