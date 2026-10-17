# V4 — NNCP consumer, actual Adam branch and a stronger classical control

2026-10-17, AFTER V3. Source reading/written analysis BEFORE the resource
screen. V1--V3 source/results remain intact. No end-to-end codec, model
forward or native PyTorch operation has been run for V4 at this writing.

## Actual consumers, with version/mode distinctions

Bellard's NNCP is a real adaptive lossless compressor: encoder and decoder
must reproduce the same neural probability computation. The current2024
release uses LibNC, whose original documentation requires deterministic
behavior and describes FP32 residual bits for BF16 master updates. Its
optimizer implementation is distributed as a binary; its public header
exposes an opaque NCSGDOptState and an indexed-gradient callback. The NNCP
C source has an OPTIONAL sparse_grad flag (the inspected parser defaults
to0). Neither the flag nor lack of source establishes its exact sparse
optimizer law or that it lacks an equally good optimization. No LibNC
binary was extracted for execution, loaded, modified or redistributed here.

The older ORIGINAL NNCPv2 source is open and explicitly supports a CPU
device/FP32 path. It uses nn.Embedding with an independent output Linear,
and torch.optim.Adam with betas=(0,.9999), zero weight decay, and a scheduled
learning rate. Its readme tested PyTorch1.7.0/Python3.6, and its published
base/large scripts use CUDA+FP16/Apex and periodic retraining. Therefore a
modern PyTorch2.8 CPU/FP32 component screen is NOT reproduction of its
published GPU timings, compression ratios or preexisting compressed files.
The source main loop also has clipping, CDF construction, arithmetic coding,
past memories, and optimizer-state switching during retraining; these costs/
state observations cannot be ignored in a proposed whole-codec replacement.

Only a bounded NECESSARY resource screen of the open model/training/coder
components is selected below. It is not a port of the complete executable,
nor a claim that user demand/adequate priority for A70 is already satisfied.

## Native branch and beta1=0 specialization

Installed PyTorch metadata is2.8.0+cpu, Git
a1cb3cc05d46d198467bebbb6e8fba50a325d4e7. The installed Adam Python source
and original C++ sources at that revision were inspected. For noncapturable,
nondifferentiable, nonfused, noncomplex, no-decay CPU float32, single-tensor
Adam uses exp_avg.lerp_, v.mul_.addcmul_, sqrt/div/add of epsilon, and
param.addcdiv_. That is NOT V1's literal operation order. The scalar/vector
Lerp implementations even use different expression forms (vector fmadd).
No general bitwise transfer from the private C prototype is asserted.

For beta1=0 and finite old first moment, a +0 gradient produces a numeric
+0 first moment in the inspected Lerp expressions, provided their
intermediates are admitted. The second-moment zero-gradient path is repeated
rounded multiplication by the converted beta2 (adding its +0 term changes
no positive variance). With finite positive denominator and finite schedule,
adding a zero update preserves each nonzero parameter. Signed-zero/native
lane behavior must be handled explicitly, rather than inferred from numeric
equality. At a new nonzero gradient, the second-moment update is monotone in
the old variance, so its actual native operator can be used for interval
endpoint admission. This is a WRITTEN specialization and read-contract lead,
not a tested adapter or proof of every compiled PyTorch kernel.

Thus beta1=0 has a competent classical weight-skipping control with no250-
step prefix. Only restoration of native variance and any concrete state
observation remain. A70 cannot claim to save all weight work uniquely.
FP16/Apex, LibNC, master/residual states, foreach, strides/SIMD tails,
checkpoint/retraining and native clocks need their own compatibility audit.

## Finite-format jump tables are another mandatory strong control

Do NOT claim that preserving repeated rounding inherently requires h native
updates. Ordinary binary lifting of a finite deterministic map can jump it
exactly. For binary32 multiplication by fixed beta in[.5,1), while results
stay normal, the transition can be tabulated on the2^23 normalized
significands, together with the exponent drop. Rounding is invariant under
power-of-two scaling in that admitted normal region. Repeated-squaring
composition provides2^j-step maps; monotone exponent drops decide which
jumps stay above the subnormal boundary. A boundary step is executed literally.
Subnormal integers n*2^-149 form another finite map n->RN_integer(beta*n),
which is also tabulatable, including its fixed points. If a boundary step
stays at the minimum normal fixed point, that fixed point can be detected.

