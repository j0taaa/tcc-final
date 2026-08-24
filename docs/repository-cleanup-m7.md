# M7 repository cleanup

This cleanup was based on the M6 tree plus the accepted T700 EOS/PAD decision. It deliberately avoids redesigning the support, token-lattice, byte-lattice, Python reference parser, Rust parser, or M7 automaton.

## Changes

- removed the obsolete in-repository Base64 bootstrap archive, materializer, marker, status file, and integrity workflow;
- made `TASKS.md` the sole source of the current milestone;
- updated the current pointer to M7/T701 without altering T700 evidence;
- separated represented-support validation from EOS/PAD-policy validation;
- clarified production module docstrings;
- restored the complete ADR index.

## Intentionally deferred

Large mechanical refactors such as moving campaign modules or splitting the established Rust parser are deferred until after the M7 correctness gate. Performing them while the EOS/PAD automaton is under active development would create churn without changing the scientific result.
