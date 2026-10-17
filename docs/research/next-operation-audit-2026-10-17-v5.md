# Structural consumers and the actual deferred-Adam operation

2026-10-17. Original papers/source inspected AFTER V4. This is a read-only
operation/antecedent audit and written necessary-condition analysis. No A70,
new scientific producer, model, forward, training, data row or timing. Prior
attempts and negative gates are unchanged; the positive user goal stays OPEN.

## 1. Tree editing already has grammar-preserving diffusion

Kapur/Jenner/Russell's FINAL ICLR2025 paper, *Diffusion On Syntax Trees For
Program Synthesis*, already corrupts programs by replacing small subtrees
with grammar-valid programs of the same nonterminal. Candidate nodes satisfy
their primitive-count restriction; the replacement sampler is constrained.
Thus grammar/typed subtree mutation alone is not an own contribution.

Their neural policy autoregressively emits an edit position and replacement.
It is not the native parallel token decoder of MDLM/LLaDA. Training also
recomputes a direct path from the corrupted tree toward the target: AppendixE
explicitly does NOT require that path to be optimal. Do not describe these
labels as the exact reverse trace or an optimal tree-edit oracle. This audit
did not train/reproduce their model or inspect their implementation beyond
the publicly indexed README description.

Parent-first frontier generation, disjoint-subtree scheduling and classical
tree contraction are not selected as own mechanisms. A parent-first frontier
can require linear depth on a chain. Invoking tree contraction without its
context representation, model contract and complete cost does not establish
a new logarithmic neural decoder.

## 2. A real hierarchical typed-JSON consumer, including original code

Ghiglino etal's FINAL ICML2026 *“Do Diffusion Models Dream of Electric
Planes?” Discrete and Continuous Simulation-Based Inference for Aircraft
Design* uses
hierarchical designs with topology-dependent continuous fields and observed
performance metrics. The paper already separates topology generation from
conditional continuous diffusion. Its reported representation has144
topologies, up to126 continuous parameters and10 observed quantities,
flattened to at most136 positions. These are AUTHOR-REPORTED facts, not
measurements of this repository.

The public implementation is pinned at
SRI-CSL/mixed-masked-diffusion@490ad6acdb46d94a4f240e686ed392ab1e9367fb.
The file manifest is preserved at
`../artifacts/raw/structural-operation-audit-v5/planes-manifest.json`.
Retrieval is not execution; no JAX/Flax/Optax package was installed or run.

The actual model distinguishes two masks:

- Absent topology coordinates have their attention edges removed by the
  outer product of the topology mask with itself.
- Observed PRESENT coordinates remain model inputs. The condition indicator
  is an embedded input feature, not permission to discard those coordinates.

The value, original node-ID and condition embeddings are concatenated. A
packing control must preserve original IDs and restrict the original edge
matrix; renumbering IDs or dropping all non-predicted fields changes inputs.
The inspected Transformer uses tokenwise normalization/MLPs and attention,
so induced-subgraph packing is a plausible CLASSICAL padding-removal control.
It is not a new typed-diffusion mechanism.

There is also a numerical boundary: the source replaces masked attention
logits by finite -1e30, not negative infinity. A hard-mask real-arithmetic
equivalence proof is therefore not automatically a proof of this literal
implementation. All-false query rows, exponential underflow, reduction order,
changed GEMM shape and random streams require a separate contract. No
bitwise pruning equivalence or source bug is claimed here. Official PyTorch
2.14 MHA documentation already describes avoiding padded positions with
NestedTensor under its listed inference restrictions; that is an antecedent,
not a JAX-training drop-in or a measured control.

The dataset is PUBLIC, not missing: Zenodo10.5281/zenodo.18763654 lists
training_data.zip,1464507452 bytes, MD5 b18abff1ee1a3fe98a0856df9c28ad4e.
Only record metadata was inspected. No ZIP, checkpoint, array or row was
downloaded. Neither data availability nor a smaller representation proves
that an own useful improvement exists.

## 3. The actual zero-loss event and a prospective necessity bound

Unlike the A58 CE/semantic loss rejected in V3, this consumer's ACTUAL
`denoising_eps_matching_loss` masks squared noise error, divides by
max(1, number of unmasked coordinates), and averages over the batch.
Under finite-valued mathematical execution, a row with no active unobserved
coordinate has identically zero loss and parameter gradient. A58's different
objective is not a counterexample to this fact.

Deleting such rows must still divide their surviving loss sum by the ORIGINAL
batch size B. It also must preserve any model-state/RNG effects. A whole zero
gradient batch does not justify skipping Adam, weight decay, EMA, learning
rate schedule or step counters. Those state changes can be nonzero.

