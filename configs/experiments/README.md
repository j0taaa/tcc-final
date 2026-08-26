# M11 experiment configurations

These TOML files are immutable, non-publication smoke configurations for the
five research questions. They fix the scientific scope, represented-support
policy, model/tokenizer and grammar provenance, seeds, deadlines, and relevant
hardware controls. Later M11 tasks may add publication configurations; they
must not silently change these files.

Load configurations through `mwpc_exact.experiments.load_experiment_config`.
The loader rejects unknown or missing fields and resolves TOML's `"none"` CUDA
sentinel to JSON `null`. Its `config_sha256` hashes sorted, compact JSON of the
fully resolved values, so comments, whitespace, table order, and the local
config path do not affect identity.

Every experiment driver must call `save_resolved_config` before doing work.
It writes `resolved-config.json` inside the run directory. Repeating the same
configuration is idempotent; trying to reuse that directory with different
resolved values fails instead of overwriting provenance.

The Q5 file reuses the already versioned T904 model, tokenizer, and one-byte
grammar smoke. It is not a final task suite or a source of benchmark claims.
Model caches and raw run directories remain untracked.

`q1_correctness_v1.toml` is the executable T1101 configuration. It keeps the
earlier Q1 schema smoke immutable while adding the exact canonical,
exhaustive, and randomized case counts consumed by the Q1 driver.

`q2_heuristic_gap_v1.toml` is the executable T1102 synthetic smoke
configuration. It keeps the earlier Q2 schema smoke immutable and freezes the
three component-selector names, two objective weight modes, paired grammar
settings, pinned EPIC exact-shrink behavior, and brute-force validation limit.

`q3_finite_slots_v1.toml` is the executable T1103 curated-counterexample
configuration. It keeps the earlier Q3 schema smoke immutable and freezes the
two T703 cases, relaxed ordered-anchor `Sigma*` baseline, explicit finite
support, required independent path enumeration, and the fact that this version
does not mine real decoder states.

`q4_scaling_v1.toml` is the executable T1104 CPU scaling configuration. It
keeps the earlier Q4 schema smoke immutable and defines one-axis sweeps for
slots, top-K, realized graph size, reachable grammar productions, token byte
length, and proposal count. Every backend repetition runs in an isolated,
RAM-limited worker. Raw artifacts retain every status; the separate plot-input
artifact contains only uncensored `OPTIMAL` or `INFEASIBLE_ON_SUPPORT` rows.
