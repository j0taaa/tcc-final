# V5 — Complete negative development decision, preserved unchanged

The written design4b2fb1f preceded source freeze
e01739d9c9bf99bb1dd209b5dab52c7e7951d9b0 and ALL new V5 model calls/labels.
The capture completed ALL640/640 trajectories (128 pilot,512 evaluation),
629 attempted/completed new pretrained forwards including one warmup,
628 actual next-canvas heads,12 complete first actions and zero cache hits.
Every trajectory preserves fixed original IDs and produces independently
valid numeric JSON. There were zero error/refusal and no parameter updates.

All640 compact likelihood/score readouts match the ordinary full-V evidence
reference: maximum log discrepancy0, alpha2.110e-15, beta9.104e-15 and anchor0.
GPU sampler peak18,591,232 bytes; CPU process RSS is separately recorded.
No competitive latency is inferred from diagnostic times.

AFTER capture closed, pinned external labels were accessed. ALL640 rewards
are zero, including128 pilot and512 evaluation. A separate json.loads/Decimal
evaluation agrees exactly with the lexeme verifier. This is no useful learning
signal: all reward-weighted gradient covariance estimates are zero, so no
ratio/improvement is credited. The declared minimum6/8 reward-variation cases
fails0/8; all favorable comparisons are0/8. The application is NEGATIVE.

Therefore complete-cost measurement, training, extra seeds/independent inputs
are NOT triggered. Do not change the threshold or replace the score/reward
after seeing labels. This rejects THIS pinned model/two-stage/PAD-tail
application under the frozen decision; it is not a general refutation of
conditional variance, other models/tasks or the observed-action likelihood.

All629 original BF16 heads,640 proposals/actions/continuations/scores/checks,
source/protocol/runtime, statuses and seeds remain in
docs/artifacts/raw/a52_two_stage_v5_initial. ALL labels, baselines, independent
audit, bootstrap diagnostics and group gradients remain in the separate
docs/artifacts/raw/a52_two_stage_v5_analysis_initial. Both inventories hash
every file. Source/preflight evidence is in work/evidence/two-stage-preflight-v5.

Post-result inspection finds long nonsensical numbers. A possible cause is
conditioning the full fixed-length head on EOT followed by actual PAD logits:
that law penalizes a short prefix by all its suffix PAD probabilities. This is
only a diagnostic hypothesis, not permission to relabel/rerun the closed gate.
Any stopped-prefix contract must be written/audited separately before code;
absorbing termination and marginalizing unused suffixes are classical. A
changed law cannot inherit V5 evidence or establish scientific novelty.

Useful measured effect, own sufficient originality and the user goal remain
OPEN. A correct implementation and this negative campaign do not fulfill them.
