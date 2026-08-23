# Bootstrap status

- Definitive repository: `j0taaa/tcc-final`
- Default branch: `main`
- Historical source snapshot: `j0taaa/tcc@2ae9fe6a888d0e97f5921810c8effa4c7024ca30`
- EPIC pinned commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- Recovered local archive SHA-256: `62b8ed1bf31a414901c4e703ba7d0be272a2d9aee15480894210471c224db489`
- Materialization state: complete; `PROJECT_MATERIALIZED` records the archive used
- Current baseline evidence: see `docs/environment-baseline.md`, `docs/baseline-tests.md`, and `docs/baseline-smoke.md`
- Not yet claimed: MWPC solver correctness, oracle agreement, tokenizer semantics, model integration, benchmark values, or end-to-end scientific results

The archive is retained as a content-addressed recovery artifact. Run
`python scripts/materialize.py --verify-only` for integrity checks. The default
command is non-destructive once `PROJECT_MATERIALIZED` exists; restoring the
historical snapshot requires the explicit `--force` option.
