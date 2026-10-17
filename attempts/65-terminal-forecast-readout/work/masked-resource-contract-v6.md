# V6 prospective SMALL masked-diffusion application screen

2026-10-17. Before selecting corpus rows, loading a model/tokenizer, new heads
or implementing this runner. This is a DISTINCT application of the terminal
readout theorem: a native Mosaic masked-denoising loop with Tiny-A2D, not the
published DiffusionGemma/JevBench execution or its last log-marginal kernel.
V4/V5 remain unchanged. No quality/training campaign is authorized by this
screen, including after a PASS; that would require own useful distinction,
competitive full costs, a separate protocol and independent evidence.

## Why this small screen, and honest limits (README1--8 reassessed)

The actual numerical consumer is still the externally authored JevBench
calibration request; its scores consume probabilities, not original IDs.
Local16GB host/12GB GPU cannot reproduce the unquantized26B/48GB setup.
Do not present that resource arithmetic as an observed OOM. Official Google
HF instructions and the Unsloth DiffusionGemma/GGUF cards were inspected:
GGUF needs a DIFFERENT llama.cpp runner; it does not directly execute the
pinned Mosaic vLLM function. No quantized weights were downloaded, no engine
was installed and no published model/result was reproduced here.

Instead test feasibility/necessary terminal variance in a clearly named small
masked-diffusion application, using an EXISTING compatible model/runtime and
Mosaic's original masked loop. Source36945e4b `mosaic/dlm/llada.py` and
`constraint.py` were read in full; their model callback is generic, mask-based,
and commits an even number of positions per step. This fits the Tiny-A2D
checkpoint's masked diffusion contract better than feeding it a DiffusionGemma
random-token denoising schedule. It remains a new application, with unknown
forecast quality. The last few masks may already carry zero semantic variance;
that unfavorable result would close THIS application rather than justify
changing steps or selecting an earlier head after seeing it.

Own candidate is the SAME original-terminal-preserving numerical readout,
not a new sampler, conditional averaging theorem, expectation semiring or
small-model forecasting invention. The comparative all-gold identity holds
only for the actual final kernel. Exact-grid DP, native normalized output,
native complete-word MAP and full-trace ensembles remain mandatory controls.
Sufficient own novelty/article significance and useful magnitude stay OPEN.

## Inputs: rules before any row selection

JevBench pin `1bcc55eb6c8cffde2306b3db03ede39b61c6152a`, the SAME revision
named by Mosaic's public consumer. Use ALL candidates from public
`datasets/public/{easy,original,hard}.jsonl`. Eligible inputs have2..6 distinct
ASCII label strings and canonical UTF-8 JSON of id/state/question/labels no
longer than6000 bytes. Exclude the ONE already exposed documentation example
`hard-sol-b-judge_hard-18`. No family/gold/output-based filtering.

Rank eligible inputs by SHA256 of canonical JSON (sorted keys, no spaces,
ensure_ascii=False) of exactly id/state/question/labels, then ID and tier.
Take the first8 globally, no replacement of a later resource failure.
Retain input-only manifest, all-candidate counts/ranks, source byte hashes,
selected IDs and source license/provenance. A selector may decode raw JSONL
lines containing `expected` to discard that field; disclose this automatic
gold-byte parsing. Never print, persist in the input manifest, inspect or use
gold VALUES for selection, generation, thresholds or evaluation. Do not claim
no gold bytes were loaded if the selector decoded them. No pristine independent
corpus claim: earlier public aggregates/example and source scopes are disclosed.

Render the original pinned `OpenAICompatAdapter.build_request` message logic
using only state/question/labels (no Task.validate on expected). Keep the same
system/user text; use the Tiny-A2D chat template with enable_thinking=False,
not DiffusionGemma thinking markers. Prompt cap1024 tokens; exceeding it is
a preserved RESOURCE_REFUSAL, not another selected input or truncation.

## Model and baseline loop, no implicit posterior substitution

`dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1` pin
`c8d24a3f4adaeef46881b450e1bf7d1005203bd7`, existing local weights SHA256
`3485d18016ce6c302e8973809b47aa6369d6612ef9978d0690b4575d1193e932`, custom
source SHA256 `624175f036b6552db473e911e5ec57a09d518c7241b11bc375a7b4bf558675ce`.
Use existing `.venv-a52`: Torch2.8.0+cu128, Transformers4.57.1, NumPy2.4.6,
automata-lib9.2.0. Do not replace a maintained environment or install updates.
BF16 eval, SDPA, no cache/gradient/updates/CFG, batch1. Source/model/tokenizer
hashes must be copied independently under A65, not imported from mutable A52.

