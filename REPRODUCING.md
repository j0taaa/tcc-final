# Reproducing the MWPC research artifacts

## Larger-canvas falsification audit (M31)

Read the [frozen protocol](docs/research/m31-relevance-audit.md) and the
[complete result and claim verdict](docs/artifacts/processed/m31_probability_v1/report.md).
All six prefixes crossed with 4/8/16 slots were fixed before the 18 new official
CPU MDLM predictions. Both call caps, refusals and the external timeout remain
recorded. The exact control is an independent standard array-counter transfer,
not execution of a published competitor. It is preferable on these schemas;
the certifying prototype has no demonstrated general performance advantage.

From the complete Git evidence checkout, recompute reference masses, verify all
35 returned certificates and regenerate/check the complete tables offline:

```bash
.venv/bin/python -m scripts.exact_commit.build_probability_audit_results --check
```

Full logits/probability matrices are large traces retained in ignored local
`results/raw/m31_probability_v1/capture`, not distributed with Git. Git contains
original retained rational probabilities, complete tokenizer semantics, full-row
normalization, source hashes and all proof/job artifacts. If that capture is
available, additionally check every retained value against the full softmax and
original token bytes with `--capture results/raw/m31_probability_v1/capture`.
The default offline check validates mathematics and tables, not unavailable
source logits. A fresh opt-in model reproduction uses new output paths:

```bash
.venv/bin/python -m scripts.exact_commit.capture_mdlm_probability \
  --config configs/experiments/m31_probability_scaling_cpu_v1.json \
  --output results/raw/fresh-m31-capture
.venv/bin/python -m scripts.exact_commit.run_probability_audit \
  --capture results/raw/fresh-m31-capture --output results/raw/fresh-m31-audit
.venv/bin/python -m scripts.exact_commit.run_probability_audit \
  --reference-followup results/raw/fresh-m31-audit \
  --output results/raw/fresh-m31-reference
```

Use a clean producing commit and the pinned CPU model environment described
below. Raw original reference times remain archived; final timing comparisons
use the separately attributed follow-up including coverage and fresh worker RSS.
Neither model predictions nor partition outcomes were replaced. Core inference
times compare different numeric/certificate interfaces, not full deployment.
Call caps limit primary selection queries; proof construction can perform
additional parsing and is included in solver time. Formal verification scope
and the limits of statistical/novelty claims remain explicit.

## Certified probability and fresh CPU dLLM predictions (M30)

Read [definitions, complete proofs and limits](docs/research/m30-probability-certificates.md)
and the [generated report](docs/artifacts/processed/m30_probability_v1/report.md).
This is a separate probability/admission API, preserving original MWPC reward
semantics and serial/EPIC/exact baselines. The model-independent input is
`ProbabilityInput(SelectionInput, probabilities)` with exact rational original
per-support probabilities; fixed rows have probability one. `probability_partition`
returns a portable partition; `verify_mass_proof` recomputes its mass and
conditional TV without an optimizer. `certified_parallel_update` refuses an
uncertified tolerance and never inserts an unbounded fallback. Mean-field
trajectory transport has explicit every-state premises, not automatic model
accuracy or future-trajectory reward optimality.

From the complete Git evidence checkout, verify/rebuild all 192 evaluation cells
and 12 source predictions offline:

```bash
.venv/bin/python -m scripts.exact_commit.build_probability_results --check
.venv/bin/python -m mwpc_exact.mass_cli --verify docs/artifacts/raw/m30_probability_v1/probes/proofs/json_schema_type-2-top8_plus_catalog-finite_language_coverage-64.json.gz --sample --max-tv 1/20
.venv/bin/python -m mwpc_exact.mass_cli --verify docs/artifacts/raw/m30_probability_v1/recursive_probes/proofs/one_child_arrays_depth3-2-top8_plus_alphabet-terminal_alphabet_coverage-64.json.gz --sample --max-tv 1/20
```

Drop `--check` only to regenerate derived prose/macros. Verification checks
complete file inventories, every hash/config/row, full original F64 softmax,
independent exact one/two-token controls and original-input proofs. It performs
no model inference or probability search. The full-vocabulary rational reference
normalizes the recorded F64 row once, before restriction; retained top-K rows
are never renormalized. Unsupported controls have no ordinary byte emission.
Coverage currently requires ABSENT EOS; generic probability certificates also
support existing EOS/PAD semantics. Full/represented scopes remain distinct.

