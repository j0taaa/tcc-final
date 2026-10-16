# V10 — Competent-backbone stopped consumer, BEFORE implementation/heads

2026-10-16. V5/V8 Tiny-A2D applications remain CLOSED. V9 is a supervised
control with an ordering limitation, not a sufficient basis for training.
This is a separate known-development RESOURCE/SIGNAL screen. A larger model,
constant prefix,64 slots or working JSON are not scientific contributions.

## Eight criteria

1. Operation: a stopped numeric JSON continuation consumed as an API result,
   using the actual original-ID full-vocabulary posterior and V7 visible
   batch-release policy. The eventual research use is a lower-noise reward
   gradient for learning that policy. This screen does not perform learning.
2. Candidate distinction: tractable visible-action likelihood for this
   grammar-conditioned stopped policy, using classical weighted inference.
   PAPL already marginalizes discarded proposals; no new general principle
   or adequate priority is presumed. A useful own application remains OPEN.
3. Possible choice: if real semantic rewards vary, integrating hidden proposals/
   length may improve full-cost gradient estimation without extra reward
   rollouts. Full/anchor/class/length/combined/known-anchor and fitted/zero/
   RLOO controls remain mandatory. V9/cheap supervised CE/grammar-marginal CE,
   PAPL, native confidence/PL and SFT are later behavioral/training alternatives.
4. Proof: V7 policy/score/progress and V8 fixed root feature remain the law.
   A supplied literal prefix means changing the scanner's initial context,
   not changing the suffix probability formula. EOS=PAD is one original ID;
   post-EOS factors integrate1 and do not require a fictitious distinct PAD.
5. First validation: small original-ID suffix/EOS-alias oracles, all original
   tokenizer emissions, compact/manual/autodiff checks and a synthetic full-V
   resource preflight. Only then freeze actual source/runtime before real
   heads. ALL8 old known questions/two trajectories each; no label selection.
6. Costs: full model projection INCLUDING prompt/fixed rows (this checkpoint
   has no indexed-head API), quantized backbone, gathered active original-ID
   rows/transfers, calibration, compiler/proposals/scores/all controls, CPU/
   GPU memory, setup/I/O and refused work. No competitive latency in this screen.
7. Objections: A32 native's known20/32 is another decoder/protocol, NOT evidence
   that the present global grammar posterior works. Prefix conditioning and
   resource/length changes prevent causal quality comparisons with Tiny-A2D.
   Greedy/native/learned simpler methods may win; confidence is not correctness.
8. Gaps: actual signal, complete-cost useful variance/updates, stronger
   behavioral controls, own sufficient originality and independent validation.
   Passing only permits considering a NEW frozen cost/variance design. It
   cannot achieve the scientific user goal or trigger training automatically.

## Model, tokenizer, runtime and exact target

Use existing local GSAI-ML/LLaDA-8B-Instruct, immutable revision
08b83a6feb34df1a6011b80c3c00c7563e963b07. Existing NF4 configuration:4-bit,
double quantization, BF16 compute, eval, no KV cache, four CPU threads.
Pin actual weights/custom sources/runtime BEFORE first forward. Existing
.venv-live metadata currently says Torch2.8.0+cu128, Transformers4.52.2,
tokenizers0.21.4, NumPy2.4.6, bitsandbytes0.50.1, accelerate1.10.1,
safetensors0.8.0. Do not change that shared environment or silently fetch code.
Earlier results are not asserted to use identical installed-library bytes.

This target is defined by the ACTUAL quantized model's recorded returned
head values; no unquantized/equivalent-native-finite-RNG claim. V126464,
true EOT=PAD126081, MASK126336. The tokenizer metadata declares126349 IDs,
0..126348, and115 undefined outputs. All126464 keep separate original IDs.
Declare those undefined IDs as empty byte emissions ONLY if the official
single/concatenation audit confirms it. Otherwise refuse/rewrite before heads;
never silently truncate the vocabulary. No approximate top-k support.

Use ALL eight input-only questions in consumer-inputs-v4.json, whose labels
have already been exposed. The prompt is EXACTLY A32 numeric_task.py's task
instruction, copied immutably rather than importing mutable other attempts:

    Solve the problem and return exactly one JSON object with the key answer
    and its numeric value. No explanation, units, or markdown in the output.
    The JSON prefix is already supplied; continue it without repeating it.
    Problem:
    {question}

