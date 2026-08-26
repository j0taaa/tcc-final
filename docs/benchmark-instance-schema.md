# Benchmark-instance schema

`mwpc_benchmark_instance` version 1 is the immutable input boundary for fair
offline selector comparisons. The implementation and authoritative validator
are in `mwpc_exact.benchmark_instance`; the versioned example is
`tests/exact_commit/fixtures/benchmark_instance_v1.json`.

## Scientific meaning

One file freezes the proposal order, MWPC weights, canvas, represented support,
exactness scope, tokenizer byte emissions, EOS/PAD policy, normalized exact
grammar, and EPIC grammar/lexical state. Serial, EPIC, exact, and guarded brute
force therefore consume the same `SelectionInput`. Replay never regenerates
support or proposals from logits.

Saved logits are optional provenance. They contain only a position-by-vocabulary
score matrix, dtype, source description, and JSON metadata; model parameters are
not part of this schema. Finite values are JSON numbers, while the portable
strings `Infinity` and `-Infinity` preserve masked scores without emitting
non-standard JSON. NaN is invalid. The matrix shape must equal canvas length by
tokenizer vocabulary size.

The schema does not change selector guarantees:

- serial remains order-greedy and reports `FEASIBLE_ON_SUPPORT`;
- EPIC remains heuristic and reports no finite-slot witness;
- exact reports `OPTIMAL` only with its independently validated certificate;
- brute force is invoked only behind its explicit completion-count guard; and
- every claim retains the serialized support scope and support fingerprint.

## Integrity and validation

The top-level required fields are:

```text
artifact_kind, schema_version, instance_id, instance_sha256
grammar, selection_input, saved_logits, epic_replay
metadata, expected_metadata
```

`grammar_sha256`, `represented_support_sha256`, `logits_sha256`, and
`instance_sha256` are SHA-256 hashes of canonical JSON payloads. Loading
reconstructs all typed contracts, rejects unknown structural fields, verifies
all hashes, rejects malformed proposal weights and metadata numbers, and checks
that canvas, support, vocabulary, logits, and EPIC decoded state agree.

`metadata` records input provenance such as seed, source kind, model/tokenizer
IDs and immutable revisions. `expected_metadata` records fixture applicability
and non-result expectations. Neither mapping is interpreted as a measured
result, and neither may contain NaN or infinity.

## EPIC replay

The grammar record stores EPIC CFG text and its start symbol alongside the exact
CNF. By default, replay reconstructs the pinned `rustformlang.cfg.CFG` from that
text. A caller may provide an explicit CFG factory for a grammar implementation
with equivalent, independently verified semantics. Lexical state is restricted
to JSON-compatible values; instances requiring opaque runtime lexical objects
are not EPIC-replayable under version 1 and must omit `epic_replay` or receive a
future versioned representation.

If the pinned EPIC runtime or CFG binding is unavailable, EPIC alone returns
`UNSUPPORTED`; the other applicable selectors still replay. This is not treated
as infeasibility.

## Migration policy

Version 1 is the first public benchmark-instance schema, so there is no legacy
migration. Unknown older and newer versions fail closed with
`UnsupportedBenchmarkSchemaVersion`. A future schema change must:

1. increment `schema_version`;
2. add a deterministic one-step `N -> N + 1` migration;
3. preserve the original fixture and add a migration regression fixture;
4. recompute all affected content hashes; and
5. document any scientific-semantic change rather than silently defaulting it.

Additive experiment annotations belong inside `metadata` or
`expected_metadata`. A change to canvas, proposals, weights, support, grammar,
tokenizer/EOS semantics, or replay behavior requires a schema version change.
