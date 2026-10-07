# AGENTS.md

## Scope and source of truth

This file applies to the repository. Current work and evidence live in `TASKS.md`.

The user explicitly removed the old test suite on 2026-10-05 to rebuild it from
scratch. M32 supersedes the old mandatory suite/benchmark workflow. Do not
restore the deleted suite, create an unsolicited replacement, or call an empty
test run a correctness pass. Historical test evidence belongs to its source commit.

The explicit 2026-10-06 request authorizes necessary fair new tests for M34.
`tests/test_cfg_posterior.py` is a focused independent suite for that extension,
including a pinned external syntax corpus; it does not restore the old suite
or establish correctness of the whole repository.

The repository implements **Exact Maximum-Weight Parallel Commitment (MWPC)** for CFG-constrained diffusion language models, using the EPIC codebase as the integration baseline. Preserve the existing serial and EPIC heuristic decoders as baselines; add the exact method as a separate strategy.

Before changing code:

1. Read this file.
2. Read only the current milestone and its dependencies in `TASKS.md`.
3. Inspect the relevant retained code, proofs and archived evidence.
4. State the scientific/behavioral contract that the change must preserve.

## Execution workflow

- Work through `TASKS.md` in dependency order. Prefer the first unchecked required task whose dependencies are complete.
- Implement one coherent task or tightly coupled task group at a time. Avoid unrelated refactors.
- Do not mark a task complete until all of its acceptance criteria and required tests pass.
- When completing a task, update its **Evidence** field with the commands run and the relevant result or artifact path.
- If blocked, add a `BLOCKED:` note under that task with the exact technical reason, observations, and the smallest next experiment. Do not claim completion.
- Continue with independent tasks when possible. Do not bypass a failed correctness gate to start performance work.
- Never invent test results, benchmark values, model behavior, citations, or TCC results.
- Do not replace `[TO BE MEASURED]`, `[MODEL_ID]`, or similar placeholders with guesses.

## Scientific contract — never violate these rules

1. **Objective.** For proposals `c_j = (position, token_id, weight)` with non-negative weights, maximize the sum of weights matched by one grammar-valid completion represented by the current finite support.
2. **Exactness scope.** A result over top-`K` or any pruned support is named `exact_on_support`, never globally exact over the full vocabulary. Every result must carry its support specification.
3. **Statuses are distinct.** `OPTIMAL`, `INFEASIBLE_ON_SUPPORT`, `TIMEOUT`, `UNSUPPORTED`, and `ERROR` must never be silently conflated. A timeout is not evidence of infeasibility.
4. **Certificate.** `OPTIMAL` requires a reconstructible witness path, witness token sequence, selected proposal IDs, and an independently recomputable objective value.
5. **Selected set.** For non-negative weights, the selected proposal IDs must equal all represented positive-weight proposals matched by the witness, including duplicate proposal IDs when applicable.
6. **Fixed positions.** A witness must preserve every already committed canvas position.
7. **Finite slots.** A witness must consume exactly the token slots permitted by the configured EOS/PAD semantics. Abstract `Sigma*` gaps are not accepted as finite-slot certificates.
8. **No hidden pruning.** Any pruning that can remove an optimal represented path invalidates `OPTIMAL`. Safe pruning needs a proof, a test, and documentation.
9. **Fallback separation.** A progress fallback may commit a token from the returned witness, but that fallback token is not retroactively counted as a matched model proposal unless it actually matches one.
10. **Per-step guarantee.** The optimizer is exact for the current proposal set and state. Do not claim global optimality over the future denoising trajectory.
11. **Weights.** Reject NaN, infinity, and negative proposal weights at API boundaries. Use `f64`/Python `float` for production scores and integer weights in most oracle tests.
12. **Determinism.** Equal-score solutions may use a deterministic stable tie-break, but only the primary MWPC score is a theorem-level guarantee unless a lexicographic objective is explicitly implemented and tested.

## Architecture boundaries

