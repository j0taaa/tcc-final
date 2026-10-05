# Falsification protocol for the probability-certificate contribution

## Decision before measurements

This audit addresses the user's request for certainty of valid, relevant gain.
Mathematical implications are proved under explicit hypotheses. Tests can find
counterexamples and validate implementations on a recorded set; they cannot
establish universal relevance, world novelty, semantic quality or fastest
decoding. Passing correctness is not passing the practical-benefit hypothesis.

Keep the ordinary MWPC/budgeted objectives and all historical negative EPIC
results unchanged. The new study concerns frozen mean-field predictions at one
MDLM step, conditioned on a byte CFG and ABSENT EOS, not an end-to-end language
model joint. Recursions/ambiguity are grammar properties; finite token slots
still impose a length bound. Model outputs cannot be relabeled synthetic and
constructed distributions cannot be relabeled real model results.

## Correctness gates

Use independently recognized byte languages, complete original-token products,
exact rational probabilities and recorded seeds. Audit partial and exhaustive
partitions, represented/full envelopes, all recorded event bounds, original
token aliases, grammar ambiguity, probability reweighting and exact integer
categorical sampling. The membership controls must not call the CFG optimizer
or its independent certificate validator. Include truncation counterexamples,
rare valid events and valid/invalid cases. An exact streaming-array reference
is separately checked against Python JSON parsing and original-token brute
force before any model performance claim.

## Same-input practical study

Freeze `configs/experiments/m31_probability_scaling_cpu_v1.json` before new
forwards. Use all six recursive-array prefixes crossed with 4, 8 and 16 free
token slots: 18 fresh official CPU MDLM predictions. Three prefixes use the
one-child recursive array schema; three use arrays containing any number of
arrays, including nested ones. These are controlled syntax applications and
scaling probes, not held-out production requests or semantic benchmarks.
The second schema is broader than M30. No probe may be selected by success.

Retain every full-vocabulary logit/probability row. Support contains every
token emitting only the grammar's terminal alphabet, plus model top-eight.
Original retained probabilities are never renormalized. Independent alphabet
coverage must establish that no valid full-vocabulary token path is omitted.
Report the conservative generic bound too, using the same returned partition.

Full logit matrices are retained in the ignored local results directory, not
committed as large traces. The versioned audit archive contains complete
tokenizer semantics, original retained rational probabilities, canvas/config,
full-row normalization and SHA-256 lineage to those matrices, every job/status
and every returned proof. Its mathematical/derived-result audit is offline;
checking the network logits additionally requires the local capture or a fresh
opt-in model run. This data-availability boundary must appear in the report.

The independent exact reference runs weighted forward/backward transfer over
streaming JSON-array counter states and original token emissions. For this
restricted schema, parent frames always resume after a completed child, so
depth plus the top-frame phase suffices; finite slots/token lengths make the
reachable state set finite. Sum *token* path probabilities, not parse counts.
This is a deliberately strong exact control using established inference, not
an execution of the published Dang--Ermon or FactorDLM implementations. Do not
infer rankings against those systems or CARS from its runtime.

For each canvas evaluate call limits 8 and 64 at full-scope TV tolerance 1/20.
Each partition job has a 30-second external process deadline including proof
construction/internal checking, and 2 GiB worker address-space limit. An
external timeout has no certificate and is not infeasibility. Record any
worker failure; do not drop it. An independently checked returned partition
must enclose the exact reference mass and its measured true TV. Compute true
TV as 1-L/Z only after independently checking accepted paths and their original
probabilities. The reference does not import the CFG parser/optimizer/checker.

Use three deterministic reference timing repetitions after one warmup; record
each duration, compilation/transition time, forward time, backward time and
sample time separately. Partition results record solve-plus-internal-check and
external check separately. Capture model forward and candidate/input building
separately; model loading is excluded. Runtime numbers are diagnostic per-cell
observations on this CPU, never population guarantees. Peak RSS includes
imported libraries; use a fresh subprocess for each parser job and report this
boundary. All returned samples must pass independent JSON/schema validation.

## Falsifiable verdict criteria

1. A bound violation, invalid accepted/sample path, false coverage, or forged
   proof accepted by the checker blocks practical claims and requires a fix.
2. Successful limited-work admission demonstrates the narrow certified-update
   capability. It does not establish a quality or speed gain.
3. An exact reference with smaller observed total inference cost and zero error
   defeats a practical advantage claim on that cell. Report it explicitly.
4. A refusal or deadline/size failure at larger slots limits scaling claims.
   Do not use a high admitted fraction on small cells to conceal it.
5. Even a positive cell cannot establish world novelty: WMC/conditioning,
   deterministic anytime bounds, GAD, CARS, exact dLLM automaton/factor inference
   and grammar-alphabet filtering remain antecedents already cited in M30.
6. Standalone optimizer-free verification and fail-closed admission are an
   engineering use. Their importance is scoped to users who require that
   interface; it is not evidence that existing exact methods are unreliable.

The final report must state which of these claims survive. No decision criterion
requires our method to win.

## Timing-audit correction after the primary campaign

The complete primary measurement is retained at producing commit `7780d94`.
Its exact controller reference validated alphabet coverage before starting the
reported compilation timer, and its memory boundary differed from the fresh
parser worker. Preserve those original observations; do not compare an omitted
coverage phase as a total reference cost. A separately committed follow-up runs
all 18 exact references on the same original inputs in fresh workers, records
coverage/compile/forward/backward/sample separately and RSS with the same import
boundary, and verifies equality with every original exact mass. No prediction,
partition outcome or case selection is changed. The final report uses these
complete reference costs and records both producing commits.
