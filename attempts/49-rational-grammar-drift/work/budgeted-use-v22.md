# V22 — A precise online use of the drift certificate

The eight questions in consolidation-v21.md apply. This is a mathematical
application/coupling corollary, not a new claimed coupling principle, deployed
decoder or measured latency benefit. All previous evidence remains immutable.

Reference: finite-horizon dLLM decoding whose step samples the frozen product
conditioned on the admitted CFG, then applies a common update/commitment rule.
Any policy input depending on original confidences is calculated from the
reference table in BOTH executions. The optimizer may replace only the table
used by the conditioned sampler. A resource refusal or unsupported input
keeps the original table; zero reference valid mass uses the common declared
failure behavior. This is not automatically the native EPIC kernel.

At each reached history, audit each considered rounded table. Choose one
only with a valid upper certificate U no larger than the remaining budget.
Deduct U. If no table is admitted, use the original table and deduct zero.
No corpus-specific threshold or favorable table is presumed; the theorem
holds for every initial budget tau in[0,1] and every admission decision.
The remaining budget controls only table admission, never the common policy.

The two trajectory laws have TV at most tau. Sequentially maximally couple
their samplers while histories match. At a common history the probability
of first disagreement is at most its certificate U, by contraction under
the common update. After divergence use arbitrary coupling. Every compressed
execution's remaining budget is nonnegative, so its path sum of U is at
most tau. The expected sum over the matching prefix is therefore at most
tau, and the union bound for first disagreements proves the result.

No enumeration or precomputation of all future histories is required: the
online wrapper guarantees the budget invariant whenever such a history is
actually processed. Nevertheless a lone recorded head does NOT demonstrate
that the wrapper ran at every step. No iterative neural validation is claimed.

What someone would use: deterministic assurance that probability-table
storage precision or another specified head-table substitution changes the
probability of ANY final bounded verifier by at most the declared budget.
No verifier labels are needed to issue the guarantee. The same guarantee
would be much more conservative with sufficiently loose cheap bounds; those
are still preferable if they already certify the chosen budget. Certification
and modified sampling have costs; full generation speed is not established.

This corollary adds an operational contract to the quantitative TV theorem.
It must not be described as newly discovering adaptive coupling or proving
an improvement in the model's semantics. Current work materializes the
mathematical contract; a practical speed claim would need a separate fair
full-cost protocol and iterative neural validation.