Fresh inference is opt-in, downloads the hash-pinned Apache-2.0 official MDLM
checkpoint (~680 MB) into ignored `.cache/mdlm`, and requires the pinned CPU
Torch/transformers dependencies from the existing EPIC environment. No new
package dependency or GPU is necessary. Work from a clean producing commit and
use **new** output paths:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4 RAYON_NUM_THREADS=1 \
  .venv/bin/python -m scripts.exact_commit.capture_mdlm_probability \
  --config configs/experiments/m30_probability_cpu_v1.json --output results/raw/fresh-capture
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4 RAYON_NUM_THREADS=1 \
  .venv/bin/python -m scripts.exact_commit.run_probability_probes \
  --capture results/raw/fresh-capture --output results/raw/fresh-probes
```

Repeat with `m30_probability_recursive_cpu_v1.json` and new paths for the
recursive phase. Frozen protocol limits/tolerances and all errors/refusals are
retained. Official source/checkpoint hashes and adapted-kernel hash are in
metadata; CPU kernels are independently tested but are not claimed bitwise
GPU-equivalent. Model loading/warmup is excluded from forward timings; support
construction, coverage, search/checking and serialization are separate fields.
The configurations preceded each phase's predictions; the recursive follow-up
is development evidence after finite-catalog observations, not held-out accuracy.
Specialized exact controls remain preferable for these small cases.

## Certified conflicts and computation reuse (M29)

[Complete report](docs/artifacts/processed/m29_conflict_v1/report.md) and
[proof/reuse specification](docs/research/m29-conflict-commitment.md):

```bash
.venv/bin/python -m scripts.exact_commit.build_conflict_results --check
.venv/bin/python -m mwpc_exact.conflict_cli --input docs/artifacts/raw/m28_budgeted_real_v1/completed/inputs/geocoding-v2-step01-ordinary-primary.json.gz --budget 2 --proof /tmp/geocoding-commit.json.gz
.venv/bin/python -m mwpc_exact.conflict_cli --verify /tmp/geocoding-commit.json.gz
```

The two-sided engine revalidates full token witnesses and checks conflicts under
safe containment, recalculating every changed reward. Its complete cohort is 72
repeated-measure inputs from 36 saved LLaDA states, not fresh model generation.
All six exact comparator/ablation results remain visible. The primary DP run was
interrupted: 68 original measurements remain; four missing measurements were
run separately. Two missing proof files were regenerated with archived scores
checked, without replacing timing rows. Content-addressed interrupted inventories
retain original bytes under `interruption-audit/`; continuation metadata names
all producing commits. This recovery is not counted as a timing improvement.

M29--M31 bulk research archives remain versioned in Git and excluded from the
library sdist/wheel, like earlier large model campaigns. Installations preserve
core APIs, proof/oracle tests, formal sources and small existing offline fixtures;
full manuscript reproduction uses the Git evidence checkout. No weights or
Hugging Face caches are distributed.

## Current mathematical contribution (M26)

Current local delivery: [mathematical source/PDF snapshot](docs/releases/math-2026-09-30.md).
The [mathematical core](docs/research/m26-mathematical-core.md) contains definitions,
six fully written theorems and corollaries. Their universal claims follow from
proofs; random/exhaustive tests check the implementation, not theorem validity.
No model, GPU, downloads or performance benchmark is needed for this contribution.

With the installed CPU package, use a new output path:

```bash
.venv/bin/python scripts/exact_commit/budget_math_example.py --output /tmp/budget-proof.json
.venv/bin/python scripts/exact_commit/budget_math_example.py --verify /tmp/budget-proof.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/exact_commit/test_budgeted_math.py
make release-wheel-smoke
make paper
```

The example emits the original resource graph, normalized CFG, rational upper
potentials and every budget witness. Verification loads the independent checker
without importing the optimizer. A valid path with reward equal to the checked
upper bound proves optimality relative to the supplied graph. This small example
illustrates a budget-dependent witness; it is explicitly not an accuracy benchmark.
`make release-wheel-smoke` installs a fresh non-editable wheel outside the checkout
and generates/verifies this proof, in addition to its existing artifact checks.

`mwpc_exact.budgeted_commit.budgeted_commit_frontier(SelectionInput, max_budget)`
accepts the existing frozen model-independent state with grammar, canvas, all
proposals, finite support, compositional-byte adapter and EOS policy. It returns
`BudgetedCommitResult` for each cap. `committed_proposal_ids` include every positive
matched ID at paid positions; `matched_proposal_ids` include the full witness
matches. `budgeted_progress_update` fills remaining capacity using witness tokens,
reports unscored fallback and rejects another input's result. The original MWPC
result and serial/EPIC/exact strategies remain unchanged. The new dimension is
implemented in the rational Python reference, not the fast Rust production solver.

Status remains explicit and exactness is current-step `exact_on_support`.
The update-round bound requires no remasking and support retaining the witness.
Dominance compares batches with the same proposals, support, fixed positions and
physical budget; native EPIC system runs do not automatically meet those premises.
The proofs do not imply higher semantic accuracy, lower latency, full-vocabulary
or future-trajectory optimality, or proof-assistant formalization.

## New budgeted method on real saved states (M28)

The [frozen protocol](docs/research/m28-real-state-replay.md) records all source
hashes and reconstruction rules. Read the
[generated report](docs/artifacts/processed/m28_budgeted_real_v1/report.md) for
certificates, exact objective comparisons and measured CPU cost. Rebuild from
the complete corrected archive, without a model or network:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/run_budgeted_real_replay.py \
  --verify docs/artifacts/raw/m28_budgeted_real_v1/completed
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.exact_commit.build_budgeted_real_results --check
```

