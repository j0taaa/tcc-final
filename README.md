# Exact finite-token inference for diffusion language models

This TCC implements a model-independent backend for constrained dLLM predictions:

- **Exact recursive-grammar posterior:** checked LL(1) byte grammars, original-token
  probabilities, valid mass, marginals and exact sampling. The compiled forest
  can be reused after reweighting, support restriction and new commitments.
- **MWPC:** exact proposal commitment, independent Python/Rust parsers, portable
  budget/conflict certificates, and unchanged serial/EPIC baselines.
- **General-CFG mass envelopes:** ambiguity-safe partial probability certificates
  with explicit admission/refusal and omitted mass.

The posterior's useful guarantee is mathematical: valid original-token sampling
without rejection or enumerating parser stacks. Typed nesting can require
exponentially many explicit automaton states while the CFG inference remains
polynomial in arithmetic work. These are established parsing principles adapted
and checked for finite dLLM token slots, not invented weighted parsing.

Exactness is **per step and on the declared support**. It is not semantic
correctness, full-vocabulary exactness for top-K, or globally optimal generation.
The posterior currently requires ABSENT EOS and checked LL(1) grammars; work
limits explicitly refuse unresolved cases. [Proofs and prior art](docs/research/m34-exact-cfg-posterior.md),
[Lean boundary](formal/README.md), [complete results](docs/artifacts/processed/m34_cfg_posterior_v1/report.md).

## Use and verification

```bash
make bootstrap
make check
make test
make bootstrap-rust-parser
make build-rust
make check-formal LAKE="$HOME/.elan/bin/lake"
make article-results-check
make paper

# Recompute and sample a genuine archived MDLM prediction; no model/network needed.
.venv/bin/python -m scripts.exact_commit.build_cfg_posterior_results --sample json-context0-16
```

The model-independent API is small:

```python
from random import Random
from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.mass_certificate import ProbabilityInput

plan = compile_cfg_sampler(source_grammar, selection_input)
posterior = plan.evaluate(ProbabilityInput(selection_input, original_probability_rows))
if posterior.valid_mass:
    tokens = posterior.sample(Random(42))
# Reuse plan.evaluate with changed unaries or a contracted/further committed state.
```

The source grammar must normalize to the supplied input grammar. Probabilities
are rational original row values (fixed singleton rows have probability one).
Aliases are distinct choices, missing support mass remains explicit, zero valid
mass and work limits are different outcomes. Expanding support or undoing an
existing commitment requires a new plan. See the focused independent examples
in [tests](tests/test_cfg_posterior.py).

## Evidence and honest comparison

All 52 previously resolved exact masses/marginals survive the integer/grammar
refinement unchanged. It resolves 8/9 fresh full-JSON MDLM canvases; one hits its
work budget. All 18 earlier MDLM array inputs resolve and match the independent
specialized counter, which generally remains cheaper. The 28 declared nesting
probes include controls favoring explicit stack transfer; six large free cases
exceed its representation budget while CFG inference completes.

Exact represented-support rejection is cheaper on the six smaller JSON cases
in the recorded seed. Its expected attempts are represented mass/valid mass;
we do not unfairly charge discarded tokens. These outcomes demonstrate a useful
capability and a scoped representation advantage, not a universal speed win or
execution of EPIC/FactorDLM/LAVE. The full audit includes every failure, negative
control, config, original probability input and producing commit. Full model
logits remain local; compact scientific data are losslessly deduplicated.

## Small maintained tree

The user removed the historical test suite and experiment framework in M32/M33;
they remain recoverable at `a98ae8e09f2066157ebf6df05f8873b8600e00fb` and `9deb3df`.
The 2026-10-06 request authorizes eight focused new posterior tests, not a
restoration of that suite or a whole-project correctness claim. Pinned external
JSON cases are packed in one small archive, with original hashes and license.
The opt-in model capture retains only the necessary audited official MDLM CPU
adapter. External EPIC production stays unchanged at `5b1b310`.

[Reproduction](REPRODUCING.md), [baseline provenance](UPSTREAM.md),
[previous cleanup](docs/evidence/m33-cleanup.md).
