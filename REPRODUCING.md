# Reproducing the MWPC research artifacts

This guide separates three different operations:

1. rebuilding the tracked tables and figures from their pinned raw rows;
2. rerunning the CPU correctness experiments to create new raw rows; and
3. optionally rerunning the CUDA end-to-end diagnostic with the pinned model.

They are not interchangeable. A fresh experiment run does not silently replace
the versioned raw evidence, and a top-`K` result is only
`exact_on_support` for one optimizer step. `TIMEOUT` remains distinct from
`INFEASIBLE_ON_SUPPORT` throughout the pipeline.

## 1. Prerequisites and checkout

The reproducibility baseline is Linux, CPython 3.11, Git, GNU Make, and a C/C++
toolchain. Rust is needed only when rebuilding a production parser binding or
rerunning an experiment that uses it. A TeX installation with `pdflatex` and
`bibtex` is needed only for `paper/main.pdf`.

Clone the repository and its read-only EPIC submodule, then create the main CPU
environment:

```bash
git clone --recurse-submodules https://github.com/j0taaa/tcc-final.git
cd tcc-final
make bootstrap
source .venv/bin/activate
make check
```

`make bootstrap` verifies the EPIC gitlink, upstream URL, clean submodule, and
license hashes recorded in `UPSTREAM.md`. It installs the project and its test
tools in `.venv`; it does not install model weights or a CUDA PyTorch build.

## 2. Parser and EPIC bindings

The independent Rust production parser is required for the Q1 and Q4 source
experiments and for the exact strategy in Q2/Q5:

```bash
make bootstrap-rust-parser
make test-rust-parser
```

The pinned EPIC CPU environment and upstream `rustformlang` binding are needed
for EPIC baseline integration and Q2:

```bash
make bootstrap-epic
python -c "import constrained_diffusion, rustformlang; print('EPIC imports ok')"
```

Run `make bootstrap-rust-parser` again after `make bootstrap-epic` when both
the EPIC and exact bindings are needed in the same `.venv`.

## 3. CPU-only artifact reproduction

No GPU, model download, tokenizer download, or external dataset is required to
recompute the final tables and figures. Their small Q1--Q5 raw JSONL inputs are
versioned under `docs/artifacts/raw/t1203_final_results_v1/`, and their hashes
are pinned by `configs/analysis/t1203_final_artifacts_v1.toml`.

In a normal clean checkout, verify that every tracked derivative is exactly the
byte sequence recomputed from those raw rows:

```bash
make final-artifacts-check
```

The generator is create-only. `make final-artifacts` is appropriate only when
both configured output directories are absent. To exercise that path without
altering the current checkout, run the disposable clean-clone rehearsal:

```bash
make rehearse-cpu-correctness
```

The rehearsal clones the current clean commit into a temporary directory,
initializes the pinned submodule, creates a new `.venv`, moves the tracked
derivatives aside inside that disposable clone, runs `make final-artifacts`,
byte-compares the regenerated correctness table with its tracked reference,
and runs `make final-artifacts-check`. The temporary clone is removed at exit.

The full provenance chain for every displayed result is:

```text
src/mwpc_research/final_artifacts.py
  <- scripts/exact_commit/build_final_artifacts.py
  <- configs/analysis/t1203_final_artifacts_v1.toml
  <- docs/artifacts/raw/t1203_final_results_v1/*.jsonl
  -> docs/artifacts/processed/t1203_final_results_v1/final-results.json
  -> docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json
  -> paper/generated/t1203_final_results_v1/*.{tex,svg}
```

The manifest closes the chain by recording source run IDs and hashes together
with every generated output hash.

### Main tables and figures

Each row below is recomputed by `make final-artifacts-check`. The common command
is intentional: the builder checks all pinned input hashes and renders the
bundle atomically, preventing a table from being mixed with a figure derived
from a different raw run.

| Evidence | Expected artifact filename | Command |
| --- | --- | --- |
| Q1 oracle agreement | `paper/generated/t1203_final_results_v1/correctness-oracle-table.tex` | `make final-artifacts-check` |
| Q2 heuristic gaps | `paper/generated/t1203_final_results_v1/heuristic-gap-table.tex` | `make final-artifacts-check` |
| Q2 gap distribution | `paper/generated/t1203_final_results_v1/heuristic-gap-distribution.svg` | `make final-artifacts-check` |
| Q3 finite-slot counterexamples | `paper/generated/t1203_final_results_v1/finite-slot-counterexample-table.tex` | `make final-artifacts-check` |
| Q4 component timing | `paper/generated/t1203_final_results_v1/runtime-breakdown-table.tex` | `make final-artifacts-check` |
| Q4 CPU scaling | `paper/generated/t1203_final_results_v1/runtime-scaling.svg` | `make final-artifacts-check` |
| Q5 end-to-end diagnostic | `paper/generated/t1203_final_results_v1/end-to-end-comparison-table.tex` | `make final-artifacts-check` |

