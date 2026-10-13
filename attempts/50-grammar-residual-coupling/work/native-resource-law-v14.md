# V14 — Resource censoring is not an exact sampling theorem

2026-10-13, separate audit AFTER V13. Do not change V13's frozen protocol,
producer or measurements. No additional forward or benchmark is performed.

V13 returns23 valid JSONs in24 correction records, with one timed resource
refusal. These are functional observations. They must NOT be presented as a
proof that the RESOURCE-WRAPPED successful outputs have exactly the target
law. The underlying unlimited residual algorithm has the law proved earlier;
an external wall timer has a distinct probabilistic contract.

## 1. Why the distinction is real

Let an exact sampler output y~rho but finish by a wall deadline with probability
s(y). Successful deadline-censored outputs have density proportional to
rho(y)*s(y), not generally rho(y). A tiny example has two equally likely
outputs, with one taking one work unit and the other two; a deadline between
them selects the first. Returning FAIL honestly does not remove this bias
when a caller conditions on successful completion. Restarting a fresh exact
sampler only on the slow outputs also does not automatically restore rho.

An ATTEMPT cap in an independent rejection sampler is different: the accepted
value's law is independent of its geometric attempt number. Conditional
success by attempt K retains rho. Nevertheless, a complete maximal-coupling
update with residual failure has the SUBPROBABILITY output measure

    min(P(y),Q(y)) + [1-(1-alpha)^K]*(P(y)-Q(y))_+,

with failure mass TV(P,Q)*(1-alpha)^K. Its conditional-success distribution
is not generally P. The source's FAIL is not an exact target draw, and neither
the23 successes nor a finite oracle can prove an unlimited software liveness
claim. The source's status FUNCTIONAL_RESOURCE_ONLY remains appropriate.

## 2. A lawful future resource handoff

Timing/preparing a proposal before its sampling randomness is drawn can
select between different EXACT rho samplers without bias, provided each
selected sampler uses fresh independent randomness and the same immutable
P,Q,original-ID domain. Preparation refusals may choose a competent alternate
sampler. Actual random sample generation must not then be wall-censored and
claimed exact. A successful primitive still has random runtime.

At a deterministic attempt cap, fresh exact-rho fallback restores rho exactly,
because BOTH cap-success and cap-failure paths use that same output law.
Original-P residual rejection is such a fallback for positive TV, but its
conditional cost is1/TV; using ordinary P alone is WRONG. If a polynomial
attempt-bound sampler has alpha>=1/B and exact rational posteriors satisfy
TV>=1/(Z_A*Z_B), choosing K>=B*ln(Z_A*Z_B) makes the fallback expected
attempt cost at most1. This follows from exp(-K/B)/TV<=1. All K work,
fallback reconstruction/random bits and preparation remain charged.

This is a classical rejection/mixture argument, not new publication priority.
It does not guarantee a deterministic deadline or repair a zero-mass/unsupported
grammar, failed original head capture or biased already-censored initial
draft. Full-dense support admission and generation costs remain unresolved.

## 3. Consequence for V13

The V7 mathematical insertion theorem remains valid under its unlimited
exact-kernel assumptions. V13 is a demonstration that valid original-ID
corrections were executed between actual model canvases; it is not formal
verification of that theorem's entire resource-managed Python realization.
Do not relabel it as exact native EPIC, a faster dJev or a new theorem. Any
production handoff must declare its FAILED/subprobability contract or implement
the lawful uncensored mixture described above before making stronger claims.
