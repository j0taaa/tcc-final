# Actual consumer, native boundary and predecessor scopes

2026-10-17, BEFORE a prototype or new model/corpus-row evaluation.

## Concrete software consumer

Read-only clone of [Mosaic](https://github.com/MhDang/mosaic), HEAD
`36945e4b3c64913e23962e0924a8b40a84c58807`, same pin as the earlier A24
source audit. No upstream file modified/imported/executed. Selected MIT source
copies and hashes are preserved in `consumer/` and its manifest.

Actually read `benchmarks/jevbench/{run_vllm,data,summary}.py`: the output is
a probability vector, scored with top-choice accuracy and a Calibration metric
combining ECE and distance to gold probabilities. The runner's original26B
DiffusionGemma revision is f7f5b7f5fa82ffc52addd066915886d497f5517b, with
128-token canvases. Aggregate README results were read, but no task, output
record, gold row, model weight or tokenizer instance was read/executed here.
The published setup uses a48GB GPU with CPU offload; local hardware metadata
shows RTX3080Ti12GB. This is not a measured OOM or a native model reproduction.

`mosaic/grammar/json_schema.py:type_probability` accepts0,0.d,0.dd and
1,1.0,1.00. The frontend bounds individual numbers, not their sum. A numeric
grid control therefore has at most101 values per field, not exponential
unrestricted precision. Simple post-normalization is mandatory. Do not claim
novel capability by compiling an exotic precision the real consumer lacks.

Read `integrations/vllm/mosaic_vllm.py:_constrained_step`: ordinary denoising
uses a joint draw from scaled logits plus constrained marginals. On convergence
the FINAL valid commit calls `_propose` on **log_probs (constrained marginals)**,
with temperature0, current pins/offsets and matcher state. It does NOT simply
return an original mean-field sample. `mosaic/sampling/parallel.py:sample` and
`_pick_tokens` confirm the state path is ALWAYS sampled; zero temperature
changes the within-edge token choice to argmax. The random terminal law and
its semantic moments must include that second reprojection and deterministic
within-edge choice. A same-input native resampler would automatically retain
the actual finite floating/RNG kernel, whereas an ideal weighted DP needs an
explicit rounding-law distinction. No bitwise law theorem is assumed.

The candidate boundary is the last converged commit that actually completes
a parseable whole forecast. Earlier committed canvases and model calls are
left literal; auxiliary NONTERMINAL proposals are charged but not continued
through new model calls. Capture must precede matcher advancement and tensor
reuse; include node, accepted-token count, remaining budget, pins, offsets,
prefix bytes and the final log_probs. The old full native output remains
provenance; the consumer receives a NEW numerical vector. This is not a sampler
preserving original word marginals or immutable-infilling text.

## Primary predecessors actually read

Lukasik et al., [RAIL2024 original](https://aclanthology.org/2024.findings-emnlp.799.pdf),
introduction, Sections2/3.1/3.2, Algorithm1 and Table1 READ. It explicitly
uses numerical mean/median MBR rules and full sampled model responses. Those
principles and risk-optimal means are antecedents, not the A65 invention.
The twelve-page file was retrieved/hashed; not its whole appendix read.

Soru/Marshall, [2501.04880v1](https://arxiv.org/html/2501.04880v1), SectionIII-B
READ: token-logprob-weighted probability guesses and their mean already
exist. Its single-token guess formula does not justify equating a multi-field
native reprojection with independent numerical fields. No exclusive general
semantic-mean claim is available. No empirical result from it is own evidence.

Beylkin/Monzon2010 [original](https://www.colorado.edu/amath/sites/default/files/attached-files/bey-mon-2010.pdf),
abstract/introduction equations1--2 only READ. Reciprocal Laplace transforms,
positive exponential sums and separated approximations are established. No
quadrature algorithm or general-precision advantage is proposed for this
two-decimal consumer; ordinary sum-state DP is a legitimate exact control.

The scoped difference to investigate is terminal sampler reuse and truthful
whole-trace integration in this actual dLLM serving consumer. No source search
or correct proof establishes sufficient own novelty or practical magnitude.
