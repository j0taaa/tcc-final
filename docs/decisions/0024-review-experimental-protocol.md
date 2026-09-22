# ADR 0024: Matched-budget review experiments

Accepted 2026-09-22. Extends ADR 0023; no historical raw result is overwritten.

The corrected exact hook receives the upstream transfer schedule computed from
the initial canvas and step count. In the nonliteral pilot this is 32 slots,
16 steps and two proposals per step for every constrained strategy. EOS suffix
canonicalization may update extra physical slots; actual forward calls, updates,
statuses and certificates are retained. Equal schedules do not imply equal
work after rejection or different trajectories.

Freeze the pilot configuration and generating source in a local commit before
execution. Use all twelve predefined recursive tasks, one seed and one timing
observation per strategy. Capture unconstrained pre-commit states at forwards
0 and 8 without conditioning on final success. Save the model's top eight
permitted choices, their logits/probabilities, actual proposals, fixed canvas,
byte emissions and model IDs. Never add a known completion. Replay nested
K=2,4,8 supports with the same frozen proposals, explicitly adding EOS/PAD and
proposal tokens. Report feasibility, gaps and timeouts including zero gaps.

Use syntax recognition independent of the parser and separate functional
checks for bracket counts/depth, arithmetic values/leaves and JSON leaves/depth.
The grammar is shared by a family and does not encode its prompt's answer.
The confirmation split contains twelve disjoint prompts defined before the
pilot; freeze its configuration after the pilot, documenting any operational
changes. Repetitions are repeated measures, never additional independent tasks.

Warm up each shape outside timing, synchronize CUDA around forward and total
generation timing, rotate strategy order, and exclude model loading. A parent
process enforces a 60-second generation limit and a 180-second setup limit even
inside blocking baseline/native code. Preserve failed and interrupted jobs as
rows with their phase and censoring limit; do not treat censored runtimes as
completed observations. This small study can expose limitations; a positive
speed or functional effect is not an acceptance criterion.

Source and configuration changes after a failed pilot require a new commit
and configuration ID. Keep every attempted campaign, including operational
failures. The manuscript must distinguish corrected nonliteral observations
from historical literal tasks whose unequal proposal budgets confounded speed.

## Pilot v1 operational correction

The first frozen pilot (source 9444c84) produced all 60 rows and 24 snapshots.
Its observation wrapper created inference tensors, conflicting with upstream
resampling that modifies logits outside inference mode (18 error rows). The
wrapper now uses no_grad, matching the baseline, with an executable regression.
The parent also records the observed CUDA runtime in common metadata; v1 kept
its missing-metadata warning. Pilot v2 changes only these observation details;
no tasks, budgets, rankings or success criteria are tuned. Preserve both runs.

## Recursive scaling extension

Use 16/32/64/128 slots, support widths 2/4/8 and fixed outer nesting depths
0/4; three repetitions per setting. The first four tokens emit individual
brackets; the next four emit (), [], (()) and [[]], exposing multi-byte
expansion as width increases. This is a compound width/byte-length axis, not
an isolated causal estimate. Save every instance and certificate; independently
check bracket syntax and use exhaustive agreement on small instances as a gate.
Limit native parsing to one second, each process to 15 seconds and address space
to 2048 MiB. Report all statuses and peak process RSS, including failed cases.

## Frozen confirmation

Pilot v2 completed all 60 jobs without observation errors: exact completed
1/12 task generations and had no functional success; serial and EPIC each
completed 7/12 and succeeded functionally on 3/12. These negative pilot results
do not trigger parameter tuning. Confirmation retains 32 slots, 16 steps,
K=2 up to 8 and the same limits. It uses the twelve predefined disjoint prompts,
seed 170302 and two repetitions (96 generations plus 12 capture jobs). Report
the two observations per task explicitly, without counting them as new tasks.
