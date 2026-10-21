# A88 V1 — Development resource and necessity qualifier

2026-10-21. Freeze source and prepared inputs before the first model call.
This qualifier can select a budget for a future INDEPENDENT test; these
same items cannot select a method and validate a central thesis claim.
No neural A88 output has been seen when writing this protocol.

## Inputs and policy

- Dataset: cais/mmlu, revision c30699e8356da336a370243923dbaf21066bb9fe,
  all/dev-00000-of-00001.parquet. Eight smallest SHA256 of
  `A88-dev-v1:<zero-based-row>` from the entire dev file. Preserve question,
  choices, subject, answer and source hash. No case replacement.
- Prompt: request a brief explanation in the reasoning region and one
  A/B/C/D option in the reserved answer region. Use the checkpoint's chat
  template. After it, 31 MASK slots, the fixed tokenization of
  `\nAnswer:`, one observed MASK slot and a fixed EOT token. All 32 generated
  slots are eligible together; the fixed delimiter and EOT are pinned.
  This small scaffold is a new resource qualifier, not a reproduction of
  the published 280+1-slot experiment or evidence of open-ended accuracy.
- Eight independent replicas per item, seeds `880001+1000*case+replica`.
  Seed only proposal RNG; no learned parameters. All original output IDs
  remain, with the disclosed shared MASK-logit suppression. EOS/PAD are
  ordinary canvas tokens and do not silently trim the observed slot.
- Proposal and confidence: temperature 1, q=p=full softmax in float64 of
  captured BF16 model logits after MASK suppression. The nominal categorical
  model is the target. Floating CDF/RNG arithmetic is an implementation
  approximation, not an exact finite-bit law. Record normalization/CDF
  errors and never call this bit-exact. Independent rational oracle is
  the exact mathematical evidence.
- Sixteen steps, two clean positions committed per step. Lower original
  physical position breaks confidence ties; implement that rule explicitly.
  The observed slot remains MASK only in the auxiliary estimator. Its
  deposited mass accounts for all original first-commit events.
- Group all model IDs by single-ID decoded emission, allowing leading or
  trailing whitespace around exactly A/B/C/D; every other ID is OUTSIDE.
  Freeze the complete group assignment and tokenizer hashes before heads.
  MASK is excluded explicitly, not assigned missing mass. No option-only
  renormalization. Report all five group probabilities, including failures.

## Methods fixed before data

Early-stopped sampled counts and selection-aware conditional readout d=0
are controls for the SAME native law. Evaluate the entire integration family
d=1,2,4,8,full, and first W<=.01/.0001 followed by exact early readout.
All are fixed before seeing any outputs. Full and the equivalent forced-last
endpoint are one variant, not two independent discoveries. The best family
member on this development qualifier may be selected prospectively for a
separate test; no adjustment of this qualifier follows an unfavorable result.

Cache identical initial heads once per item for all replicas/methods.
Additionally identify every queried canvas by an exact hash. An optimistic
global-cache comparator is required when repeated later canvases occur.
Never count a duplicate root forward as a baseline expense. Reusing heads
does not couple the independent proposal uniforms between replicas.

For auxiliary path i store the five-bin a_t, W, state hashes, shared step
costs, integration-specific work and first-commit law. These allow exact
conditional moments over the hypothetical native first-commit time, without
sampling away rare events. Let p_t=W_(t-1)A_t and R_t=a_t/A_t. Then

    E[||R_0||^2 | path] = sum_t p_t ||R_t||^2,
    E[C_sigma | path]   = sum_t p_t C_t.

Each partial variant is a conditional mixture with mean Y; compute its
nonnegative conditional variance directly, preserving all events/tails.
For the one-hot control the conditional variance trace is 1-||Y||^2.
Across independent paths, estimate each method's total variance as sample
variance trace of Y plus the mean of its conditional variance trace. Do
not infer a truly zero variance from eight identical observed vectors.

## Costs, limits and decision

Use the already-local LLaDA-8B-Instruct snapshot
08b83a6feb34df1a6011b80c3c00c7563e963b07, all weight/config/tokenizer hashes,
NF4 double quantization with BF16 compute, batch 1, no KV cache, four CPU
threads and the verified output-head crop to requested response positions.
Do not edit the model or vendor EPIC. Peak GPU allocated/reserved and host
RSS are recorded. Refuse when foreign CUDA processes are active, available
GPU memory is below 7 GiB before load, context exceeds 2048 without
truncation, or the cooperative 30-minute/968-new-forward ceiling is reached.
Every refusal/error/interruption remains in the output. No automatic rerun.

There are at most 1,024 logical full-endpoint steps, but only 968 new
forwards after sharing eight roots. Repeated nonroot states can reduce
physical calls further. Charge root/source preparation and model load
separately, then report amortization for the fixed 8-replica budget.
Charge RNG, categorical preparation, ranking, full-V-to-five-bin reductions,
vector updates, cache accesses/copies and output. A control must not pay for
candidate-only reductions at steps at which it would not have committed.
Offline analytic moments and serialization are research overhead, reported
separately. Profiles/replay cost predictions are not measured end-to-end
decoder latency. A necessary query/cost screen alone cannot establish a
central result or imply better semantic accuracy.

Report every item and every preregistered variant. Development signals are
same-law validity, useful option mass, variance reduction and complete-cost
precision against BOTH early controls. Require at least six of eight items
to retain >=.9 estimated option mass for a classification-interface claim.
Require material advantage (point estimate at least 10% and paired uncertainty
reported) on at least six of eight items to justify an independent competitive
test. Multiplicity/selection is disclosed; this is a necessity screen, not
a significance claim or confirmation of generality. A zero/unstable moment
is inconclusive, not an infinite speedup. A negative qualifier is preserved;
do not change rows, lengths, seeds, temperature, groups or controls to rescue it.
