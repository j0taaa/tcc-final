# Exact-commit scripts

Versioned correctness campaigns, experiment drivers, and artifact-generation
scripts live here. Scripts must write raw outputs separately from derived
tables and figures.

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
