# A56 evidence and reproduction scope

Initial written proof7fb3daf449a2cce1d7507a733630710f229d4bce and GPU preflight
contractb1f88d6e478ecb45f30d508ebcb2b7b1b05e4471 precede the prototypes.
The original A51 controls are independently copied from full commitd61565e,
with exact bytes/hashes in ../copy-origin-v2.json. They are old controls.

CPU correctness:

```
.venv/bin/python -m unittest tests.test_static_rounding_sampler -v
.venv/bin/python -m unittest discover -s tests -v
```

Four focused tests pass, full311 pass88.119s. Complete exit0 logs were copied
AFTER process completion into reference-v1/. SymPy is not required. Ruff
check/format-check pass for all five new Python files. No old suite restored.

GPU correctness, existing optional environment:

```
.venv-mosaic-native/bin/python -m attempts.56-static-rounding-sampler.work.gpu_preflight --output /tmp/a56-gpu-preflight-v2-second
```

All output was copied after exit0 into gpu-v2-correctness/. The actual invoked
Git HEAD in summary.json is the WRITTEN protocol commit; the new prototype
files were not yet committed at that invocation. Their exact executed SHA256
values are recorded in the summary and match the preserved files. Do not call
that protocol commit the producer of uncommitted source or a timing campaign.
The code+evidence consolidation commit is separately recorded in the catalog.

The FIRST invocation in .venv failed before GPU work because Triton was absent;
gpu-v2-import-failure/ preserves its original log and executed sources. This
is an environment selection failure, not a failed scientific cost gate.

The successful audit has185 exact mass checks,336 literal retained-prefix
replays,4096 full-word prefix outcomes across16 events and14 emitted PTX
modules. No timing, pretrained/model call, real-head readout, external-input
performance selection, source fitting or sufficient novelty/usefulness claim.
../primary-decision-v2.md explains the direct ADZ antecedent and open user goal.
