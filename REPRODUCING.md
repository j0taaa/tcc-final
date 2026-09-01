# Reproducing the MWPC research artifacts

The immutable private-repository reproducibility release is
[`v0.1.0`](https://github.com/j0taaa/tcc-final/releases/tag/v0.1.0). Its tag is
the common source reference for the code, paper, configurations, and evidence
archive; individual experiment rows retain their earlier producing commits.

> **T1203 name clarification.** `final` denotes the deterministic output of
> this artifact build, not publication-level benchmark status. Later
> publication-mode evidence must use a new bundle ID and never overwrite
> `t1203_final_results_v1`.

This guide separates three different operations:

1. `artifact-rebuild`: rebuilding tracked tables and figures from pinned raw
   rows;
2. `source-experiment-rerun`: rerunning CPU correctness from code and config to
   create new raw rows and a new table; and
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
git clone --branch v0.1.0 --recurse-submodules \
  https://github.com/j0taaa/tcc-final.git
cd tcc-final
make bootstrap
source .venv/bin/activate
make check
```

`make bootstrap` verifies the EPIC gitlink, upstream URL, clean submodule, and
license hashes recorded in `UPSTREAM.md`. It installs the project and its test
tools in `.venv`; it does not install model weights or a CUDA PyTorch build.

Verify the non-editable release artifact separately:

```bash
make release-wheel-smoke
```

This command builds an sdist and wheel with the pinned `build` and Hatchling
versions, inspects the wheel for both `mwpc_exact` and `mwpc_research`, and
installs it into a new temporary virtual environment. From a working directory
outside the checkout, that environment runs the Q3 finite-slot experiment and
creates the T1202 statistical-summary fixture. The rehearsal rejects imports
whose module paths resolve into the checkout, so an editable installation or
`PYTHONPATH` cannot hide a missing package.

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
both configured output directories are absent.

### Rehearsal level 1: artifact-rebuild

To exercise the create path without altering the current checkout, run:

```bash
make rehearse-artifact-rebuild
```

This command requires a clean worktree. It clones the current commit into a
temporary directory, initializes the pinned submodule, builds the release wheel
from that clean clone, and installs it non-editably in a new virtual
environment. From the wheel-installed packages, it moves the tracked
derivatives aside, rebuilds the bundle, byte-compares **every** processed and
paper output against its tracked reference, and verifies the rebuilt outputs.
Expected temporary artifacts are
`docs/artifacts/processed/t1203_final_results_v1/*` and
`paper/generated/t1203_final_results_v1/*`. A missing package, source-tree
import, hash error, missing/extra output, or byte difference fails the command.
The temporary clone is removed at exit. `make rehearse-cpu-correctness` remains
an alias for this level only.

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

### M13 article result selection

The article uses exactly three compact generated result elements. Verify their
hash-pinned derivation with:

```bash
make article-results-check
```

The provenance chain is:

```text
configs/analysis/m1301_article_results_v1.toml
  <- T1203 processed results and pinned Q1 rows
  <- M12.5 Q2/Q4/Q5 publication summaries and pinned rows
  -> docs/artifacts/processed/m1301_article_results_v1/article-results.json
  -> paper/generated/m1301_article_results_v1/article-result-values.tex
  -> paper/generated/m1301_article_results_v1/r1--r3*.tex
```

The builder verifies every input SHA-256 and recomputes all displayed values.
It keeps the synthetic Q2 results illustrative, the real-state singleton gap
as a null alignment result, and the Q4 compound graph-size axis distinct from
representative workload scaling. `make paper` depends on this byte-verification
step, so hand-edited article values fail before LaTeX runs.

## 4. CPU source-experiment reruns

These commands create new ignored raw/processed run directories. They validate
the executable experiment paths but do not overwrite or amend the pinned T1203
evidence bundle.

### Rehearsal level 2: source-experiment-rerun

Run the clean release-oriented Q1 rehearsal with:

```bash
make rehearse-source-correctness
```

Like level 1, this command starts from a clean clone and a non-editable
`mwpc-exact` release wheel. It also builds and non-editably installs the
independent Rust-parser wheel. It then executes the configured 249-case Q1
campaign and creates these temporary outputs:

```text
source-experiment-rerun/raw/q1-cases.jsonl
source-experiment-rerun/processed/q1-summary.json
source-experiment-rerun/semantic-summary.json
source-experiment-rerun/correctness-rerun-table.tex
```

The semantic validator compares the new rows with the pinned Q1 rows by case
ID, family, solver statuses, result status, objective value, agreement, and
independent certificate-validation count. Timing and run-metadata fields are
intentionally excluded from byte identity. Any missing/extra case or semantic
mismatch fails the command; different legitimate timings do not. The generated
table is a rehearsal product, not a new publication artifact, and is removed
with the temporary clone.

The equivalent manual Q1 command below is useful for keeping outputs for
inspection, but it uses the active development environment rather than testing
the release-wheel boundary.

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

Neither clean CPU rehearsal claims to rerun the EPIC-dependent Q2 study, Q4
timing/scaling campaigns, or any Q5 CUDA/model campaign. Those remain explicit
manual or external runs with their own configurations and dependencies. In
particular, the T1260 rehearsal did not download a model, access a GPU, or
recreate prior Q5 observations.

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
are the reproducibility boundary. The `v0.1.0` GitHub release also carries the
verified PDF, an evidence-only archive, and their `SHA256SUMS`. The archive is
not a substitute for the tagged recursive clone because it intentionally does
not copy the EPIC submodule; its exact contents and rebuild command are in
`docs/releases/v0.1.0.md`.
