# Native terminal replay V4: correctness gate passed, utility still unmeasured

2026-10-17. Contract/source copies `3a2b57ef5b5cfcef1b63c8190d862dec53b4c7f8`
precede adapter/oracle/runner `3e62727105068826281b93b4ff6252bcad047e3c`.
The first actual native run exits1 after16 CPU records because the zero-sum
fixture accidentally permits a positive decimal suffix. Exact failed source,
records and restoration metadata remain in `evidence/v3-draft/`. Written
correction `c5a571b` precedes corrected runner
`2f55fc4a8b46a43114e447010f6361418a35851a` and its second, complete run.
Neither draft nor result is relabeled or erased.

The corrected command is recorded in `evidence/v4/origin.json`, with a directly
observed exit0. ALL48 tuples pass: six fixed fixtures x CPU/CUDA x seeds17/29
x read_only false/true. This executes96 original constrained steps (baseline
and capture),560 native proposals total, including320 additional helpers.
Eight original partial-canvas outputs are ineligible and correctly skip every
helper. All320 ACTUALLY sampled helpers complete; rejection of incomplete
helpers after an eligible first is covered by the rational oracle, while the
native partial fixture's positive incomplete paths are independently enumerated
and observed. Do not imply native random draws exercised that missing branch.

All original IDs, aliases, thinking-offset pins, accepted numeric prefix,
active/inactive canvas slots, histories, counters, output tensors and complete
caller RNG states match literally before/after capture and replay. Advancing
the live matcher and overwriting returned log-marginals after capture leaves
the cloned helper kernel intact. Caller Python/NumPy/Torch CPU/CUDA RNG,
precision and thread policy are restored. Helper streams are seeded ONCE per
readout and advance; they are not reset per draw. Snapshots are provenance;
these checks do not mechanize ideal iid random bits or their finite-RNG law.

The path oracle independently enumerates the frozen small operator's paths
and original token-path marginals. Maximum absolute marginal error is
`1.9073504518019035e-6`, below the frozen5e-5 tolerance. Full fixture has96
positive complete words; partial fixture16 complete/94 incomplete words;
zero-sum control has one complete zero vector and exactly zero variance.
These are CONSTRUCTED logits, not observed neural uncertainty. Every actual
proposal is in the enumerated support. The separate post-run audit checks
all48 expected tuples,120 means recomputed with exact fractions,320 helper
accounts and14 unchanged pinned native file hashes. GPU peak allocation is
8,706,560 bytes; this small synthetic allocation is NOT model memory usage.

No pretrained tokenizer/model was loaded, no dataset/gold row read, no
backbone forward or update run. No competitive latency, quality or statistical
variance experiment was performed. Pinned native functions are AST-extracted
unchanged with original imports, one tensor-parallel worker and synthetic
self-conditioning; the vLLM service/plugin registration/model was NOT executed.
The maintained345-test suite is unchanged and not rerun/credited here.

This closes only T8802's minimal native replay obligation. Next, BEFORE real
heads or labels, freeze resource/input selection and a necessary terminal-
variance screen. Measure zero/failed/incomplete cases and full cost, including
capture, every helper, parsing and rendering. Controls remain normalized native
output, native sampling/MAP, exact101-value integer-sum semantic DP and complete
trace ensembles. Need an actual feasible model with clearly named scope;
the reported DiffusionGemma26B/48GB setup is not reproduced on local12GB.
The classical all-gold risk identity, this correct adapter and a favorable
constructed variance do not establish useful own novelty or fulfill the goal.