The actual mask generator chooses ONE mode for the batch, uniformly from
joint/posterior/likelihood/Bernoulli(.3)/Bernoulli(.7). In a random mode it
resets a row to ALL FALSE if all T condition bits were true. Suppose a row
has S>=1 topology-active coordinates. In the IDEAL independent Bernoulli(r)
contract, its zero-prediction probability AFTER that reset is exactly

    r^S-r^T.                                                 (1)

Proof: all S active bits must be conditioned, probability r^S, except that
the all-T-conditioned subevent, probability r^T, is reset and predicts again.
For S=T the event is impossible, as the guard requires. Under the additional
premise that EACH of the three fixed modes leaves an active predicted field,

    E[zero-row fraction] <= (.3^S_min+.7^S_min)/5,             (2)
    Pr[entire B-row batch zero]
        <= (.3^(sum_j S_j)+.7^(sum_j S_j))/5.                 (3)

The selector is common to the batch, so multiplying unconditional per-row
probabilities would be wrong. Formula3 conditions on the random-mode choice
before multiplying. If any fixed mode can be empty its probability MUST be
added; this source/dataset premise has not been checked on actual rows.

For S_min>=10 the bound2 is (.3^10+.7^10)/5, about0.5651 percent. This is
ONLY a conditional mathematical bound, not an empirical dataset statistic,
forward-time saving or audit of JAX's native finite PRNG law. The paper's10
observations motivate checking that premise; they do not establish it on
the uninspected dataset/index mapping. There is no basis to start a large
training campaign from this zero-row shortcut.

## 4. The optimizer issue leads to a genuine external consumer

Official PyTorch SparseAdam documentation explicitly says that it masks
parameter AND moment updates of unmaterialized gradients and approximates
Adam. Official Keras2 Adam documentation instead specifies applying momentum
decay/updates to unused slices to match its dense semantics; it also warns
that epsilon placement depends on the Adam formulation. TensorFlow2.16.1
TPU embedding Adam exposes lazy_adam=False for applying zero-gradient
updates to unlooked-up rows. Thus the distinction has a real API contract;
it is not merely the difference between two names for one optimizer.

More directly, the original ASPLOS2026 GS-Scale paper ALREADY defers Adam
updates in large-scale 3D Gaussian Splatting. It stores non-geometric
parameters/optimizer state on the host, reconstructs them before use, and
uses an approximate factorization involving epsilon. Section4.3 derives
it; Section5.5 discloses and evaluates that approximation. It is NOT our
invention, nor an undisclosed exactness error in a claimed exact theorem.

The authors' default epsilon is1e-15 and beta2=.999; their experiments also
include larger epsilon/beta2. Their rendering tables are THEIRS, not rerun
here. Do not select an artificially large epsilon, assert a semantic failure
from a scalar error bound, or compare only against eager dense updates.

Pinned source SNU-ARC/GS-Scale@6471e958f7e318f4870234d8107e0aa91c2d6932
confirms the deferred host reconstruction in `cpu_adam/src/cpu_adam.cpp`:
`adam_deferred_update` precomputes16 delay entries, decays moments, restores
the parameter with `correction*m_prev/(sqrt(v_prev)+eps)`, and applies the
current gradient's bias-corrected update. `calculate_update_ids` includes
counter==15 rows; `update_counter` scans/increments all row counters.
The host code also sets flush-to-zero/denormals-to-zero. None was compiled,
imported or executed here. The manifest is
`../artifacts/raw/structural-operation-audit-v5/gs-scale-manifest.json`.

Removing that delay cap or using timestamps/queues alone is not selected as
own science. A competent lazy control can use those ordinary data structures,
stable block sums and a certified small tail; it must receive them too.

## 5. Written reduction: the epsilon-preserving query, not a new algorithm

Fix ONE scalar coordinate, actual zero gradients for h consecutive optimizer
steps AFTER s, 0<beta1,beta2<1, nonnegative learning rates eta_j, epsilon>0.
There is a tensor of zero gradients at each step, not `.grad=None` with its
different step/decay semantics. Use Adam Algorithm1's epsilon OUTSIDE the
square root of bias-corrected variance; other formulations need another
derivation. Define q=sqrt(beta2), x=sqrt(v_s)>0, and

    c_j=sqrt(1-beta2^(s+j))*q^(-j),
    A_j=eta_j*(beta1/q)^j*sqrt(1-beta2^(s+j))
                         /(1-beta1^(s+j)),    j=1,...,h.

Then the exact mathematical drift and moment states are

    D=m_s sum_j A_j/(x+epsilon*c_j),
    theta_(s+h)=theta_s-D,
    m_(s+h)=beta1^h m_s,   v_(s+h)=beta2^h v_s.               (4)

