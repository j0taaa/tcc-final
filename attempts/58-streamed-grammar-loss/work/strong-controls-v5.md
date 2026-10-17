# V5 — Strong physical-layout controls, BEFORE their code/timings

2026-10-16. V1 eight criteria still govern the candidate. This version is a
competent-control refinement for the SAME original-ID class-LSE/target/full
gradient operation. It does NOT change the loss, tolerance or earlier data.

1. Use remains full H/W/bias backpropagation through a grammatical loss.
2. CCE/segmentation/physical permutation/manual gradient assembly are KNOWN;
   these controls cannot be claimed as our new theory or protagonist.
3. A candidate is useful only against these optimized controls, not200 generic
   full-vocabulary autograd scatters or a weight copy on every call.
4. The permutation/adjoint proof below precedes code and all measurements.
5. First test the SAME eight frozen synthetic V3 fixtures against dense FP64,
   plus literal input/gradient permutation and tied-embedding/optimizer oracles.
   No performance run before a SEPARATE immutable timing/resource protocol.
6. Charge cold compilation/permutation and optimizer-state conversion once;
   warm steps may maintain the physical layout. Same dtype/grammar/objective,
   full original-ID gradients, metadata reuse and actual input validation.
7. Permanent sorting, many small classes and a few large CCE calls may remove
   all useful advantage of the candidate. Both can match asymptotic memory.
8. A substantive systems distinction, full-cost speed/memory and native model
   integration remain OPEN; arithmetic/control success does not achieve them.

## Physical layout and exact original-ID interpretation

For threshold T in{0,8,32,128}, order classes with size<=T first, then all
larger classes, retaining each class's contiguous member IDs. Let perm[k]
be the ORIGINAL ID at physical row k and inv its inverse. Store once

    Wphys[k]=W[perm[k]], bphys[k]=b[perm[k]], targetphys=inv[target].

Class outputs still use their original CLASS index; caller token IDs remain
unchanged. The dot product at targetphys is the original target dot product.
For a classifier-only branch, gradients transform as

    dWoriginal[v]=dWphys[inv[v]], dboriginal[v]=dbphys[inv[v]].

This follows directly from the chain rule for a coordinate permutation. It is
not a new loss, distribution or quantization. With tied input embeddings,
input lookup ALSO uses inv[original IDs]; its gradient is ADDED to the head
gradient at those physical rows. Converting head rows but not tied lookup is
wrong. A coordinatewise optimizer with equally permuted state (including
momentum/Adam moments) commutes with this permutation in real arithmetic.
Floating accumulation order can differ and must be checked, not called bitwise.

The benchmark cannot require a per-step V*D permutation/copy when this stable
layout can be kept throughout training. Initialization/checkpoint import and
export are cold costs; include them separately. No actual model/optimizer is
changed by implementing this small control reference.

## Batched small classes and direct class gradients

All small-class rows form one physical prefix. One ordinary GEMM computes
their N*S logits, S=sum_(small C)|C|<=T*C. A segmented stable LSE computes
each small class's summary. On backward, recompute that prefix GEMM, multiply
by its class softmax/adjoint, and use GEMMs for dH and the disjoint dW prefix.
This can retain an N*S matrix, which must be measured. If S=V there is NO
activation compression and no false claim that this is always memory efficient.

Each large class receives a contiguous Wphys VIEW and the current native CCE
direct LSE operator, filtering OFF. The control keeps native per-class reverse
contexts, uses the incoming class adjoint and assembles dW/db into their
DISJOINT physical slices. It sums only the N*D hidden gradients across classes.
It must NOT allocate/scatter a full V*D zero matrix per class. Target-logit
adjoints are added once by indexed dot/backpropagation in original-ID order.

A Torch-only checkpointed control uses the same physical layout/assembly,
but panel GEMMs/LSE recomputation for large classes instead of native CCE.
Dense ordinary GEMM plus segmented class reduction/full-gradient GEMMs is
also legitimate. Fixed threshold variants are controls, not post-hoc choices
that may be omitted if they beat the candidate.

## Explicit API/preparation boundaries

V3's candidate checks all finite inputs on every call; the controls must not
be handicapped with unnecessary duplicated work to match that prototype.
Any later unchecked finite-domain entry point, fused validation, small-class
dispatcher, faster dtype or tiling is a NEW source/configuration to validate
and freeze before timing, never attributed to the V3 correctness source.
Cold and repeated-call measurements must state which validations/preparations
are included. No candidate change is authorized by writing this control note.

## Primary reading supplement, scope only

The OpenReview PDF still redirects to verification/HTTP403. More PRIMARY
indexed excerpts of that SAME official PDF were readable through search:
https://openreview.net/pdf?id=Fopv5Hpm1C
https://openreview.net/pdf/7a5d48a074a6024887ad8cf5acf8761aeb4732f3.pdf
Actual new scope: batched user-function table/corollary2.1.1 discussion and
Listing2's forward/context/partial backward interface, plus the start of
Listing4's cross-entropy-between-two-parameterized-distributions example.
They explicitly already expose streamed forward and locally recomputed
adjoints in a general torch.autograd.Function factory. The COMPLETE theorem,
proof, listing and downloadable source were NOT retrieved. This narrows our
possible own claim further; do not call generic arbitrary-adjoint streaming
new or silently treat excerpts as a full original read.

Primary MDLM config https://huggingface.co/kuleshov-group/mdlm-owt/blob/main/config.json
was inspected for geometry ONLY: hidden_dim768/vocab50258/model_length1024.
No model weights/hidden states/heads, labels or new forward were read. A
resource protocol must pin its input metadata source before using this geometry.
