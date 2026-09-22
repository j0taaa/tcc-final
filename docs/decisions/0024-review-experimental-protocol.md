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
