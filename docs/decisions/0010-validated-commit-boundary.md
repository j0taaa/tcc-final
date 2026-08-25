# ADR 0010: Physical commits require a typed validated result

- Status: Accepted
- Date: 2026-08-25
- Applies to: exact orchestration, adaptive orchestration, and decoder updates

An `ExactCommitResult` is the serializable scientific result. A physical exact
commit additionally requires `ValidatedExactCommit`, which pairs an optimal
result with a typed `ValidationReport` whose recomputed objective and proposal
IDs agree with the result. Non-optimal results remain raw because fallbacks
must preserve their original status without acquiring an exact guarantee.

The production M9 adapter must call the validated solve APIs before invoking
`apply_exact_commit_result`. Those APIs carry the live typed report emitted by
the independent validator; reconstructing a report from result diagnostics
cannot create commit authority. A JSON boolean in diagnostics is evidence for
serialization, not authorization to mutate the canvas.
