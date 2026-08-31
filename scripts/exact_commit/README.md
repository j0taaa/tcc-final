# Exact-commit scripts

Versioned correctness campaigns, experiment drivers, and artifact-generation
scripts live here. Scripts must write raw outputs separately from derived
tables and figures.

All Q1--Q5 drivers treat `--run-directory` as the immutable raw directory and
accept an optional distinct `--processed-directory`. When the raw path is
under `results/raw/`, the default processed path mirrors it under
`results/processed/`; an arbitrary raw path defaults to a non-nested
`<run>-processed` sibling. Resolved configs and replay failures stay with raw
JSONL, while summaries and Q4 plot-ready rows go to the processed directory.
Existing files are never silently overwritten.

Publication-facing CSV, SVG, and LaTeX inventories are rebuilt only from raw
JSONL with a versioned config:

```bash
python scripts/exact_commit/build_publication_artifacts.py \
  --config configs/analysis/t1201_q3_artifacts_v1.toml
python scripts/exact_commit/build_publication_artifacts.py \
  --config configs/analysis/t1201_q3_artifacts_v1.toml \
  --verify-existing
```

The first command is create-only. Delete the declared processed and paper
output directories before rebuilding. The second command verifies every
tracked derivative byte-for-byte and fails if a number or label was edited.
See `docs/artifacts/README.md` for storage and publication rules.

Statistical summaries use one shared, model-independent implementation for
Wilson score intervals, absolute and relative gap distributions, type-7
runtime quartiles, normalized median overhead, and explicitly labelled event
rates. The versioned formula-regression artifact runs with:

```bash
make statistics-check
```

Its input is deliberately synthetic and carries `benchmark_claim=false`; it
tests formulas and edge semantics rather than reporting model performance.
Relative gaps for zero optima are undefined and excluded, with the excluded
count retained. Per-step and per-generation event rates always carry separate
denominators. Q5 generation rows report generation-level rates only and state
that step-level rates are unavailable because those rows aggregate steps.

The M3 three-way oracle campaign is configured by
`configs/exact_commit/m3_differential.toml` and runs with:

```bash
python scripts/exact_commit/run_m3_differential.py
```

It writes a versioned summary and stores replay fixtures for every failing
seed in the configured ignored artifact directory.

The M4 weighted terminal/epsilon-DAG campaign is configured by
`configs/exact_commit/m4_graph_differential.toml` and runs with:

```bash
python scripts/exact_commit/run_m4_graph_differential.py
```

It compares normalized max-plus parsing with direct original-graph path
enumeration and validates every saturated edge's original provenance.

The T600 tokenizer audit requires the separately pinned EPIC dependencies and
downloads only the tokenizer files at the immutable configured revision:

```bash
make bootstrap-epic
HF_HOME=.cache/huggingface \
  python scripts/exact_commit/audit_t600_llada_tokenizer.py
```

Add `--local-files-only` to reproduce from an already populated cache. The
script tests the entire base vocabulary, all added/special tokens, byte
coverage, curated text classes, and the seeded random campaign, then writes
`docs/evidence/t600-llada-tokenizer-audit.json`.

The T904 live-model smoke uses a separate optional CUDA environment so the
CPU-pinned baseline environment remains unchanged:

```bash
python3.11 -m venv .venv-live
.venv-live/bin/python -m pip install -r requirements/t904-live-cu128.txt
.venv-live/bin/python -m pip install --no-deps -e .
VIRTUAL_ENV="$PWD/.venv-live" PATH="$PWD/.venv-live/bin:$PATH" \
  .venv-live/bin/maturin develop \
  --manifest-path vendor/EPIC-Decoding/rustformlang_bindings/Cargo.toml --release
.venv-live/bin/python scripts/install_epic_checkout.py
.venv-live/bin/python scripts/exact_commit/run_t904_llada_live_smoke.py \
  --config configs/exact_commit/t904_llada_live_smoke.toml
```

After the exact revision is cached, add `--local-files-only`. The driver loads
one NF4-quantized model instance, invokes the original serial and EPIC-enabled
constrained loops and the parent-side exact hook, independently recognizes all
three outputs, and saves raw model/tokenizer/device/certificate metadata. It
does not produce a latency, throughput, quality, or comparative benchmark.

The T1101 Q1 correctness experiment requires the independent Rust production
binding and runs its canonical, exhaustive, and randomized finite-support
families with:

```bash
make bootstrap-rust-parser
python scripts/exact_commit/run_q1_correctness.py
```

The driver creates unique ignored raw and processed directories unless paths
are supplied. It writes immutable raw JSONL, the resolved config, and exact
replay fixtures to raw storage, and writes the computed summary separately. A
single disagreement makes the command exit nonzero.

The T1102 Q2 heuristic-gap experiment requires both pinned EPIC and the exact
Rust production binding:

