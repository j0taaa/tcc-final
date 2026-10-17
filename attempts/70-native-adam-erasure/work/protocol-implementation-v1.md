# V1 source realization, BEFORE source freeze/build/audit

The original theory/protocol commit is802a8634. This additive record fixes
implementation details before any scientific execution; it does not change
the768-case grid, head cap, correctness decision or absence of a timing gate.

C source exposes the exact individual arithmetic functions for independent
oracle tests. The primitive corpus has bits0,1,007fffff,00800000,3f7fffff,
3f800000,3f800001, plus negative zero, negative least subnormal,-1,R(.1),
R(.999),R(1e20). Test every ordered pair for add/multiply/divide (division
by zero outside contract) and square root on its nonnegative nonnegative-
zero members. Nonfinite native outputs are retained as OUTSIDE_FINITE and
are not credited as passed primitive identities. They do not remove any
of the768 admitted primary cases. Rational midpoint/squared-midpoint oracle
must match every finite output bit, including signed zeros.

The weight-absorption-plus-moment-replay control is actually executed on
every primary case, using the SAME head/guard and literal moment replay,
and compared to the eager next state. Its h moment updates are charged as
operation counts; no timing superiority is inferred from those counts.

All source/proof/protocol bytes must equal their current committed blobs
before the driver builds or loads C. Compiler settings are recorded. The
native scalar table is retained as a complete binary artifact, with layout
array of{float a,float d}, index0 unused. The protocol's library/scalar
oracle distinction and finite FP environment remain unchanged.
