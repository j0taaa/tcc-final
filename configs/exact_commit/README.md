# Exact-commit configurations

Immutable experiment and reproduction configurations live here. Every result
artifact must identify its configuration, support policy, seed, grammar hash,
model/tokenizer revision when applicable, and exactness scope.

`m5_rust_differential.toml` freezes normal and extended cross-language
campaigns. Each epsilon-normalized graph is solved by Python, Rust, and an
exhaustive path oracle; generated summaries are versioned under
`docs/evidence/` and exact mismatch fixtures go to ignored `artifacts/`.

`m6_finite_lattice_differential.toml` freezes normal and extended campaigns
over small explicit token supports and variable raw-byte vocabularies. Direct
token-path enumeration is the oracle for both finite-lattice backends, and
every failing seed writes a complete replay fixture under ignored `artifacts/`.

`m7_eos_finite_slot_differential.toml` freezes normal and extended campaigns
over explicit finite slots with required/optional EOS, canonical PAD suffixes,
and fixed ordinary or special positions. A separate token-row EOS interpreter
is the exhaustive oracle; every optimal parser certificate also passes the
public independent finite-slot validator.

`t600_llada_tokenizer.toml` pins the first LLaDA model/tokenizer interface,
expected vocabulary shape, random audit seed, and raw ByteLevel policy. Its
audit summary is versioned under `docs/evidence/`; tokenizer files and model
weights remain in ignored external caches.
