# ADR 0002: Candidate set and schedule semantics

- Status: Accepted
- Date: 2026-08-23
- Applies to: proposal policy, exact decoder orchestration, offline baseline
  comparisons, and fallback accounting

## Context

The existing denoising schedule determines how much progress a decoding step
attempts. The exact optimizer must compare fairly with serial and EPIC
selection without silently changing which model proposals are eligible or
confusing a schedule budget with a second optimization objective.

## Decision

At denoising step `s`:

1. Rank currently masked physical positions using the schedule's recorded
   confidence value, descending. Break equal confidence deterministically by
   ascending absolute canvas position.
2. Let `P_s` be the first `k_s` positions in that order, or all remaining
   masked positions when fewer than `k_s` remain.
3. Construct the candidate collection `C` only from model proposals attached
   to positions in `P_s`. The initial schedule-compatible policy contributes
   one main proposal per position.
4. Freeze `C`, its input order, weights, confidences, and support metadata
   before invoking grammar optimization. The solver cannot create candidates
   or move proposals to other positions.
5. Include finite-support token alternatives needed to form a completion.
   Any alternative that does not match a proposal in `C` has zero proposal
   reward.

The optimizer has no additional constraint `|selected_proposal_ids| <= k_s`.
Under the initial one-proposal-per-position policy, `|C| <= k_s`, so the
selected set and the number of proposal-backed committed positions are also at
most `k_s` automatically. The generic API permits multiple distinct proposal
objects for one selected position. If several propose the witness token, every
positive-weight ID is selected; the ID count can then exceed `k_s`, but only
one physical token is committed at that position and no more than `k_s`
candidate positions are committed.

The witness may contain zero-reward alternatives at candidate or other finite
slots so that it remains a complete grammar-valid certificate. Such a token is
not proposal-backed and is not committed as part of the matched MWPC batch.
If orchestration uses a witness token as a progress fallback, it records that
action separately and does not retroactively add a proposal ID or reward.
T803 chooses among still-masked positions by the model probability assigned to
the returned witness token, descending, then by ascending absolute canvas
position. The probabilities are supplied explicitly at the model-independent
decoder boundary; the decoder does not reload logits or infer model state.

## Determinism and comparison

The canonical candidate order is schedule rank followed by proposal input
order; aggregation retains first-seen token-choice order and proposal-ID
order. Equal primary MWPC scores follow the solver's documented stable
traversal. This affects which optimal witness is returned, not the guaranteed
score.

Offline serial, EPIC, exact, and brute-force comparisons must consume the same
saved canvas, `P_s`, `C`, weights, and finite support. Method-specific
candidate regeneration is not a fair comparison.

## Consequences

- Grammar compatibility may reduce the proposal-backed batch below `k_s`.
- The exact result is optimal for this step's frozen `C` and represented
  support, not for future denoising steps.
- Expanding top-K token support can change feasibility and the optimum but does
  not change `C` unless a separately recorded policy explicitly rebuilds it.
- A true exact cardinality budget is a different problem and remains optional
  O100 work.

## Executable enforcement

T101 provides deterministic proposal aggregation and preserves all matching
IDs. T800 implements schedule-compatible construction of `P_s` and `C`; its
tests exercise confidence ties, `k_s` larger than the remaining mask count,
zero-reward alternatives, and multiple proposal objects at one position. The
independent validator in T105/T702 recomputes selected IDs and reward rather
than trusting solver bookkeeping. T803 additionally rejects an optimal decoder
input without recorded independent certificate validation, recomputes
proposal matches at commit time, and verifies that witness-backed updates
remain completable by the same witness.
