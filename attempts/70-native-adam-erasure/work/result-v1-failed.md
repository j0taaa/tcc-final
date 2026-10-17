# V1 runtime failure, preserved before the namespace repair

Proof/protocol802a8634 preceded producer803fce7937d5f9548d622c2701f5f7c5131c64ad.
ONE initial command built the C library successfully, then the Python child
terminated by signal11: direct subprocess return-11, outer shell245. It is
NOT a passing audit or mathematical counterexample. Diagnostic elapsed1.550s
is not competitive timing. Raw build/schedule/primitive artifacts and the
empty persisted primary JSONL remain in
docs/artifacts/raw/a70_native_erasure_v1_initial. No primary completion count
is inferred from buffered output lost at the crash.

The source exported the generic global symbol `step`. Static disassembly
showed its internal run_zero call through step@plt; libc exports a conflicting
legacy step@GLIBC_2.2.5. A SEPARATE loader-only probe (no numerical audit
replay) confirmed binding of this library's step reference to libc, while
moments/weight bound to the intended library. Actual binding lines and
library hash are in docs/evidence/a70-v1-linker-diagnosis.json. The initial
exit receipt/log are docs/evidence/a70-v1-initial-{exit.json,audit.log}.

The namespace/linkage bug is ours, not a flaw in Adam or third-party source.
Repair only in NEW V2 files, with a fresh source freeze before execution;
do not overwrite V1 source/evidence or attribute the initial run to V2.
All original numerical conditions/cases/cap remain. No new model, training,
performance, successful certification fraction, priority or fulfilled goal.
