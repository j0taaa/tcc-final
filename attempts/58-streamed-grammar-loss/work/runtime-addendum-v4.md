# V4 — Repair control runtime, before a SEPARATE full replay

2026-10-16. Initial GPU producer8fea71fe2a5844ad92dcee8f4ffe7ce035b7fe07
has32 records: candidate/dense/checkpoint each8/8 PASS,95188 comparisons each,
four refusals PASS; CCE8/8 ERROR because packaging is absent. Overall ERROR.
Maximum candidate absolute error is1.1837109923362732e-6 against FP64.
All original fixtures/source/runtime/errors remain literal in gpu-v3-initial.
No missing-control failure is credited as a win or successful full preflight.

Before replay, install ONLY packaging==25.0 in .venv-mosaic-native. It is a
control-import dependency, not a model, new input or scientific method change.
Record package version with runtime metadata and preserve exact new producer
source. Run ALL32 method/fixture combinations again in a NEW output directory,
same shapes, inputs, controls, tolerances, guards and resource budgets. Verify
all eight new input files against their original hashes. No tolerance, class
selection or method is relaxed. If another failure appears, retain it.

No CCE vendor edit is permitted. The CPU sixth oracle and completed321-test
suite88.353s concern the corrected zero-class source; they are not timings of
GPU operation or a model update. A full replay PASS still means only synthetic
arithmetic correctness, not systems novelty, memory/latency benefit or a
training/application gate. V1's eight criteria and V3's scope remain unchanged.
