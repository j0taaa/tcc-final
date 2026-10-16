# V4 — Bounded real-consumer resource screen, before implementation/heads

2026-10-16. This is DEVELOPMENT/resource validation, not a timing, quality,
training or independent-confirmation campaign. V1/V2/V3 proofs/oracles remain
separate. No novelty is claimed for a JSON-number automaton, class reductions,
frozen-backbone planning or the mathematical conditional-mean identities.

## Concrete operation and eight criteria

1. Use: a typed numeric-answer API for externally authored arithmetic questions,
   producing a JSON object with one numeric field named answer, followed by true
   EOT and PAD. The eventual consumer is training/auditing a grammar-conditioned
   dLLM release planner, not JSON validity alone. This small screen tests only
   that the full original-token proposal/actions/scores fit a real model pipeline.
2. Difference: V3's exact observed-action score collapses hidden proposal IDs and
   an auxiliary anchor while preserving the CURRENT grammatical proposal. The
   mathematical mechanisms are classical. Sufficient own originality and a
   useful measured consequence are still OPEN; a new training decoder cannot
   be justified merely by passing this resource screen.
3. Choice: possible gradient variance reduction without another neural forward.
   Full-triple and known-anchor intermediate scores are valid controls of the
   SAME policy, not biased straw men. Fixed-anchor and position-only gates have
   cheaper analytic specializations. No actual cost/variance gain is assumed.
4. Proof: V3 supplies law/progress/score/chain/count results. The byte lexer/DFA,
   token-effect classes and positive inside/outside used in this screen are
   classical implementations. They must preserve original IDs, including aliases
   and every defined empty emission. V3 does not prove a rounded GPU sampler law.
5. Experiment: frozen8 known-development questions, one checkpoint, one config,
   at most9 REAL model forwards (one warmup plus8 recorded initial states), four
   joint samples per recorded state. No answer label is inspected by the runner.
   No tuning, training update or later rollout is authorized by this resource
   protocol; those require their own justified complete-cost/quality protocol.
6. Cost: record source/model/tokenizer/runtime, full-V input/softmax, compiler
   sizes, original-V class/gate reductions, proposals, all score paths, transfers,
   memory and raw output. Resource elapsed times are diagnostic ONLY. Any later
   competitive comparison must pay all model/gradient/setup work for all methods.
7. Objections: classical evidence inference implements the same collapse; simpler
   masks, one-shot joint generation, native confidence/PL policies, optimized
   baselines or more iid data may be better. Raw confidence need not be semantic
   reliability, and the small checkpoint may perform poorly. No quality inference
   follows from validity. A regular schema does not validate arbitrary recursion.
8. Article gap: distinct contribution/antecedent audit, useful complete-cost
   variance, actual parameter updates, strong behavioral controls and independent
   confirmation. No publication/master's admission, human review or achieved
   goal is asserted. Only this bounded resource program is justified next.

## Frozen inputs and model

Use ALL first8 train selections from A32's earlier question-only input manifest,
copied independently into consumer-inputs-v4.json, with the original file hash.
These inputs/old application outcomes are KNOWN development, not new independent
evidence and not reopening A32's rejected coupling application. Source GSM8K:
openai/grade-school-math3101c7d5072418e28b9008a6636bde82a006892c.
The source data contains labels; the copied manifest contains ONLY questions.
No claim that nobody previously downloaded or saw those labels is made.

Checkpoint: dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1, revision
c8d24a3f4adaeef46881b450e1bf7d1005203bd7. Its official card declares Apache2.
The complete7184-byte modeling_qwen3.py was read before execution, SHA256
624175f036b6552db473e911e5ec57a09d518c7241b11bc375a7b4bf558675ce.
It replaces causal masking by a padding-only bidirectional mask, registers
custom Auto classes and leaves a conversion script behind an unexecuted main
guard. Force evaluation mode, no KV cache and SDPA attention; inspect/pin a
compatible Transformers runtime before loading. Existing .venv-live4.52.2 is
older than the checkpoint's declared4.57.0 and must remain unchanged.

Chat template uses enable_thinking=False per the author card. User message:

    Solve the following problem. Return only a JSON object with one field
    named "answer", whose value is a JSON number.
    Problem: {question}

