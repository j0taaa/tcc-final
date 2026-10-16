# V18 — Conditional-variance necessity probe, BEFORE code/new auxiliary data

2026-10-16, after V17 functionality. V15 stays unfavorable/exploratory. This
is development on ALL16 KNOWN old paths/70 states, not independent questions,
full decoder-cost validation, training or a publication claim. Conditional
Monte Carlo, state baselines and variance identities remain CLASSICAL.

## Eight criteria

1. Estimate reward-gradient variance of V14's SAME9-parameter frozen-proposal
   actor. Fresh posterior auxiliaries reuse old heads ONLY. No new neural
   forward/decoder trajectory/label/update. All original paths/states stay.
2. Families: exact observed-action/regular-proxy readouts and conditional
   auxiliary averaging of existing competent partial-score estimators.
   Generic RB/resampling is not novelty. Useful specific difference is OPEN.
3. Purpose: determine whether hidden noise is large enough to justify an
   expensive fresh-path/full-cost study. A zero-overhead necessity pass cannot
   establish real sample efficiency, own novelty or the user's scientific goal.
4. V16 supplies conditional means/covariances; formulas below remove the
   finite-M mean-estimation contribution to the paired variance estimate.
   Original visible-path uncertainty remains: only2 paths/question.
5. First minimal rational moment/tail-baseline oracles. Freeze exact source,
   runtime/protocol/input hashes BEFORE fresh head-derived auxiliaries and
   variance calculations. No fitting coefficients on evaluated auxiliaries.
6. Retain every word/status/score/actor/verifier/preparation/CDF/bit/RSS cost.
   CPU four threads, no CUDA/model,3600s whole/60s operation/2GiB process RSS.
   Diagnostic timings are NOT competent per-method deployment costs. The
   screen optimistically grants candidate zero extra cost, a necessary test.
7. All7 score methods,4 fixed state baselines,27 fixed (C_regular,W_full_sem,
   W_anchor_sem) coefficient triples from V15 are retained. All get the cheap
   pre-state semantic certificate below. RLOO full variance is unestimable
   from one old group/question; report conditional auxiliary noise separately,
   never call it full RLOO variance. Independent fitting/horizon critics,
   partial enumeration and optimized cost controls remain a later obligation.
8. Gaps: population uncertainty, complete costs, RLOO/full strong comparisons,
   learning/application, sufficient originality and external confirmation.
   A pass only permits reconsidering a NEW frozen fresh-path protocol.

## Strong cheap state certificate, before measuring it

Starting with the supplied fixed JSON prefix, concatenate ONLY the contiguous
already-fixed response IDs from slot0 up to the first unfixed slot. If those
bytes parse as the complete one-number JSON object, the numeric grammar allows
only whitespace/epsilon/first-EOS afterward. Every valid future completion has
the SAME answer. This uses pre-action fixed IDs, no current auxiliary word or
gold restriction of the sampler. The label merely evaluates that known reward.

At such states, replace the local reward-gradient contribution by ZERO for
EVERY method/configuration. Its conditional mean at the pre-action state is
zero: R is constant and E[policy score|s]=0. Every control's statewise mean
is also zero. Turning off these control coefficients there is valid. Earlier
gradient terms still use the actual final R. All states and draws remain in
the record; this is not dropping unsuccessful paths or changing generation.
Check this certificate with independent small grammar completions first.
The identity assumes the declared completing monotone decoder, not a reward
that additionally penalizes random resource failure after the value is fixed.
All old16 paths completed; every new failure remains and disqualifies this
probe. Do not transfer the tail-zero claim to censored finite-budget successes.

## Fresh auxiliary design and fixed estimators

At EACH70 old states, collect64 iid conditional words/anchors (8 independent
batches of8) and64 prefix-history-stratified ones (8 independent batches of8).
Total8960 new AUXILIARY words, zero new decoder words/forwards. Separate seeds
are first8SHA256 bytes little-endian of
`52180:{case}:{replica}:{step}:{method}:{batch}`. All original IDs/B/F and
RNG globals must remain unchanged. Same V17 numerical boundary applies.

Store word/anchor/semantic verifier and all7 ACTOR9 score vectors; full per-ID
score tensors need not be duplicated because old heads and exact producers
remain. Use V13's pinned C_regular and prior masses, with no new query needed
for this diagnostic instrument. Same fixed V15 baselines0,1/2,p_s,p_root and
all27 coefficient triples in{0,1/2,1}^3. Apply the certificate uniformly.

For each fixed configuration/old path let H_r be its full trajectory gradient
under iid conditional replica r. Different steps use independent streams and
replica indices align only to form full auxiliary paths. Let mu_A and mu_B be
means of the first32/last32 replicas. For each question's two paths define

    Dhat = .5*(mu_A,0-mu_A,1) dot (mu_B,0-mu_B,1),
    What_1 = .5*(trace(sampleCov(H_0,64))+trace(sampleCov(H_1,64))).

Dhat is unbiased for .5||E[H_0|O_0]-E[H_1|O_1]||^2. It may be NEGATIVE;
retain that value, never clip to manufacture a win. What_1 estimates the
conditional hidden contribution to the expected paired trace estimator.
The expected paired trace at iid M is estimated by Dhat+What_1/M.
For prefix-stratified M8, estimate its hidden term from the8 independent
batch means, using the SAME Dhat. Do not treat the8 dependent individual
replicas inside a stratified batch as iid. Report all four actor blocks and
all questions, summing/64 for the equal8-question mean as in V15.

This Rao--Blackwellizes the old paired estimator over auxiliaries, NOT over
the original visible paths. It is NOT a new high-precision estimate of the
population variance or independent semantic quality. No significance claim.

## Frozen development-only necessity decision

FamilyA: exact visible score, all fixed baselines/controls, versus ALL six
partial-score single-auxiliary controls/configurations. FamilyB: M8 prefix-
stratified averaging of any of the7 methods/configurations, versus ALL seven
single-auxiliary controls/configurations (including exact visible readouts).
IidM8 is a mandatory ablation. Preserve all2268 table entries.

Select the minimum within each candidate family by estimated aggregate trace;
ties choose fewer queries/draws, then method/baseline/coefficient lexical order.
A family passes this ZERO-EXTRA-COST necessary screen only if its selected
estimate is finite/positive and<=.8 times EVERY applicable finite positive
control estimate. Nonpositive estimates/zero-denominator comparisons receive
NO win and are reported inconclusive. Selection on these SAME known paths is
optimistic development; do not report a selected estimate as independent.

If neither family passes, do not start a large new neural campaign on this
application. This is a frozen resource decision, not statistical refutation
of all methods or permission to relax the screen afterward. A pass still
requires independently fitted controls, fresh visible paths, real full cost
and RLOO before useful benefit can be claimed. No training branch yet.