Copy the original Mosaic masked loop/constraint/modules and license with new
manifest before executing it. Use loop `generate` unchanged: steps16,
gen_length64, block_length64, temperature0, remasking=low_confidence,
commit_by=constrained, cfg_scale0. Tensor full output dimension151936 is
retained. Native compiler uses tokenizer length151670 and rejects the extra
266 IDs by ITS original policy; do not silently call this full original-head
conditioned inference over those266 empty-decoding IDs. EOT151645/PAD151643,
MASK151669. Original token IDs/aliases/pins are kept. The native kernel here
uses final MODEL logits, not the DiffusionGemma log-marginal reprojection;
conflating these would invalidate the experiment.

One64-token response block, one warmup and all8 fixed originals. Root seed65060,
case seed65060+index; at most129 attempted forwards TOTAL (1+8*16). Count
attempts including failures/warmup; never retry a refused case or extend its
response. The hook captures the actual LAST proposal before all remaining masks
are committed. Clone its original logits, free/pinned canvas, fresh matcher
node/budget and original IDs BEFORE updates. It must preserve the original
trajectory and main RNG; no earlier favorable head selection. A last proposal
that does not complete the whole forecast stays ineligible/unchanged.

## Preflight and per-case work

Before loading weights: freeze selector/adapter/runner/protocol source; capture
input-only manifest before any forward. Run native fake-head CPU/CUDA replay
of this DIFFERENT masked loop in Torch2.8, including original IDs/full trace,
all remaining masks versus last selected IDs, padded head IDs and EOT/PAD.
Verify the captured terminal `_propose` call (converted mask to native FREE)
literally reproduces original matcher.propose_x0 at the saved RNG and restores
the caller; original return_marginal pass must also leave the same final state.
No actual model calls in this prerequisite. Preserve all draft failures.

For each eligible REAL terminal capture:

* Retain raw/normalized original and original complete trace/head bits/pins,
  input-only prompt, all attempted forwards/control provenance.
* Readout budgets0/1/7, separate stream ONCE per readout seeded
  650600+100*index+budget. Charge every helper/incomplete/parser/render/copy.
  No diagnostic extra128-draw variance campaign is smuggled into this cap.
* Exact-grid classical DP mean/alpha/V on the SAME final native ideal path law,
  plus native-path Viterbi complete-word control, all original syntax/value
  semantics. DP may reuse efficient shared edge reductions; no Python
  full-vector enumeration or unoptimized field-product straw control.
* Record raw alpha/rounding residuals. For the theoretical binomial formula
  ONLY, clamp alpha to[0,1] if residual<=1e-9 and report adjustment; larger
  residual, NaN, negative variance below-1e-9 or invalid mean is ERROR.
  These are ordinary floating ideal-kernel diagnostics, not exact finite-RNG
  certificates or actual gold-quality differences.
* Diagnostic wall/CPU and GPU memory include native compile/preparation,
  full original forward/loop, capture, all readouts, DP/MAP, transfer, parse,
  normalization and serialization. Report cold/shared preparation separately.
  No claim of competitive latency from a single ordered resource pilot.

Guards:30 minutes total including model load,120s per compile/query,2GiB
sampler workspace over the loaded model baseline,10GiB GPU total allocated,
500000 semantic DP states/5000000 transitions,1024 prompt/64 response tokens.
Every resource failure remains one of8. No concurrent workload/testing.

## Frozen necessary decision, not a primary scientific success

Require at least6/8 valid original complete traces and four of the ORIGINAL
eight with ideal N=7 removable squared-risk amount
`V*(1-E[1/(1+Bin(7,alpha))]) >= 0.005`.
This threshold is a modest half percentage point of unnormalized multiclass
Brier risk, chosen prospectively as a NECESSARY magnitude screen. It neither
establishes measured gold benefit nor makes those cases independent confirmation.
Zero/low variance, ineligible, failure and DP-winning cases are all retained.

Failure closes this Tiny-A2D/16-step64-slot application; do not change schedule,
head, model or threshold after measurement and call the new result a pass.
A PASS permits considering a SEPARATELY frozen full-cost/quality protocol only
if own significance survives antecedents and the optimized DP/native MAP/
normalization/whole-trace ensemble controls. Their quality is not evaluated
without labels here; ensembles cost all their real extra forwards. No training,
extra seeds, label inspection or independent campaign is triggered automatically.
