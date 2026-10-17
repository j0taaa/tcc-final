# V6 — Finite-domain launch configurations and metadata, BEFORE code/timings

2026-10-16. V1 eight criteria and V5 controls apply. This is a NEW source/
configuration refinement, not a relabeling of V3/V4 arithmetic or a new method.
No performance has been measured in selecting these fixed configurations.

## Proposed finite-domain entry point

Keep V3's guarded public API and kernels unchanged. Add a separate internal
finite-domain launch interface for resident nonempty contiguous FP32 H/W/b,
positive row mass, valid original targets and a static complete class map.
It calls the SAME _project/_merge/_targets/_backward kernels, allowing row/
vocabulary tile pairs(16,32),(32,64),(64,64),(64,128), reduction tile32.
Larger row tiles reduce the number of partial dW accumulations; larger
vocabulary tiles increase small-class padding. Those are competing classical
tiling effects, not a speed claim or an own differentiation theorem.

An unchecked finite-domain call is not allowed to silently replace the old
input-refusing API. It has an explicit precondition. In a repeated immutable-
input primitive screen, ALL methods may validate once; validation/preparation
is included in cold costs. In future changing-parameter training, a common
finite-input/gradient policy and its actual cost must be specified. No old
V3 refusal result is attributed to this internal interface.

Statistics, exact-real backward, original IDs and dense gradient storage are
unchanged. FP32 IEEE arithmetic only initially; no fast mixed-precision or
bitwise-equality claim. Re-run the eight frozen V3 inputs, unchanged tolerance,
for ALL four tile pairs before timing. Do not drop a failing configuration
from the packet. Unsupported configurations receive no win.

## Real tokenizer metadata, not real model observations

For a later primitive resource screen, prepare the full GPT2+MASK50258
original-ID global JSON lexical class map from ONLY vocabulary.json in the
already public A24 first-full-head-v2/packet.zip. Do NOT open the numerical
head array. Copy the immutable lexer/table definitions from original commit
303cff72d6e49e8b1dab29ea3ea84c79f4780646 into this attempt, record each origin
and SHA256, then serialize EVERY original ID/class. Maintained tokenizer-byte
adapter code/version is recorded too. Classes/IDs cannot be selected by timing.
This is metadata construction, not a new neural forward/head readout.

Geometry comes from the primary pinned MDLM config (hidden768,vocab50258,
max sequence1024); fetch ONLY its small config JSON at revision
d0958fa851335ece6c15260ce0025f030673c0fb. No model weights are requested.
Record file/packet/tokenizer hashes and class-size counts. A SEPARATE complete
primitive timing/resource protocol must be committed before any benchmark.
Synthetic H/W/b values at real geometry are still synthetic; neither model
training benefit nor downstream quality can be inferred from that screen.
