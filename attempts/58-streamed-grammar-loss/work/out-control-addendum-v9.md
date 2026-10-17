# V9 — Native output-buffer control, still BEFORE ANY resource timing

2026-10-16. V7/V8's benchmark has NOT run. The following stronger control is
added prospectively; no prior case/result is removed or relabeled.

Reading the pinned native cce_backward.py shows zeros_like allocations for
each class's dH/dW/db, then the wrapper returns those tensors. Copying a giant
class gradient into the final dW can nearly double the instantaneous output
storage. That is an API allocation choice, not a defensible own lower bound.
The native _mm_backward always uses tl_lock_add, which reads/adds the existing
output buffer. It can accumulate directly into correctly initialized final
buffers and disjoint physical slices; no gradient math/kernel change is needed.

Add CCE_out: use the SAME pinned unmodified native linear-LSE forward without
dummy targets and the SAME native backward kernel. A new explicitly credited
FP32/LSE-only host adapter supplies final dH/dW/db views instead of allocating
per-class outputs. Filtering is OFF; full original gradients are retained.
Initialize final dH/dW/db once, and keep native locks. Locks are released to0
by the native kernels; under this SINGLE-STREAM sequential plan they may be
cached by shape between completed calls. A failed plan is not reused.
No CCE vendor file is edited. Preserve its license with the adapter/provenance.

Torch checkpoint/dense controls may also write GEMM gradients DIRECTLY into
their final disjoint dW slices via torch.mm(out=...), in their custom first-
derivative backward. Do not retain an unnecessary temporary just to make the
candidate's memory look better. Higher-order derivatives are outside this
prototype contract. The unchanged target term is added exactly once.

V7/V8's complete control family is now FOURTEEN: its original13 plus
CCE_out128. PhaseI includes ALL original three controls PLUS CCE_out128.
The same eight N/all eight candidates/three repetitions/gates/resources and
conditional negative-only shortcut remain. Remaining ten controls are still
conditionally measured on ALL N. No warm data has been seen in choosing this.

First replay all eight V3 input fixtures at the unchanged tolerance for all
four thresholds, adding CCE_out alongside dense/checkpoint/CCE. This expands
the control correctness packet to128 configurations, not a claim that older
96-record packets already used output buffers. Also retain literal physical/
original-ID and tied-input/optimizer tests. The lower-level API/source is
pinned, explicit and not a new algorithm. A synthetically correct control
or faster port alone does not meet the scientific contribution goal.
