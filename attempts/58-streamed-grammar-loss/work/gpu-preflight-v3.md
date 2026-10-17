# V3 — Bounded GPU arithmetic preflight, BEFORE kernels/execution

2026-10-16. V1's eight answers still apply. This version authorizes ONLY an
opt-in synthetic GPU correctness prototype of the grouped head and equally
informed controls. It does not authorize a performance/model-training campaign.
No new inference mechanism or novel reverse-mode principle is claimed.

## Scope and CPU boundary correction

V2 source6ef8f37ab151e1d600bfcaa8bbbe87455079f2ec passed five oracles and full320
tests88.638s, but its affine-head numerical implementation was only exercised
with finite logits. The separate structural-zero fixture at that SAME source
has finite loss and nonfinite4 H/4 W/2 bias gradient entries. Preserve its
negative packet. V3 handles an all-minus-infinity class by a finite placeholder
normalizer; its exponentials and adjoints are zero. This is V1's stated
zero-mass derivative convention, not a new mathematical claim. The new sixth
oracle independently compares finite supported logits and literal zero gradients.
No previous source/result is overwritten or relabeled as the corrected code.

## Frozen synthetic fixtures and comparison

Use FP32 H/W/bias and FP32 gradients; class LSE/output logits are FP32. IEEE
FP32 matrix products (torch precision highest and Triton input_precision ieee)
are required for this initial correctness packet, not a fast mixed-precision
claim. Full mixed-precision training remains a separate future obligation.
Scalar/downstream reference is dense FP64 over the ORIGINAL FP32 inputs.

Fixed (N,D,V,C) shapes, in order:

    (1,3,7,6), (4,3,7,6), (7,5,11,5), (17,33,67,7),
    (33,65,257,13), (65,64,1024,17), (5,17,17,17), (2,2,4,3).

The first two use the tiny JSON original-ID mapping(0,0,1,2,3,4,5).
Cases2--6 (zero-based index) use a local CPU Torch generator seed58030+index:
assign class IDs by a random permutation of arange(V)%C. Alternate balanced
and skewed classes: on odd index>=3, all but the final C-1 pre-permutation
IDs belong to class0. H,W,b are0.2*randn from the SAME local generator,
targets are local randint original IDs, and signed dz/dt are local randn.
No fitted target or selected fixture based on performance. Every row/ID stays.

The last case is the fixed structural-zero fixture from zero-class-v3-before-
fix.json, mapping(0,1,1,2), b=(0,-inf,-inf,.1), targets(0,3), original explicit
H/W from test_reference.py. Only supported class outputs enter the scalar
loss; the blocked class output remains -inf with ZERO dW/db/hidden contribution.
An all-unique class case is deliberate: then summary memory can be N*V and
padding may be wasteful. Do not call that a favorable memory regime.

Candidate uses row tiles16, vocabulary panels32, reduction dimension32,
two stages (panel LSE then per-class merge), direct ORIGINAL-ID weight loads
and recomputed tiled full dH/dW/db. No gradient filtering, copied reordered W
or dense N*V activation/gradient buffer. Full dW/dH/db are allocated/counted.
Cached class panels are compile metadata; no dynamic class changes here.

Compare EVERY fixture with dense FP64 scalar/autodiff, dense GPU FP32 and the
ordinary checkpointed Torch grouped head. Include class-wise CURRENT CCE with
return_lse=True, reduction=none, filter_eps=None, accum_e_fp32/accum_c_fp32=True,
using its DIRECT LSE adjoint. All receive identical ID classes/targets/inputs.
CCE is pinned at3de376c106a1916bc5e1b619f9c77c87a461ee1c, read-only cache
/home/jota/.cache/tcc-final/a58/ml-cross-entropy. Individual file hashes are
recorded separately. Its input gathers/zero-class guards are explicit; do not
silently modify its source or give candidate credit for an adapter error.

For the all-zero class, ALL controls may skip its analytically zero derivative
and return -inf; a meaningless LSE(-inf,...,-inf) derivative is not required.
All methods still process the fixture. Candidate must implement its own safe
zero-class exponent rule. Target logits must retain original IDs even if aliases.

## Pass/refusal rules and provenance

For each method record all LSE/target/dH/dW/db checks against dense FP64; require
finite supported outputs/gradients and abs(error)<=5e-5+5e-5*abs(reference)
elementwise. Preserve maximum absolute/scaled error and every failure. No
passing by dropping a shape/control or relaxing tolerance afterward. Unsupported
hardware/library/adapter failure is explicit and receives no performance win.
The source can be corrected in a separate later packet, never relabel this one.

Also require candidate refusal for empty N, NaN hidden input, out-of-range
original target and an all-blocked bias vector (zero total row mass). These
are contract checks, not evidence about real training quality. Preserve inputs
and class mappings, source hashes, full producer commit, runtime/device,
library commit, gradient flags and counts. Commit executed code BEFORE running;
protocol commit must not be mislabeled as containing later kernels.

Resources: one GPU, one process,900s total,120s per fixture,2GiB incremental
allocated GPU memory. Local generators only; restore Python/NumPy/Torch CPU/
CUDA RNG and matmul/thread flags after run. No global stream changes retained.
Record every status and partial output on refusal/error. Internal library
compilation/autotuning may run; this is NOT competitive timing evidence.
No model download, head/hidden-state readout, forward, optimizer step, new
semantic label or external data is authorized by this arithmetic protocol.

## Decision after this preflight

A PASS establishes only an arithmetic/kernel contract on synthetic matrices.
Before benchmarking, freeze a separate complete operation with metadata from
real tokenizers, strong grouped/checkpointed/CCE controls and all preparation/
grammar/backbone/optimizer costs. Both exact streamed controls can match the
asymptotic memory. An implementation with no substantive own architecture or
useful complete-step consequence is a control, not an achieved article goal.
