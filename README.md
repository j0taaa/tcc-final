# Certified grammar inference for diffusion language models

This TCC develops **closure certificates for structured dLLM predictions**.
The input is a frozen product of original token probabilities, a finite canvas
and fixed context. The JSON reference returns a valid bounded-depth sample,
valid mass and original-token marginals, with a deterministic error bound
against conditioning on the complete recursive language.

The certificate pays attention to the **probability of closing** a deep structure
in the remaining slots. A refinement keeps grammatical syntax through the
first overflowing original token and uses a lexical counter afterward. It
preserves aliases, token boundaries and intratoken depth. It is an incremental
specialization of established weighted abstraction and inference principles.

The useful result is now supported by both mathematics and independent evidence:

- A fixed-tokenizer JSON family proves **constant-depth certification versus
  linearly growing first-overflow certification depth**. The resulting
  exponential state separation applies to explicit stacks, not every CFG solver.
- The complete independent query campaign has **1,215/1,215 records** across
  all five eligible external documents and 15 masked states. The selected
  method meets the prespecified wall **and** CPU criterion against all six
  mandatory controls in **3/15 states**, including cold preparation in two.
  The criterion is a paired median reduction of at least 20%, with favorable
  sign in every completed repetition, not a universal speedup.
- **30/30 actual iterative MDLM executions** return valid JSON, preserve fixed
  original IDs and use 184 new model forwards. Certified intervals implement
  the same conditional-confidence decisions as the full reference policy.
  One seed demonstrates application, not statistical whole-decoder speed.
- A separate reweighting corollary certifies a strict valid-mass increase when
  its integer condition holds. All 33 captured frames offer such a certificate.
  It intentionally changes the product distribution; it is not semantic quality.

[Implementation, proof and criteria](attempts/24-certified-depth-approximation/README.md),
[full independent evidence](attempts/24-certified-depth-approximation/work/evidence/independent-v1/decision.md),
[main article source](paper/main.tex), [research notebook](docs/research/contribution-plan.md).
Every loss and refusal remains available. Native EPIC/CARS/FactorDLM generation
superiority, scientific priority, human review and publication are not claimed.

## Run a complete public model-head example offline

This packet includes all original logits/probabilities, tokenizer bytes, fixed
context and licenses of one capture chosen before performance observations.
It requires NumPy but **no model weights, Torch, GPU or network**:

```bash
make bootstrap
.venv/bin/python -m attempts.24-certified-depth-approximation.work.demo \
  --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip \
  --tolerance 1/1000 --seed 42
```

The command prints valid JSON, original IDs, the lower mass, normalized error
certificate and full-posterior intervals for the sampled original tokens.
It reports packet audit, preparation and query costs; one example is not a
benchmark. Resource refusal is inconclusive. This reference remains isolated
in its attempt rather than duplicating another solver in the production core.

The packet supports an additional opt-in bit-equal Torch CPU softmax check:

```bash
.venv-live/bin/python -m scripts.exact_commit.full_head_packet \
  --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip \
  --torch-exact
```

The other large heads and exact matrices remain local with published hashes.
The packet reproduces logits-to-softmax, not an independent backbone rerun.
Actual full-V policy zeroes MASK, retains unsupported ordinary emissions in
the denominator, and does not use top-K or answer injection.

## Guarantees and alternatives

For shallow valid mass `L` and a sound deep-tail upper mass `U`, sampling is
exact on `J_d`, with TV error at most `U/(L+U)` against the complete frozen
posterior. Confidence thresholds are decided by intervals; ambiguous decisions
refine or fall back to full inference while retaining the same sampled word.
A common-policy coupling bounds the whole frozen-posterior decoder's output
TV, provided preparation and recognition conclude. It is **not** the native
conditioned MDLM trajectory or semantic correctness.

Simple exact methods and rejection remain faster on easy inputs. Handoff has
stronger bounds at the same depth, but no additional 20% runtime gain over
closed was demonstrated. Compact CFG inference remains an essential control.
[Attempt25](attempts/25-exact-envelope-sampling/README.md) separately investigates
exact envelope sampling, including finite-budget FAIL and strong counter+CARS
controls. Its complete702-record development failed all18 primary first-sample
gates; one secondary batch gain remains unconfirmed independently. Its timings
cannot inherit the query wins of attempt24. The timer error is retained and
the negative decision has error-independent blockers for all candidate states.

The maintained core retains separate contracts:

- `src/mwpc_exact/cfg_posterior.py`: checked LL(1) byte grammars, exact original-token
  mass, marginals and sampling; reusable after compatible reweighting,
  support restriction and further commitments, ABSENT EOS.
- MWPC: maximum declared proposal-weight commitment in represented support,
  independent Python/Rust parsers and portable certificates. Per-step utility
  does not imply future-trajectory optimality.
- General-CFG probability envelopes: ambiguity-safe partial certificates,
  explicit support scope and resource refusal.
- Serial and pinned upstream EPIC remain separate production strategies.

```python
from random import Random
from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.mass_certificate import ProbabilityInput

plan = compile_cfg_sampler(source_grammar, selection_input)
posterior = plan.evaluate(ProbabilityInput(selection_input, original_probability_rows))
if posterior.valid_mass:
    tokens = posterior.sample(Random(42))
```

Top-K results remain `exact_on_support`. General posterior preprocessing has
cooperative deadlines/work limits; canonical source comparison can be exponential
and is refused at its cap. Expansion of support, releasing fixed positions or
changing grammar/tokenizer/EOS requires new preparation. These work limits do
not constitute hard OS preemption. The experimental JSON campaigns separately
use equal physical solver limits.

## Verification and preservation

```bash
make check
make test
make build-rust
make check-formal LAKE="$HOME/.elan/bin/lake"
make article-results-check
make paper
```

The focused suite has 87 independent checks, including exact original-token
product/random-law oracles. The historical suite remains removed as requested.
The article generator recomputes adoption decisions from every archived raw
record and verifies all application transitions; this differs from rerunning
all large solvers/neural forwards. Lean checks selected count/algebra specifications,
not the complete Python/Rust software, tokenizer, backbone or trajectory.
[Formal boundary](formal/README.md).

All 25 research attempts, starting with the initial repository and first working
prototype, have independent frozen source/proof/evidence snapshots. Refinements
never overwrite earlier versions. [Index](attempts/README.md),
[catalog](attempts/catalog.json), [current tasks](TASKS.md).
`make attempts-check` verifies integrity, not novelty or usefulness. Models and
large caches are excluded. Rejected directions, failed external transfer and
faster controls remain in the archives; semantic attempts15/16 are not the
article's protagonists. Code, sources and article are synchronized on `main`.

MIT applies to project software; preserve upstream and dataset licenses in
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) and the pinned [UPSTREAM.md](UPSTREAM.md).
