# ADR 0001: MWPC objective and weight modes

- Status: Accepted
- Date: 2026-08-23
- Applies to: proposal construction, reference and production solvers,
  certificate validation, and experiment reporting

## Context

At one denoising step the model-independent optimizer receives a finite
proposal collection

```text
C = {c_j = (proposal_id, position, token_id, weight)}.
```

It also receives a finite represented completion support constrained by the
current canvas, tokenizer/EOS policy, and CFG. Proposal weights must be finite
and non-negative. Two proposal objects may name the same position and token,
but their IDs and rewards remain distinct.

## Decision

For every represented grammar-valid completion `y`, define

```text
matched(y) = {j in C | y[position_j] = token_id_j}
score(y)   = sum(weight_j for j in matched(y)).
```

MWPC maximizes `score(y)`. An `OPTIMAL` certificate selects exactly the IDs of
the matched proposals with strictly positive weight and independently
recomputes the same sum. A matched zero-weight proposal contributes nothing
and is not part of the selected positive-reward set.

Proposals with an identical `(position, token_id)` choice are aggregated by
summing every distinct proposal object's weight while preserving every ID.
The implementation uses `math.fsum`; confidence metadata is not included by
that operation.

The supported weight modes are:

- `arbitrary`: the caller supplies any finite non-negative utility;
- `unit`: every proposal has weight `1.0`, so the objective maximizes the
  number of matched proposal objects;
- `confidence`: a versioned proposal policy converts model confidence into a
  finite non-negative utility and records that conversion in configuration.

In `confidence` mode, the summed score is a preservation utility. It is not a
joint probability, sequence likelihood, or calibrated probability of CFG
validity. `Proposal.model_confidence` remains separate from `Proposal.weight`
so analysis metadata cannot silently change the theorem-level objective.

Every represented alternative that is not the token of a proposal at that
position receives zero proposal reward. Fixed-position conflicts are excluded
from support rather than assigned a finite penalty.

## Ordering and equal scores

The primary summed MWPC score is the only theorem-level objective. Proposal
aggregation preserves first-seen `(position, token_id)` order and input ID
order. Candidate builders must provide deterministic input order, and each
solver must document a stable traversal order for equal-score updates.

Choosing the first stable equal-score witness is not a lexicographic secondary
objective. Independent implementations and tests may return different valid
witnesses with the same score; comparisons therefore use objective equality
and certificate validity, not witness identity.

## Alternatives considered

- Multiplying confidences was rejected because the proposal objective is an
  additive utility and model probabilities do not form an independent joint
  probability here.
- Using confidence only as an undocumented tie-break was rejected because it
  would create a hidden secondary objective.
- A separate batch-cardinality dimension is deferred to optional task O100;
  candidate-set truncation is not that constraint.

## Executable enforcement

`Proposal`, `AggregatedProposal`, and `aggregate_proposals` enforce finite
non-negative weights, distinct IDs, stable provenance, and confidence
separation. `tests/exact_commit/test_proposals.py` covers invalid weights,
duplicate IDs, accurate sums, duplicate choices, multiple alternatives, and
stable ordering.
