# Two further primary comparisons

2026-10-11. Actual reading scope, not exhaustive priority certification.

[Jing Jia et al., Antithetic Noise in Diffusion Models, v2 (2026-01-30)](https://arxiv.org/html/2506.06185v2),
HTML SHA25623eeb60f9e757999ad31659781aa6f54100ca52dfbab76b1bc366580a7ca6c27.
Read intro/setup/Section3 and Section4, plus AppendixA.6 Proposition7/8 and
their monotonicity proofs. They already preserve each generative marginal
with antithetic noise and use reduced downstream-score variance. The latter
requires appropriate score correlation; their FKG conditions require partial
monotonicity. This is NOT an every-verifier guarantee for arbitrary nonlinear
CFG recovery. Coordinate correlation of images is different from arbitrary
semantic verification. Negating initial Gaussian noise is a legitimate cheap
control, not an intrinsically weaker decoder to omit. Their work precludes
claiming that generative antithetics or unbiased score means are new here.
No complete reading of their other appendix proofs or all experiments.

[SRT, original v1 (2026)](https://arxiv.org/html/2601.09083v1), HTML SHA256
4c7f0ef92cbed73e86381406dc5ebc7520751e3c4f83073cd2b1ec416907a181.
Read intro/motivation and Section3. They already cache model-free per-prompt
rollout substrings, update caches online and verify speculative drafts under
the current autoregressive policy. A40 instead records exact neural heads
with unchanged weights and uses a frozen independent-anchor cache for its
conditional law. This difference does NOT make deterministic memoization or
conditioning novel. SRT's online updates underline why dynamic-cache controls
are mandatory. No direct numerical comparison from different hardware/task;
no complete experimental/proof audit.

Makur2025 full PDF still returns404; its indexed excerpts are not a full
original reading. OpenReview MDM-stability PDF is browser-challenged/403;
arXiv supplies the current v2 (2026-05-21), to inspect independently.
