# V4 — Prospective optimistic resource gate for NNCPv2 components

Written BEFORE source/import/forwards/timings. ONE CPU/FP32 resource screen,
not a decoder-quality/codec benchmark or implementation of A70. V1--V3 intact.

Use the original unmodified NNCPv2 MemTransformerLM and arithmetic coder
source from the pinned archive. Record their hashes/license, installed
Torch2.8.0+cpu Git revision, NumPy/Python, CPU/RAM, threads and actual producer
commit. Source freeze BEFORE any original module/model execution. No model
checkpoint, external corpus, labels, CUDA/Apex or LibNC execution/download.

## Fixed configuration and input frames

Take the original base script's geometry: vocabulary16388,12 layers,
d_model512,8 heads/d_head64,d_inner2048,attn_type1,tied_r_bias,GELU,
tgt_len1, ext_tgt_len31,mem_len160,batch64,init_std.013,eps1e-9,
beta=(0,.9999),zero decay,LR7.9e-5,clip.25. Use the VALID FP32 CPU mode,
not the script's published FP16/Apex mode. Original normal-mode eval() has
dropout disabled. Use8 physical CPU threads and interop1 for every method;
record that this is one fixed setting, not an optimal-hardware assertion.

Seed1111. Two constructed frames: empty memory, and full-shaped160-step
memory tensors generated at scale.013 with a separate fixed seed1112.
Legal input IDs are fixed seeded32x64 integers, next-symbol targets64 IDs.
These are shape/resource fixtures, not real text or trained decoder states.
Common setup performs ONE actual model forward/backward/native Adam update,
then snapshots all weights/moments/clocks. Every trial restores the SAME
snapshot and model/RNG state outside its timer. Input/memory tensors common.
Do not grow vocabulary/model or pick later favorable text after this screen.

## Four competent native/optimistic controls

native_single and native_foreach: installed torch.optim.Adam with foreach
False/True, fused/capturable/differentiable/maximize/decay allFalse/zero.
ideal_single and ideal_foreach use the corresponding native mode but remove
ONLY word_emb.weight from its optimizer parameter list. All its gradient/
model/softmax/clipping costs remain. Removing its work is an UNATTAINABLE
zero-overhead optimistic comparator, NOT an A70 trajectory or bit-preserving
optimizer. Every other parameter is still updated natively. Do not substitute
a slow own scalar loop for the native controls. Native foreach law agreement
is reported on the actual common frames, never assumed universally.

Timed full component cycle: clear ALL model gradients with set_to_none=False;
build input/target tensors; original model forward; actual source softmax*
1e7/round/int/max1/cumsum CDF; original coder writes all64 symbols; source
log_softmax/NLL mean; backward; full clip_grad_norm_; optimizer.step().
Return outputs/memories without another model call. Do not time only the
optimizer or remove source normalization/other native work. Coder final flush,
hash validation, one-time initialization/snapshot restoration and fixtures
are outside this amortized cycle, recorded separately. This is not a cold
first-compressed-file latency claim. Exact current-loss/CDF/gradient and
native state digests are checked outside the timing interval.

One warmup per method/frame, followed by SEVEN paired measured repetitions.
Order rotates through all four methods.56 measured records+8 warmups+ONE
common setup=65 real model forwards/backwards/optimizer calls, no accumulated
training claim. Record all statuses, wall perf_counter and process CPU
(all worker threads), peak RSS and memory availability. Preserve partial
errors/refusals; never call a missing record a success. No concurrent tests/
archive or model jobs on this workspace during the timed campaign.

## Gate frozen before observations

For a frame, resource feasibility passes only if at least one ideal method
has paired median wall AND CPU <=.8 of BOTH native methods, with favorable
wall/CPU sign in EVERY paired repetition. Use the actual full measured
cycle. Candidate compilation/coordination would only add work; positive
feasibility is NOT a measured candidate advantage. The artificial ideal
control does not prove a universal physical lower bound (cache/scheduling
are not monotone mathematical costs).

If neither of the two frames passes, close this screened CPU/FP32 component
application; do NOT port the full codec/train new models, add seeds, enlarge
vocabulary, change threads/caches/dtype or relax the gate to rescue it.
This is a small resource screen, not a statistical refutation of all NNCP/
graphics/sparse-embedding applications or the native-state theorem.
If feasibility passes, first audit actual native compatibility and input-only
inactive-gap demand, then freeze an independent FULL-COST candidate study
including variance-only lazy replay, beta1=0 exact shortcuts and the classical
finite-state/jump/interval controls. No positive user-goal claim follows here.
