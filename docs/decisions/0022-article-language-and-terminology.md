# ADR 0022: Use an English article body and canonical MWPC terminology

- Status: accepted
- Date: 2026-09-01
- Scope: T1259 and M13

## Context

The implementation, task evidence, ADRs, and generated artifacts use English,
while the manuscript and legacy implementation plan used Portuguese. This
made scientific terms inconsistent immediately before result integration.
The institutional format requires a Portuguese `Resumo` and permits an English
article body; no advisor or institutional constraint requiring a Portuguese
body is recorded in the repository.

## Decision

The article title, body, section titles, theorem and algorithm names, captions,
code, and repository documentation use English. The institutionally required
`Resumo` remains in Portuguese and is paired with an English `Abstract`.
Official institution names and cited work titles may retain their original
language.

The legacy Portuguese `IMPLEMENTATION_PLAN.md` is archived verbatim. Its root
path becomes an English supersession index pointing to the maintained
contracts in `AGENTS.md`, `TASKS.md`, accepted ADRs, `REPRODUCING.md`, and
`UPSTREAM.md`. The archive is historical context and cannot override them.

## Canonical terminology

| Term | Required meaning and usage |
| --- | --- |
| `exact_on_support` | Exact only for the finite support recorded in the result; never a claim of full-vocabulary or future-trajectory global exactness. |
| `OPTIMAL` | The represented-support optimum, accompanied by a reconstructible witness path, witness token sequence, selected proposal IDs, and independently recomputable objective value. |
| `INFEASIBLE_ON_SUPPORT` | No grammar-valid completion exists on the represented finite support; it is distinct from timeout. |
| `TIMEOUT` | The solver did not finish within its budget; it is never evidence of infeasibility. |
| `UNSUPPORTED` | The requested valid instance or semantics are outside the implemented solver capability. |
| `ERROR` | Malformed input or an internal failure; it is not silently converted to another status. |
| finite slots | A witness consumes exactly the token slots allowed by the configured EOS/PAD semantics; abstract `Sigma*` gaps are not certificates. |
| proposal | An indexed `(position, token_id, non-negative weight)` candidate; duplicate proposal IDs remain independently represented. |
| witness | The independently validatable grammar path and token sequence certifying a result and preserving every fixed canvas position. |
| progress fallback | A witness-derived token committed to prevent stalling; it is not counted as a matched model proposal unless it actually matches one. |
| serial baseline | The preserved exact serial validation strategy. |
| EPIC baseline | The preserved EPIC heuristic parallel-selection strategy, with serial fallback reported when used. |
| exact strategy | The separate MWPC strategy; it does not replace or rename either baseline. |

Only the primary non-negative MWPC score is a theorem-level objective unless a
lexicographic objective is explicitly implemented and tested. “Per-step
optimal” always refers to the current proposals and state, not the future
denoising trajectory.

## Consequences

T1300 and T1301 must write English prose around generated English tables and
captions. Translation alone cannot change equations, claims, citations,
status semantics, evidence, or measured data. Mixed-language prose outside the
Portuguese `Resumo`, official proper names, and cited titles is a regression.

