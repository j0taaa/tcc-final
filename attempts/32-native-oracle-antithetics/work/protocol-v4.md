# A32v4 frozen complete-EPIC numerical-answer protocol

This refines, rather than replaces, `protocol-v4-inputs.md` and its eight
criteria. No A32 real head has been computed when this protocol is written.
The question-only selection and all negative A31 results remain immutable.

## Operation and admission

Return two candidate numerical JSON answers consumed by a verifier. The grammar
accepts ANY JSON number, not a gold list. Only exact numeric equality with the
official GSM8K `####` answer counts. Duplicates, strings, bools, extra keys,
errors, incomplete outputs and resource refusals are incorrect, never dropped.
This is a regular subclass of CFGs, NOT an experiment on arbitrary recursion.
Direct structured answers omit reasoning text in every method; no claim of
matching the model's unconstrained chain-of-thought benchmark accuracy.

All32 train questions and all64 test questions were selected by question hash
alone. Train gold is opened only AFTER protocol/producer source commit/push.
Test gold is not opened until the independent branch is activated. The original
public combined files contain labels even during question selection; this is
disclosed, not described as zero exposure to their bytes.

## Competent methods and full distribution boundaries

The executable JSON defines16 methods at temperatures0.5 and1.0, plus a
deterministic native control. No top-K, support pruning or deterministic ranking
tail is introduced. Every method uses complete native EPIC, original recovery,
native optimizations, identical prompt/grammar and the same cold per-batch
2GiB frozen-head cache. Independent seeds are shared for matched first paths.

Candidates are bounded class-only walks with budgets4/16, root-only and
sufficient-state coordination. The class divides numerical-prefix original
token IDs by a pre-noise estimated median; it is not a gold-aware class and
does not filter any token. The walk itself never consumes the probability.

Controls are native iid2, native iid4, a first stochastic plus second
deterministic response, exact finite-ticket raw-noise root/history/state
coupling copied from frozen A31, and BOTH compact sequential AND batched
empirical pools of budget16 at root/state. The pools have the SAME pair law
as walk16; no expected-quality superiority over them is asserted. The density-
aware maximum class-disagreement control uses ideal continuous Plackett–Luce
probabilities and conditional row rejection (512 total-row budget). It is
competitive but its second native FINITE rounding law is only approximate;
all budget refusals remain failures, and the first path stays literal.

The original native decoder SHA is guarded. Class setup decodes the original
entire vocabulary; aliases retain IDs. The native public `additional_stuff`
cache is supplied equally: its pinned implementation returns early with
supertokens, NOT an expensive full-token lexical table. This optimization is
available to every baseline, not an invented speed advantage.

## Costs and execution

Record grammar/prelex preparation, per-question prompt preparation, class
preparation and tensor transfer, full native generation/recovery, actual new
forwards, cache/transfers, all auxiliary rows, verification/output, CPU/wall
and peak CUDA allocation. Model/tokenizer load is excluded as one declared
common deployment cost; report it separately. Report class/grammar first-use
cost AND amortization over the deployment's complete same-method campaign.
Charge each method the setup it needs, including mixtures' first temperature.
No cost argument omits the extra model histories caused by diversity.
Per-record output write/flush costs are measured AFTER the main row, in the
separate IO journal, and added by analysis to `full_wall/full_cpu`; sidecar
research journaling itself is outside the returned-answer operation. Frozen
head digest logging is common telemetry INCLUDED in measured batches; this
comparison does not establish the fastest possible uninstrumented EPIC.

Run methods in question/seed-specific shuffled order using an independent
Python RNG. Empty the model cache before each batch. Do not run heavy tests,
builds, LPs or unrelated model jobs during competitive measurements. First-path
audit compares IDs, output, status, recovery, rejection count, native-complete
and model query count; time/caching and diagnostic head hashes are separate.
Retain every row/error and flush immediately. Never overwrite earlier output.

## Frozen decision rules

The pilot is the first development seed on ALL32 cases, BOTH temperatures and
ALL16 methods, plus32 deterministic controls:1056 records. It checks literal
first-path equality and the direction of the semantic effect. If no walk has
at least two absolute percentage points of macro pass@2 gain over matched
iid2, the pilot may screen this application out; this is a negative resource
decision, NOT a statistical proof that the full campaign cannot succeed.
Any unexplained first-path mismatch blocks a positive claim.

Only a promising pilot triggers the remaining three development seeds. No
pilot configuration or case is dropped from that full development report.
Candidate selection requires macro pass@2 gain>=0.02 over matched iid2 and
full wall AND CPU per correct request no greater than iid2. Also reject a
candidate dominated by ANY control configuration (including other temperature,
iid4, mixed and deterministic): control coverage>=candidate and wall/CPU per
correct<=candidate with one strict inequality. Pools may tie in quality and
must compete on cost. Of eligible candidates select maximal gain over iid2,
then lower full mean wall, then smaller budget, root before state, T0.5 first.
No surviving candidate means no independent branch.

Confirmation uses ALL64 frozen test inputs, eight NEW seeds, the ONE selected
candidate and ALL12 noncandidate controls with both temperatures (deterministic
once/case). Gate: gain>=0.02 versus matched iid2, paired95% case-cluster
bootstrap lower bound>0 (10000 draws, seed329999), and full wall AND CPU per
correct no greater than matched iid2. Confirmed result must remain undominated
by all control configurations under the above rule. Report differences versus
EVERY control, losses and uncertainty, not only the winning comparison.
No change to metric/method/budget/gate after seeing heads or gold.

This gate can establish a particular real-operation quality/cost advantage.
It cannot establish general EPIC superiority, scholarly priority, editorial
acceptance, semantic superiority for arbitrary verifiers, or full Lean proof.
The written universal nondecrease is ONLY against iid of the SAME native
decoder/kernel. The stronger local coupling can worsen later diversification,
so no monotonicity in budget is assumed. Prior Nacu–Peres construction and
finite-probability availability remain serious originality objections.
