# Six-pool safety correctness evidence

Written proof commits precede these NEW checks:

- e970ffe: arbitrary-class six-pool proof and original-payload lift.
- 1a39f02: exact sum-of-squares identity.
- 9a1aae9: endpoints and the proved subinterval0<=t<=1/15.

Commands from the repository root, in the existing `.venv`:

```
.venv/bin/python -m unittest tests.test_six_empirical_tower_safety -v
.venv/bin/python attempts/45-random-order-empirical-towers/work/symbolic_six_v3.py
.venv/bin/python -m unittest discover -s tests -v
```

All processes finished with exit0 BEFORE their output files were copied here.
Focused five tests pass; full307 tests pass88.256s. The ten optional standalone
symbolic identities use SymPy1.14.0. Maintained CI does not import SymPy.
Ruff check and format-check pass for all four new Python files.

The rational oracle enumerates35 production conditional rows/12412 complete
integer-RNG leaves, eight independent positive-remainder expansions,
192 population-law entries/115 matrix directions/334 Boolean verifiers,
508 endpoint/verifier/square checks and4096 original-payload tapes including
aliases and failed sources. It retains the unsafe t=1/6 control exactly.
Finite counts are correctness evidence, not extrapolation to a universal proof.
That claim rests on the separate written square identities and inequalities.

No new pretrained neural call, timing campaign, source fitting, external data
capture, semantic quality, priority, human review or achieved user goal.
Even budgets>=8 and the upper family remainder remain OPEN at this version.
