# V5 — Two actual CTR consumers and a native first-moment proof obligation

Written BEFORE any V5 prototype/primitive execution. V4's negative NNCP gate
remains closed; V1--V4 source/proofs/data are not changed. No new model/corpus/
training/timing/quality campaign is selected. Only a bounded native primitive
audit is justified below. The scientific positive goal remains OPEN.

## Source consumers: absence of a feature is not sufficient

1. rixwew/pytorch-fm, immutable f74ad19771eda104e99874d19dc892e988ec53fa,
   examples/main.py uses Adam(weight_decay=weight_decay); CLI DEFAULT1e-6,
   lr.001,batch2048. Its DeepFM selection has embedding16,MLP(16,16),dropout.2.
   torchfm/layer.py uses ordinary dense-gradient Embedding for first/second
   order tables; Criteo's field dimensions are computed from actual counts
   with minimum threshold10, not a fixed handpicked vocabulary. The absent
   row's DATA gradient is zero, but coupled Adam adds lambda*w before its
   moments. The declared zero-gradient A70 law therefore DOES NOT apply to
   this default. Do not silently remove regularization or replace Adam by
   SparseAdam/AdamW and call that a native-preserving optimization. The CLI
   allows other settings, but no observed useful no-decay workload is supplied
   merely by that option. No default-workload campaign is selected.

2. chenxijun1029/DeepFM_with_PyTorch, immutable
   f12a2ccc3b0d23277112ae0efbf4c08bf0411b58, main.py really uses
   Adam(lr=1e-4,weight_decay=0.0),CPU,embedding4,hidden(32,32),batch100.
   Its literal Num_train=9000, sampler0..8999 and epochs5 give **450 updates**
   (not the comment's900000 examples). model/DeepFM.py uses row lookup in
   first/second-order tables, BCE-with-logits, no inspected global embedding
   penalty or optimizer-state export in fit; batchnorm/dropout and periodic
   evaluation are additional state/RNG/cost obligations. Actual feature
   sizes/input frequencies/gradients/timings have NOT been obtained.
   This source shows a genuine no-decay consumer rather than changing the
   first consumer's defaults. It does NOT show V3's32768/65536-step useful
   erasure frequency or sufficient full-cost benefit in its450-step run.
   Changing its sampler/epochs/table dimensions would be another workload,
   not confirmation of this source configuration. No large build is selected.

Both are real CTR uses, another allowed TCC scope; neither supplies a new
dLLM/CFG result. A known exact sparse optimizer/compiler or generic interval
erasure remains a mandatory competent control, not excluded by either source.

## Native lerp is not the private C recurrence

The pinned original PyTorch2.8 CPU sources from V4 show, for converted
float32 weight c<1/2 and admitted finite intermediates, two relevant forms:

    S(m) = R(m + R(c * R(g-m)))
    V(m) = R(m + c * R(g-m))       [last operation is fused multiply-add]

Here R is round-to-nearest-even binary32 with gradual underflow. These are
source-level scalar/vector forms, NOT an exhaustive compiled-library/ISA
proof. Native Adam's Python branch calls lerp_(grad,1-beta1). The private
V1 recurrence R(R(beta1*m)+R(c*g)) is different and monotone in m. No previous
proof/fixture claimed transfer to native lerp. V4 beta1=0 is also distinct.

For c=R(.1),g=1, put u=2^-27 (one ulp at c),

    L=3u                  bits32c00000
    X=4u=2^-25            bits33000000
    U=2^-25+2^-48         bits33000001

Then L<X<U, but BOTH S and V have values

    F(L)=F(U)=c+3u        bits3dccccd0
    F(X)=c+4u             bits3dccccd1.

Proof: R(1-L)=R(1-X)=1; the second is the tie choosing even1. For U just
above X, R(1-U)=1-2^-24. Since c*2^-24=(.8000000119...)u, the product
rounds to c-u in S, and adding U rounds to c+3u. The fused result is
c+(3.199999988... plus2^-21)u, rounding to the same c+3u. L and X are
exact3u/4u additions to c. All operations are finite, nonzero and normal.

Thus arbitrary-interval endpoint agreement for native lerp is UNSOUND:
equal F(L),F(U) does not exclude the interior different value. This does
NOT by itself refute a special ZERO-ANCHORED interval test [0,B] or [-B,0];
the counterexample's L is positive. It invalidates a blanket monotonicity
argument for transfer, not the declared monotone V1 theorem or V4 result.
Do not exaggerate this into a native-Adam bug: lerp never promised this
particular property. It is our proposed optimizer proof's responsibility.

## Positive safe admission for native expression boxes

For any admitted finite interval [L,U] and c>=0 define

    Dlo=R(g-U), Dhi=R(g-L)
    Slo=R(L+R(c*Dlo)), Shi=R(U+R(c*Dhi))
    Vlo=R(L+c*Dlo),     Vhi=R(U+c*Dhi)     [fused corners]

Rounding is monotone and fused multiply-add is monotone in each of these
two arguments separately when c>=0. Therefore every S(m) and V(m) for
L<=m<=U is enclosed by

    [min(Slo,Vlo), max(Shi,Vhi)].

The proof never treats the dependent occurrences of m as independent
equalities; it uses a sound BOX superset. If its two endpoints are the SAME
NONZERO bits, assigning that value is exact for all intermediate m and
either source form. Nonfinite corners or zero ambiguities refuse admission.
For c=R(.1),g=1 and [0,2^-80], all four corners equal c, a nonvacuous
positive erasure. The adverse [L,U] above instead produces a wider box,
correctly refusing the naive endpoint conclusion.

This is elementary CLASSICAL interval arithmetic with a native-expression
specialization, not a new generic interval theorem. It proves no useful
gap frequency, full native software identity or latency advantage. Native
zero-gradient decay itself differs from R(beta*m); its enclosure/fallback,
scalar/vector partition, schedule, denominator, signed zeros, export and
whole adaptive-training contract still need a separate proof before a port.

## Bounded prospective primitive check

Freeze new standalone source before execution. One stdlib Fraction binary32
RNE oracle independently computes both declared S/V forms, the adverse triple
and the expression-box corners. Check literal Torch lerp_ CPU output for
the triple in shapes1,2,15,16,17,31,32,33,64,65, three shifts of each pattern,
with1 and8 Torch threads (60 kernel calls). Also check boxes [-B,0],[0,B],
[-B,B], B=2^-40/2^-80,g=+/-1,+/-2^-10, one three-point native array per box
per thread setting (48 kernel calls). All constants remain fixed.

Expected: actual adverse-triple bits match the rational S/V values; naive
endpoint admission is rejected by the box; all24 tiny boxes have identical
nonzero corners and their sampled native values equal that value. Preserve
all failures/actual exits/hashes. No model forward/backward/update, benchmark,
external dataset, setting search or claim about every compiled kernel.
Only108 primitive tensor calls are prescribed; do not infer workload benefit.

Source metadata/scopes: primary-source-manifest-v5.json. Original sources
were read from immutable revisions, not executed. The second repository has
no inspected LICENSE file; only URLs/hashes/scopes are redistributed here,
not its full source. This check does not establish sufficient own priority.