For a fresh execution, use a clean checkout, a new output directory and the
committed `configs/experiments/m28_budgeted_real_replay_v1.json`. CPU MWPC and
EPIC bindings are required for baselines. `inputs/` stores losslessly mapped
model token IDs and source references; `proofs/` stores gzip-compressed original
input certificates. `rows.jsonl` retains statuses, scores, committed positions,
full witnesses, baseline diagnostics and timings. Timings cover the shared
budget-0--2 frontier, not three independent single-cap solves; no new model
forward is measured. Input reconstruction is timed outside the optimizer.

The ordinary-reward comparison uses the native EPIC byte batch selector plus
a cap and finite-support validation. Pending serial fallback is excluded from
scored comparisons. These results do not replace the complete historical EPIC
decoder experiments. The interrupted first attempt is retained separately;
its harness errors are not treated as algorithm failures or scored losses.

## Historical live dLLM study (M24/M25)

Historical local delivery: [2026-09-30 dLLM snapshot](docs/releases/dllm-2026-09-30.md).
Source, frozen configs, raw archives, generated tables and recorded query
attempts are versioned. No model weights or remote publication are included.

With the CPU environment described below, independently validate archives and
regenerate the manuscript products without model inference or network:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_policy_campaign.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_grounded_campaign.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/freeze_grounded_confirmation.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_live_article_results.py --grounded --check
make query-demo-check
make paper
```

Removing `--check` regenerates derived tables from unchanged raw archives.
`make article-results` performs this regeneration for the current article;
`make article-results-check` checks both historical and current study products.
[Detailed M24 commands](docs/research/m24-reproduction.md),
[M25 commands/data audit](docs/research/m25-reproduction.md) and
[live/replay query](docs/research/m25-query-demo.md) distinguish archive
verification from new GPU measurements. Each raw row retains its producing
commit and revisions; the final documentation commit does not replace them.

`make rehearse-artifact-rebuild` clones clean committed source, builds a wheel,
installs it non-editably in a new Python 3.11 environment and regenerates the
M24/M25 report collection and article tables byte for byte, alongside historical
products. It also verifies all eight query records offline. This checks clean
artifact reproduction, not remeasurement of GPU timings. New inference needs
a cached pinned checkpoint and an idle GPU; tests never download models.

## Auxiliary certified JSON repair study (M21)

Historical repair delivery: [2026-09-28 repair snapshot](docs/releases/repair-2026-09-28.md).
The former M20 bundle/patch and v0.2.0 remain historical. No remote publication.

Rebuild the complete analysis from hash-verified archived output without a GPU,
model, tokenizer or json_repair installation:

```bash
.venv/bin/python -m scripts.exact_commit.build_json_repair_results
.venv/bin/python -m scripts.exact_commit.build_json_repair_results --check
make article-results-check
make paper
```

Raw evidence: `docs/artifacts/raw/m21_repair_v1/{pilot,confirmation,mechanism}`.
Analysis: `paper/generated/m21_repair_v1/`; includes a full report, all status
counts, document-level paired comparisons and descriptive bootstrap intervals.
The source run commit is `47b93c4`. To repeat precisely, create a detached worktree
at that commit and install the pinned experiment tools. Current source also
accepts the frozen configs but records its different source commit.

```bash
.venv/bin/python -m pip install -c requirements/constraints-py311-linux.txt -r requirements/repair-experiments.txt
.venv/bin/python -m scripts.exact_commit.run_json_repair --config configs/experiments/m21_repair_pilot_v1.toml --run-directory results/raw/repair-pilot-new
.venv/bin/python -m scripts.exact_commit.run_json_repair --config configs/experiments/m21_repair_confirmation_v1.toml --run-directory results/raw/repair-confirmation-new
.venv/bin/python -m scripts.exact_commit.run_json_repair --config configs/experiments/m21_repair_mechanism_v1.toml --run-directory results/raw/repair-mechanism-new
```

Runs require a clean checkout, production binding, Linux resource limits and
cached `tokenizer.json` for `GSAI-ML/LLaDA-8B-Instruct` revision
`08b83a6feb34df1a6011b80c3c00c7563e963b07`. If absent, download that tokenizer file
explicitly through Hugging Face before running; no model weights are needed.
At the producing commit, the optional requirements file lists only json-repair:
install `jsonschema==4.25.1`, `tokenizers==0.21.4` and `huggingface_hub==0.36.2`
under its constraints as well. All rows record the installed versions.
Outputs require new directories and preserve failure/timeout rows. These are
controlled corruptions, not observed model errors. See the [frozen protocol](docs/research/m21-repair-protocol.md)
and [interpretation](docs/research/m21-findings.md).


## Earlier selector audit

The current manuscript uses M19's stronger comparator and common deadline;
M18 remains historical evidence. Frozen measurement source/config: `196d48c`.
Run from a clean checkout into a new directory:

```bash
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --config configs/experiments/m19_selection_audit_v1.toml \
  --run-directory results/raw/m19-selection-audit-new
