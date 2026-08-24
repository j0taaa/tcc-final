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
