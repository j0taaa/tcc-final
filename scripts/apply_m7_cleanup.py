#!/usr/bin/env python3
"""Apply the focused post-M6 cleanup without changing the T700 EOS/PAD decision."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}: found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def remove_obsolete_bootstrap() -> None:
    directory = ROOT / ".bootstrap"
    if directory.exists():
        shutil.rmtree(directory)
    for relative in (
        "BOOTSTRAP_STATUS.md",
        "PROJECT_MATERIALIZED",
        "scripts/materialize.py",
        ".github/workflows/bootstrap.yml",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()


def write_entry_documents() -> None:
    (ROOT / "README.md").write_text(
        """# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Research and implementation workspace for the TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

The project implements an exact, certificate-producing optimizer for selecting the maximum-weight compatible set of token proposals at one denoising step. EPIC's serial and heuristic decoders remain read-only baselines. Results over pruned alternatives are reported as exact on the represented support, never as full-vocabulary or future-trajectory optimality.

## Sources of truth

- [`AGENTS.md`](AGENTS.md): scientific and engineering invariants;
- [`TASKS.md`](TASKS.md): authoritative current milestone, completed evidence, and remaining work;
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md): explanatory design and evaluation plan;
- [`UPSTREAM.md`](UPSTREAM.md): immutable EPIC provenance;
- [`docs/decisions/`](docs/decisions/): accepted architecture and scientific decisions;
- [`paper/`](paper/): SBC LaTeX article.

Do not duplicate the current task in this README. Locate the first incomplete required task in `TASKS.md`.

## Setup

```bash
git clone --recurse-submodules https://github.com/j0taaa/tcc-final.git
cd tcc-final
make bootstrap
source .venv/bin/activate
make check
```

Build and verify the independent Rust production parser when the current task requires it:

```bash
make bootstrap-rust-parser
make test-rust-parser
make test-m6-differential
```

Install the heavier pinned EPIC environment only for baseline or model-integration work:

```bash
make bootstrap-epic
```

Model weights, datasets, caches, credentials, and generated raw results are not committed.

## Agent handoff

```text
Read START_HERE.md, AGENTS.md, UPSTREAM.md, and TASKS.md. Locate the first
incomplete required task and continue in dependency order. Do not repeat
completed milestones or bypass correctness gates. Update a task's Evidence
field only after every acceptance criterion and required command passes.
Never invent measurements or replace article placeholders without versioned,
reproducible artifacts. Keep vendor/EPIC-Decoding read-only.
```

## Repository map

```text
src/mwpc_exact/            Runtime contracts, reference solvers, validation, and orchestration
crates/                    Independent Rust parser and thin PyO3 binding
vendor/EPIC-Decoding/      Read-only pinned EPIC baseline
configs/                   Immutable correctness and experiment configurations
scripts/exact_commit/      Reproduction and campaign entry points
tests/                     Unit, oracle, differential, regression, and integration tests
docs/                      ADRs, evidence, history, and reproducibility records
paper/                     SBC LaTeX article
```

## Attribution

EPIC remains governed by its own license and third-party notices inside the submodule. The exact upstream commit is recorded in `UPSTREAM.md`.
""",
        encoding="utf-8",
    )

    (ROOT / "START_HERE.md").write_text(
        """# Start here - AI agent handoff

You are implementing a correctness-critical research artifact. A passing demo is insufficient unless the mathematical contract, exactness scope, and independent certificate checks remain valid.

## First session

```bash
git submodule update --init --recursive
make bootstrap
source .venv/bin/activate
make check
```

Build the Rust binding only when the current task depends on it:

```bash
make bootstrap-rust-parser
make test-rust-parser
```

## Read in this order

1. `AGENTS.md` in full;
2. `UPSTREAM.md`;
3. `TASKS.md`, beginning with the first incomplete required task;
4. only the relevant sections of `IMPLEMENTATION_PLAN.md`;
5. the affected source, ADRs, tests, and evidence files.

`TASKS.md` is the sole source of the current milestone. This file intentionally does not repeat a task number, so it cannot become stale after a gate closes.