This follows by substituting the decayed moments in each Adam step and
dividing its denominator by q^j/sqrt(1-beta2^(s+j)). The c_j are increasing:
c_j^2=beta2^(-j)-beta2^s. Zero initial moment/variance implies zero drift;
an arbitrary inconsistent checkpoint with v_s=0,m_s!=0 needs separate
admission. Formula4 is not a theorem about native rounded/flush-to-zero
recurrences, about gradients at changed future model states, or training
quality. Bias correction and the zero-gradient run's schedule are retained.

The scalar sum is an ordinary positive Stieltjes/Cauchy-kernel query. For
C=sum_j A_j and c_min/max over the run, a CLASSICAL constant-query bound is

    C/(x+epsilon*c_max) <= |D/m_s|
                        <= C/(x+epsilon*c_min).              (5)

For m_s=0 return zero; the displayed ratio otherwise cancels its sign.
The GS-Scale-style frozen-denominator approximation in this convention is
D_g=m_s*C/(x+epsilon). A direct written error certificate is

    |D-D_g| <= |m_s|*C*epsilon*max_j|c_j-1|
                /[(x+epsilon)*(x+epsilon*c_min)].             (6)

Subtract individual reciprocal denominators and use positive A_j to prove6.
Large gaps can make5/6 loose even though the late momentum tail is tiny.
For the non-bias-corrected constant-rate case with beta1/q<1, a competent
control can sum a head and bound the remaining absolute drift geometrically;
its work need not grow with the full gap. An epsilon=0 geometric estimate,
when its error is certified small, is another mandatory control. Comparing
only with a literal h-step loop would manufacture the asymptotic benefit.

More generally, positive kernel sums already admit standard block/series
approximation. In a pole block b_j=epsilon*c_j in [B/2,B], put
u_j=(B-b_j)/(x+B), so 0<=u_j<=1/2, and expand

    1/(x+b_j)=(1/(x+B))*sum_(k=0)^(P-1) u_j^k + remainder.

The positive omitted fraction is u_j^P<=2^-P of the exact term. Weighted
block moments therefore supply a classical relative-error bound. This is
ordinary geometric-series/moment compression, not own FMM, quadrature or
numerical analysis. Precomputing moments and answering ranges still costs
work/storage/precision. It is a strong analytical control for any eventual
optimizer-specific candidate, not an implemented new sampler/optimizer.

AdamW would additionally require the product of all intervening decay
factors and their weights inside4. Global parameter coupling (e.g. trust
ratios), per-step EMA overwrites, changing betas, clipping/status, checkpoint
export, model/RNG state and parameter-dependent learning rates cannot be
silently omitted. Exact rational powers can have output bit length linear
in the gap; a few real-arithmetic operations are not a constant bit-runtime
proof. No certified native numerical engine or bit complexity theorem was
implemented/established in this audit.

## 6. Eight-criterion decision before an implementation

1. Real use: typed-JSON aircraft diffusion is real, and GS-Scale supplies a
   particularly concrete sparse zero-gradient optimizer consumer. The latter
   is a DIFFERENT justified TCC scope, not a demonstrated dLLM/CFG application.
2. Own difference: grammar-valid tree mutation, topology-aware fields,
   padding removal, generic lazy Adam and positive-kernel compression already
   have competent antecedents. Equations4--6 alone do not establish sufficient
   own novelty. A useful epsilon-preserving implementation remains a question.
3. Choice: relevant operation would be certified reconstruction at declared
   precision, full cost and real native schedules/states. No such practical
   advantage or unserved demand for a specified certificate is measured yet.
4. Proof: 1--6 are self-contained WRITTEN identities/bounds, not mechanical
   verification, a new numerical engine, or proof of final trained quality.
5. Experiments: no large prototype/campaign selected. Before any timing,
   freeze the exact epsilon/step/rounding contract, independent oracle,
   real input selection, competent controls and complete-cost gate.
6. Full cost: projection/backbone/RNG/state/mean normalization for diffusion;
   table scans, timestamp/cache preparation, bias correction, optimizer/EMA,
   copies, rounding/bit precision and final materialization for lazy updates.
   Fixed-gradient replay would not validate an entire changed training path.
7. Fatal controls: existing TreeDiff/MaskeDiT, classical packing, GS-Scale,
   unlimited lazy timestamps, geometric tail/epsilon-small controls, the
   same positive-kernel/block certificates and vectorized/fused updates.
   An equally cheap classical bound can erase a proposed certification edge.
8. Article gap: identify a specific useful consequence beyond that composition,
   audit its closest originals and prove/validate complete cost at relevant
   inputs. Human review, priority and publication remain unconfirmed.

Decision: do NOT open A70 for generic typed-tree generation, row packing,
zero-row skipping, or basic deferred Adam. Preserve the newly identified
epsilon-preserving reconstruction OPERATION and its strong controls as a
lead. The next substantive step requires a sufficiently distinct practical
consequence or another real operation; it must not begin a campaign merely
because4 is correct. This is progress toward the goal, not its fulfillment.

