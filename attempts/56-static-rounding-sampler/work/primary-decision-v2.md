# Primary-source audit and decision after the minimal GPU checks

## Original ADZ report now actually available

Denise and Zimmermann, *Uniform Random Generation of Decomposable Structures
Using Floating-Point Arithmetic*, INRIA RR-3242, September1997:
https://inria.hal.science/inria-00073447/document . Downloaded original PDF
SHA2569eb5910791f17c0869989c9753d310c2e6eda874ecc2d66b669170e70ffddb6a.
The20-page deposit contains the16-page report at PDF pages4--19. All those
pages were read via OCR because its text layer has broken font encoding;
report page6/Lemma3.1 was also inspected as a rendered image. This is the
1997 ORIGINAL REPORT, not a claimed full reading of the1999 journal version.

Lemma3.1 and Proposition3.2 already propagate deterministic floating errors
through positive combinatorial recurrences. Section4's ADZ schemes use one
approximation plus certified error bounds, retain the ambiguous random value
for exact refinement and analyze expected versus worst-case work. Section5
also implements direct lower/upper arithmetic as a tighter control. Thus the
claimed generic switch from two directed values to one approximation with
static certificates is an established mechanism. This is a NEGATIVE own-
mechanism audit, not a measured latency refutation of the present GPU code.

The author listing https://members.loria.fr/PZimmermann/papers/ links this
report; the journal DOI10.1016/S0304-3975(98)00323-5 and publisher abstract
were checked separately. Earlier A51 notes honestly recorded failed original
fetches. That historical reading scope is not rewritten by today's access.

## Other scoped checks

Higham and Mary2019, DOI10.1137/18M1226312, original introduction, equation1.2,
Model2.1, Lemma2.2 and Theorem2.4/proof were read:
https://epubs.siam.org/doi/pdf/10.1137/18M1226312 . Deterministic multiplicative
error propagation is standard. Their probabilistic improvement requires extra
rounding assumptions; A56 does not assume those or use it as an exact certificate.

The PepTune original paper introduction/section2.1 and official README's
generation/evaluation contract were examined:
https://arxiv.org/html/2412.17780v2 and
https://github.com/programmablebio/peptune . They establish a real discrete
molecular generator, but do NOT establish the needed source/evaluator cost
ratio or informative classes for our pair selector. Pareto search is a
different operation from unbiased model evaluation. No molecular campaign,
new model download or favorable-use claim was initiated from that inspection.

SparseMAP's original introduction/sections2.1--2.2 and PMLR description were
also checked, without a new prototype:
https://proceedings.mlr.press/v80/niculae18a/niculae18a.pdf . Generic marginal-
polytope projection is an established alternative, not a new contribution to
claim by adding a diffusion label. No full reading of its later proofs is claimed.

## What has actually been checked in A56

The written contracts7fb3daf/b1f88d6 PRECEDE the new implementation. Four
small rational oracles pass:1793 brute-grid roundings,3024 circuit enclosures,
1024 uniform-prefix cells and an actual counterexample to a DAG-height-only
product budget. Full311 maintained tests pass88.119s. These are mathematical
and implementation correctness checks, not speed measurements.

The opt-in GPU audit passes185 independent exact class/suffix/root comparisons,
336 literal retained-prefix replays and all4096 prefixes of a16-event dyadic
word law. It covers JSON/UTF8, original aliases/fixed ID, >256-ID reductions,
rejected terminals, zeros and normal/subnormal/underflow handling. Two tiny-
weight cases correctly rerun the directed frontend; they are not silently
discarded. Fourteen emitted PTX modules are preserved, no FTZ qualifiers;
explicit RNE primitives and the reduction layouts were inspected. This is
finite evidence, not a compiler/software formal proof or all-hardware theorem.

No fresh or old neural head was evaluated. There are ZERO new pretrained
forwards and ZERO competitive timings. The first attempted invocation used
the CPU environment and failed to import Triton; its log and exact source are
retained. Repeating in the existing Torch2.13/CUDA13 environment succeeded.

## Decision

Preserve the guarded GPU implementation as a potentially useful CONTROL and
correctness artifact. Do NOT promote the static-certificate mechanism as new
sampling theory or the positive scientific result requested by the user.
The original ADZ arithmetic-only variant is a mandatory same-operation control
for any later systems study, alongside equally optimized directed intervals,
graph capture and approximate sparse GPU where applicable. It must receive the
same layout and source information, not a deliberately coarse/slower template.

There is no measured own systems advantage, substantial new architecture or
confirmed publication significance yet. A successful toy kernel alone does
not justify a broad neural campaign. Any expansion needs a concrete additional
systems distinction and a new frozen complete-cost protocol, including real
consumer value. A51's failed gate, A24's earlier query-only result and all
negative applications remain untouched. The user's actual goal stays OPEN.
