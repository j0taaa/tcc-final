# Q1 correctness experiment

T1101 compares three independently implemented paths on the same explicit
finite token support:

- direct enumeration of every represented token completion;
- the Python reference finite-lattice parser; and
- the Rust production finite-lattice parser.

The five canonical cases cover jointly incompatible proposals, duplicate
matching proposals, fixed-position infeasibility, multi-byte tokens, and
distinct token IDs with identical bytes. The exhaustive family contains all
144 combinations induced by the following bounded definition: two positions;
token IDs `0` and `1`; every non-empty free support row or valid singleton
fixed row; and every subset of one positive integer proposal for each
represented `(position, token_id)` choice. The randomized family uses 100
contiguous seeds beginning at the configured seed and retains M6's multi-byte,
same-byte/different-ID, fixed-position, and forced-infeasibility stressors.

Agreement means equal solver statuses and, for `OPTIMAL`, equal objective
values plus independent validation of both backend certificates. Witnesses may
differ when several optima exist. Every row records its grammar and support
hash, input sizes, seed, statuses, property-check counts, and separate oracle,
Python, and Rust timings. Any disagreement or exception writes the complete
input and failure metadata before the overall command exits nonzero.

This is an `exact_on_support`, per-step correctness experiment. It does not
claim full-vocabulary or future-trajectory optimality, and its smoke timings
are not publication benchmarks.
