# ADR 0018: Use task-specific finite-slot schedules in Q5

- Status: accepted
- Date: 2026-08-31
- Supersedes for execution: Q5 v2 in ADR 0017

## Context

The clean v2 JSON run passed all gates (40 measured rows, 70 EPIC selector
calls, maximum EPIC batch two, zero contract failures). The v2 expression run
did not: the model emitted the shorter `0+0`, the 16-slot state made EOS/PAD
candidates dominate, EPIC made no ordinary regular-cover selector call, and 24
constrained rows failed. Neither partial v2 result is used as the complete
two-task publication campaign.

## Decision

The v3 manifest freezes a finite schedule per task:

- fenced JSON: 16 slots, eight diffusion steps, schedule budget 16;
- infix expression `0+0`: four slots, one diffusion step, schedule budget four.

Both tasks keep the same model/tokenizer revision, top-K support, weight mode,
EPIC exact verification, seed set, repetition count, timing protocol, and
independent output checker. The driver records the selected task schedule in
each comparison contract. The v1 and v2 files remain immutable audit records.

## Consequences

Runtime summaries must remain stratified by task before any aggregate is shown.
The task schedule is part of the represented finite support and comparison
fingerprint. A run still fails unless EPIC invokes regular-cover selection and
commits a batch larger than one, and unless every constrained output passes the
independent checker. Every exact `OPTIMAL` step remains `exact_on_support` and
requires an independently valid certificate.
