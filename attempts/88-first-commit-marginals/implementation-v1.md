# A88 V1 — implementation details before any model call

The earlier protocol, proof and rational oracle remain unchanged. This file
fixes implementation choices left open there, before the one native capture.

The prompt requests a brief explanation and one letter; the exact prompt,
chat-template IDs, 31+1 eligible positions, delimiter IDs, entire V=126464
partition and unchanged selected MMLU rows are in native-inputs-v1.json.
The independent observed-slot generator uses seed+1000000000. It records
only a coupled first hit, never a completed native output. Free proposals
have separate CUDA generators. CPU checks run before freezing this source.

Only root q/CDF tensors are retained, on GPU, once per item. All later
queries are recomputed physically; exact (canvas, public-step) hashes permit
an optimistic offline global-cache comparator. Public time is part of the
state hash. No CPU copy of full heads is retained. Captured data are grouped
five-bin values, original committed IDs and profiles. Model/config/tokenizer
files are streamed through SHA256 during preparation and checked again
before loading. The source/inputs must equal HEAD before --capture.

All family members use the same full clean categorical heads. Timers charge
model+categorical preparation per state; per-visit free RNG, rank, canvas,
state hash and cache access; integration reductions/updates only before d;
tail decision RNG on each tail visit, and selection-aware reductions only
at an actual tail hit. MC does not pay any a5 reduction. qf5 on nonterminal
steps is diagnostic research overhead. Diagnostic observed proposals during
integration are excluded from modeled method costs. Full query/capture wall
time still includes all those operations. Final scalar/vector serialization
is charged separately; JSONL research trace output is separately reported.
Profiles synchronize CUDA: these are measurements of kernels within this
capture, not end-to-end implementations of every decoder. Python dispatch,
timer/profiler effects and cache realizations limit latency conclusions.

For each path, first-hit probabilities are Wprev*A. The analyzer explicitly
sums every hit, tests simplex/conditional means, and computes nonnegative
conditional variance as a squared distance. It reconstructs every canvas
from frozen input and original committed IDs. The global-cache expected
union probability is 1-product(1-visit_i), conditional on the auxiliary
paths and independent stopping coins. States are prepared once, kernels
remain per visit. Costs are block costs for N=8, divided by eight.
Preparation, source re-verification and load are amortized equally over
8 items and 8 replicas and reported separately; no repeated root is charged.
The root-only comparator additionally reports a distinct-third-replica
U statistic for variance times mean cost. The nonlinear global-cache
product is explicitly exploratory. Paired percentile intervals use 2,000
whole-replica bootstrap samples, seed 888801; neither steps nor tokens are
independent bootstrap units. No multiplicity correction or significance
claim; all seven candidates are reported against both controls. A zero
empirical variance is inconclusive. A point advantage of >=10% in >=6/8
items plus the >=.9 option-mass gate can only support a future independently
frozen protocol; modeled costs alone leave end-to-end qualification open.

Floating softmax sums/CDF endpoints, zero clean probabilities and cutoff
ties are recorded. searchsorted(right=True) skips zero plateaus. A uniform
outside the floating CDF causes ERROR, not silent last-token reassignment.
Tiny negative b from roundoff is clamped to zero and explicitly recorded;
there is no option-only or output-vector renormalization. BF16 logit,
softmax, confidence comparison, reduction and CUDA RNG errors prevent a
bit-exact claim. The exact rational oracle remains separate evidence.

Commands, from repository root:

    .venv-live/bin/python attempts/88-first-commit-marginals/native_v1.py --prepare
    .venv-live/bin/python attempts/88-first-commit-marginals/test_native_v1.py
    # Commit exact source/inputs/protocol before the next command.
    .venv-live/bin/python attempts/88-first-commit-marginals/native_v1.py --capture --output artifacts/a88-native-v1.jsonl
    .venv-live/bin/python attempts/88-first-commit-marginals/analyze_v1.py artifacts/a88-native-v1.jsonl --output artifacts/a88-analysis-v1.json

No retry, row replacement, model tuning or independent follow-up test is
part of this bounded qualifier. An interruption or refusal is preserved.
