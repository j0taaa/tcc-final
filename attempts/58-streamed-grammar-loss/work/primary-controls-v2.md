# V2 — Primary controls, before the arithmetic prototype

2026-10-16. Supplements, does not overwrite, the written V1 scopes.

Xu et al.2018 ORIGINAL PDF
https://proceedings.mlr.press/v80/xu18h/xu18h.pdf was read at Definition1,
§4.1 and §5.1 including the downward derivative pass. Negative log satisfying
mass, its addition to an existing loss and compilation/backpropagation are
explicit ANTECEDENTS. No semantic regularization or weighted-count gradient
claim is new here. Reading these sections fulfills V1's before-code obligation.

CCE original v1 §§4.2--4.3 explicitly permits arbitrary incoming LSE gradients.
The CURRENT official cce.py was inspected:
https://github.com/apple-aiml-research/ml-cross-entropy/blob/main/cut_cross_entropy/cce.py
It exposes return_lse, accepts grad_lse_out separately from grad_out, passes
dlse to the backward kernel and disables filtering when filter_eps=None.
Thus class-wise CCE can supply each class's LSE directly; do NOT handicap it
with an unnecessary dummy-target cancellation. Vocabulary sorting/indirect
loads are also known CCE optimizations. A real future benchmark must pin an
immutable current source revision BEFORE execution. No CCE execution, model
parameter read or performance measurement took place here.

MONOIDREDUCE's OpenReview forum/PDF and hashed PDF return verification HTML;
raw urllib retrieval of the hashed official PDF returned HTTP403. The PRIMARY
search-indexed first two pages of the official PDF were readable:
https://openreview.net/pdf/7a5d48a074a6024887ad8cf5acf8761aeb4732f3.pdf
They explicitly unify CCE/attention by commutative folds and a local-gradient
condition, and discuss streaming/parallel/recomputed backward. This is a
direct GENERAL antecedent to the algebraic principle. The complete theorem,
proof and AppendixB implementation were NOT obtained/read. Do not infer
their capabilities or absence of a segmented implementation from that gap.

The remaining candidate is ONLY a substantive useful grouped execution and
real full-training-step benefit over equally optimized class-wise CCE and
checkpointed class aggregation. Both may MATCH asymptotic workspace. The
generic memory-efficient reverse-mode principle is not ours. A minimal
derivative oracle is justified to audit the variable-EOS contract; passing it
does not trigger broad implementation, an own-novelty claim or a model campaign.
