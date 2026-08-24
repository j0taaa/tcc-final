# Start here — AI agent handoff

You are implementing a research artifact, not merely a software feature. A passing demo is insufficient unless the implementation preserves the mathematical contract and emits independently checkable certificates.

## Read in this order

1. `AGENTS.md`
2. `UPSTREAM.md`
3. the current milestone in `TASKS.md`
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`
5. affected source and tests

## Current state

M0 through M3 are complete. The pinned EPIC baseline has been reproduced, the scientific contracts are frozen, the token-aligned Python solver is implemented, and its objective agrees with both exhaustive oracles over the configured deterministic campaign. No tokenizer, Rust-production-parser, runtime benchmark, or end-to-end dLLM result has been asserted.

The next required task is `T400`: validate and index a generic weighted terminal DAG. Preserve the completed evidence unless a regression or explicit review finding invalidates it.

## Non-negotiable rules

- Never edit `vendor/EPIC-Decoding` directly. Use it as a baseline and integrate through `src/mwpc_exact/epic_adapter/`.
- Never report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` optimization globally exact; label it `exact_on_support`.
- A timeout is not infeasibility.
- Do not move to Rust, token lattices or dLLM integration until the earlier differential-test gates pass.
- Preserve deterministic seeds and save every counterexample as a regression test.
- Do not fabricate measurements or fill article placeholders from estimates.

## Definition of the next deliverable

Implement M4's generic weighted terminal-DAG reference solver without weakening the completed M3 gate. The DAG implementation must validate acyclicity and stable IDs, reconstruct a certificate, agree with explicit path enumeration on tiny graphs, and reduce exactly to the token-aligned solver on layered per-slot DAGs.