```bash
make bootstrap-epic
(cd crates/mwpc_parser_py && ../../.venv/bin/maturin develop --release)
python scripts/exact_commit/run_q2_heuristic_gap.py
```

It replays each configured weighted input through
`greedy_exact_feasibility`, `epic_regular_cover`, and `exact_mwpc`, and also
uses guarded brute force to validate the exact reference score. Raw rows and a
computed summary are written separately. Any missing/inconclusive selector,
exact-oracle disagreement, or negative measured gap emits a complete benchmark
fixture and makes the command exit nonzero.

The T1103 Q3 finite-slot experiment replays the versioned T703 corpus with:

```bash
python scripts/exact_commit/run_q3_finite_slots.py
```

It records the concrete abstract `Sigma*` witness, available slots, minimum
required physical tokens, exact finite status, and either a reconstructible
finite witness or a reason for represented-support infeasibility. The finite
parser is checked against complete finite-path enumeration. Raw JSONL and the
computed summary are immutable and separate; any replay error remains distinct
from `INFEASIBLE_ON_SUPPORT` and makes the command exit nonzero.

The T1105 Q5 paired live-model experiment reuses the pinned T904 CUDA
environment and additionally installs the Rust production binding:

```bash
VIRTUAL_ENV="$PWD/.venv-live" PATH="$PWD/.venv-live/bin:$PATH" \
  .venv-live/bin/maturin develop \
  --manifest-path crates/mwpc_parser_py/Cargo.toml --release
.venv-live/bin/python scripts/exact_commit/run_q5_end_to_end.py \
  --config configs/experiments/q5_end_to_end_v1.toml
```

The driver loads one local-only NF4 model instance and resets seed and CUDA
memory statistics before applying unconstrained, serial, EPIC, and Rust exact
selection to the same prompt and generation schedule. Raw JSONL retains every
generated token row, independent syntax/target checker result, batch and
fallback count, exact status/scope/certificate, elapsed time, process RSS, and
CUDA peak allocation. This single fixed-order run has no warmup and supports
only a diagnostic smoke conclusion; T1106 adds robust timing controls.

The T1106 timing configuration uses the same executable Q5 driver after one
warmup per strategy and records eight repetitions in balanced cyclic order:

```bash
.venv-live/bin/python scripts/exact_commit/run_q5_end_to_end.py \
  --config configs/experiments/q5_timing_v1.toml
```

Model/tokenizer loading, grammar compilation, shared preprocessing, and each
method's runner/environment setup occur before the measured call. The timer
synchronizes CUDA before resetting peak counters and again after generation.
Every raw row retains its repetition ID, elapsed time, sampled per-call process
RSS peak, process lifetime RSS high-water mark, and CUDA allocated/reserved
peaks. The computed summary uses type-7 linear interpolation for runtime median
and IQR and excludes timeout, error, and incomplete rows from runtime samples.
This small fixed-task result validates instrumentation; it is not a publication
benchmark.

The M5 Python/Rust/oracle campaigns are configured by
`configs/exact_commit/m5_rust_differential.toml` and run with:

```bash
make test-m5-differential
```

Rebuild the release binding with `make bootstrap-rust-parser` first. Every
mismatch writes its exact serialized input plus failure metadata under the
configured ignored artifact directory.

The M6 finite tokenizer-aware campaigns are configured by
`configs/exact_commit/m6_finite_lattice_differential.toml` and run with:

```bash
make test-m6-differential
```

Each seed constructs a small explicit support with variable and multi-byte
token emissions, same-byte/different-ID choices, proposal provenance, and
optional fixed positions. Direct enumeration defines the exact-on-support
answer; both the Python debugging solver and Rust production solver must agree
with it. Exact mismatch inputs and failure metadata are saved for replay.

The T703 finite-slot counterexample corpus is replayed with:

```bash
make test-m7-counterexamples
```

The command verifies concrete witnesses for the relaxed abstract `Sigma*`
intersection, recomputes their required-EOS slot shortfalls, and compares the
finite EOS-lattice parser with independent complete-path enumeration. It writes
the deterministic, versioned summary to
`docs/evidence/t703-finite-slot-counterexamples.json`.

The T704 seeded finite-slot EOS/PAD differential campaigns are configured by
`configs/exact_commit/m7_eos_finite_slot_differential.toml` and run with:

```bash
make test-m7-differential
```

The oracle enumerates the explicit token-row Cartesian product and applies an
independent EOS interpreter before CFG recognition. It does not use product
lattice states, epsilon normalization, or parser backpointers. The campaign
randomizes required/optional termination, EOS position, canonical PAD suffixes,
fixed ordinary/EOS/PAD slots, special controls, proposal weights, and support
rows. Every optimal parser witness is checked by the public independent
certificate validator, and every failure saves its exact input for replay.
