# M21: frozen controlled repair experiment

Status before execution: protocol and implementation, no reported measurements.
This is the first bounded application of the four-week plan, not completion of
its future real-model campaign. Development diagnostics motivated the opening-
container hypothesis; confirmation uses new values and larger records, not a
claim of unseen error mechanisms or representative model-error frequencies.

## Task and hypothesis

A shared schema accepts an envelope with integer `id` and `payload`, an array of
records with integer `a` and `b`. Values vary independently of the repair methods.
All records have the same key order; the CFG encodes that order and field types,
not the answers. Primary hypothesis: on systematic opening-brace substitutions,
exact repair recovers the original record contents more often than json_repair,
including its schema-guided standard and salvage modes. The same comparison is
reported on every other corruption/control. No success-only denominator.

Pilot: seeds 210100–210103, one/two records. Confirmation: seeds 211000–211019,
three/four records. Every document contributes six cases: valid, all payload object
openers swapped, all payload object closers swapped, payload colons swapped,
missing final delimiter, and a syntactically valid wrong value. The final two
are deliberate capability controls. This is controlled corruption of generated
fictional records, **not observed dLLM errors**. The mix is balanced by design and
cannot estimate deployment prevalence. The small collection shares structural
templates; distinct values do not create independent error mechanisms.

Two separate profiles: UTF-8 byte tokens, and the real cached LLaDA ByteLevel
vocabulary/tokenization (revision 08b83a6feb34df1a6011b80c3c00c7563e963b07).
There is no model inference. No model retry is timed or compared in this study.
A real-model/retry cohort remains future work and is required for that claim.

## Repair contract

Original tokens receive unit weight. Fixed token slots, no EOS/PAD padding,
no insertion/deletion. Only same-byte-length swaps between `{`/`[`, `}`/`]`
and `:`/`,` outside strings are proposed. Original choices remain represented.
BPE alternatives must exist in the actual vocabulary; at most 32 byte combinations
per token are examined in deterministic product order. Every report identifies
its tokenization, rows and pruning policy. Missing alternatives reduce coverage.
An ID byte interval is supplied equally to the methods; exact/greedy/enumeration
freeze every intersecting token. Protecting a subspan can also freeze punctuation
in a multi-byte token, a conservative limitation tested explicitly.

Maximizing sum_i w_i [y_i = d_i] minimizes sum_i w_i [y_i != d_i] because their sum
is constant. This is exact_on_support, not global edit-distance optimality.
Independent existing grammar/certificate validators and Python-vs-Rust/exhaustive
checks remain mandatory. Duplicate-key checks may abstain after CFG optimization;
key uniqueness is not silently treated as a CFG constraint. Inconclusive statuses
have no output/certificate. The API has a cooperative deadline; workers impose a
hard bound on measured calls. The initial CLI offers a broader integer-JSON grammar
(ASCII and escaped strings, whitespace), not arbitrary JSON Schema or floats.

Grammar construction removes only unreachable source nonterminals before CNF:
every symbol in a start derivation is reachable along production bodies, hence
no start derivation uses a removed rule; retained rules are original. Therefore
the complete start language is unchanged. Exhaustive small-language tests check
this optimization. No token support or competitive chart path is pruned by it.

## Comparators and fairness

1. Unchanged input.
2. json_repair 0.63.5 default.
3. The same package with the shared complete schema, standard mode.
4. The same package with that schema, salvage mode.
5. Independent enumeration in increasing substitution count on identical support,
   validated with stdlib JSON plus jsonschema, stopping at the common deadline.
6. Existing order-greedy exact feasibility, with witness reuse and the identical
   grammar/support/weights/locks.
7. Exact MWPC with the same represented input.

Schema-guided json_repair is stronger than a schema-free strawman. Enumeration is
also a strong small-case baseline and may be faster than parsing; report that.
All methods receive the same draft, allowed protected ID and shared schema.
The reference answer is used only by the evaluator, never as a repair input,
proposal, grammar terminal or support alternative. In the fixed-order generated
records, the enumerator's schema language and CFG agree on represented candidates.

