# V5 — Implementation prerequisites before its first new head

Written foundation4b2fb1f preceded V5 code. Two compact/reverse oracles,
two original-ID continuation/numeric-verifier oracles and one exact RLOO
group-law oracle pass in the maintained229-test suite74.834s. make check and
focused Ruff pass. The exact two-draw RLOO example has mean3/16 and variance
15/256; treating individual contributions as independent would be wrong.
Head indexing matches full logits literally in two BF16 RANDOM-model calls,
ZERO pretrained calls in V5 so far. V4's prior9 calls remain separately counted.

The capture implementation never reads labels. It verifies all initial packet
hashes, preserves original-ID masks/canvases, caches only identical complete
states, records every new head's original BF16 bits at active positions, and
checks the compact score against ordinary independent full-V evidence inference
on every draw. Full/cheap-anchor/known-anchor/collapsed scores are on the SAME
draw. No model-weight derivative or update is implemented/claimed by V5.

The separate analyzer verifies the closed640-record capture before reading
the external pinned labels and fitting16-pilot baselines. It computes variance
of independent8-draw GROUP means, including RLOO dependencies. Primary is fixed
to collapsed:pilot against ALL nine configurations of the three other score
estimators. Ordinary evidence supplies the SAME collapsed estimator and is an
independent implementation check, not a fictitious variance competitor.

This is a conservative development decision. A fail of an added condition,
especially reward variation, is not a general mathematical impossibility of
other policies/tasks/learning. No timing/quality superiority, novelty, useful
training or achieved goal follows from prerequisite checks or a variance pass.
Source/runtime/config/seed details are frozen in consumer-protocol-v5.json
BEFORE the actual capture. All earlier evidence remains unchanged.
