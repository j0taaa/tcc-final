# ADR 0013: Compact ranked support at the model boundary

- Status: Accepted
- Date: 2026-08-26

Live model adapters rank only the maximum configured adaptive width once, on the model device. They transfer compact token-ID rankings to CPU and reuse prefixes for each adaptive attempt. Dense full-vocabulary logits remain inside the model adapter and are consulted only to gather probabilities for a returned witness. The exactness claim remains `exact_on_support`; this changes representation cost, not the optimization problem.