Batch1, response canvas32 masks, prompt limit1024 tokens, temperature1, no
classifier-free guidance or gold-derived candidate list. Model output is
BF16; crop only the last32 requested positions via a verified model API,
then compute full-V softmax/confidence in float64. No head is executed before
the runner/source/protocol commits are frozen. Every attempted/completed
forward, including warmup and failures, is counted.

## Original IDs and language

The model has151936 output logits, tokenizer length151670, ordinary BPE
IDs0..151642, added IDs151643..151669, EOT151645, PAD151643 and MASK151669.
Do NOT crop logits to len(tokenizer). A read-only local tokenizer check found
empty decoding for151670 and151935; verify ALL266 undefined IDs before capture.
If every one decodes empty with skip_special_tokens=False and cleanup=False,
retain EACH as its own epsilon-emitting original ID before EOT. Otherwise
REFUSE before heads and document a separate revised contract; do not invent
an empty/invalid meaning after observing model outputs.

Ordinary IDs use the pinned byte-level BPE inverse. Verify its ASCII emission
against the actual tokenizer; non-ASCII bytes cannot belong to this ASCII
schema. Added IDs retain their literal spellings except explicit EOT/PAD
control roles. The language is optional JSON whitespace, object with the exact
key answer, colon, an unrestricted JSON number (sign/integer/fraction/exponent),
closing brace, optional whitespace, EOT, then zero or more PAD ORIGINAL IDs.
No gold number/catalog, arbitrary output truncation or silent epsilon-ID removal.
Every sampled fixed/original ID and true termination must survive reconstruction.

Token classes are equality of effects on ALL byte-DFA states, with original-ID
membership retained. Class mass/gate mass are sums over ALL original IDs;
never substitute a representative confidence/gate. This is a classical
finite-automaton compiler and quotient, not a new theorem or advantage claim.

## Fixed sampler/readout, checks and budgets

Only V3 with uniform anchor over all32 active positions and
g[i,v]=c[i,v]/(c[i,v]+1/100), where c is the FULL-V original model probability.
No learned planner or optimized hyperparameter in this screen. Use one fixed
seed52040 and per-case/per-draw derived integer seeds recorded with all IDs.
Four full (X,A,B) draws per head,32 draws total. Compute full-triple,
known-anchor conditional and fully collapsed scores on those SAME draws.
Validate fixed-anchor and position-only branches on toy/head readouts as
analytic controls; no competitive speed/quality gate is evaluated here.

Before real heads: verify the floating adapter against independent rational
small laws, both score adjoints/anchor probabilities, aliases/fixed IDs/EOT/PAD
and original-V class reductions. Floating GPU operations are an APPROXIMATION
to the smooth mathematical law; finite numerical checks are not a proof of the
native RNG distribution. Record precision, directed/ordinary operations and
maximum error honestly; do not import A51's exactness claims without its source
and all premises. Preserve every failure/draft separately.

For real rows: check all outputs using independent json.loads plus exact
numeric-type/key/termination/ID checks; compare observed-action log mass to a
separate NumPy float64 forward reference (absolute log discrepancy<=1e-7).
Check projected gate/anchor scores against the independent CPU calculation
(absolute1e-10 plus relative1e-7). Resource refusals stay cases. Prior toy rational
oracles establish the algebra; two floating implementations do not establish
an exact real-head probability certificate.

Caps:32 response slots,1024 prompt tokens,2,000,000 symbolic arcs,
2GiB sampler workspace,60 seconds compile/query operation and20 minutes
whole screen excluding model download. A cap failure is RESOURCE_REFUSAL,
not zero posterior mass. Six of8 complete correct cases are necessary merely
to consider a separately frozen cost/variance probe; never a useful-effect gate.
No test/installation/other model workload overlaps capture. Store ALL statuses,
BF16 logit bits, prompt IDs, token-byte/effect provenance, source hashes,
confidence/gate config, random seeds, original outputs and numerical checks.
Large arrays may use separate immutable packets, not be silently omitted.

The later cost/variance/training branches remain UNTRIGGERED. This resource
protocol alone cannot justify new quality labels, additional seeds, model
updates, claims of speed, sufficient novelty or goal completion.
