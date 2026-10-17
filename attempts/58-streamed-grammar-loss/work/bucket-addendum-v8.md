# V8 — Ragged merge refinement BEFORE ANY resource measurement

2026-10-16. V7 has been written/implemented, but its benchmark has NOT been
executed and NO competitive timing has been observed. V1 eight criteria,
V5 controls and V7 inputs/tolerance/gates/cost boundaries remain unchanged.
This pre-data addendum EXPANDS candidates; it does not remove old variants.

The actual complete tokenizer map has194 classes, largest41709 IDs. V3/V6's
merge launches one program per row/class padded to the maximum panel count.
That wastes up to C*max(K_c) reduction work for sums requiring only sum K_c.
It is a prototype implementation issue; known segmented/bucketed reductions
and the strong controls already avoid it. Their principle is not ours.

Add a second merge implementation: group classes by

    B_c=2^ceil(log2 K_c), K_c=ceil(|class c|/vocabulary_tile).

If K_c=1, copy its already computed panel LSE with a two-dimensional32x32
row/class tile, without exp/log/reduction. Otherwise launch one reducer per
class/row tile of at most16 rows, with row tile=min(16,max(1,2048/B_c)).
Use exactly B_c panel lanes, mask missing panels, stable log-sum-exp and the
same original class output indices. Projection, target dots and backward
are the UNCHANGED V3 kernels. Backward consumes the resulting SAME z values.

Correctness is immediate from disjoint partition of classes and associativity
of real LSE: each old panel is included exactly once in its own class's sum;
one-panel sums are identity. Each B_c<2K_c unless K_c=1, so per VALID row the
merge inspects fewer than2*sum K_c lanes, versus C*max power-of-two padding.
Include row padding (at most15 rows per reduced class and31 for copy tiles)
in implementation costs. This is a classical work/layout improvement over
OUR padded prototype, not a separation from equally optimized controls or
a new theorem of differentiable reductions.

Before timings, replay ALL eight old V3 inputs/four tile pairs for the new
merge, same tolerance and original-ID full gradients. Failures are retained.
The initial and new implementations remain independent files/source hashes.

V7's final candidate family now includes EIGHT configurations:
tile16x32,tile32x64,tile64x64,tile64x128 (unchanged), and
bucket16x32,bucket32x64,bucket64x64,bucket64x128. PhaseI measures ALL eight
against the SAME three predeclared strong controls, on ALL eight N values.
The rule still requires ONE fixed candidate to pass at least3/8 cases; the
remaining ten controls are triggered only by the SAME optimistic decision.
No metric, resource allowance, control, geometry or favorable-case count is
relaxed. Synthetic primitive correctness/timings still do not establish
whole-training benefit, systems originality, model quality or the user goal.