## Non-negotiable rules

- Keep `vendor/EPIC-Decoding` read-only and integrate through adapters.
- Preserve serial and EPIC baseline behavior.
- Never return or report `OPTIMAL` without a reconstructible witness and independently recomputable objective.
- Never call top-`K` or explicit support globally exact.
- Never treat `TIMEOUT` as `INFEASIBLE_ON_SUPPORT`.
- Keep represented-support validation distinct from EOS/PAD-policy validation.
- Any disagreement with an exhaustive oracle blocks later optimization and model integration.
- Preserve deterministic seeds and save every discovered counterexample as a regression fixture.
- Do not enter measured values in the article until their raw artifacts, configuration, generation script, and commit are versioned.

When blocked, record:

```text
BLOCKED:
Cause:
Evidence:
Smallest next experiment:
```
""",
        encoding="utf-8",
    )


def update_task_pointer() -> None:
    path = ROOT / "TASKS.md"
    old = """## Current starting point

**M4 / T400.** M0 through M3 are complete at the immutable commits and artifacts
summarized below. The full historical checklist and per-task evidence as it
stood at the M3 gate is archived in
[`docs/history/TASKS-through-M3.md`](docs/history/TASKS-through-M3.md).
"""
    new = """## Current starting point

**M7 / T701.** M0 through M6 and T700 are complete at the immutable commits and
artifacts recorded below. The first incomplete required task is T701: compose
the finite token choices with the EOS/PAD automaton defined by ADR 0007. The
historical M0--M3 checklist remains archived in
[`docs/history/TASKS-through-M3.md`](docs/history/TASKS-through-M3.md).
"""
    replace_once(path, old, new)


def update_validation_boundaries() -> None:
    validator = ROOT / "src/mwpc_exact/validator.py"
    replace_once(
        validator,
        '''class EOSWitnessValidator(Protocol):
    """Validate finite-slot EOS/PAD behavior for witness token IDs."""

    def __call__(self, token_ids: tuple[int, ...], /) -> bool: ...
''',
        '''class SupportWitnessValidator(Protocol):
    """Validate membership in the represented finite token support."""

    def __call__(self, token_ids: tuple[int, ...], /) -> bool: ...


class EOSWitnessValidator(Protocol):
    """Validate finite-slot EOS/PAD behavior for witness token IDs."""

    def __call__(self, token_ids: tuple[int, ...], /) -> bool: ...
''',
    )
    replace_once(
        validator,
        '    TOKENIZER_REJECTED = "tokenizer_rejected"\n    EOS_REJECTED = "eos_rejected"\n',
        '    TOKENIZER_REJECTED = "tokenizer_rejected"\n    SUPPORT_REJECTED = "support_rejected"\n    EOS_REJECTED = "eos_rejected"\n',
    )
    replace_once(
        validator,
        '''    tokenizer_validator: TokenizerWitnessValidator | None = None,
    eos_validator: EOSWitnessValidator | None = None,
''',
        '''    tokenizer_validator: TokenizerWitnessValidator | None = None,
    support_validator: SupportWitnessValidator | None = None,
    eos_validator: EOSWitnessValidator | None = None,
''',
    )
    marker = '''    _run_injected_check(
        name="eos",
'''
    insertion = '''    if support_validator is not None:
        _run_injected_check(
            name="support",
            call=partial(support_validator, result.witness_token_ids),
            rejected_code=ValidationCode.SUPPORT_REJECTED,
            issues=issues,
            skipped=skipped,
        )
    _run_injected_check(
        name="eos",
'''
    replace_once(validator, marker, insertion)

    finite_solver = ROOT / "src/mwpc_exact/finite_solver.py"
    replace_once(
        finite_solver,
        '''"""T605 bridge from finite token support to an independently validated solve.

