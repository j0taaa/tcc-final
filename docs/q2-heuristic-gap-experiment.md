# Q2 heuristic optimality-gap experiment

T1102 is an offline comparison of component selectors, not complete denoising
decoders. The stable artifact names are:

- `greedy_exact_feasibility`: the order-greedy feasibility-preserving
  component historically used to model serial selection;
- `epic_regular_cover`: the unchanged pinned EPIC regular-cover component,
  with its exact-shrink check enabled and its minimum-batch behavior retained;
- `exact_mwpc`: the Rust production exact optimizer.

All three consume the identical ordered proposal tuple, model confidences,
canvas, explicit per-position support, tokenizer mapping, and paired grammar
representations. EOS/PAD side effects and decoder fallbacks are outside this
component-selection experiment. In particular, an empty EPIC batch remains an
empty heuristic selection; it is not silently replaced with a serial fallback
inside the reported score.

## Configured synthetic states

The executable non-publication configuration contains three deterministic
finite-slot states. `all-compatible` is a zero-gap control. The two crafted
adversarial states admit either one high-ranked proposal or two jointly better
proposals. `adversarial-weight-mode-divergence` is chosen so that the exact
choice differs between the unit and confidence objectives.

Each state is evaluated separately with:

- `unit`: every primary proposal has weight `1.0`;
- `confidence`: the saved finite non-negative model confidence is copied to
  the MWPC weight.

The proposal positions, token IDs, ordering, confidences, support, and grammar
are unchanged between the two modes. Only the explicitly recorded objective
weights differ. Confidence sums are preservation utilities, not probabilities
or sequence likelihoods.

## Row and gap semantics

One raw row corresponds to one common instance ID and one weight mode. It
records the common-state and weighted-input hashes, grammar and support hashes,
the full support specification, selector statuses, selected proposal IDs,
scores, cardinalities, runtimes, witnesses when available, and diagnostics.
For each non-exact selector the row computes:

```text
absolute_gap = exact_score - heuristic_score
relative_gap = absolute_gap / exact_score
score_equal  = isclose(exact_score, heuristic_score)
```

All configured exact scores are positive, so the relative gap is defined for
every row. Cardinality is the number of selected positive-weight proposal IDs;
the configured candidate universe has at most one proposal per physical
position. Summary equality rates and gap aggregates are derived from the raw
row payloads rather than entered manually.

Every `exact_mwpc` result must be `OPTIMAL`, carry a reconstructible finite
token witness, and match the independent guarded completion oracle. Serial and
EPIC retain `FEASIBLE_ON_SUPPORT` and `HEURISTIC` statuses respectively; these
statuses never acquire an optimality claim. Direct support enumeration also
checks that each reported baseline selection is extendable to a valid finite
completion. Any incomparable status, exact-oracle disagreement, invalid
baseline subset, or baseline score above the verified optimum fails the run
and writes a deterministic benchmark replay fixture.

The scope is per-step `exact_on_support(kind=explicit)`. These synthetic smoke
rows do not establish a full-vocabulary, future-trajectory, real-model, or
runtime-performance claim. Their single-repetition timings are diagnostic
fields only; robust timing and memory methodology is deferred to T1106.
