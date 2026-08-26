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