The same command verifies the machine-readable outputs:

- `docs/artifacts/processed/t1203_final_results_v1/final-results.json`
- `docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json`

These are expected filenames, not promises of particular measured values.
Inspect `artifact-manifest.json` for the exact source run IDs, configurations,
and hashes used by the checked-out commit.

## 4. CPU source-experiment reruns

These commands create new ignored raw/processed run directories. They validate
the executable experiment paths but do not overwrite or amend the pinned T1203
evidence bundle.

Q1 compares the exhaustive oracle, independent Python reference, and Rust
production solver:

```bash
make bootstrap-rust-parser
python scripts/exact_commit/run_q1_correctness.py \
  --config configs/experiments/q1_correctness_v1.toml
```

Q2 compares the common serial, EPIC, and exact selectors on identical finite
supports:

```bash
make bootstrap-epic
make bootstrap-rust-parser
python scripts/exact_commit/run_q2_heuristic_gap.py \
  --config configs/experiments/q2_heuristic_gap_v1.toml
```

Q3 replays the finite-slot counterexamples and independently enumerates finite
paths:

```bash
python scripts/exact_commit/run_q3_finite_slots.py \
  --config configs/experiments/q3_finite_slots_v1.toml
```

Q4 runs the separate Python and Rust backends over the configured CPU scaling
axes. Its outputs are diagnostic CPU smoke measurements, not publication
benchmarks:

```bash
make bootstrap-rust-parser
python scripts/exact_commit/run_q4_scaling.py \
  --config configs/experiments/q4_scaling_v1.toml
```

Any oracle disagreement blocks later use of the new rows. Timeout and censored
Q4 rows remain recorded but are not plotted as successful runtimes.

## 5. Optional CUDA end-to-end reproduction

The tracked Q5 table can be rebuilt CPU-only from its pinned rows as described
above. The commands in this section are needed only to create a new live-model
diagnostic. They require CUDA device 0, a compatible CUDA driver, sufficient
local storage, and the exact model snapshot already present in a Hugging Face
cache. The run is deliberately local-files-only.

Create the isolated CUDA environment without changing `.venv`:

```bash
python3.11 -m venv .venv-live
.venv-live/bin/python -m pip install --upgrade pip
.venv-live/bin/python -m pip install -r requirements/t904-live-cu128.txt
.venv-live/bin/python -m pip install --no-deps -e .
VIRTUAL_ENV="$PWD/.venv-live" PATH="$PWD/.venv-live/bin:$PATH" \
  .venv-live/bin/maturin develop \
  --manifest-path vendor/EPIC-Decoding/rustformlang_bindings/Cargo.toml \
  --release
.venv-live/bin/python scripts/install_epic_checkout.py
VIRTUAL_ENV="$PWD/.venv-live" PATH="$PWD/.venv-live/bin:$PATH" \
  .venv-live/bin/maturin develop \
  --manifest-path crates/mwpc_parser_py/Cargo.toml \
  --release
```

Keep the model cache outside the repository. If the model host requires
authentication, use its credential store or a process-scoped environment
credential; never write a token into this repository, a TOML file, a shell
script, or a captured experiment log. Cache the exact configured snapshot:

```bash
export HF_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/mwpc-huggingface"
.venv-live/bin/python - <<'PY'
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="GSAI-ML/LLaDA-8B-Instruct",
    revision="08b83a6feb34df1a6011b80c3c00c7563e963b07",
)
PY
```

The task prompt, grammar, checker, model/tokenizer revisions, support policy,
seed, and generation settings are already pinned in the versioned config. No
external task dataset is used. Run the one-repetition correctness diagnostic or
the warm repeated timing diagnostic with:

```bash
.venv-live/bin/python scripts/exact_commit/run_q5_end_to_end.py \
  --config configs/experiments/q5_end_to_end_v1.toml

.venv-live/bin/python scripts/exact_commit/run_q5_end_to_end.py \
  --config configs/experiments/q5_timing_v1.toml
```

Both commands write new ignored raw/processed directories. The checked-in Q5
configuration sets `publication_mode=false`, `local_files_only=true`, and
`benchmark_claim=false` in the resulting evidence. It supports only a
fixed-task integration and instrumentation conclusion. Run it from a clean
worktree so the recorded commit and configuration provenance remain valid.

## 6. Paper build

After artifact verification, build the article separately:

```bash
make paper
```

The expected local output is `paper/main.pdf`. It is ignored because it is a
build product; the versioned LaTeX sources and generated table/figure inputs
are the reproducibility boundary.
