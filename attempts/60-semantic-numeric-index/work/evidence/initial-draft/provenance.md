# Initial execution ordering deviation, preserved literally

2026-10-17. Written theory e107296 and addendum220c1e1 preceded all code.
The intended source freeze command was guarded by Ruff with `&&`; Ruff found
one101-character test line (E501), so that command DID NOT create a commit.
The separately issued oracle command then ran anyway. Its four oracles passed
in0.707s, but this first source was NOT committed before that execution.
Do not label it prospectively source-frozen. No model, head, competitive timing,
data selection, or correctness repair resulted from this run. Both its Ruff
failure and complete oracle log are retained here. The next change only wraps
that test line, then commits the source BEFORE a separate final oracle run.
