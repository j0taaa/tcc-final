# Start here — AI agent handoff

You are implementing a research artifact, not merely a software feature. A passing demo is insufficient unless the implementation preserves the mathematical contract and emits independently checkable certificates.

## Read in this order

1. `AGENTS.md`
2. `UPSTREAM.md`
3. the current milestone in `TASKS.md`
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`
5. affected source and tests

## Current state

M0 through M6 and T700 are complete. The pinned EPIC baseline has been
reproduced, the scientific contracts are frozen, and both the token-aligned and
generic weighted terminal-DAG Python solvers agree with their independent
exhaustive oracles over the configured deterministic campaigns. Weighted
epsilon edges are normalized with reconstructible original-edge provenance.
The independently implemented Rust production parser and thin PyO3 binding
agree with Python and brute force on all configured M5 normal and extended
cases. The pinned LLaDA tokenizer audit defines a compositional raw ByteLevel
adapter for ordinary tokens and explicitly excludes added control tokens.
Per-position support construction deterministically handles full, top-K, and
explicit rows with fixed-slot validation and canonical fingerprints. The
finite layered token lattice now preserves every represented token choice,
absolute position, aggregate reward, and positive proposal provenance while
making every complete path consume exactly the physical canvas slots. Its
byte expansion uses private raw-byte paths with stable token identity and
single reward attachment, explicitly rejecting unsupported or empty-emission
tokens. Precisely scoped arithmetic, tiny assignment DSL, and restricted JSON
value byte grammars now have documented syntax and versioned valid/invalid
corpora whose labels are recomputed by the independent Boolean recognizer. The
finite-lattice solve bridge now dispatches to the Rust production parser or
Python reference backend, reconstructs terminal-edge certificates to exact
token/proposal provenance, and independently validates every result before
returning `OPTIMAL`. The deterministic M6 normal and extended campaigns passed
2,500/2,500 cases and independently enumerated 42,396 finite token paths. CI
now builds the independent Rust binding, runs Rust-backed differential tests,
replays the normal M6 campaign, and validates the frozen M6 evidence. ADR 0007
freezes the pinned LLaDA EOS/PAD policy: task-specific absent, required, and
optional modes; contextual EOS/PAD roles for the aliased token ID; canonical
PAD-only suffixes; and distinct physical-slot and grammar-content endpoints.
No runtime benchmark or end-to-end dLLM result has been asserted.

The next required task is `T701`: compose token choices with the documented
`BEFORE_EOS`/`AFTER_EOS` automaton while preserving all physical token IDs,
proposal weights, and provenance.
Preserve the completed evidence unless a regression or explicit review finding
invalidates it.

## Non-negotiable rules

- Never edit `vendor/EPIC-Decoding` directly. Use it as a baseline and integrate through `src/mwpc_exact/epic_adapter/`.
- Never report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` optimization globally exact; label it `exact_on_support`.
- A timeout is not infeasibility.
- Do not move to Rust, token lattices or dLLM integration until the earlier differential-test gates pass.
- Preserve deterministic seeds and save every counterexample as a regression test.
- Do not fabricate measurements or fill article placeholders from estimates.

## Definition of the next deliverable

Complete T701's EOS/PAD regular constraint as a separate composition step.
Permit only the transitions frozen by ADR 0007, consume every physical slot,
preserve EOS/PAD reward provenance, normalize any introduced epsilon edges
safely, and reconstruct every valid physical token ID. Do not weaken or mutate
the completed ordinary-token M6 path.
