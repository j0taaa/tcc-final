# V2 linkage-only repair protocol, BEFORE its source/build/execution

V1 producer803fce79 crashed by signal11 after a successful build. The
loader-only diagnosis confirms a collision with libc's legacy `step`.
Preserve V1 files, packet and failed result unchanged.

V2 consists of independent source copies native_v2.c/audit_v2.py, with every
our exported C function prefixed a70_v2_ and internal function references
bound locally using -Wl,-Bsymbolic-functions. Python explicitly resolves those
prefixed symbols; convenience aliases do not resolve an unprefixed API.
Record build/source hashes and symbol-table output. These are linkage/API
changes ONLY; arithmetic expressions, recurrence,768 cases, H=512, supplied
scalar bits, primitive corpus, independent oracle and correctness decision
remain identical to the frozen V1 protocols. Do not tune the grid/cap after
the runtime failure. V1 mathematical proof remains WRITTEN, not validated
by its unsuccessful run.

After a new source commit, execute ONE corrected numerical audit into a
NEW output directory, with faulthandler enabled and a direct exit receipt.
Record a finite failure/partial result if any; no automatic source edit and
rerun under the same version. Passing would mean numerical correctness/
nonvacuity only. No training/competitive campaign/priority/goal completion.
