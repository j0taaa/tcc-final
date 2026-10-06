# Exact commitment and probability certificates for diffusion language models

The retained TCC implementation has three parts:

- Finite-token CFG inference with independent Python and Rust parsers, exact
  proposal commitment, and the serial/EPIC baselines through a LLaDA adapter.
- Rational budgeted/conflict commitment with portable optimality certificates
  and safe reuse of conflicts/witnesses.
- Probability-mass/error certificates and admission/refusal for one frozen
  mean-field prediction. Grammar ambiguity does not duplicate original tokens;
  unresolved and omitted mass remain explicit.

Exact reward means `exact_on_support` at the current step, not globally optimal
future generation. A probability certificate bounds the declared conditional
mean-field distribution, not semantic accuracy. [Mathematical definitions](docs/research/m26-mathematical-core.md),
[probability proofs](docs/research/m30-probability-certificates.md),
[Lean scope](formal/README.md).

## Small working tree

The user requested a clean test restart and code reduction. All old owned tests,
Rust test modules and upstream tests were removed. The historical campaign
framework, duplicate oracles, repair experiment and `mwpc_research` package were
removed from the maintained source tree. The prior implementation and tests
remain recoverable at Git commit `a98ae8e09f2066157ebf6df05f8873b8600e00fb`.
No replacement test suite was created; `make test` explicitly reports its absence.

Only the current larger-canvas probability campaign/configuration and exact
counter control remain maintained. Recorded outcomes, original inputs/proofs, generated paper
products, all Lean mathematical sources and license notices remain unchanged.
[Reproduction and historical recovery](REPRODUCING.md).

## Use

```bash
make bootstrap
make check
make bootstrap-rust-parser
make build-rust
```

Algorithms are imported from their explicit modules; the root package exposes
only shared data contracts:

```python
from mwpc_exact import SelectionInput, Proposal, EOSPolicy
from mwpc_exact.solver import solve_exact_commit
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.mass_solver import probability_partition
from mwpc_exact.mass_certificate import verify_mass_proof
```

Verify and sample an archived real model prediction offline:

```bash
.venv/bin/python -m mwpc_exact.mass_cli --verify docs/artifacts/raw/m30_probability_v1/probes/proofs/json_schema_type-2-top8_plus_catalog-finite_language_coverage-64.json.gz --sample --max-tv 1/20
make article-results-check
make check-formal LAKE="$HOME/.elan/bin/lake"
make paper
```

These are operational, proof and artifact checks; they do not constitute an
implementation regression suite. EPIC is a pinned production snapshot;
[its provenance](UPSTREAM.md) records every retained hash and test-only removal.

The [complete scaling audit](docs/artifacts/processed/m31_probability_v1/report.md)
retains all 18 new CPU MDLM predictions and all 36 jobs. At 64 queries, admission
at 4/8/16 free slots is 5/6, 1/6 and 0/6. The compact exact control is cheaper on
every completed pair. General practical superiority and substantial novelty
remain unestablished; removing code/tests does not change that conclusion.
