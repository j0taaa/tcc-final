# ADR 0009: Adaptive timeout classifies late results without mislabeling them

- Status: Accepted
- Date: 2026-08-25
- Applies to: adaptive support orchestration and decoder fallback decisions

`total_timeout_seconds` bounds which adaptive result may be returned as
conclusive. Support construction that exhausts the deadline does not start a
parser. A Python reference attempt already in progress cannot be interrupted
safely, so caller-visible latency is not bounded for that backend; if the
attempt finishes late, its result is discarded and the public status is
`TIMEOUT`. Rust receives the remaining deadline before each solve and is the
production backend for bounded parser attempts. Timeout is never converted to
infeasibility.
