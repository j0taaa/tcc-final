# V7 — Frozen development resource screen, BEFORE ANY competitive timing

2026-10-16. This tests the full finite-domain HEAD PRIMITIVE (class LSE,
indexed target and full H/W/bias VJP). Grammar inference, backbone and optimizer
are NOT executed here. Its result is a resource decision, never whole-training
speed, a new loss, a quality improvement or the achieved user goal.
V1's eight answers and V5/V6 hypotheses/controls remain unchanged.

## Inputs and domain

Use ALL original50258 IDs and ALL194 lexical classes in evidence/metadata-v6/
mapping.json. Record SHA256 and provenance. No vocabulary/support pruning or
favorable class selection. This map was derived from vocabulary.json ONLY,
using independently copied/pinned lexer sources; no numerical head was opened.
Use hiddenD768 from the pinned public MDLM config, not loaded model parameters.
The eight N values are16,32,64,128,256,512,1024,2048, all retained.

H/W/b and signed class/target adjoints are SYNTHETIC. One local CPU Torch
generator seed585700 supplies W[V,768] and bias[V] as0.02*randn. For each N,
local seed585700+N supplies H[N,768]=0.2*randn, original targets=randint(V),
dz[N,C]=randn/sqrt(N),dt[N]=randn/sqrt(N). Pin Torch/NumPy versions and each
tensor's byte hash so exact inputs can be reconstructed. Weights are shared
across N/methods; repetitions are timing repetitions, not independent datasets.
No model read/forward/update, label or gold-based selection.

FP32 IEEE/highest precision and ALL filtering disabled. Validate finite inputs
once before their repeated IMMUTABLE calls. Targets, metadata and zero-support
pattern are immutable. Controls may hoist their nonfinite-class check into
the same cold preparation; the candidate finite-domain entry point is allowed
only under the explicit V6 precondition. This does not preserve/refute V3's
guarded invalid-input API. Later changing-parameter training needs its own
common validation policy/cost. No actual optimizer update occurs in this probe.

## Fixed candidate/control families

Candidates: V6 finite-domain tiles16x32,32x64,64x64,64x128, all with reduction32.
No favorable configuration is silently discarded. Every variant must first
pass all eight old V3 arithmetic fixtures at their unchanged tolerance.

Controls: physical layouts/direct assembly from V5, metadata cached:

* dense segmented GEMM/full-gradient control, threshold0;
* CCE thresholds0,8,32,128, native direct LSE adjoints, no filtering;
* checkpointed Torch thresholds0,8,32,128 with panel2048 AND8192.

These are13 configurations. Small classes are batched; large classes get
contiguous physical views. Parameters are kept in their physical layout,
including gradients. Do NOT retain an unnecessary original GPU weight copy
or permute it on every call. Targets remain original IDs through the inverse
map; raw gradient comparisons reverse only for VALIDATION, outside timings.
Cold import/permutation/metadata and first-call preparation are separately
recorded. Input/gradient transfer for validation is excluded equally; outputs
are resident GPU tensors, as a GPU optimizer would consume them.

The measured scalar downstream function is the same linear contraction
sum(dz*z)+sum(dt*target_logits), followed by backward. Its class adjoints can
have either sign. No claim that random adjoints are actual trained grammar
marginals; disabled filtering/fixed execution makes this a primitive screen.

## Correctness before timing at each geometry

Independent dense FP64 original-ID logits/LSE/autodiff provide the scalar,
all class/target outputs and full H/W/bias gradients. A bounded column-stream
FP64 reference is also allowed if it computes the SAME full result and
records its code before execution. All methods use the original FP32 inputs.
Require the previous elementwise5e-5+5e-5*abs(reference) tolerance, finite
gradients and correct original-ID interpretation. Record every discrepancy.
Failure receives NO timing win. No relaxed tolerance after data.

## Repetitions and recorded work

One GPU/process, CPU Torch4 threads with relevant BLAS thread limits set
BEFORE interpreter start; restore in-process RNG/precision/thread state.
Limits:3600s whole,180s per configuration/geometry including initial compile,
8GiB incremental GPU allocated,16GiB CPU RSS. Preserve partial/error/refusal
records. Never charge a timed-out control a fabricated large number.

For EACH method/N: record metadata/layout preparation and first invocation
wall/CPU/GPU allocation separately. Existing compiler cache may be reused;
label first-call observations, NOT fresh-cache compilation comparisons. No
claim of a clean cold advantage from shared cache/order. A later full-cost
native protocol must account for actual startup/amortization independently.

Then run3 unmeasured warmups and3 measured paired repetitions, each consisting
of5 complete forward+scalar+backward calls with gradients reset toNone.
Synchronize the GPU before/after each measured block. Record total wall and
process CPU ns divided by5, plus peak GPU allocated increment INCLUDING full
dW/dH/db and summaries. Persistent W/b/H/targets/adjoints are common inputs,
listed separately. Physical-layout controls have no duplicate resident W.
Do not call incremental activation workspace total model memory.

At each repetition use a fixed hash permutation of method names seeded by
SHA256('a58-v7:N:rep:method'); preserve actual execution order. Collect all
timing repetitions, no best-of-repeat or warmup relabeling. No concurrent GPU
tasks or test suites; record device and source/runtime/library hashes.

## Predeclared feasibility gate and negative-only shortcut

For a candidate/configuration at one N, speed gate requires median paired wall
<=0.8*EVERY applicable completed control median, favorable sign in ALL3 paired
repetitions, and peak incremental GPU allocation<=1.10*the minimum control
peak. A memory alternative requires peak<=0.75*EVERY control peak with wall
<=1.10*the fastest control median. Missing/error controls give NO positive win.
Zero/nonfinite measurements give NO win. Preserve CPU/GPU diagnostics.

At least ONE fixed candidate must meet one of these gates on at least3/8 N
values to justify writing a later native/whole-loss resource protocol. This
is an optimistic development gate, not independent statistical confirmation.
A pass still leaves cold costs, actual grammar/backbone/optimizer, mixed
precision alternatives, useful systems distinction and priority unresolved.
No model campaign or main-paper promotion follows directly from a pass.

First measure ALL four candidates and THREE strong controls: dense, CCE128,
checkpoint128/panel8192. These were chosen by architecture/metadata BEFORE
timing. If even this optimistic subset leaves every candidate fewer than3/8
possible wins, the FULL gate is necessarily false under this frozen resource
rule. Stop the remaining timings, preserve all results and explicitly list
unexecuted controls; do not invent their measurements or call the stop a full
benchmark. If the subset leaves a possible gate, execute ALL remaining
controls on ALL eight N, including unfavorable cases, then apply the original
rule. This shortcut can only reject, never award a win.

If the gate fails, no native training campaign is triggered for this simple
layout/kernel family. This is not a theorem that every future implementation,
precision/context or training objective is useless; any later direction must
have a substantive new distinction and separate frozen protocol. Never
relax this gate or relabel old timings after observing the data.
