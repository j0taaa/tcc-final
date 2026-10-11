# Draft replay refusal: timestamp equality is not the decision contract

2026-10-11. Preserve the original draft and failure BEFORE changing it.
The first FAKE case cpu/seed0/temperature0/max_resamples1 failed its overly
strong comparison. Native IDs, rejection POSITION and failure/complete flag
were identical; elapsed rejection timestamps differed. Full evidence/source
hashes: `evidence/native-draft-failure-v4.json`. No new model head/timing claim.

Upstream generate_constrained.py lines522--526 stores `(position, elapsed)`
in resamples. The first draft mistakenly compared the elapsed component as
though it were a deterministic decision. Suspended generators necessarily
accumulate different diagnostic elapsed time during auxiliary work. Do NOT
claim the joint law of runtime timestamps or physical latency is preserved.
Keep the original native resamples values in payloads; project ONLY the
diagnostic time away for a decision-equivalence check.

The start_time variable is used only by that diagnostic, not for the global
rejection budget, which uses len(resamples). check_valid uses a local Rust
intersection timeout100 and regular-cover selection has its own resource
scope. Need audit those separately: equivalence of the computational kernel
assumes conclusive queries/resources. No mathematical guarantee that wall
deadline behavior or nondeterministic hardware is unaffected by extra work.
Native finite rejection-budget outcomes still remain in the sampler law;
do not silently resample/filter them.

Correction planned only for the comparison projection. The native generator,
its event/control state and actual timestamps will not be edited or forged.
RNG tapes and all token decisions still require an independent full replay.
