# V3 — Preserve fixed-slot probability one in the fixture

The V2 oracle at producer8661645 stopped when constructing json-fixed/low-mass.
Its input generator scaled an ALREADY FIXED slot below probability one, which
the maintained ProbabilityInput correctly rejects. This is a setup error,
not a solver counterexample or a successful completed oracle. All earlier
rows and failure.txt stay in evidence/oracle-v2; do not overwrite them.

V3 scales only free slots in that fixture. All cases/modes and mathematical
checks are preserved. The reference algorithm is unchanged. Ruff-only fixes
use pairwise, explicit strict zip and tuple unpacking; they change no intended
test cases or calculations. Re-run the entire oracle into a NEW directory.

The geometric tail statement in theory-v1 is interpreted with k>=1 for its
strict inequality; k=0 has failure probability one. The original draft stays
unchanged. A finite cap always returns explicit FAIL, never an uncorrected P
sample. This clarification does not claim novelty or a measured speed gain.
