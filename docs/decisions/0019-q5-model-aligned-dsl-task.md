# ADR 0019: Replace the rejected infix task with a model-aligned DSL task

- Status: accepted
- Date: 2026-08-31
- Supersedes for execution: Q5 v3 in ADR 0018

## Context

The clean v3 infix run proved that a four-slot schedule was not enough to make
the comparison meaningful. The initial pinned-model state proposed only one
ordinary token (`0`) and termination tokens. Serial and EPIC both produced the
valid target by sequential resampling, but EPIC had no regular-cover selector
call, the maximum batch remained one, and the gate rejected the run.

A read-only initial-logit probe compared two explicit structured prompts. The
fenced DSL target `ADD 0 0` produced ten aligned ordinary token proposals,
followed by EOS and PAD, in a 12-slot state. No output from that probe is used
as a result; it selected the task before the v4 campaign was run.

## Decision

Q5 v4 uses the already validated fenced JSON task and a fenced `ADD 0 0` DSL
task. The DSL schedule is 12 finite slots, six diffusion steps, and schedule
budget 12. The publication seeds, repetitions, model/tokenizer revision,
support, EPIC exact verification, checker, and timing protocol remain frozen.

## Consequences

The final Q5 campaign contains two nontrivial structured literal tasks and is
reported as such; it is not evidence across a broad task distribution. The
same hard gates remain: a real EPIC selector call, at least one EPIC batch
larger than one, independent output validity, and independently certified
per-step `exact_on_support` results.
