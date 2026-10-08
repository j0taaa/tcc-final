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
make research-note

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

Compilation uses one cooperative deadline through LL(1) admission, both
normalizations, token-DAG and forest construction. `max_preprocessing_work`
(default 1,000,000 symbol/copy/alternative units) bounds preprocessing, including
projected nullable-body expansion before allocation. Canonical comparison can
still be exponential and is refused at its cap; it is not skipped or replaced
by an unchecked equivalence assumption. Chart/forest caps remain separate.
These are work/cancellation limits, not hard OS memory or preemption guarantees.

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
M34 introduced eight focused posterior tests; M35 extends them to eleven with
archived recomputation and preprocessing/deadline checks. M36 adds one research
oracle for confidence-selected commitment events and four focused checks for
the execution-conditioning research reference. The continuation adds four
adaptive-stream/prefix-control checks and two structural-core checks.
CI runs these twenty-two checks;
this is not restoration of the old suite or whole-project correctness. Pinned external
JSON cases are packed in one small archive, with original hashes and license.
The opt-in model capture retains only the necessary audited official MDLM CPU
adapter. External EPIC production stays unchanged at `5b1b310`.

[Current research notebook](docs/research/contribution-plan.md): primary-source
novelty review, candidate event-reduction proof and explicit human-review gates.
This investigation does not establish a new scientific priority or change the
production decoders. A separate [research supplement](paper/semantic-conditioning.tex)
specifies the execution-conditioning algorithm and a tight scoped comparison:
all union-profile masses require `3^m` products in a non-negative bilinear plan,
versus `2^m` using the known signed covering-product transform. It does not
claim a general lower bound for FactorDLM, sparse inputs or single target masses.

The small research API reuses an original-token forest:

```python
from scripts.exact_commit.semantic_json import boolean_rule_grammar, evaluate_semantics

source = boolean_rule_grammar(("a", "b"))  # independent of records and labels
plan = compile_cfg_sampler(source, selection_input)  # input uses this source grammar
posterior = evaluate_semantics(plan, probability_input, boolean_records)
tokens = posterior.sample(target_profile, Random(42))  # only if its mass is positive
```

It fills Boolean rules matching the declared records, not arbitrary JsonLogic
programs or unseen-record labels. Slots, probabilities and support retain their
previous contracts. Work caps refuse unresolved instances. The frozen integration
config and opt-in CPU capture/replay are in
`configs/experiments/m36_semantic_reference_v1.json` and
`scripts/exact_commit/capture_semantic_reference.py`.
The [archived real MDLM illustration](docs/artifacts/raw/m36_semantic_reference_v1/)
was checked against all 108 represented rules and the pinned official JsonLogic
consumer on eight Boolean records. Both declared positive targets were sampled;
the impossible canvas target remains zero mass. CI recomputes the archive with
current code without a model or network. This is an application/reproduction
check, not an external benchmark or proof of novelty/generalization.

The [adaptive research stream](scripts/exact_commit/adaptive_semantics.py)
conditions on requirements discovered through rejected rules and verifies
every declared record before returning tokens. With sufficient resources it
preserves the exact conditional distribution and rejects at most `m` rules
over the entire stream, for `m` requirements. Active profiles remain capped
at twelve; a refusal is unresolved. The supplement proves a scoped exponential
representation gap for non-prefix behavior against zero-rejection prefix
exclusion, including CARS's trie; automata and other competent compact semantic
solvers can share that advantage. The frozen complete-label audit protocol is
`configs/experiments/m36_adaptive_semantics_v1.json`. It includes eager inference,
enumeration and a perfect-oracle prefix control, not native EPIC/CARS timing.

`compile_semantic_core` certifies a smaller subset of requirements using
positive auxiliary weights on every original supported token. Omitted records
must have exactly zero violating paths, so the certificate survives arbitrary
new model weights, support contraction and added commitments. Samples still use
the actual model probabilities. Expansion/released commitments require a new
certificate. Certification and all later queries are included in the cost
analysis; neither minimum-core selection nor universal speed superiority is
promised. A zero model probability alone cannot justify removing a requirement.

[Reproduction](REPRODUCING.md), [baseline provenance](UPSTREAM.md),
[previous cleanup](docs/evidence/m33-cleanup.md).