This module intentionally accepts an already constructed
''',
        '''"""Bridge from finite token support to an independently validated solve.

This module intentionally accepts an already constructed
''',
    )
    support_function = '''def _finite_support_witness_is_exact(
    support: PerPositionSupport,
    token_ids: tuple[int, ...],
) -> bool:
    return len(token_ids) == len(support.rows) and all(
        token_id in support.rows[position] for position, token_id in enumerate(token_ids)
    )
'''
    support_and_eos = support_function + '''


def _absent_eos_witness_is_exact(
    adapter: CompositionalByteLevelAdapter,
    token_ids: tuple[int, ...],
) -> bool:
    """Validate the completed M6 profile in which every slot is ordinary content."""

    unsupported = frozenset(adapter.unsupported_token_ids)
    return not any(token_id in unsupported for token_id in token_ids)
'''
    replace_once(finite_solver, support_function, support_and_eos)
    replace_once(
        finite_solver,
        '''        preliminary_result = ExactCommitResult(
''',
        '''        if not _finite_support_witness_is_exact(support, token_path.token_ids):
            raise _CertificateValidationError(
                "reconstructed witness is outside the represented finite support"
            )
        preliminary_result = ExactCommitResult(
''',
    )
    replace_once(
        finite_solver,
        '''            eos_validator=lambda token_ids: _finite_support_witness_is_exact(
                support,
                token_ids,
            ),
''',
        '''            support_validator=lambda token_ids: _finite_support_witness_is_exact(
                support,
                token_ids,
            ),
            eos_validator=lambda token_ids: _absent_eos_witness_is_exact(
                tokenizer_adapter,
                token_ids,
            ),
''',
    )

    token_lattice = ROOT / "src/mwpc_exact/token_lattice.py"
    replace_once(
        token_lattice,
        '''This module deliberately stops before detokenization.  A :class:`TokenChoice`
identifies one represented token alternative across one physical canvas slot;
T603 expands those choices into byte-bearing ``TokenArc`` objects.
''',
        '''This module deliberately stops before detokenization. A :class:`TokenChoice`
identifies one represented token alternative across one physical canvas slot;
the byte-lattice layer expands those choices into byte-bearing ``TokenArc`` objects.
''',
    )

    package = ROOT / "src/mwpc_exact/__init__.py"
    replace_once(
        package,
        '''    GrammarRecognizer,
    TokenizerWitnessValidator,
''',
        '''    GrammarRecognizer,
    SupportWitnessValidator,
    TokenizerWitnessValidator,
''',
    )
    replace_once(
        package,
        '''    "SupportPolicy",
    "TerminalEdge",
''',
        '''    "SupportPolicy",
    "SupportWitnessValidator",
    "TerminalEdge",
''',
    )

    test_validator = ROOT / "tests/exact_commit/test_validator.py"
    replace_once(
        test_validator,
        '''        tokenizer_validator=lambda tokens, labels: (tokens, labels)
        == ((10, 20), ("a", "b")),
        eos_validator=lambda tokens: len(tokens) == 2,
''',
        '''        tokenizer_validator=lambda tokens, labels: (tokens, labels)
        == ((10, 20), ("a", "b")),
        support_validator=lambda tokens: tokens == (10, 20),
        eos_validator=lambda tokens: len(tokens) == 2,
''',
    )
    replace_once(
        test_validator,
        '''        ("tokenizer", ValidationCode.TOKENIZER_REJECTED),
        ("eos", ValidationCode.EOS_REJECTED),
''',
        '''        ("tokenizer", ValidationCode.TOKENIZER_REJECTED),
        ("support", ValidationCode.SUPPORT_REJECTED),
        ("eos", ValidationCode.EOS_REJECTED),
''',
    )
    replace_once(
        test_validator,
        '''        "tokenizer_validator": lambda tokens, labels: True,
        "eos_validator": lambda tokens: True,
''',
        '''        "tokenizer_validator": lambda tokens, labels: True,
        "support_validator": lambda tokens: True,
        "eos_validator": lambda tokens: True,
''',
    )
    replace_once(
        test_validator,
        '''            "tokenizer": "tokenizer_validator",
            "eos": "eos_validator",
''',
        '''            "tokenizer": "tokenizer_validator",
            "support": "support_validator",
            "eos": "eos_validator",
''',
    )


def write_decision_record() -> None:
    decisions = ROOT / "docs/decisions"
    (decisions / "0008-validation-boundaries.md").write_text(
        """# ADR 0008: Separate support membership from EOS/PAD validation

