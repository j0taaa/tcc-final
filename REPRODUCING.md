# Reproducing the reduced project

The user requested removal of the old test suite and excess implementation.
M34/M35 add a small focused posterior suite; the historical suite remains
removed. The commands below check that extension, builds, selected mathematical
proofs and original-input certificates, not universal implementation correctness.

## Setup

```bash
make bootstrap
make check
make test
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
`article-results` regenerates the maintained M31/M34 products. Earlier generated
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

## M34: exact recursive-CFG posterior (current extension)

The old suite stays removed. `make test` runs eleven focused independent tests,
including every pinned <=128-byte external JSON syntax case, deadline/work limits
and live archived recomputation; no network/model is required. CI requires this
target. `make article-results-check` separately checks
M34's losslessly packed input archive, every config/source hash and all 52
unchanged before/after mass/marginal pairs, then regenerates products in memory.
That artifact check does not run the current posterior implementation. The new
suite recomputes the smallest free canvas (case ID breaks ties) from each final
scaling, array-model and JSON-model cohort against archived rational mass and
all marginals. Selection never reads success or timing. To recompute every one
of the 55 final inputs, without changing recorded timings or artifacts:

```bash
.venv/bin/python -m scripts.exact_commit.build_cfg_posterior_results --check
.venv/bin/python -m scripts.exact_commit.build_cfg_posterior_results --recompute
.venv/bin/python -m scripts.exact_commit.build_cfg_posterior_results --sample json-context0-16
```

`components.json.gz` deduplicates grammar/tokenizer/permitted-vocabulary values;
`inputs.json.gz` restores exact original inputs by SHA-256; `runs.json.gz` retains
all phase configs, metadata and outcomes. The manifest records original compressed
input hashes and producing command forms. Recorded commits are `952c24d` (initial
array replay), `5ec4a89` (corrected initial scaling grid), `03630c9` (all nine fresh
JSON forwards), `6331e37` (all 55 identical-input integer replays), and `e5b28e1`
(all 27 rejection/reuse follow-ups). The aborted first scaling input construction
has no measured case and remains explicitly recorded. The first fresh-capture
commit had a formatting error later fixed; it is not a claim of a passing lint gate.

To repeat campaigns, use a clean producing commit and a new output directory:

```bash
.venv/bin/python -m scripts.exact_commit.run_cfg_posterior_audit --mode scaling --output results/raw/new-scaling
.venv/bin/python -m scripts.exact_commit.run_cfg_posterior_audit --mode replay --output results/raw/new-arrays
# Opt-in: needs the pinned official MDLM/GPT-2 artifacts and CPU model dependencies.
.venv/bin/python -m scripts.exact_commit.capture_cfg_json_demo --output results/raw/new-json
```

The replay source is the complete archived M31 cohort, not chosen successes.
Post-refinement timings are attributed to their actual producing code; current
reweight/restriction handling can incur different overhead. Rejection follow-up
is transparently added after the initial audit, with an independent recognizer,
integer categorical draws from the same represented rows, seed 20261006 and
10,000-attempt/30-second limits. Exact posterior probability and implied geometric
trial counts are not end-to-end model accuracy or measured universal speedups.
Full logits/checkpoints remain excluded from Git. No new dependencies were added.

Full local logits can also be checked opt-in, without new model forwards:

```bash
.venv/bin/python -m scripts.exact_commit.check_cfg_model_capture --capture results/raw/m34_cfg_posterior_v1/json-model
.venv/bin/python -m scripts.exact_commit.build_probability_audit_results --check --capture results/raw/m31_probability_v1/capture
```

Both checks were executed on all nine new JSON and all 18 original array
captures. They verify source hashes, full non-mask softmax, rational normalization
and retained original probabilities. The fresh check additionally checks the
entire declared top-32 cohort, rather than selecting solved cases. These local
logits are intentionally absent from the default offline checkout audit.

## Bounded posterior compilation

`compile_cfg_sampler(..., timeout_seconds=30, max_preprocessing_work=1_000_000)`
shares a cooperative deadline across admission, canonical source/input matching,
private binarization/normalization, token graph and forest construction. The
preprocessing budget counts symbol visits/copies and intermediate alternatives;
it checks projected nullable expansion before allocation. Identical nullable
bodies are deduplicated in stable first-occurrence order. Distinct optional
symbols can still require exponential canonical output and trigger
`CompilationLimit`, never an infeasibility/zero-mass verdict. This preserves
exact structural source/input verification and the old CNF representation.

Standalone `check_ll1` and `normalize_to_cnf` accept an optional shared
`mwpc_exact.reference.limits.WorkBudget`. Their default reference behavior has
no work cap; callers preparing custom input grammars should pass a budget too.
Compilation's forest caps remain `max_chart_cells`/`max_alternatives`.
Cooperative checks cannot preempt an individual Python operation or enforce an
OS memory cap. This change does not relabel historical runtime measurements.

## Execution-conditioning research reference (M36)

The source and mathematical supplement are separate from production decoder
strategies. Build the supplement with `make research-note`; its PDF is copied
to `output/pdf/semantic-conditioning.pdf`. `make test` includes three focused
execution/profile/sampling oracles and a real archived-input recomputation.
They do not establish scientific priority.

The frozen MDLM/JsonLogic integration config is
`configs/experiments/m36_semantic_reference_v1.json`. A capture requires the
already audited local CPU MDLM environment/cache and a clean producing commit;
it never belongs to the default network-free test path. Use
`scripts.exact_commit.capture_semantic_reference --capture --directory PATH` in
that environment, where PATH is new. Optional `--consumer PATH/logic.js` checks
the pinned official JsonLogic implementation under Node; its exact URL and hash
are in the config. Optional `--full-capture .cache/semantic-reference-v1.npz`
independently checks full softmax/rational rows. Full logits remain local.

Without `--capture`, the same module recomputes the archived inputs and checks
every template completion independently without loading a model. The illustration
declares lexical support before logits/targets; it is not an external benchmark,
an end-to-end decoder comparison or accuracy on unseen records. The target not
representable by the frozen canvas must remain zero mass. The signed covering
transform is known; the research dossier and supplement delimit the comparator.

The completed capture is in `docs/artifacts/raw/m36_semantic_reference_v1/`,
produced from clean source `2be61a9773a016930dc407ab051d6f2d497704a0`.
`SHA256SUMS` fixes the config, input and original results; replay verifies those
hashes, recomputes all profile masses against independent enumeration, and
compares recorded target masses/statuses. Run the offline check and regenerate
the displayed probabilities/geometric trial counts with:

```bash
.venv/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1
.venv/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1 --summary > docs/research/generated/m36-semantic-summary.md
# Optional: pinned consumer and full local logits, without another model forward.
.venv-live/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1 --consumer .cache/jsonlogic/logic.js --full-capture .cache/semantic-reference-v1.npz
```

Ordinary replay reports `official_consumer=NOT_RUN` and
`full_logits_checked=false`. The original capture records both optional checks
as passed; those observations are not attributed to the offline run. External
users can verify inference on published rational rows; auditing their entire
softmax origin additionally needs the local NPZ or a fresh opt-in capture.
The consumer file is not vendored. See `docs/evidence/m36-semantic-reference.md`
for commands, licenses, scope and the remaining human-review boundary.
