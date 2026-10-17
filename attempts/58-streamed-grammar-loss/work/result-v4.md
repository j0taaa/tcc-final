# V4 — Full synthetic arithmetic preflight passes; usefulness unmeasured

2026-10-16. This is a correctness/implementation result, NOT the user's goal.
The own candidate is a systems execution specialization. No new semantic loss,
class quotient, CRF derivative, monoidal backward or CCE principle is claimed.

## Written before implementation and actual source

V1 c271080a1eb47ddf7595fd683f5d984c9cb7f0fe specifies the eight criteria,
forward statistics, variable-EOS occupancy correction and full head chain.
Primary-controlsdfcb112 precedes the CPU prototype6ef8f37. The independent
GPU protocol is de762b08ef884af02cff632a230fc3bee787f1f9, BEFORE kernels.
Initial executed GPU source8fea71fe2a5844ad92dcee8f4ffe7ce035b7fe07 is committed
and its exact file hashes are in gpu-v3-initial/config.json.

Two distinct failures remain preserved:

* CPU structural-zero fixture at6ef8f37: finite loss but4 H/4 W/2 bias
  nonfinite gradient entries. V3's safe normalization fixes this boundary;
  it is not retroactively attributed to V2.
* Initial GPU packet: all24 candidate/dense/checkpoint method-fixtures pass;
  ALL8 CCE cases ERROR before execution because packaging is absent. Overall
  status remains ERROR. No absent control gives a candidate win.

V4's BEFORE-replay runtime addendumd883e12 pins packaging25.0. The separate
full replay producer is fc224fa, whose full hash is in its config. Kernel,
inputs, tolerance and controls are unchanged; the runner only adds package
version metadata. No CCE vendor source was edited. The official library is
pinned3de376c106a1916bc5e1b619f9c77c87a461ee1c, filtering disabled, direct LSE
adjoints, IEEE FP32, original-ID class slices, full dH/dW/bias.

## Actual validation

Six CPU oracles PASS0.873s. Exact scalar dual enumeration independently
checks252 logit derivatives, while another252 loss/mass/full-head coefficients
compare original-ID JSON enumeration with class inference. Four panel widths
and arbitrary signed/nonlinear class adjoints check full H/W/bias gradients;
maximum FP64 CPU error1.7763568394002505e-15. EOS/future fixed IDs/empty aliases,
zero supports, row-shift invariance and explicit wrong-occupancy/filtering
counterexamples are included. Full321 maintained tests PASS88.353s. Earlier
five-test/320-test logs remain literal and separate.

The new GPU replay is COMPLETE32/32 PASS,380752 scalar comparisons and4/4
explicit refusals. EACH of candidate/dense32/checkpoint/CCE passes8/8 and95188
comparisons against dense FP64 over the same original FP32 inputs. Maximum
absolute errors are respectively1.183711e-6,7.236376e-7,1.047158e-6,1.449135e-6;
the frozen elementwise abs+relative tolerance is unchanged. Structural-zero
outputs stay -inf and have finite zero derivative contributions. The all-unique
class fixture is retained; it has no claimed summary-memory advantage.

The AFTER-data input-identity audit verifies ALL8 replay NPZs are literally
byte-identical to the first packet, in addition to every input array matching.
Python/NumPy/Torch CPU/CUDA RNG, matmul precision and thread settings are restored.
Runtime: RTX3080Ti, Torch2.13.0+cu130, Triton3.7.1, CUDA13.0, packaging25.0.
Actual device/runtime fields in raw config take precedence over this prose.

There were ZERO model parameter/hidden-state/head readouts, model forwards,
optimizer updates or new semantic labels. The matrices are explicitly
SYNTHETIC. Internal library compilation/autotuning is not a competitive
timing study. No head-only or whole-training memory/latency benefit was measured.

## What must happen before useful systems claims

Both checkpointed projection and class-wise CCE can MATCH the asymptotic
activation workspace. The current original-order CCE correctness adapter
gathers submatrices and lets generic autograd scatter them; that is NOT yet
the strongest performance control. A future benchmark MUST include:

* cached metadata for ALL methods, not rebuilding class ID lists each call;
* permanent class-sorted classifier layout with original-ID input/target/output
  maps and equally permuted tied embeddings/optimizer state when applicable;
  static classes cannot justify charging that copy on every training step;
* direct assembly of disjoint class gradients without C full-V zero scatters,
  and batched small/singleton-class GEMMs plus CCE on large classes;
* the same grammar objective/inference and all graph/normalizer/optimizer/
  backbone costs, actual feasible batch sizes, cold/warm preparation and
  meaningful applicable precision alternatives.

The current candidate also pads small classes to32, uses a max-width merge
for each class and separately scans inputs for validity. Those costs must
not disappear from reports. With many singleton classes there is no N*C
compression. A copied/permuted-weight penalty or a weak200-call control
alone cannot establish a useful own advance.

Next is a separately frozen resource/comparator investigation, not a broad
training/quality campaign. No training launch is triggered by toy arithmetic
PASS alone. The complete MonoidReduce original/source capability still needs
checking; only indexed primary introductory pages were obtained, not its full
proof/implementation. Sufficient systems originality, useful complete-step
benefit, real integration and independent evidence remain OPEN. Do not promote
A58 to the main paper or mark the scientific goal achieved from these checks.
