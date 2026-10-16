# V4 — Bounded real-consumer result, not a useful-effect result

Frozen producer854a733c53ff978349021d6d75a050fd231fed4e completed ALL8/8
KNOWN development cases under consumer-resource-v4.md/consumer-protocol-v4.json.
There were exactly9 attempted/completed pretrained forwards (one warmup),
32 sampled full proposals and32 observed actions, with zero error/refusal.
All original-ID proposals pass an independent JSON parser and true EOT/PAD
checks. Each action retains23--31 of32 positions. This does not establish
semantic correctness, useful diversity or an end-to-end iterative decoder.

All32 observed-action GPU log probabilities/projected planner gradients agree
with independent scaled NumPy forward/outside calculations. Maximum absolute
discrepancies: log probability3.553e-14, alpha6.551e-15, beta4.441e-14,
anchor6.939e-17. These finite comparisons are not probability-error bounds or
verification of the rounded RNG law. Full/known-anchor/collapsed scores use
the SAME32 joint draws; no variance advantage is inferred from four draws/head.

Sampler peak allocation is414412992--422932672 bytes (below2GiB), with persistent
sampler tables and original head input counted. CPU process peak RSS includes
model loading and is recorded separately. Times are diagnostic ONLY, not a
competitive gate. Every original BF16 head, INCLUDING warmup, prompt ID,
original word/action/anchor, byte/effect table, numerical check, seed, status,
source/runtime/model pin and run log is preserved in
docs/artifacts/raw/a52_consumer_resource_v4_initial; manifest.json hashes each
file and audit-summary.json is generated from the rows, not manually edited.

The6/8 feasibility condition passes. It permits CONSIDERING a new, separately
written/frozen complete-cost variance protocol. No labels, parameter updates,
additional seeds/heads or quality measurement occurred under V4. Generic
weighted evidence/mixture/conditional-mean principles remain known. Specific
originality, relevant measured benefit, actual useful training, independent
confirmation and the scientific user goal remain OPEN.
