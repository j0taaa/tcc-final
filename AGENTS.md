# AGENTS.md

## Scope and source of truth

This file applies to the entire repository. It is intentionally concise. Detailed work items, dependencies, acceptance criteria, and evidence requirements live in `TASKS.md`.

The repository implements **Exact Maximum-Weight Parallel Commitment (MWPC)** for CFG-constrained diffusion language models, using the EPIC codebase as the integration baseline. Preserve the existing serial and EPIC heuristic decoders as baselines; add the exact method as a separate strategy.

Before changing code:

1. Read this file.
2. Read only the current milestone and its dependencies in `TASKS.md`.
3. Inspect the relevant existing code and tests.
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

- `constrained_diffusion/exact_commit/reference/`: small, readable Python reference algorithms and exhaustive oracles. Correctness first; no model dependencies.
- `constrained_diffusion/exact_commit/`: proposal policy, finite-support construction, tokenizer adapter, orchestration, validation, diagnostics, and decoder integration.
- `rustformlang/`: performance-critical weighted CFG-on-DAG parser and certificate reconstruction.
- `rustformlang_bindings/`: thin PyO3 bindings. Do not duplicate parsing logic here.
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

## Required implementation order

1. Reproduce the unmodified EPIC baseline.
2. Freeze data contracts and exactness terminology.
3. Implement token-aligned CKY max-plus in Python.
4. Implement exhaustive completion/subset oracles and randomized differential tests.
5. Implement a generic weighted acyclic terminal-graph solver and backtracking.
6. Port the production solver to Rust and expose it through bindings.
7. Build a finite token-slot lattice with exact token provenance.
8. Implement the mandatory byte-level tokenizer-aware path; add a lexical transducer only as an optional extension.
9. Add EOS/PAD semantics and independent witness validation.
10. Integrate as `serial | epic | exact` without deleting baselines.
11. Run correctness, optimality-gap, finite-slot, scaling, and end-to-end experiments.
12. Update the TCC only from versioned code, configurations, and generated result artifacts.

## Repository and dependency rules

- Preserve `LICENSE` and `THIRD_PARTY_LICENSES.md`; record the upstream EPIC commit used.
- Do not commit model weights, Hugging Face caches, private datasets, credentials, tokens, large traces, or machine-specific absolute paths.
- Tests must not require network access. GPU/model tests must be opt-in and clearly marked.
- Lock dependency changes. Add a dependency only when the current task requires it and document why.
- Do not change branches, rewrite history, force-push, or push remotely unless the user explicitly requests it.
- Do not delete or weaken existing baseline tests to make a change pass.

## Coding conventions

### Python

- Target the Python versions declared by the repository, with Python 3.11 as the reproducibility baseline.
- Use type hints for public APIs and dataclasses/enums for scientific data contracts.
- Keep reference solvers free of `torch`, model downloads, global caches, and hidden mutable state.
- Raise explicit validation errors for malformed inputs; return solver statuses for valid-but-unsolved instances such as timeouts.
- Keep tensor-to-CPU conversion at integration boundaries, not inside generic graph/parser code.

### Rust

- Put weighted parsing logic in a dedicated CFG module with unit tests.
- Return `Result`/explicit solver status for user-controlled input; do not panic on malformed graphs, timeouts, or infeasible instances.
- Store backpointers by stable IDs, not borrowed transient objects.
- Validate topological order and graph endpoints at construction.
- Keep production weights neutral unless a task explicitly introduces weighted grammar productions.

### Tests

- Compare objective values and certificate validity; do not require identical witnesses when several optima exist.
- Every bug fix adds a minimal regression test.
- Random tests use recorded seeds and print the seed on failure.
- An independent validator must check the final witness rather than trusting parser internals.
- A correctness test failing against brute force blocks integration and benchmarking work.

## Commands

Initial setup, following the EPIC layout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install maturin
python -m pip install -e .
(cd rustformlang_bindings && maturin develop --release)
```

Baseline/complete Python tests:

```bash
python -m pytest -q
```

Exact-commit Python tests after they exist:

```bash
python -m pytest -q tests/exact_commit
```

Rust parser tests after Rust changes:

```bash
cargo test --manifest-path rustformlang/Cargo.toml
cargo fmt --manifest-path rustformlang/Cargo.toml --all -- --check
```

Bindings and differential tests after changing the Rust API:

```bash
(cd rustformlang_bindings && maturin develop --release)
python -m pytest -q tests/exact_commit/test_rust_differential.py
```

Run the existing constrained-decoding regression tests after integration changes:

```bash
python -m pytest -q tests/test_constrain_utils.py tests/test_bindings.py
```

Use the smallest relevant command while developing. Before completing a milestone that changes public behavior, run the full Python suite plus relevant Rust and binding tests. Report commands that could not run and why.

## Experimental integrity

- All experiment runs use immutable config files and emit JSONL metadata containing git commit, seed, model and tokenizer revisions, grammar hash, support policy, exactness scope, hardware, software versions, and solver status counts.
- Store raw outputs separately from analysis products. Tables and figures must be generated by scripts, not edited by hand.
- Compare methods on the same saved logits/canvas instances whenever measuring selection quality.
- Time model forward, candidate construction, lattice construction, parsing, backtracking, and update separately.
- Synchronize CUDA around GPU timing and exclude one-time model loading from per-instance decoding time.
- Never write a result into the LaTeX paper unless the producing command, config, raw artifact, and code commit are recorded.

## Definition of done for the required implementation

The required implementation is complete only when:

- the token-aligned and finite-lattice solvers agree with exhaustive oracles on all configured small cases;
- the independent validator accepts every returned `OPTIMAL` certificate;
- the finite-slot tests distinguish bounded canvases from abstract unbounded gaps;
- the exact strategy works through one real dLLM adapter without breaking serial or EPIC modes;
- heuristic-gap, runtime/memory, and end-to-end scripts run from versioned configs;
- a clean environment can reproduce the main tables/figures; and
- the TCC accurately states the implemented support, tokenizer semantics, limitations, and measured results.