## 7. Primary-source scope and hashes

All paper bytes were retrieved as read-only evidence, extracted with
pdftotext, and inspected in the following LIMITED scopes. Papers/source were
not executed. Source files are represented by immutable URLs and metadata
manifests; full third-party source/checkpoints/PDFs are not copied here.

- TreeDiff FINAL ICLR2025 original:
  https://proceedings.iclr.cc/paper_files/paper/2025/file/666dd0d92a64396e753c691db93493d4-Paper-Conference.pdf
  5910793 bytes, SHA256
  83ef71df17e342f9f3fb5f2d1e7237639fd101b241c8770609258bac185adf4e.
  Read Sections3.1/3.2.1/3.2.2/3.3/3.4, beginning4.1, AppendixE/Algorithm1.
  Earlier HTML2405.20519v1 is distinct from this final. Not all experiments,
  appendix/proofs or original implementation. Code lead:
  https://github.com/revalo/tree-diffusion .
- Aircraft FINAL ICML2026 publication:
  https://proceedings.mlr.press/v306/ghiglino26a.html ; actual PDF:
  https://raw.githubusercontent.com/mlresearch/v306/main/assets/ghiglino26a/ghiglino26a.pdf
  17336832 bytes, SHA256
  89f9d5f5c755b1325f7d20ba764914106ee57109b9dea3330323000acec48394.
  Read Section3 representation/preprocessing/dataset/notation and Section4.3
  architecture/masking/training, not full experiments/simulation/appendices.
  An EARLIER author PDF was read first, Sections3/4.2/4.3 relevant paragraphs:
  https://adamcobb.github.io/documents/ghiglino_diffusion_2026.pdf ;26583625
  bytes, SHA256
  711addb9f1d89c33a037ca7d54c3a28e8e6a9a40401a888493f5f43884af36bb.
  Do not relabel the author PDF as the final publication.
- Aircraft original source, immutable revision above:
  https://github.com/SRI-CSL/mixed-masked-diffusion/tree/490ad6acdb46d94a4f240e686ed392ab1e9367fb
  Ten files retrieved including LICENSE (CC-BY-NC-SA4.0). Read full Simformer,
  Transformer and attention files, indices helper, eps loss and adjacent DSM,
  relevant diffusion_mask mask/loss/train/sample sections and README links.
  dataset.py/discrete_encoding.py retrieved but NOT read/audited. No whole
  package/dataset/checkpoint validation. Zenodo record metadata only:
  https://zenodo.org/records/18763654 .
- Official padding-removal antecedent, fastpath conditions/NestedTensor
  paragraph only:
  https://docs.pytorch.org/docs/2.14/generated/torch.nn.MultiheadAttention.html .
  No PyTorch2.14 installation, JAX replacement or timing.
- Official optimizer contract paragraphs/API only:
  https://docs.pytorch.org/docs/stable/generated/torch.optim.SparseAdam.html
  (rendered PyTorch2.14), https://keras.io/2/api/optimizers/adam/ ,
  https://www.tensorflow.org/api_docs/python/tf/tpu/experimental/embedding/Adam
  (TensorFlow2.16.1). No library execution or audit of their complete kernels.
  TensorFlow Recommenders embedding quick-start was inspected as a consumer
  lead; its displayed MovieLens example uses Adagrad, NOT evidence of an
  Adam training run: https://www.tensorflow.org/recommenders/examples/tpu_embedding_layer .
- GS-Scale ORIGINAL author-hosted ASPLOS2026 final:
  https://99dhl.github.io/assets/pdf/asplos26_gsscale.pdf ;3986912 bytes,
  SHA256
  6d437cd04eaa50a34fe9a8436c71a8871b6a800df829492409f8fbb1bb2f1dd9.
  Read Section4.3/4.3.1/4.3.2, displayed Figure10, adjacent integration text
  and Section5.5/Table4. Not full evaluation/appendix or reproduction.
  Initial retrieval command `python` failed127 BEFORE download because that
  command is absent; corrected `python3` fetch/extraction completed0. This
  was a reader-environment failure, not a failed scientific run.
  Original source:
  https://github.com/SNU-ARC/GS-Scale/tree/6471e958f7e318f4870234d8107e0aa91c2d6932
  Five files retrieved including MIT LICENSE. Read deferred host update,
  update-ID/counter functions and SelectiveAdam wrapper; original CPU header
  retrieved but not audited, remaining CPU/CUDA/training source not audited.

Searches for exact/lazy/deferred/epsilon-preserving Adam did not establish
absence of prior art. GS-Scale was found during this audit and is mandatory;
secondary summaries/search snippets are leads, not priority certificates.
