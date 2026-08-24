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

## Current implementation status

M0 through M5 and T600 are complete: the EPIC baseline and environment are
recorded, scientific contracts are frozen, and the token-aligned and generic
weighted terminal-DAG Python solvers agree with independent exhaustive oracles
on their configured deterministic campaigns. The independent Rust parser and
thin PyO3 binding also agree with Python and brute force on all configured M5
campaigns. The pinned LLaDA tokenizer now has an audited compositional raw-byte
interface for ordinary tokens with added controls rejected explicitly. The
next required task is M6/T601. No token lattice, runtime benchmark, or
end-to-end model result is claimed yet; implementation-dependent article
placeholders remain unchanged.

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

Build and verify the independent Rust production parser binding with:

```bash
make bootstrap-rust-parser
make test-rust-parser
make test-m5-differential
```

The EPIC model experiments and CUDA setup are intentionally separate from the lightweight correctness environment:

```bash
make bootstrap-epic
```

Model weights, datasets and Hugging Face caches are never committed.

## Give this instruction to the coding agent

```text
Read START_HERE.md, AGENTS.md, UPSTREAM.md and TASKS.md. Continue from the
first incomplete required task in dependency order (currently T601). Do not
redo completed milestones or bypass correctness gates. Update task checkboxes
and Evidence fields only after running the required commands.
Never invent benchmark values or replace implementation-dependent placeholders.
Keep vendor/EPIC-Decoding read-only; implement new code under src/mwpc_exact
and crates, using adapters for EPIC integration.
```

## Next concrete target

M5's production-parser gate and T600's tokenizer audit have passed. The next
target is T601: construct deterministic per-position support with fixed-token
invariants, exactness metadata, canonical serialization, and fingerprints.

## Directory map

```text
src/mwpc_exact/            Python contracts, reference solver and orchestration
crates/                    Independent Rust parser and thin PyO3 binding
vendor/EPIC-Decoding/      Read-only pinned EPIC baseline
paper/                     SBC LaTeX article
configs/                   Reproducible experiment configurations
docs/                      Scientific and engineering records
tests/                     Unit, differential and integration tests
results/                   Generated locally; ignored by Git
```

## Attribution

EPIC remains under its own license and third-party notices inside the submodule. This repository records the exact upstream commit in `UPSTREAM.md`; do not copy or remove attribution notices silently.
