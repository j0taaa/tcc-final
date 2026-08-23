# Start here — AI agent handoff

You are implementing a research artifact, not merely a software feature. A passing demo is insufficient unless the implementation preserves the mathematical contract and emits independently checkable certificates.

## Read in this order

1. `AGENTS.md`
2. `UPSTREAM.md`
3. the current milestone in `TASKS.md`
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`
5. affected source and tests

## Current state

The repository structure, pinned upstream baseline, LaTeX article, CI skeleton and core Python data contracts are present. No baseline build, oracle agreement, parser correctness, tokenizer property, runtime result or end-to-end result has been asserted.

Begin at `T000`. Verify the submodule SHA and licenses, then produce reproducible environment evidence. Do not mark a task complete because files exist; execute its acceptance checks.

## Non-negotiable rules

- Never edit `vendor/EPIC-Decoding` directly. Use it as a baseline and integrate through `src/mwpc_exact/epic_adapter/`.
- Never report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` optimization globally exact; label it `exact_on_support`.
- A timeout is not infeasibility.
- Do not move to Rust, token lattices or dLLM integration until the earlier differential-test gates pass.
- Preserve deterministic seeds and save every counterexample as a regression test.
- Do not fabricate measurements or fill article placeholders from estimates.

## Definition of the first deliverable

Create the token-aligned Python reference solver and two independent exhaustive oracles. Randomized tests must demonstrate:

```text
max-plus CKY optimum
  = exhaustive valid-completion optimum
  = exhaustive compatible-subset optimum
```

for every tested finite instance. Record commands, seed ranges and test counts in the relevant `TASKS.md` Evidence fields.
