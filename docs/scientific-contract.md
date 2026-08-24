# Scientific contract

The optimizer receives non-negative weighted proposals `c = (position, token_id, weight)` and a finite represented set of possible completions. It maximizes the sum of all positive-weight represented proposals matched by one grammar-valid completion.

An `OPTIMAL` result certifies optimality only over the declared support. For
`SupportKind.TOP_K`, `SupportKind.EXPLICIT`, vocabulary pruning, or any other
support restriction, use `exact_on_support` terminology. `SupportKind.FULL`
means the current finite-slot instance represents the declared full
vocabulary; it does not make the future denoising trajectory globally optimal.
Never infer broader infeasibility from `INFEASIBLE_ON_SUPPORT`.

A public solver must validate that the declared support kind matches the
alternatives actually represented. In particular, `FULL` requires complete
vocabulary coverage. An explicit support may not omit an already committed
token or contain a token that the active token-to-terminal interface cannot
interpret. A support claim is part of the certificate boundary, not free-form
metadata supplied without verification.

Every optimal result must allow an independent implementation to verify:

- the token path uses the permitted physical slots;
- all fixed positions are preserved;
- EOS/PAD rules hold;
- terminal labels follow from the token path;
- the terminal path is accepted by the CFG;
- selected proposal IDs are exactly the matched positive-weight proposals;
- the objective equals their summed weights;
- the represented support matches the declared exactness scope.

The theorem-level guarantee is per denoising step. It does not imply that the resulting future denoising trajectory is globally optimal.
