# ADR 0020: Freeze compact real-state support for Q2 replay

- Status: accepted
- Date: 2026-08-31
- Amends: the Q2 v1 predeclaration in ADR 0016

## Context

The accepted Q5 v4 tasks expose seven and four successful EPIC selector states,
respectively. Five states per task are therefore not available without adding
artificial steps. Full-vocabulary logits would also duplicate hundreds of
megabytes although the comparison uses one primary proposal per masked slot.

## Decision

Capture the last four successful EPIC selector states for each of two tasks and
three seeds, producing 24 real denoising snapshots. Each portable snapshot
stores the fixed canvas, every ordinary primary model proposal and confidence,
the exact target witness token for each remaining slot, the actual-to-local
token map, grammar representations, and semantic-alignment cases. It does not
store model weights or unused vocabulary logits.

For EPIC replay, each compact token ID receives a deterministic terminal name.
The EPIC CFG is generated from every grammar-valid token sequence in the saved
finite support, and semantic alignment is exhaustively rechecked over that same
support. This avoids pretending that arbitrary tokenizer pieces are grammar
terminal names while preserving exactly the represented snapshot language.

All three selectors replay the identical snapshot hash. The represented row at
each masked position is the saved primary proposal plus the independently known
target token; fixed positions remain singleton rows. Consequently the claim is
`exact_on_support` for this explicit support, not top-K or full-vocabulary
exactness. Baseline subsets are independently checked by finite enumeration;
exact witnesses, selected IDs, objectives, CFG validity, and parser
certificates are independently recomputed. Timeouts, failures, and zero
optima remain explicit rows/counts.

## Consequences

The original six synthetic Q2 rows remain illustrative canonical/adversarial
cases and are never mixed into the real-state aggregate. The real sample is
small and model/task-specific, so it supports only a bounded empirical report,
not a population-wide claim about EPIC's average loss.
