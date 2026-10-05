# Lean verification and its boundary

Lean 4.34.0 is pinned in `lean-toolchain`. The project uses only Lean's standard
library; `lake-manifest.json` has no external packages. After explicitly
installing [Elan](https://github.com/leanprover/elan/releases/tag/v4.2.4), install
the proof toolchain once:

```bash
elan toolchain install leanprover/lean4:v4.34.0
make check-formal
make check-project
```

`check-formal` fails if the toolchain is unavailable. It does not install one
silently or treat missing verification as success. `check-project` also runs
Python/Rust tests, baseline integration and manuscript artifact checks. This
combined gate does **not** mean the Lean kernel proves all foreign source code.

## Universal claims and concrete evidence

| Claim | Lean definition/theorem | Implementation correspondence |
| --- | --- | --- |
| Epsilon and CNF derivation reward bounds | `Certificates.lean`: `epsilon_bound`, `derivation_bound` | Exact resource arcs/potentials exported from portable v2 proof |
| Witness attaining upper bound is optimal | `certified_optimal` | Generated proof constructs the actual epsilon paths and CNF parse; kernel checks every arc/production membership |
| Absent roots certify infeasibility | `certified_infeasible` | Kernel checks finite potential inequalities and all budget-permitted final roots |
| Free-position relaxation bounds every budgeted batch | `Bounds.lean`: `batch_upper`, `upper_attained` | `budget_bounds.py`, independent token validation and exhaustive token/subset tests |
| Additive and multiplicative quality, tightness | `certified_gap`, `multiplicative_bound`, `bound_attainment` | Exact binary-rational rewards; no tolerance or probability interpretation |
| Support expansion cannot improve an attained universal bound | `Selection.lean`: `support_expansion_certificate` | All frozen proposals, including alternatives outside represented support, enter Python relaxation |
| Shared prefix bytes and closing token emission | `Prefixes.lean`: `prefix_walk_emits_prefix`, `closing_emits_token` | Independent `check_budget_graph` checks every original choice and prefix/closing arc |
| Deduplication preserves prefix membership and does not increase nodes | `unique_prefixes_membership`, `compact_node_count` | Private/compact layouts agree with independent original-completion/subset oracle |
| Reward-preserving encodings preserve optima | `representation_preserves_optima` | General lemma has explicit encoding/decoding premises; the actual Python compiler is not universally refined in Lean |
| Same-input dominance, fixed reward offset, budget monotonicity, capacity targets | `Selection.lean` | These assume the specified optimum; generated resource certificates establish it for checked instances |
| Updating with a retained witness preserves feasibility | `witness_update_preserves_feasibility` | Explicit preservation premise; Python update and fixed-slot tests |
| Certified conflicts and a member-complete search cover bound every feasible batch | `Conflicts.lean`: `conflict_cover_bound`, `conflict_certified_optimal` | Original-input Python checker validates each CFG infeasibility proof, cover branch and rational bound |
| Infeasible conflicts transport under contraction; feasible witnesses under expansion | `conflict_transport`, `feasible_witness_transport`, `fixed_conflict_discharge` | Conservative support/semantics containment and independent validation of retained full token witnesses |
| Amortized feasibility-query count | `amortized_conflict_queries` | Trace charges one failed main query plus at most B deletion queries per learned conflict; Python counter/oracle tests |

`scripts/exact_commit/check_formal_project.py` verifies the main four-budget
example, aliases/shared prefixes, fixed split UTF-8 with EOS/PAD, empty emission
and infeasibility. It also changes an upper bound and requires kernel rejection.
These finite cases exercise the bridge; they are not a benchmark win rate.

## Trust map

The mathematical kernel proof is over `Grammar`, `Graph`, `Potentials`,
`Epsilon` and `Derivation`. Nonnegative rational weights become exact natural
units through their common positive denominator. The exporter is untrusted:
it emits proof constructors and finite checks, all rechecked by Lean. Neither
`native_decide` nor admitted proofs nor project axioms are used. `Audit.lean`
prints theorem dependencies; standard logical axioms are listed explicitly.

The independent **Python** checker binds the graph to the original proposals,
token bytes, fixed slots, complete support and EOS/PAD semantics, and checks
original-token witness metadata. An expected external input/fingerprint can
also be supplied. Hashes identify inputs; they are not axioms or mathematical
proofs of compiler correctness. The Lean proof therefore establishes resource
graph optimality; original-input correspondence is a separate checked boundary.

The universal implementation correctness of the Python graph compiler, Python
DP, Rust parser, PyO3/FFI and external tokenizer has not been proved in Lean.
The existing independent oracles and differential/regression tests remain
necessary. The paper's DP completeness proof, infinite-language separation
constructions and exact update-round formula remain written proofs; the
formalized certificate soundness does not silently mechanize all of them.
Model probabilities, quantization, CUDA, system timing, semantic correctness
and future denoising trajectories are outside the formal guarantee.

The new conflict cover is a mathematical specification with explicit leaf
bounds and valid-conflict premises. It does not prove the master/Python source
or tokenizer compiler correct. Concrete learned CFG-conflict certificates can
be exported through the existing resource bridge with
`python -m scripts.exact_commit.build_conflict_results --lean /path/to/lake`;
the report names the concrete certificates checked and retains this boundary.

## Export and verify a portable proof

```bash
.venv/bin/python scripts/exact_commit/budget_math_example.py \
  --verify docs/artifacts/math/m27-budget-proof.json --lean

# New output path: certificate source is deterministic and refuses replacement.
.venv/bin/python scripts/exact_commit/budget_math_example.py \
  --verify docs/artifacts/math/m27-budget-proof.json \
  --lean-source /tmp/BudgetCertificate.lean
cd formal
lake build
lake env lean /tmp/BudgetCertificate.lean
lake env lean Audit.lean
```

The JSON includes the original input, graph meanings, exact potentials and
every budget's witness. `examples/BudgetExample.lean` is its checked-in export.
Historical M26 proofs remain readable with their narrower graph-only scope.
Normal Python tests have no network/Lean dependency; the separate mandatory
CI formal job installs the pinned toolchain and cannot skip the formal gate.

M30 adds `MWPC/Probability.lean`: universal disjoint-partition mass bounds,
scaled L1/conditional error arithmetic, event intervals, finite error-budget
sums and closed CFG yield/support transport. Rational inputs use common natural
units. Python independently checks disjoint token boxes, actual tokenizer/EOS
correspondence and finite-language coverage. The written coupling proof gives
trajectory-TV composition; Lean checks its finite error-budget arithmetic,
not a full probability-library coupling or source-level Python/Rust refinement.
