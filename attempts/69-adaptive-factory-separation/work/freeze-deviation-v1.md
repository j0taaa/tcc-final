# Recorded freeze deviation before the corrected audit

2026-10-17. The written proof358eb48 and protocol9ca78d4 preceded code.
The intended code-freeze shell command failed Ruff E501 at audit.py line213,
so it did NOT commit the source. The outer orchestration nevertheless invoked
the next audit command. That was a workflow error, not successful preregistration.

The initial audit finished PASS/direct0 in7.121567s, with exact draft bytes
recorded by its hashes. Original raw data remain untouched in
docs/artifacts/raw/a69_adaptive_separation_v1_initial. Its source_commit field
contains the ACTUAL HEAD9ca78d4 (a PROTOCOL commit); that commit DOES NOT contain
the uncommitted producer source. Do not claim otherwise or retroattribute a
later source commit to that execution. Exact draft files are preserved here
in evidence/unfrozen-draft/{audit,separation}.py, matching the raw hashes.

Only a long scope string will be split to satisfy formatting; no algorithm,
case, bound, count or validation rule changes. Freeze those final files with
this deviation before one repeated complete correctness audit, using a NEW
raw directory. The repeat is justified to meet the recorded source-before-
execution requirement; both results remain. It is not an independent benchmark,
new empirical application or evidence of sufficient novelty/user-goal completion.
