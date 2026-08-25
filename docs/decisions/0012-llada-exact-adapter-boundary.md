# ADR 0012: Parent-side LLaDA exact-step boundary

- Status: Accepted
- Date: 2026-08-25
- Applies to: T901 and later LLaDA exact-mode integration

The first model adapter targets the pinned EPIC LLaDA loop immediately after
it has produced the primary token, confidence, and existing `k_s` transfer
budget, but before regular-cover or serial commitment. The EPIC submodule
remains read-only.

Only the generated region is part of the exact canvas. Model tensor position
`p` maps to exact canvas position `p - prompt_length`; prompt positions are
snapshotted and never passed to the byte grammar. Support logits cover every
finite generated slot, including future blocks, while proposals and
witness-progress updates are restricted to currently masked slots in the
active block. A positive `k_s` is reused unchanged as the proposal budget.

The adapter calls `solve_exact_commit_adaptive_validated`, so only the live
independent validation report can authorize an `OPTIMAL` mutation. It maps all
recorded canvas commits back to the single-batch model row and decoded tracking
list. If the generated canvas contains a configured termination token, every
remaining masked physical slot is canonicalized to the pinned PAD ID. This is
the exact-strategy EOS behavior defined by ADR 0007; it is the only update
allowed to cross the active-block boundary. Non-optimal statuses remain on the
decoder result, and a configured serial/EPIC fallback requires an explicit
adapter callback.

Top-K results remain `exact_on_support`. The adapter does not place tensor,
tokenizer, or LLaDA logic in the generic parser. Its tensor surface uses only
CPU snapshot and indexed assignment operations, so runtime Torch remains an
EPIC integration dependency rather than a core solver dependency.