.venv/bin/python scripts/exact_commit/build_selection_audit.py
make article-results-check
make paper
```

Analysis verifies archive hashes and uses the independently checked confirmation
tasks for the witness/functional audit. See
`docs/reviews/2026-09-22-selection-audit.md` for findings and limits.

## Maintained and historical measurement commands

M18 retires the separate branching launcher, branching report CLI and nonliteral
live supervisor. Their complete source remains at the immutable `v0.2.0` tag;
the M16/M17 measurement commands below refer to that source version. To repeat
them without changing your working branch, use `git worktree add --detach
/tmp/mwpc-v020 v0.2.0` and follow the setup there. The current tree retains all
raw evidence, independent oracles, baseline tests and `build_review_results`
for regenerating the submitted tables. It maintains one bounded offline runner
for recursive scaling and model-state replay, and the original Q5 live driver.

The batch-selection experiment uses the same offline runner:

```bash
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --config configs/experiments/m18_batch_selection_v1.toml \
  --run-directory results/raw/m18-batch-selection-new
```

Regenerate its analysis and manuscript values from the checked-in raw archive:

```bash
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --analyze-directory docs/artifacts/raw/m18_batch_selection_v1 \
  > paper/generated/m18_batch_selection_v1/summary.json
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --analyze-directory docs/artifacts/raw/m18_batch_selection_v1 --latex \
  > paper/generated/m18_batch_selection_v1/batch-values.tex
