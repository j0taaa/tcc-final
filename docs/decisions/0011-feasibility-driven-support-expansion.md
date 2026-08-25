# ADR 0011: Adaptive support expansion stops at first feasibility

- Status: Accepted
- Date: 2026-08-25
- Applies to: T802 and later exact-mode configuration

Adaptive top-K expansion retries only after `INFEASIBLE_ON_SUPPORT` and stops
at the first conclusive feasible support. It is therefore a
**feasibility-driven first-feasible policy**, not an optimization over every
configured width through `k_max`. Each returned optimum remains exact on its
represented support. Diagnostics use `stopping_policy=first_feasible` and
`observed_optimal_objectives_non_decreasing`; they do not imply that wider
feasible supports were evaluated.
