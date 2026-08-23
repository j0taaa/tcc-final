# ADR 0003: Exactness scope and failure terminology

- Status: Accepted
- Date: 2026-08-23
- Applies to: every solver result, support expansion, fallback, diagnostics,
  experiment artifact, and TCC claim

## Context

The weighted parser can be exact for the finite graph it receives while that
graph represents only a top-K or explicitly pruned subset of model tokens.
Feasibility can also remain unknown because of a timeout or unsupported
semantic feature. Without separate scope and status fields, these cases are
easy to overstate as global optimality or infeasibility.

## Support kinds

Every solve records an immutable `ExactnessScope` with tokenizer vocabulary
size, included special-token IDs, support kind, pruning description, and any
adaptive top-K widths.

### `SupportKind.FULL`

Every vocabulary token permitted by the configured tokenizer and EOS/PAD
semantics is represented at every non-fixed finite slot. Fixed slots still
contain only their committed token. An `OPTIMAL` result is exact over this
declared full-vocabulary, finite-slot instance.

The allowed wording is:

```text
exact over the declared full-vocabulary finite-slot instance for this step
```

It is not a claim about future denoising steps, another tokenizer revision,
unbounded strings, semantic program correctness, or a different grammar.

### `SupportKind.TOP_K`

Each relevant slot represents the recorded model top-K alternatives plus the
recorded required special tokens. The base `top_k` is mandatory. The allowed
short name for an optimal result is:

```text
exact_on_support(kind=top_k, top_k=K, ...)
```

It must never be called globally exact or full-vocabulary optimal.

### `SupportKind.EXPLICIT`

The instance uses explicitly recorded token alternatives per slot, such as a
small oracle fixture or replay lattice. The exact set is carried by the input
arcs/fixture and identified by the scope's pruning description. The allowed
short name is:

```text
exact_on_support(kind=explicit, ...)
```

An explicit support may happen to contain every token in a toy vocabulary,
but it is named `FULL` only when full representation is validated as such.

## Adaptive top-K expansion

For a top-K policy, `ExactnessScope.top_k` is the initial width and
`adaptive_expansions` is the strictly increasing sequence of later widths
attempted, each bounded by `vocabulary_size`. The effective width of the
current result is the last expansion, or `top_k` when no expansion occurred.

Each width is a separate exact-on-support solve. Infeasibility at width `K`
may justify trying the next configured width, but is not evidence of
infeasibility at that larger width. The final result records:

- every attempted width and its solver status;
- special tokens added outside model top-K;
- the scope of the result actually returned;
- whether resource limits prevented another configured expansion.

If an expansion represents and validates the entire vocabulary, orchestration
constructs a `FULL` scope for that attempt instead of describing it as top-K.
Support expansion changes the represented problem and must not be hidden as
parser pruning.

## Solver statuses

Statuses are mutually exclusive and retain these meanings:

- `OPTIMAL`: a grammar-valid witness and independently recomputable objective
  certify the maximum over exactly the recorded support.
- `INFEASIBLE_ON_SUPPORT`: the exact solver completed and found no
  grammar-valid finite-slot path in exactly the recorded support. Under a
  validated `FULL` scope this establishes infeasibility for that declared
  finite instance only; otherwise it says nothing about omitted tokens.
- `TIMEOUT`: the configured deadline expired before a conclusive result.
  Feasibility and optimality are unknown.
- `UNSUPPORTED`: the implementation recognizes that the requested semantics
  are outside the implemented contract, for example an unavailable tokenizer
  mapping or grammar feature. It is not an infeasibility result.
- `ERROR`: processing failed for a reason not represented by the other
  statuses. Malformed values detected at public data-contract construction
  raise explicit validation errors before solving; runtime/internal failures
  that are returned use `ERROR` with diagnostics.

No non-`OPTIMAL` result carries an objective or public certificate fields.
Partial internal progress may be logged only in diagnostics and is never
presented as certified.

## Fallback and logging

Orchestration may use a fallback to make decoder progress after any
non-optimal status, subject to its configured policy. Fallback does not change
the solver status. Every fallback event records at least:

- original status and exactness scope;
- timeout/unsupported/error reason and elapsed limit where applicable;
- support-expansion attempt history;
- fallback strategy and committed position/token;
- whether that token actually matched a proposal in the frozen candidate set;
- proposal ID and reward only when such a match really exists.

A witness-derived progress token that matches no proposal has zero proposal
reward and is not retroactively counted as selected. In particular, a timeout
followed by a successful serial fallback remains a `TIMEOUT` solver event, not
`OPTIMAL` or `INFEASIBLE_ON_SUPPORT`.

## Required reporting language

Public reports combine status and scope. Examples:

```text
OPTIMAL, exact_on_support(kind=top_k, top_k=32, effective_k=64)
INFEASIBLE_ON_SUPPORT, kind=explicit, fixture=case-017
TIMEOUT, kind=top_k, effective_k=128, limit_seconds=5
```

Claims are always per current proposal set, canvas, finite slots, grammar,
tokenizer semantics, and denoising step.

## Alternatives considered

- A single `None`/failure result was rejected because it conflates timeout,
  unsupported semantics, errors, and proved support infeasibility.
- Calling every parser optimum “exact” was rejected because omitted vocabulary
  tokens can change feasibility and score.
- Treating a successful fallback as solver success was rejected because it
  erases the guarantee actually obtained.

## Executable enforcement

`SolveStatus` defines five distinct values. `ExactnessScope` requires support
metadata and rejects top-K without `K`, invalid special tokens, and malformed
expansion sequences. `ExactCommitResult` permits objectives/certificates only
for `OPTIMAL`. The focused regressions are
`tests/exact_commit/test_exactness_scope.py` and
`tests/exact_commit/test_graph_and_result_contracts.py`. T801/T804 will make
adaptive-attempt and fallback diagnostics executable without changing these
meanings.