make paper
```

This verifies the archive manifest before analysis. Producing source/config:
`3d573b2c8ea2312b681f81108abaa11f8a497d3f`; observations and scope are documented
in `docs/reviews/2026-09-22-practical-selection.md`. The current manuscript
supersedes these claims with the M19 audit; the historical v0.2.0 release remains unchanged.


## Current review evidence

The corrected experiments add evidence without overwriting Q1--Q5. The protocol
and pilot observation correction are in
docs/decisions/0024-review-experimental-protocol.md. Raw records are archived
under docs/artifacts/raw/m17_review_v1 with checksummed compressed JSONL and
original per-run metadata. The first pilot's observation failures are retained.

Rebuild the new manuscript results without a model or network:

    .venv/bin/python scripts/exact_commit/build_review_results.py
    .venv/bin/python scripts/exact_commit/build_review_results.py --check
    make article-results-check
    make -C paper

Fresh experiments require a clean committed checkout and a new output directory:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.exact_commit.run_branching_study --run-directory results/raw/new-branching-run
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.exact_commit.run_review_offline --config configs/experiments/m17_recursive_scaling_v1.toml --run-directory results/raw/new-scaling-run
    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.exact_commit.run_review_offline --config configs/experiments/m17_real_replay_v2.toml --run-directory results/raw/new-replay-run

Replay consumes all 24 archived corrected-pilot snapshots at K=2,4,8 without
loading the model. The independent unit for an inference about tasks would be
the prompt, not each forward/width/method condition. Replay counts are
descriptive conditions, with no population confidence claim.

For fresh GPU generation, use the pinned CUDA environment and local checkpoint
described below:

    PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python -m scripts.exact_commit.run_nonliteral_live --config configs/experiments/m17_nonliteral_pilot_v2.toml --run-directory results/raw/new-pilot-run
    PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python -m scripts.exact_commit.run_nonliteral_live --config configs/experiments/m17_nonliteral_confirmation_v1.toml --run-directory results/raw/new-confirmation-run

Pilot v1 is excluded from performance comparisons because its observation
wrapper interfered with baseline resampling. All corrected-pilot/confirmation
failures and incomplete outputs remain included. Generation is bounded by
60 seconds and setup by 180 seconds. Scaling/replay use a one-second native
limit, a 15-second process limit and 2048 MiB address space. New timings and
statuses are new measurements; never replace archived rows to make checks pass.

The current reviewed delivery is the **2026-09-28 source snapshot**; see
[`docs/releases/review-2026-09-28.md`](docs/releases/review-2026-09-28.md).
The local v0.2.0 release and remote v0.1.1 remain historical. Each experiment row
names its own producing commit. The review patch does not create new measurements.

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

## Post-release maintenance checkout

The current working tree includes the fixes documented in
[`docs/review-hardening.md`](docs/review-hardening.md); they are not part of
the historical `v0.1.1` measurements. The maintained CPU/dev setup uses exact
Python package constraints in `requirements/constraints-py311-linux.txt` and
Rust 1.98.0 in `rust-toolchain.toml`. Those constraints target Linux x86_64,
CPython 3.11; they are not a newly verified CUDA lock or a cross-platform lock.
`make bootstrap`, `make bootstrap-epic`, and CI consume the constraints.

M5/M6/M7 differential scripts now write fresh temporary output directories by
default. Use `--output-directory <new-directory>` to keep a new run. Existing
summary files are protected against overwriting; the historical paths inside
the campaign configurations identify prior evidence, not mutable output files.

## 1. Prerequisites and checkout

The reproducibility baseline is Linux, CPython 3.11, Git, GNU Make, and a C/C++
toolchain. Rust is needed only when rebuilding a production parser binding or
rerunning an experiment that uses it. A TeX installation with `pdflatex` and
`bibtex` is needed only for `paper/main.pdf`.

Clone the repository and its read-only EPIC submodule, then create the main CPU
environment:

```bash
git clone ./mwpc-review-base.bundle tcc-final
cd tcc-final
git checkout --detach a43e1cf904eceff8bbcc802b5c0b2abb1c10c059
git apply ../mwpc-review.patch
git submodule update --init --recursive
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

### Formal and original-input certificate gates (M27)

Install Elan explicitly, then `elan toolchain install leanprover/lean4:v4.34.0`.
No Mathlib or additional Lean package is required. The checking command does not
download a missing toolchain and fails rather than skipping missing verification.

```bash
make check-formal
make check-project
.venv/bin/python scripts/exact_commit/budget_math_example.py \
  --verify docs/artifacts/math/m27-budget-proof.json --lean
```

If Elan is outside `PATH`, use `LAKE="$HOME/.elan/bin/lake"` with Make, or
`--lake "$HOME/.elan/bin/lake"` with the script. Ordinary `pytest` stays offline
and does not require Lean. The CI formal job is mandatory and uses the pinned
toolchain. [The coverage and trust map](formal/README.md) identifies the exact
kernel statements and the separate Python check of original-input graph
correspondence. The five concrete bridge profiles and rejection result are in
`docs/evidence/m27-formal-checks.json`.

The budget API defaults to prefix sharing; `graph_layout=BudgetGraphLayout.PRIVATE`
retains the independently checked comparison construction. Physical token
identity and paid closings remain explicit. `certify_budget_batch` independently
validates an incumbent and returns exact lower/upper bounds; it does not make
an interrupted solver `OPTIMAL`, nor promise continually improving search.
The tightness test uses all frozen proposals, including outside-support choices,
and assumes later support expansion changes none of the other input semantics.

After artifact verification, build the article separately:

```bash
make paper
```

The expected local output is `paper/main.pdf`. It is ignored because it is a
build product; the versioned LaTeX sources and generated table/figure inputs
are the reproducibility boundary. The review snapshot in
`dist/review-2026-09-28/` contains the PDF, base Git bundle, review patch,
evidence archive, manifest and SHA256SUMS; see
`docs/releases/review-2026-09-28.md`. The source bundle requires the pinned EPIC submodule
for baseline execution. The historical remote v0.1.1 assets remain unchanged.

## Historical release checkout (M17 only)

For the historical local submission release, not the current reviewed article:

```bash
git clone ./mwpc-exact-v0.2.0.bundle tcc-final
cd tcc-final
git checkout v0.2.0
```

Current `make paper` checks M13, M17 and M19 derivatives and then checks the
compiled PDF's 10–16 pages, unresolved references and overfull boxes. Poppler's
`pdfinfo` is required along with TeX. The historical result tables retained in
`paper/supplement-method.tex` are not additional tables in the main article.
