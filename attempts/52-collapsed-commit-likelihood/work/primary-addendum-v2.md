# V2 primary antecedents and model metadata, 2026-10-16

No model was loaded or evaluated. These readings do not establish priority.

| Primary original / PDF SHA-256 | Actual scope and implication |
| --- | --- |
| [dUltra v1](https://arxiv.org/pdf/2512.21446v1), e9088f4e6b337a2b7909858a450387db76170924365d611ea5dd8eb58c0b721b | Sections3.1–3.2: hidden-state Bernoulli planner, position selection before tokens, explicit transition likelihood. Those principles are antecedents. |
| [Learning Unmasking Policies v3](https://arxiv.org/pdf/2512.09106v3), 7eb74ba192081be522a13f23b3c3fdb0a8f0b956e44297bdb78c235f631d2c5e | Sections3.1–3.2/4.4: confidence-based Bernoulli policies and frozen-backbone RL already exist. Maximum-confidence and hidden-state variants are controls, not evidence our token-aware proposal helps. |
| [MD4 v2](https://arxiv.org/pdf/2406.04329v2), 1b6df9e4b69542b11f107b038cc42c950473168acd41b82e887e1a9a330cf45c | Section6/Eq11–12: token-value-dependent masking schedules, reverse kernels and RLOO schedule gradients are known. Token dependence itself is NOT new. AppendixI's full proofs were not reread here. |
| [NeSyDM v2](https://arxiv.org/pdf/2505.13138v2), c3c05126e0b2b2c44607b180863bca2c0ce9dcf756d217073df7bba322b86013 | Sections3.2–3.4 and generative-work/conclusion excerpts: diffusion/local symbolic inference are antecedents. Our path mass does not compute its generally intractable full variational entropy. |

Five V2 oracles after651b8dd cover8 joint distributions,256 actions/4096 score
coordinates, the confidence chain rule, wrong bit-only retry and tiny2^-1000
exit mass. A Markov oracle has31 FAKE-head sufficient states,52 observed paths
and88 full auxiliary paths. It checks full-path conditional scores/covariance
with changed toy heads, not a neural model. Combined11 oracles PASS1.224s;
full216 PASS73.155s; make check/focused Ruff PASS. No new forward/update/timing.

## Potential available consumer, metadata only

The official [Tiny-A2D collection](https://huggingface.co/collections/dllm-hub/tiny-a2d)
and [dLLM framework](https://github.com/ZHZisZZ/dllm) provide smaller diffusion
checkpoints and RL recipes. The Qwen3 model card/config pin is:

    dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1
    c8d24a3f4adaeef46881b450e1bf7d1005203bd7

It declares Apache2, a2d-qwen3,28 layers/hidden1024, V151936, EOT151645,
pad151643 and Transformers4.57.0. Config SHA256:
02494589af3c9284b381929c576e5865c8f026b5bfed4b9a08d1b38bd4b8623e;
tokenizer_config SHA256:
ffe505983791f3fd517c246cc8fb173bbefc2ef657ce9cf2182ac9d97951f77b.
Only metadata was fetched into ignored .cache/a52-model-metadata. No weights,
custom code execution or inference. Runtime compatibility and actual license
files require verification before use. This is not a performance protocol.

## Next objection, before more implementation

V2's joint nonempty condition changes its word marginal and needs augmented
inference. A forced auxiliary anchor chosen independently of the complete
proposal may ensure progress while retaining that proposal marginal; integrate
the anchor after observing retained IDs. This is a separate written refinement,
not a correction to V2. Anchor-forcing is a standard sampling construction.
Establish its law, competing reductions and actual cost/consumer before code.
