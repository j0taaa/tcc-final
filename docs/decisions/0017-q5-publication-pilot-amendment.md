# ADR 0017: Amend Q5 after the failed structured-task pilot

- Status: accepted
- Date: 2026-08-31
- Supersedes for execution: the Q5 v1 configuration named in ADR 0016

## Context

The first clean Q5 v1 pilot (`json_x_zero`, seed 125301) was rejected by the
predeclared correctness gates. EPIC's selector was called 50 times but selected
no regular-cover batch, the maximum commit batch was one, and 34 constrained
method rows failed the complete/independent-output contract. The 32-slot target
also exposed a driver bug: a partial `OPTIMAL` exact step was recorded as the
whole generation instead of continuing exact steps over the remaining masks.
The rejected pilot is not publication evidence.

## Decision

Use `q5_structured_publication_v2.toml` and `q5_structured_tasks_v2.toml` for the
accepted campaign. The amendment was made before any Q5 publication result was
accepted:

- use 16 finite slots and eight diffusion steps, so each upstream step offers
  two ordinary candidates to the EPIC regular-cover selector;
- make the JSON literal match the pinned model's observed deterministic fenced
  JSON form while retaining an exact independent byte/CFG check;
- repeat exact optimization until completion or a terminal non-`OPTIMAL`
  status, retaining every optimizer outcome and independent certificate;
- retain the original seeds, ten repetitions, top-K support, model revision,
  timing method, EPIC gates, and publication bundle ID.

The v1 files remain versioned as the original predeclaration. Its failed raw
pilot remains under ignored `results/` and is not copied into a paper bundle.

## Consequences

The publication campaign still fails unless `regular_cover_selector_calls > 0`
and an EPIC commit batch has cardinality greater than one. Exact completion may
take several per-step `exact_on_support` optimizations; every `OPTIMAL` outcome
must carry an independently valid certificate. This amendment does not broaden
the per-step or finite-support exactness claim.
