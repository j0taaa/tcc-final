# A38 native functional/cost pilot — frozen BEFORE implementation/forwards

2026-10-11. Theorems give a plausible comparative contribution; priority
still open. This is a SMALL real integration pilot, not an independent
statistical victory or another attempt to reopen A32/A34's negative gates.

## Application and fixed external inputs

Translate natural-language word problems into executable recursive JSON
trees, consumed by a rational arithmetic interpreter. Fixed grammar permits
add/sub/mul/div with recursively nested arguments and arbitrary JSON numeric
literals; it does not enumerate answers. The model's original EPIC sampler
is the unchanged upstream at5b1b31098f34ed3691d2a9f4aae14fdf5839d072.

Use the FIRST FOUR input-only SHA256-ranked records of ALL1000 SVAMP
questions. Rank Body+'\n'+Question as UTF-8; no answers/equations/types in
eligibility, ordering, prompt, grammar, key or sampler. Pin repository
arkilpatel/SVAMP at78e727689e1c1bebfc4be39c446898e8e10b0518, fileSVAMP.json
SHA2565be77703a6d891ae476d7c082787ad361392aa02453b132516cdd5f4e7934e3e.
All four remain even if impossible/incorrect/slow. The official set tests
structural variations of word problems; this four-record pilot is not the
full benchmark. Golds are exported separately and ONLY read after the
entire generation capture, for descriptive audit rather than key selection.

## Frozen operation/model settings

Two replicate seeds per record; seven methods/configurations,56 pair records.
Full original calls, never prefix/timing replays. Each original call advances
the unchanged generator to exhaustion, retains original token IDs, text,
complete flag, retries and failures. A fixed canonical key is sorted-key,
compact JSON of the complete output, with numeric literals normalized by
the same fixed parser; incomplete/invalid/error outcomes get declared keys
and are NEVER resampled away. No gold-dependent classification.

LLaDA8BInstruct revision08b83a6feb34df1a6011b80c3c00c7563e963b07,
local cached NF4 double quantization/bfloat16. Threads4, temperature1,
gen_length128,block_length128,steps16,max_resamples256,max_prompt1024.
The existing fast native regular-cover/DFA flags are identical for everyone.
Grammar normalization twice is the same classical preparation for all;
include its actual time. Only the common initial model head may be cached,
CLONED on reuse for all methods. Prepare it before method timings and
record its common cost. No future-state cache, token/support change or
change to vendor code. Synchronize CUDA at all timed boundaries.

## Competent controls, costs and preserved distinctions

- pool4: classical same-law four-draw empirical coupling, implemented by
  the small equivalent multiplicity rule, not an intentionally slow sort.
- early_pool: its known safe omission of draw4 when keys2=3 (mean4-c).
- adaptive4: the written pointwise-minimum rule (mean4-2c+s3).
- mean3: the frozen independent half mixture (mean3-c+s3/2).
- iid2: two original EPIC executions, preserving the original independent law.
- novelty3: retain first; choose a uniformly random different-key candidate
  among draws2/3 if available. Competent cheap diversity/search control;
  its second marginal is generally BIASED, explicitly reported, not excluded.
- seed_half: original first uniform32-bit seed and second shifted by2^31
  modulo2^32, a cheap systematic/antithetic seed control with original
  individual seed marginals. No invented monotonicity guarantee.

Use identical predefined draw-seed tapes for equivalent methods and iid2;
auxiliary selection coins are a SEPARATE stream. Rotate method order per
replicate. Actually rerun requested native calls; no credit for skipping
a call that was executed earlier and fetched from a replay bank. Include
all helpers/coordination/key parsing/failures and both selected payloads.
Record wall/CPU, new forwards, head queries, calls, original IDs, literal
first preservation and every status. Exclude only common model loading,
explicitly record it; include amortized common grammar/head preparations.

## Purpose, gates and exclusions

This pilot must find adapter failures, confirm real requested-call stopping
and demonstrate executable original JSON on an external source. Require
no unexpected error, literal first unchanged across same-tape methods and
no helper/gold filtering. At least two different successful canonical keys
must be observed somewhere to show this is not only a constant oracle.
All failures invalidate unsupported claims, never silently drop a record.

Report ALL56 records and any incomplete capture. Compare FULL cost, including
negative cases and the cheap controls. Medians/p95 and descriptive semantic
pass@2 may be shown, but TWO replications cannot establish a competitive
statistical latency or semantic win. No20% gate is invented after observing
results. The expected same-law work theorem is separate from physical timings.
If there is no plausible full-cost benefit versus the strongest methods for
the intended consumer, do not promote the pilot as general EPIC superiority.

The distinction between unbiased two-output sampling and best-candidate
search must remain meaningful to the application; it is not a device for
excluding novelty3. More iid candidates, informed logits and classical
rank/stratification methods remain external alternatives for a larger
evaluation. This pilot does not qualify as independent confirmation.
