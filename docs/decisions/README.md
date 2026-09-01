# Architecture decisions

Numbered architecture decision records live here. Each ADR states the affected scientific contract, alternatives, consequences, and executable evidence.

- `0001-objective-and-weights.md`: MWPC objective and weight modes.
- `0002-candidate-set-and-schedule.md`: schedule-selected candidates, alternatives, and tie order.
- `0003-exactness-scope.md`: exact-on-support and failure terminology.
- `0004-grammar-normalization.md`: controlled CFG normalization and provenance limits.
- `0005-epsilon-edges.md`: weighted epsilon normalization and path provenance.
- `0006-tokenizer-byte-semantics.md`: pinned LLaDA ByteLevel raw-byte mapping.
- `0007-eos-pad-semantics.md`: task-specific EOS modes, canonical padding, and content endpoints.
- `0008-validation-boundaries.md`: separate represented-support and EOS/PAD validation.
- `0009-adaptive-timeout-semantics.md`: backend-specific total-timeout semantics.
- `0010-validated-commit-boundary.md`: live independent validation required for commits.
- `0011-feasibility-driven-support-expansion.md`: first-feasible adaptive top-K policy.
- `0012-llada-exact-adapter-boundary.md`: generated-canvas tensor mapping and active-block/EOS rules.
- `0013-compact-ranked-support.md`: compact top-K ranking at model boundaries.
- `0014-fair-selector-comparison.md`: precise offline selector names and shared candidate universe.
- `0015-paired-grammar-alignment.md`: executable alignment evidence for exact/EPIC grammar pairs.
- `0016-publication-evidence-tier.md`: final-article evidence tiers, claim boundaries, and predeclared publication campaigns.
- `0017-q5-publication-pilot-amendment.md`: rejected Q5 pilot and the pre-evidence v2 amendment.
- `0018-q5-task-specific-schedules.md`: v3 task-specific finite-slot Q5 schedules after the v2 expression rejection.
- `0019-q5-model-aligned-dsl-task.md`: v4 fenced DSL replacement after the v3 EPIC-candidate rejection.
- `0020-q2-real-snapshot-support.md`: compact explicit support for 24 shared live Q2 snapshots.
