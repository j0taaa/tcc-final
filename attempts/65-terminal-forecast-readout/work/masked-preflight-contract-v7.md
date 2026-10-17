# V7 literal masked-loop preflight before its first execution

2026-10-17. Implements only the prerequisite of V6, not a changed application
or gate. The previous turn made concrete progress: native Gemma-step and
classical moment control passed; masked-loop source/input manifest was frozen.
No masked loop or real model has been executed yet.

Load only the16 hashed files in masked_source_v6, native matcher plus original
`mosaic.dlm.llada.generate`. Extract unchanged `_offset_groups`/`_propose`
from that root for replay. Do not import the earlier Gemma root concurrently.
Use the actual Python3.11/Torch2.8/automata9.2 environment `.venv-a52`.

Sixteen cases: device CPU/CUDA x seed17/29 x dtype float32/BF16 x
(L8/steps2 or L64/steps16). Tiny synthetic tokenizer is the previous25-ID
fixture, plus three unavailable model-only IDs, using the last unavailable
ID27 as mask. Prompt IDs2/3. Deterministic fake head depends on position,
token, call ordinal and current input IDs, with high weight on unavailable
IDs. It has no trained parameters and no pretrained model/tokenizer load.
Run original and instrumented native loop on the SAME seed, distinct fake
head instances. Preserve EVERY model-input and logit-bit digest, returned
canvas and after-RNG. All sixteen cases, including BF16, must pass.

Hook actual matcher.propose_x0: at its FINAL call clone the raw BF16/float32
bits for provenance and a float32 copy for the sampler (native code already
casts to float32), and convert mask positions to FREE=-1. Real EOT/PAD IDs
are explicit aliases through a tokenizer view, never assumed synthetic names
on the actual tokenizer. Assert exactly4 masks remain before final commit,
all are replaced, and the final response equals the captured whole proposal.
The snapshot reuses the actual final MODEL logits; not Gemma log-marginals.

Literal replay of `_propose` without return_marginal must reproduce the final
original call WITH return_marginal and its after-RNG (the marginal pass is
deterministic). Advance live matcher/overwrite the caller's last-score buffer
only AFTER returning; frozen clone remains intact. Budgets0/1/7, fresh stream
once per readout, no reset per helper, caller/main RNG and compiled buffers
unchanged. Preserve all raw outputs/IDs and normalized/rendered points.
All fake calls/helpers are counted separately from real neural forwards.

New V6 DP/MAP preparation will share sparse original-ID edge reductions on the
fixed float32 log-softmax, with max-shifted layer weights to avoid underflow.
It must match previous independent small path enumeration in alpha/mean/V,
including the low-completion partial fixture; tolerance5e-5. Viterbi maximizes
the same native STATE-PATH mass, not the original independent logits or an
unproven MAP of merged output strings. Token aliases may merge paths; label
that distinction. This semantic control is classical, no novelty claim.

Before any real model, verify input-only build_request AST extraction produces
the exact pinned system/user messages, copy/check model metadata/custom source
and tokenizer hash manifest under A65 (weights stay cached outside snapshots).
Custom source hash remains the V6 pin; review it before loading. No install or
dependency update. Freeze own source/protocol before any scientific run; any
draft/error and its exact producer stay preserved before correction. This
preflight has600s total/2GiB GPU guards, not a competitive timing gate. Only a
complete PASS can allow considering the bounded8-input resource screen.
