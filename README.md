# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Research and implementation workspace for the TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

The project adds an exact, certificate-producing optimizer for choosing the maximum-weight compatible set of token proposals at one denoising step. It preserves EPIC's serial and heuristic decoders as baselines and treats exactness over pruned top-`K` alternatives explicitly as **exact on the represented support**.

## Repository status

- Scientific and engineering contract: [`AGENTS.md`](AGENTS.md)
- Ordered implementation backlog: [`TASKS.md`](TASKS.md)
- Explanatory implementation plan: [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
- TCC article in SBC LaTeX format: [`paper/`](paper/)
- Pinned EPIC baseline: `vendor/EPIC-Decoding` at the immutable SHA in [`UPSTREAM.md`](UPSTREAM.md)
- New code belongs in `src/mwpc_exact/` and later in `crates/`; the EPIC submodule is read-only.

No benchmark result, correctness result, or model result is claimed in this bootstrap commit. Placeholders must remain placeholders until backed by reproducible artifacts.

## Clone

```bash
git clone --recurse-submodules https://github.com/j0taaa/tcc-final.git
cd tcc-final
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

## Local setup

CPU-only setup for reference algorithms and unit tests:

```bash
make bootstrap
source .venv/bin/activate
make check
```

The EPIC model experiments and CUDA setup are intentionally separate from the lightweight correctness environment:

```bash
make bootstrap-epic
```

Model weights, datasets and Hugging Face caches are never committed.

## Give this instruction to the coding agent

```text
Read START_HERE.md, AGENTS.md, UPSTREAM.md and TASKS.md. Start at T000 and
continue in dependency order. Do not bypass correctness gates. Update task
checkboxes and Evidence fields only after running the required commands.
Never invent benchmark values or replace implementation-dependent placeholders.
Keep vendor/EPIC-Decoding read-only; implement new code under src/mwpc_exact
and crates, using adapters for EPIC integration.
```

## First concrete target

The first scientific gate is a small token-aligned max-plus CKY implementation whose score agrees in every generated small case with both exhaustive completion enumeration and exhaustive proposal-subset enumeration. Do not begin tokenizer, model or performance integration before that gate passes.

## Directory map

```text
src/mwpc_exact/            Python contracts, reference solver and orchestration
crates/                    New Rust parser and PyO3 binding (created in M5)
vendor/EPIC-Decoding/      Read-only pinned EPIC baseline
paper/                     SBC LaTeX article
configs/                   Reproducible experiment configurations
docs/                      Scientific and engineering records
tests/                     Unit, differential and integration tests
results/                   Generated locally; ignored by Git
```

## Attribution

EPIC remains under its own license and third-party notices inside the submodule. This repository records the exact upstream commit in `UPSTREAM.md`; do not copy or remove attribution notices silently.
