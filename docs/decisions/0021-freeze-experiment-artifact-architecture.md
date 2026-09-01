# ADR 0021: Freeze the experiment and artifact architecture for M13

- Status: accepted
- Date: 2026-09-01
- Scope: M12.5 and M13

## Context

M11 and M12 already provide experiment configuration, metadata capture,
raw/processed separation, statistical summaries, generated tables and figures,
and reproducibility checks. Those layers are sufficient for the remaining
article work. Adding another abstraction would increase validation surface
without strengthening the scientific result.

T1201's two-row artifact inventory and T1202's synthetic formula artifact are
internal pipeline fixtures. They demonstrate that validation machinery works;
they are not research findings and must not be imported or cited as results.
The T1203 Q1--Q5 artifact is the only currently assembled scientific-result
bundle. Files under `m125_publication_results_v1` are staged publication
evidence for the M12.5 corrections and may be consumed by the existing M13
paths; they do not establish a second framework or overwrite T1203.

## Decision

M13 must reuse the current:

- experiment TOML configuration;
- run-metadata contract;
- raw and processed artifact directories;
- statistical-summary utilities; and
- final-artifact generation paths.

M12.5 and M13 must not add a plugin system, general workflow engine, another
artifact schema, generic charting framework, database, dependency-injection
layer, second statistical library, or second raw/processed convention. A
task-specific driver or validator is allowed only when it directly produces or
checks evidence required by a task and reuses the contracts above.

Large modules are split only if a required functional change makes the split
necessary. File size or aesthetics alone are not sufficient reasons before the
article is complete.

## Consequences

Article work should mostly select, describe, and cite existing evidence. It
must not cite T1201 or T1202 as scientific results. Any later publication
bundle may use a new bundle identifier, but it must be built through the
existing artifact architecture.
