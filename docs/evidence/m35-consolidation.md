# M35: correction gates, bounded compilation and article consolidation

The review of `db8bc99` correctly identified two gaps: CI did not run the
focused posterior suite, and original source/input matching could expand
nullable bodies without the compiler's work/deadline protection. Neither a
green historical CI nor the archived result checker proved current posterior
outputs correct.

## Preserved contract and changes

CI now runs `make test VENV_PY=python`. The focused suite adds three archived
input recomputations, one per final M34 cohort, chosen only by free-slot count
then case ID. It compares rational valid mass and every token marginal with
the immutable archived output. Two additional tests cover preprocessing caps,
shared deadlines, long nullable productions and byte-prefix construction. The
historical suite remains removed.

`compile_cfg_sampler` now shares one cooperative deadline through LL(1)
admission, source/input matching, private binarization and normalization, token
DAG construction and forest building. `max_preprocessing_work` defaults to
1,000,000 work units (symbol visits/copies and intermediate alternatives).
Nullable expansion checks projected work before allocating its growing lists;
stable deduplication removes identical bodies while retaining first-occurrence
order. A 24-distinct-nullable-symbol grammar is refused at its work cap, rather
than materializing all 2^24 combinations; 24 repeated epsilon-only symbols
compile successfully after deduplication.

The canonical source/input equality check remains mandatory. There is no claim
of a polynomial algorithm for arbitrary canonical normalization or CFG
equivalence. Distinct optional bodies can still require exponential output and
are refused. These are cooperative checks, not an OS memory cap or hard
preemption of one Python operation. `CompilationLimit` leaves feasibility and
valid mass unresolved. Original posterior masses, marginals, sampling law,
support/fixed-slot contracts and the EPIC snapshot remain unchanged.

The article now introduces and formulates the posterior first, places its
empirical evidence first in Results, and presents MWPC/certificates as
complementary capabilities. Reproduction documentation distinguishes archive
consistency (`--check`), current-solver replay (`--recompute`) and optional
full-logit provenance checks. Git contains the rational probabilities and
tokenizer semantics, not complete model logits; full-softmax provenance is
still not an offline checkout guarantee.

## Validation

- `make check test`: Ruff/format/MyPy (58 source modules), unchanged EPIC
  production and all 11 focused tests pass, including original independent
  product/RNG/external-corpus oracles and three current-solver archive replays.
- `.venv/bin/python -m scripts.exact_commit.build_cfg_posterior_results --recompute`:
  all 55 final archived inputs attempted; 54 reproduce exact mass and all
  marginals, one remains unresolved without an archived numerical oracle.
  This is a correctness replay, not a new speed or semantic experiment; no
  recorded timings/results are overwritten.
- `make build-rust`: retained parser/FFI format and Clippy pass.
- `make check-formal LAKE="$HOME/.elan/bin/lake"`: library, canonical example
  and all 41 audited declarations pass; no additional source refinement claim.
- `make paper` (including `make article-results-check`): 3,683 prior scientific
  hashes, M31 certificates and M34 archive/products pass unchanged. Article has
  16 pages, no overflow or undefined references. All-page render overview and
  detailed review of introduction/formulation/method/table/limits/conclusion
  confirm the final layout.
- Remote CI gate: pending publication and execution of the changed workflow.

No universal source refinement, semantic benefit, new scientific priority or
general decoder superiority follows from these checks.
