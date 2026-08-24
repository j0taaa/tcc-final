# ADR 0008: Separate support membership from EOS/PAD validation

- Status: Accepted
- Date: 2026-08-24
- Applies to: public certificate validation, the finite-lattice bridge, and M7

## Context

A finite witness must satisfy two different predicates:

1. every physical token choice belongs to the represented per-position support;
2. the complete token sequence obeys the configured EOS/PAD policy.

The M6 bridge previously passed support membership through the validator's EOS hook. The boolean result was conservative, but a failure would have been classified as `EOS_REJECTED`, obscuring whether support construction or termination semantics was at fault. T701 introduces real EOS/PAD behavior, so the distinction must be executable before that work continues.

## Decision

The independent validator exposes an optional `SupportWitnessValidator` and the stable failure code `SUPPORT_REJECTED`. The existing `EOSWitnessValidator` is reserved for termination and padding semantics.

The completed ordinary-token M6 bridge performs both checks separately:

- support membership verifies one represented token at every physical slot;
- the `ABSENT` EOS profile verifies that every witness token has an ordinary byte emission.

T701 and T702 may replace only the EOS-policy check with the automaton from ADR 0007. They must preserve the independent represented-support check.

## Consequences

- diagnostics identify the correct violated contract;
- M6's no-EOS behavior remains unchanged;
- M7 can add `REQUIRED` and `OPTIONAL` termination semantics without overloading support validation;
- callers that do not have an external support object are not forced to provide a support validator.

## Tests

`tests/exact_commit/test_validator.py` independently covers support rejection alongside grammar, tokenizer, and EOS rejection. The finite-solver and M6 differential suites continue to exercise the full support-to-certificate path.