The straightforward tables cost O(2^p log(H+2)) words/preparation for a
maximum admitted gap H, with O(log(H+2)) queries; explicit exponent/status
and subnormal handling count. This is a CLASSICAL finite-state/lookup
control, not invention of binary lifting or a new A70 theorem. More compact
functional-graph representations, on-demand tables and persistent reuse are
also allowed. A70 may avoid that preparation/storage on certified erasures,
but table construction cannot be charged afresh when the actual application
can reuse it. No table implementation, universal lower bound, measured
advantage or adequate own priority is claimed in this source audit.

## Eight-criterion reassessment and decision

1. Real operation: lossless online neural compression independently motivates
   reproducible probabilities. NNCPv2's native sparse input embedding is a
   concrete possible target; its observed useful gap distribution is unknown.
2. Own difference: native observable-state erasure is still a candidate
   specialization of classical interval/rounding tools. beta1=0 and the
   finite-state control remove generic exclusivity arguments. Priority OPEN.
3. Choice: first test whether eliminating ALL input-embedding optimizer work
   could plausibly save20% of a full component cycle against competent native
   controls. Passing is not an A70 win; failure closes this screened variant.
4. Proof: preceding paragraphs delimit the native operation. No literal
   PyTorch/CUDA/LibNC/whole-codec identity is inferred from V3's C fixtures.
5. Experiment: protocol-v4-resource.md fixes the model geometry, two memory
   frames, native/ideal controls, inputs/repetitions/full-cycle metrics and
   failure branch BEFORE forwards. No actual A70 adapter is built yet.
6. Complete cost: timed cycle includes batch construction, full model forward,
   CDF/coder writes, log loss, backward, clipping, gradient clearing and all
   nonskipped native optimizer work. One-time setup/paired-input restoration
   and validation are recorded separately, not called an amortized cold win.
7. Fatal objections: native beta1=0 shortcuts, exact jump tables/interval
   controls, already sparse LibNC, small whole-model share, or insufficient
   gaps. Memory/copy/table/export/codec work and native dtype differences
   remain mandatory. Do not choose a slow eager control or inflate vocabulary.
8. Article: real source/frame resource feasibility first; actual native
   adapter, useful input-only workload/certification frequency, full-cost
   independent benefit and priority remain missing. User goal OPEN.

Decision: execute only the prospective optimistic resource screen, BEFORE a
substantive adapter/table/codec build. Do not rerun more seeds/geometries or
alter its20% gate to rescue a negative result. Other consumers/the theorem
are not refuted by a failure of this particular CPU/FP32 component variant.

## Primary retrieval and reading scopes

- NNCP official page/readmes: https://bellard.org/nncp/ ; LibNC original
  documentation https://bellard.org/libnc/libnc.html, Sections2.4/3.1/3.2/
  3.5/4 and public header optimizer/indexed-gradient declarations read.
- NNCP2024 archive1180969 bytes, SHA256
  7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119.
  Only selected source/header/readme paragraphs read, not the complete C
  program or proprietary implementation. No original binary execution.
- Original NNCPv2 archive25411 bytes, SHA256
  ced40f3cee1cb2948a5465ead64dffa2614c54abe0ed12fdce084f5c63c29fb1,
  https://bellard.org/nncp/nncp_v2-2021-02-06-1.tar.gz . Read readme, base/
  large scripts, nncp.py initialization/optimizer/main training/coder/retrain
  excerpts and model embedding/output/forward/attention excerpts. No whole
  application execution or original GPU/Apex experiment was reproduced.
- PyTorch original CPU Lerp/Lerp.h, Pointwise addcmul/addcdiv, mul/div and
  adjacent loop dispatch excerpts inspected at the immutable revision above;
  not the whole compiled library/vector ISA or a full software proof. Local
  package files were READ, without importing/executing Torch before this
  protocol. Retrieval manifests retain exact scopes/hashes.
- Web gzip fetch reported unsupported content type; direct urllib retrieval
  succeeded. An uppercase README read failed2; the actual lowercase readme
  was subsequently read. These were reader failures, not scientific runs.