- Status: Accepted
- Date: 2026-08-24
- Applies to: public certificate validation, the finite-lattice bridge, and M7

## Context

A finite witness must satisfy two different predicates:

1. every physical token choice belongs to the represented per-position support;
2. the complete token sequence obeys the configured EOS/PAD policy.

The M6 bridge previously passed support membership through the validator's EOS hook. The boolean result was conservative, but a failure would have been classified as `EOS_REJECTED`, obscuring whether support construction or termination semantics was at fault. T701 introduces real EOS/PAD behavior, so the distinction must be executable before that work continues.

## Decision

The independent validator exposes an optional `SupportWitnessValidator` and the stable failure code `SUPPORT_REJECTED`. The existing `EOSWitnessValidator` is reserved for termination and padding semantics.

The completed ordinary-token M6 bridge performs both checks separately:

- support membership verifies one represented token at every physical slot;
- the `ABSENT` EOS profile verifies that every witness token has an ordinary byte emission.

T701 and T702 may replace only the EOS-policy check with the automaton from ADR 0007. They must preserve the independent represented-support check.

## Consequences

- diagnostics identify the correct violated contract;
- M6's no-EOS behavior remains unchanged;
- M7 can add `REQUIRED` and `OPTIONAL` termination semantics without overloading support validation;
- callers that do not have an external support object are not forced to provide a support validator.

## Tests

`tests/exact_commit/test_validator.py` independently covers support rejection alongside grammar, tokenizer, and EOS rejection. The finite-solver and M6 differential suites continue to exercise the full support-to-certificate path.
""",
        encoding="utf-8",
    )
    (decisions / "README.md").write_text(
        """# Architecture decisions

Numbered architecture decision records live here. Each ADR states the affected scientific contract, alternatives, consequences, and executable evidence.

- `0001-objective-and-weights.md`: MWPC objective and weight modes.
- `0002-candidate-set-and-schedule.md`: schedule-selected candidates, alternatives, and tie order.
- `0003-exactness-scope.md`: exact-on-support and failure terminology.
- `0004-grammar-normalization.md`: controlled CFG normalization and provenance limits.
- `0005-epsilon-edges.md`: weighted epsilon normalization and path provenance.
- `0006-tokenizer-byte-semantics.md`: pinned LLaDA ByteLevel raw-byte mapping.
- `0007-eos-pad-semantics.md`: task-specific EOS modes, canonical padding, and content endpoints.
- `0008-validation-boundaries.md`: separate represented-support and EOS/PAD validation.
""",
        encoding="utf-8",
    )


def write_cleanup_record() -> None:
    (ROOT / "docs/repository-cleanup-m7.md").write_text(
        """# M7 repository cleanup

This cleanup was based on the M6 tree plus the accepted T700 EOS/PAD decision. It deliberately avoids redesigning the support, token-lattice, byte-lattice, Python reference parser, Rust parser, or M7 automaton.

## Changes

- removed the obsolete in-repository Base64 bootstrap archive, materializer, marker, status file, and integrity workflow;
- made `TASKS.md` the sole source of the current milestone;
- updated the current pointer to M7/T701 without altering T700 evidence;
- separated represented-support validation from EOS/PAD-policy validation;
- clarified production module docstrings;
- restored the complete ADR index.

## Intentionally deferred

Large mechanical refactors such as moving campaign modules or splitting the established Rust parser are deferred until after the M7 correctness gate. Performing them while the EOS/PAD automaton is under active development would create churn without changing the scientific result.
""",
        encoding="utf-8",
    )


def main() -> None:
    remove_obsolete_bootstrap()
    write_entry_documents()
    update_task_pointer()
    update_validation_boundaries()
    write_decision_record()
    write_cleanup_record()


if __name__ == "__main__":
    main()
