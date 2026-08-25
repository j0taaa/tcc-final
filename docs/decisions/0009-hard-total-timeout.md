# ADR 0009: Adaptive total timeout is a hard returned-status deadline

- Status: Accepted
- Date: 2026-08-25
- Applies to: adaptive support orchestration and decoder fallback decisions

`total_timeout_seconds` bounds the complete adaptive operation as observed by
the caller. A Python reference attempt cannot be interrupted safely, but if it
finishes after the deadline its result is discarded and the public status is
`TIMEOUT`. The attempt history records no objective or certificate for that
late attempt. Rust continues to receive the remaining deadline before each
solve. Timeout is never converted to infeasibility.