Every raw row preserves output, statuses, costs when defined, certificate for exact
or greedy, and success evaluation. A repaired result is successful only when its
strict parsed object equals the original data (object key order ignored, types
preserved); returning a valid empty payload is a failure. The baseline APIs do not
support positional locks, so protected-ID correctness is evaluated uniformly.
Do not compare json_repair's reserialization to token costs: its edit model differs.

## Timing, limits and analysis

Two seconds total per method/input, 2048 MiB worker address space; supervisor allows
0.5 seconds for communication/teardown, reported separately as supervised wall
time. TIMEOUT remains distinct from infeasibility. One-time grammar/tokenizer/schema
loading is excluded. Structural support construction is timed and charged only to
methods that consume it. Construction is measured once per case/profile and reused
as a paired common cost; this is not an independent timing replicate. Child repair
and full supervised wall times are recorded. Exact/greedy additionally record
lattice, parser, backtracking, validation and instrumentation components; greedy
component times accumulate, while size counters describe the last call.
No model/commit-update phase exists in this postprocessor.

Method order rotates by case and repetition; confirmation has two repetitions.
Analyze successes at document level within each family/profile (both repetitions
must succeed for a stable success), and take within-document median timings first.
Paired wins/ties/losses and ratios include only jointly successful calls for speed,
with every timeout/failure reported alongside. Report all family/profile cells,
including any losses. Bootstrap paired documents with fixed seed 212000 (2000
resamples) for descriptive timing intervals; no population-prevalence claim.
The required practical result is a reproducible restricted advantage, not a
promise of general superiority or speed over microsecond repair libraries.

## Reproduction and dependencies

The only added package is optional json-repair 0.63.5, installed without changing
the existing pinned jsonschema/tokenizers stack. It is absent from the core API's
runtime requirements. Wheel SHA-256 from PyPI on 2026-09-28:
`0e39b3066f7829b4bd7fc614e463cfd4ff7a4c46f82f5b65431fc11e29a74c81`.
Primary API documentation: https://github.com/mangiucugna/json_repair (schema modes).

Run from a clean local commit containing the code and TOML configuration:

```bash
.venv/bin/python -m pip install -c requirements/constraints-py311-linux.txt -r requirements/repair-experiments.txt
.venv/bin/python -m scripts.exact_commit.run_json_repair --config configs/experiments/m21_repair_pilot_v1.toml --run-directory results/raw/m21-repair-pilot-v1
.venv/bin/python -m scripts.exact_commit.run_json_repair --config configs/experiments/m21_repair_confirmation_v1.toml --run-directory results/raw/m21-repair-confirmation-v1
```

Raw gzip JSONL, metadata, manifest and summary are written into a new directory;
existing runs cannot be overwritten. All rows record source/config/grammar/schema/
input/support hashes, seed, revisions, hardware/software and status. Any code fix
requires a new clean commit and a new run ID; preserve the previous run. Historical
M13–M19 evidence is unchanged. No remote publication is part of this task.

## Additional mechanism control frozen before measurement

Add a single unweighted CFG completion (`feasibility`) to both main cohorts. In
a rigid schema this can already suffice; speed over repetitive greedy validation
is not evidence that weights are needed. Add a separate ambiguity study, seeds
213000–213007, one/two records, all six families, both tokenizers, one repetition.
Its CFG accepts generic integer JSON objects; it has no answer-specific types.
Exact, greedy and unweighted feasibility receive this identical weaker CFG.
Schema-guided json_repair and enumeration retain the stronger complete schema;
any exact advantage over them cannot be attributed to withholding schema input.
Report this cohort separately, without pooling its weaker-grammar objective with
the full-schema objective. This tests whether minimizing edits can matter when
several structures are legal. The frozen configuration is
`configs/experiments/m21_repair_mechanism_v1.toml`.
