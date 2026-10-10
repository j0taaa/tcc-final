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
silently or treat missing verification as success. `check-project` also checks
Python/Rust builds and recorded manuscript artifacts; the user removed the
historical regression suite in M32 and authorized focused M34 tests later. Historical suite evidence remains attributed to its
source revisions. The current formal command checks the library/axiom audit
and canonical resource example, not the deleted fixture/rejection campaign. This
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

`scripts/exact_commit/check_formal_project.py` builds the retained library and
new `MWPC.CfgSampling`, `MWPC.SemanticProfiles` and `MWPC.AdaptiveSemantics`
modules, audits 66 statements across `Audit.lean` and
`AuditCfgSampling.lean`, and checks the canonical resource example. Historical
fixture/forgery campaigns are recoverable in their source commits; they do not
run in the reduced tree. The focused posterior suite runs separately: eight
M34 checks, three M35 regressions and one M36 research event oracle. M36's
action-event reduction has not been mechanized; its finite oracle is not a novelty
proof or a substitute for the requested independent human review.

M34 adds row-product scaling, two-type opening-stack counting/distinctness and
a finite fooling-set state lower bound. The state bound assumes explicit
prefix/suffix soundness; instantiation with balanced delimiters is a written
proof. This is not a Lean-verified tokenizer, grammar normalizer, forest compiler,
inside/outside implementation or complete sampling-law refinement. Existing
formal sources and their archived hashes remain unchanged; the new module/audit
are separate additions.

The continued M36 research adds nine audited semantic-profile statements,
including `semantic_nonnegative_bilinear_lower_bound`: the full `3^m` lower
bound for non-negative natural-coefficient bilinear plans with a positive
uniform tensor scale. It reduces coefficients to finite support rectangles
and counts distinct ternary witnesses in the kernel. Rational denominator
clearing and the arbitrary-real coefficient case remain written arguments.
Signed `2^m` optimality, the execution-conditioned sampling law and Python
semantic lifting are not source-refined in Lean. The three focused semantic
oracles and opt-in MDLM/JsonLogic demonstration are separate evidence; they
do not provide the missing independent human novelty review.

`MWPC.AdaptiveSemantics` adds thirteen selected statements: a rejected
candidate violates a fresh requirement, distinct refinement indices number at
most `m`, and eliminating all invalid parity words through sound prefix
exclusions needs `2^(n-1)` prefixes for `n` choices. The latter applies even
with a perfect prefix-validity oracle. It is a zero-rejection representation
bound, not an expected-time bound on native CARS. The exact adaptive stream
law, JsonLogic encoding, complexity instantiation and Python source are written
or independently tested obligations; they are not fully mechanized.

Three additional core statements check that zero counted violations imply an
omitted requirement, that every requirement then agrees with the core predicate,
and that this equality preserves arbitrary natural-weight sums after domain
restriction. These statements do not certify the CFG-to-path-count compiler;
uniform positive counting and rational scaling are explicit separate obligations.

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
The focused suite was rebuilt after the user-authorized reset and now contains
87 posterior, semantic and independent research checks; the historical suite
remains archived rather than restored. The paper's DP completeness proof, infinite-language separation
constructions, the CFG posterior/sampling law and exact update-round formula remain written proofs; the
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
`grammar_yield_alphabet` and `alphabet_support_transport` additionally prove
terminal-alphabet containment and its explicit support-coverage consequence,
including productive recursive grammars. The Python checker scans every
original vocabulary emission and checks all masked rows (ABSENT EOS only).

M29's small constructed two-slot conflict certificate is kernel-checked in
`docs/evidence/m29-concrete-conflicts-lean.json`. A real 75-node replay resource
export exceeded the 180-second deadline; that report retains the incomplete
attempt explicitly. All replay certificates pass the independent Python
checker, but no claim that every large replay certificate passed Lean is made.
The optional `--lean-limit N` selects the N smallest serialized distinct cores
with stable fingerprint tie-breaking and records its scope; without it all
31 distinct replay cores are attempted. Formal subprocess deadlines now kill
Lake's actual Lean descendants, covered by an executing process regression.

## Certified closure and finite-budget envelope boundary

`MWPC/ExactEnvelope.lean` adds seven universal integer-count specifications:
factorization and summation of returned counts, complete partition identity,
local law after finite-budget acceptance, rejected count versus upper tail,
power-monotonic finite refusal and its normalized cross-multiplied certificate.
`MWPC/CertifiedAmplification.lean` adds two comparisons: transport of a lower
conditional numerator to the true count, and the strict valid-mass improvement
after multiplying one original weight. `AuditExactEnvelope.lean` prints their
axioms; the mandatory runner builds and audits both modules. The complete
formal command passed, with source hashes and verification recorded in
`attempts/25-exact-envelope-sampling/work/evidence/formal-v2`.

Counts have explicit partition/coverage premises. These proofs do not establish
that Python constructs the covered event envelope, performs its random choices
or validates token bytes correctly. The closure-frontier coverage, factorial
certificate separation and full confidence-policy coupling are written proofs.
The finite interrupted sampler has FAIL; local accepted-law equality does not
assert equality of an entire run conditioned on successful completion. The
trajectory comparison is to a decoder of frozen-product posteriors, not the
native conditioned MDLM law. New tests and actual neural application evidence
complement these delimited specifications; they do not extend Lean's scope.
