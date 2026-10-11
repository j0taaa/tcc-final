# Coverage refusal, not a decoder mismatch

2026-10-11 BEFORE changing the fixture. All144 CPU/CUDA FAKE full first
decision trajectories passed, but the observer reported ZERO successful
regular-cover batches. The explicit coverage gate refuses this as enough
validation; all144 rows/calls/source hashes are preserved in
`evidence/native-cover-fixture-refusal-v6.json` (failure reproduced for capture).
No model weights/head or competitive timing was used.

The fake grammar accepts ONLY ONE digit. Its two-slot canvas cannot commit
two digit proposals jointly. Upstream correctly declines a batch smaller
than its minimum2; enabling the feature alone is not branch coverage.
The required correction is a SECOND proof fixture admitting two digits for
the valid-proposal profile, while keeping the original one-digit alias/refusal
profile. This changes a correctness-test input, not native code, application
data or any experimental competitor. Observe the original helper's actual
returned batch size, never manufacture a successful return.
