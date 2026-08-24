# Exact-commit configurations

Immutable experiment and reproduction configurations live here. Every result
artifact must identify its configuration, support policy, seed, grammar hash,
model/tokenizer revision when applicable, and exactness scope.

`m5_rust_differential.toml` freezes normal and extended cross-language
campaigns. Each epsilon-normalized graph is solved by Python, Rust, and an
exhaustive path oracle; generated summaries are versioned under
`docs/evidence/` and exact mismatch fixtures go to ignored `artifacts/`.
