# Start here — AI agent handoff

You are implementing a research artifact, not merely a software feature. A passing demo is insufficient unless the implementation preserves the mathematical contract and emits independently checkable certificates.

## Read in this order

1. `AGENTS.md`
2. `UPSTREAM.md`
3. the current milestone in `TASKS.md`
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`
5. affected source and tests

## Current state

M0 through M5 are complete. The pinned EPIC baseline has been reproduced, the
scientific contracts are frozen, and both the token-aligned and generic
weighted terminal-DAG Python solvers agree with their independent exhaustive
oracles over the configured deterministic campaigns. Weighted epsilon edges
are normalized with reconstructible original-edge provenance. The independently
implemented Rust production parser and thin PyO3 binding agree with Python and
brute force on all configured M5 normal and extended cases. No tokenizer-aware
lattice, runtime benchmark, or end-to-end dLLM result has been asserted.

The next required task is `T600`: audit a candidate model/tokenizer at an exact
revision and choose a tested token-to-byte semantics. Preserve the completed
evidence unless a regression or explicit review finding invalidates it.

## Non-negotiable rules

- Never edit `vendor/EPIC-Decoding` directly. Use it as a baseline and integrate through `src/mwpc_exact/epic_adapter/`.
- Never report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` optimization globally exact; label it `exact_on_support`.
- A timeout is not infeasibility.
- Do not move to Rust, token lattices or dLLM integration until the earlier differential-test gates pass.
- Preserve deterministic seeds and save every counterexample as a regression test.
- Do not fabricate measurements or fill article placeholders from estimates.

## Definition of the next deliverable

Complete T600's tokenizer/model audit without assuming that concatenated
per-token decoding equals full-sequence decoding. Record the exact revision,
Unicode/whitespace/byte-fallback/special-token behavior, unsupported tokens,
and the chosen compositional or stateful adapter in ADR 0006 before byte-lattice
implementation begins.