The exact spaces/newlines are frozen in the actual question/prompt producer.
Use the official chat template on the user instruction, generation prompt,
then append tokenizer.encode('{"answer":', add_special_tokens=False), as in
that native consumer. Verify the prefix's original IDs/decoded bytes literally.
The literal prefix is external fixed input, not latent sampled/released IDs.

The response canvas has64 MASK/unfixed positions. Its language is the
unrestricted JSON-number/closing-brace/whitespace suffix of that supplied
prefix, followed by the ORIGINAL true EOT. Initialize lexical context after
the prefix (NumericJSON state10); no number/range/gold/length catalog. The
returned API text is literal prefix plus generated bytes through first EOT.
EOS/PAD aliasing is explicitly allowed in the new STOPPED suffix class;
do not modify the old distinct-EOT/PAD full-word classes or old evidence.

Every model call sees the SAME full prompt/prefix+64-slot canvas with fixed
original IDs, all other positions MASK and attention1, including unused suffix
positions after a fixed EOT. Explicit fixed bits determine eligibility, never
the numerical MASK value alone. Native forward projects all positions; record
its full output shape/work, then gather exactly the active response positions
that can occur before the fixed EOT (all64 if absent). Save every such original
BF16 head row plus query positions/input context, including warmup/new roots.
If actual output dtype differs, preserve it and refuse; do not relabel its bits.

## Initial policy and finite-resource contract

Temperature1, initial alpha offsets0, beta1 and anchor logits0. Uniform
anchor is eligible only within the sampled stopped prefix. At each question's
root, compute the V8 expected-release feature ONCE at the default policy:
target min(2,(1+E[T])/2),48 bisections[-64,64], residual<=1e-8 and strict
finite active gates. Keep that SAME feature for all later steps/replicas.
This initializer is declared from the native two-releases/step configuration,
not selected by new gold outcomes. Subsequent expected counts need not be2.
Only release the forced anchor and sampled eligible token-dependent gates.
Never discard a fixed original ID when stopping; at most64 transitions.

Capture one warmup plus eight NEW root heads, shared by the two trajectories
of each known question. Every following canvas receives a new forward; no
cross-trajectory head cache. Worst-case new forward cap1017=1+8+16*63.
Per-step seeds are first8 SHA256 bytes, little endian, ASCII
52100:{case}:{replica}:{step}:joint. Save the first proposal as a paired
one-shot proper stopped baseline, using no further head. It is a functional
comparison, not a quality-win condition.

Caps:64 transitions/trajectory,16 trajectories,1017 new forwards,2GiB tracked
sampler scratch above frozen-model storage (also report process/RSS/total
GPU),2M symbolic arcs,60s each numeric/head operation,300s model setup and
1800s whole screen. Include preparation/timeouts/I/O; no replacement cases.
No parameter updates, seed/temperature search or competitive timings.

Validate EVERY transition against independent manual/Torch differentiation:
log error<=1e-7; alpha/beta/anchor abs1e-10+rel1e-7. Independently check JSON,
literal original-ID commits, first EOT and full-V/tokenizer identities.
Resource condition: both trajectories complete for at least6/8 questions,
zero score-correctness errors and full isolation condition below. Signal:
at least one correct candidate in at least2/8 questions. Attach already-known
labels ONLY after capture closes. No significance/independence claim.

Before capture, require no other GPU compute process. During capture poll
NVML with a line-FLUSHED one-shot query loop (not buffered nvidia-smi -l/-f),
record CPU preparation too, and check occupancy before each neural/score call.
ANY recorded foreign compute PID invalidates whole-capture isolation, prevents
positive credit and stops new neural work; retain all partial outcomes/refusals.
No hidden retry or substitution follows. Five/one-second polling is still
sampling, not a proof against hypothetical sub-poll concurrent jobs. No tests,
installation or unrelated model work are deliberately overlapped with capture.

If resource/signal fails, close THIS declared consumer/initialization without
tuning on its outputs. A failure of the technical screen alone is not a
statistical refutation of all models/policies. If both pass, ONLY consider a
new strong-control complete-cost reward-gradient protocol before any training.
