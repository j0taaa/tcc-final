# V4 capture receipt: distinguish start producer from end HEAD

The resource driver was frozen at full commit
cc36fab56ea1a53e3ba3952948ef67e7f8bc2636 BEFORE import/model execution. Its
manifest records HEAD at start and checks its own source, protocol and each
original component byte against that HEAD before importing Torch. During the
unchanged capture, a DIFFERENT stdlib-only post-checker was committed at
da74d38b6ae1e2c7de9bd5d7e5cde237f0c88f7f. It was not imported/executed in the
timed process; no benchmark source/inputs/control/gate was edited.

The outer receipt incorrectly names a git rev-parse performed AFTER wait()
`producer_commit`. That field is the END HEAD, not the actual driver producer.
Preserve the original receipt unchanged, and use the pre-import manifest's
producer plus independent Git byte comparisons to establish actual source.
Do not attribute the measured data to the later post-checker commit.

The da74d38b static checker has NOT been executed. Its planned equality of
those differently timed HEAD fields is invalid. BEFORE any checker execution,
an independent `verify_resource_v4b.py` copy will instead require the exact
known start producer and check every recorded source against BOTH start and
reported end Git revisions, and their ancestry. No scientific rerun, timing
adjustment, changed threshold or rewritten receipt follows from this fix.
This is a metadata interpretation repair, not a candidate performance result.