- `src/mwpc_exact/reference/`: independent, readable Python reference parsing and grammar construction. Correctness first; no model dependencies.
- `src/mwpc_exact/`: proposal policy, finite-support construction, tokenizer adapter, orchestration, validation, diagnostics, and decoder integration.
- `vendor/EPIC-Decoding/rustformlang/` (pinned production snapshot; upstream tests removed) and `crates/mwpc_parser/` (new production solver): performance-critical weighted CFG-on-DAG parser and certificate reconstruction.
- `crates/mwpc_parser_py/`: thin PyO3 bindings. Do not duplicate parsing logic here.
- Existing EPIC modules remain usable without the exact strategy enabled.
- Model-specific code must call a model-independent exact-commit API. Do not put LLaDA/Dream/Qwen-specific logic inside the solver.
- The Python reference solver and the Rust production solver must remain independently implemented so differential tests are meaningful.

Recommended public result shape:

```text
ExactCommitResult
  status
  objective_value
  selected_proposal_ids
  witness_token_ids
  witness_terminal_labels
  witness_graph_edge_ids
  exactness_scope
  diagnostics
```

Do not expose a bare tuple whose fields are easy to confuse.

## Repository and dependency rules

- Preserve `LICENSE` and `THIRD_PARTY_LICENSES.md`; record the upstream EPIC commit used.
- Do not commit model weights, Hugging Face caches, private datasets, credentials, tokens, large traces, or machine-specific absolute paths.
- Future tests must not require network access; new GPU/model runs are opt-in.
- Lock dependency changes. Add a dependency only when the current task requires it and document why.
- The user requires local/GitHub synchronization (2026-10-06). Commit and push
  completed repository changes to the configured upstream before reporting
  completion. This is standing authorization for normal fast-forward pushes;
  report any synchronization failure explicitly.
- Do not change branches, rewrite history or force-push unless the user explicitly requests it.
- The user-authorized reset removed owned/upstream tests; preserve the baseline production source and its manifest.

## Coding conventions

### Python

- Target the Python versions declared by the repository, with Python 3.11 as the reproducibility baseline.
- Use type hints for public APIs and dataclasses/enums for scientific data contracts.
- Keep reference solvers free of `torch`, model downloads, global caches, and hidden mutable state.
- Raise explicit validation errors for malformed inputs; return solver statuses for valid-but-unsolved instances such as timeouts.
- Keep tensor-to-CPU conversion at integration boundaries, not inside generic graph/parser code.

### Rust

- Put weighted parsing logic in a dedicated CFG module. A future test suite must verify it independently.
- Return `Result`/explicit solver status for user-controlled input; do not panic on malformed graphs, timeouts, or infeasible instances.
- Store backpointers by stable IDs, not borrowed transient objects.
- Validate topological order and graph endpoints at construction.
- Keep production weights neutral unless a task explicitly introduces weighted grammar productions.

### Current verification commands

```bash
make check
make build-rust
make check-formal LAKE="$HOME/.elan/bin/lake"
make article-results-check
make paper
```

These check structure/builds, mathematical proofs and recorded artifacts. They
are not a substitute for the future independent regression/oracle suite.
`make test` now runs only the user-authorized focused M34 suite. Future tests must
compare objectives and independently validated certificates, use recorded
seeds, and keep failures distinct from timeouts and support infeasibility.

## Experimental integrity

- All experiment runs use immutable config files and emit JSONL metadata containing git commit, seed, model and tokenizer revisions, grammar hash, support policy, exactness scope, hardware, software versions, and solver status counts.
- Store raw outputs separately from analysis products. Tables and figures must be generated by scripts, not edited by hand.
- Compare methods on the same saved logits/canvas instances whenever measuring selection quality.
- Time model forward, candidate construction, lattice construction, parsing, backtracking, and update separately.
- Synchronize CUDA around GPU timing and exclude one-time model loading from per-instance decoding time.
- Never write a result into the LaTeX paper unless the producing command, config, raw artifact, and code commit are recorded.

## Completion boundaries

Preserve the per-step/support/probability contracts above. Keep serial/EPIC/exact
usable and mathematical/provenance checks independent of optimization. No
cleanup, compiler run, model demo or certificate check establishes universal
source correctness, scientific priority or practical superiority.
