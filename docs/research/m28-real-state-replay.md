# Budgeted commitment on real saved dLLM states

## Frozen protocol (2 October 2026, before outcome evaluation)

The question is whether the new exact-rational budgeted implementation can
consume authentic model states, return finite-slot commitments and export
independently checkable optimality certificates. This is an offline replay,
not a new model generation, an accuracy benchmark or a proof of faster decoding.

`configs/experiments/m28_budgeted_real_replay_v1.json` freezes 27 source hashes:

- All 24 M17 confirmation snapshots: four prompts in each of three recursive
  grammar families, with saved forwards 0 and 8, seed 170302. These are actual
  LLaDA outputs on researcher-authored prompts, not an external test population.
- All 12 pre-commit states of the archived geocoding-v2 trajectory, seed 250929:
  `Find the geographic coordinates of "Belo Horizonte".` This is one existing
  application example, not 12 independent requests.

Both archives use LLaDA-8B-Instruct and tokenizer revision
`08b83a6feb34df1a6011b80c3c00c7563e963b07`. No prompt, target, probability or
original fixed token is edited. Token IDs may be losslessly compacted; each
input retains the local-to-model map. The recursive replay uses saved top-2
alternatives, primary proposals and EOS/PAD. The query retains the historical
Cartesian positional domains, required EOS additions, and catalog byte CFG;
it does not restrict the witness to the catalog's canonical tokenizations.

The recursive archive originally preselected a small proposal set. This replay
instead reconstructs one primary proposal at **every masked position** from
its saved top permitted token and full-vocabulary probability. It does not
renormalize top-K logits or keep the original position preselection. The query
already saved one primary proposal per masked position. Proposal IDs remain
traceable through physical positions and the original source archive.

Each of the 36 states is evaluated with caps 0, 1 and 2 and two reward profiles:

- `all_primary`: every captured primary proposal, including EOS/PAD.
- `ordinary_primary`: identical canvas, grammar, emissions and support, with
  EOS/PAD proposals removed from the objective. EOS/PAD remain legal witness
  choices. This aligns candidate eligibility with EPIC's batch-selector API.

The 72 inputs and budget frontiers are repeated measurements of 36 source
states, not independent samples. No case is selected or discarded by score,
feasibility, elapsed time or advantage over a comparator.

## Execution and comparisons

Each method runs in a fresh bounded CPU process (180 seconds for the rational
frontier, 30 seconds for each baseline job; 4 GiB address-space cap). Both caps
1 and 2 are checked for each baseline. A timeout has no objective value and is
never counted as infeasibility, a zero score or an exact-method win.

The reference API preserves the ordinary MWPC contract by keeping complete
witness matches separate from positions actually committed under the budget.
It emits one portable original-input proof per solved frontier, covering all
three caps. The offline verifier checks graph completeness, token provenance,
fixed positions, EOS/PAD, exact binary-rational weights, upper potentials and
witness attainment. Progress updates are independently replayed against their
witness; fallback positions remain separate from scored commitments.

Comparators use the same frozen input/profile:

1. `confidence_preselection`: keep the B highest-confidence proposals, then
   run the existing Rust MWPC solver and validate the resulting batch against
   the original input. This is a strong version of confidence preselection.
2. `unbudgeted_then_cap`: use the existing Rust MWPC witness, then retain its
   B highest-reward matched positions. Scores are independently recomputed as
   exact binary rationals even though the historical solver uses binary64.
3. `epic_regular_cover_then_cap`, ordinary profile only: call the unchanged
   pinned native EPIC selector, using the same byte CFG and all ordinary
   primary candidates; then retain at most B selected positions. Validate
   that capped batch by seeking a completion on the original finite support.
   EPIC's abstract-gap feasibility is not accepted as a finite-slot witness.

The EPIC comparison is explicitly its batch selector followed by a budget
cap. It is **not** a replay of the full EPIC denoising/resampling policy. An
infeasible finite batch, an unresolved validation or an unsupported call is
reported distinctly and excluded from feasible objective-gap comparisons.
Native selector diagnostics and selected IDs are retained.

Model forwards are historical observations only. Current CPU measurements
separate lattice construction, parsing, backtracking and certificate checking;
validated updates and worker/process overhead are recorded separately. The
frontier solver time amortizes budgets 0--2; it is not a single-cap time. One
repetition provides descriptive timings, not a statistical speed claim.

## Reproduction

The producing command requires a clean checkout with committed code/config:

```bash
.venv/bin/python scripts/exact_commit/run_budgeted_real_replay.py \
  --config configs/experiments/m28_budgeted_real_replay_v1.json \
  --output results/raw/m28_budgeted_real_replay_v1
.venv/bin/python scripts/exact_commit/run_budgeted_real_replay.py \
  --verify results/raw/m28_budgeted_real_replay_v1 \
  --summary results/processed/m28_budgeted_real_replay_v1.json
```

No model download, GPU or network is needed. CPU Rust/EPIC bindings are required
for comparators. Python certificates establish this replay's optimality;
the existing Lean coverage remains as documented in `formal/README.md`.
This protocol does not silently promote real-state certificates to new
kernel-checked Lean instances.
