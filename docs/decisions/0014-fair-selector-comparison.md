# ADR 0014: Distinguish component selectors from complete decoders

- Status: Accepted
- Date: 2026-08-26

Offline Q2 comparisons use the names `greedy_exact_feasibility`, `epic_regular_cover`, and `exact_mwpc`. They share one ordered tuple of ordinary, represented, one-per-position proposals with saved confidence and MWPC weight. EOS/PAD side effects are excluded from this proposal-selection comparison. Complete end-to-end strategies retain the names `serial`, `epic`, and `exact`. The greedy selector uses one total deadline across all feasibility calls.
