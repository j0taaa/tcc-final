#!/usr/bin/env python3
"""Apply the post-M8 review fixes while preserving completed evidence artifacts."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {relative}, found {count}: {old[:80]!r}")
    write(relative, text.replace(old, new))


def move_research_campaigns() -> None:
    mapping = {
        "src/mwpc_exact/reference/differential.py": "src/mwpc_research/token_aligned_differential.py",
        "src/mwpc_exact/reference/graph_differential.py": "src/mwpc_research/graph_differential.py",
        "src/mwpc_exact/rust_differential.py": "src/mwpc_research/rust_differential.py",
        "src/mwpc_exact/finite_differential.py": "src/mwpc_research/finite_differential.py",
        "src/mwpc_exact/eos_differential.py": "src/mwpc_research/eos_differential.py",
        "src/mwpc_exact/finite_slot_counterexamples.py": "src/mwpc_research/finite_slot_counterexamples.py",
    }
    destination_root = ROOT / "src/mwpc_research"
    destination_root.mkdir(parents=True, exist_ok=True)
    write(
        "src/mwpc_research/__init__.py",
        '"""Research campaigns, replay fixtures, and evidence-generation helpers."""\n',
    )
    for source_name, destination_name in mapping.items():
        source = ROOT / source_name
        destination = ROOT / destination_name
        if not source.exists():
            raise RuntimeError(f"missing campaign module: {source_name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)

    import_replacements = {
        "mwpc_exact.reference.differential": "mwpc_research.token_aligned_differential",
        "mwpc_exact.reference.graph_differential": "mwpc_research.graph_differential",
        "mwpc_exact.rust_differential": "mwpc_research.rust_differential",
        "mwpc_exact.finite_differential": "mwpc_research.finite_differential",
        "mwpc_exact.eos_differential": "mwpc_research.eos_differential",
        "mwpc_exact.finite_slot_counterexamples": "mwpc_research.finite_slot_counterexamples",
    }
    for path in tuple((ROOT / "src").rglob("*.py")) + tuple((ROOT / "tests").rglob("*.py")) + tuple((ROOT / "scripts").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in import_replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    pyproject = read("pyproject.toml")
    pyproject = pyproject.replace(
        'packages = ["mwpc_exact"]',
        'packages = ["mwpc_exact", "mwpc_research"]',
    )
    write("pyproject.toml", pyproject)

    for relative in (
        "README.md",
        "START_HERE.md",
        "IMPLEMENTATION_PLAN.md",
        "scripts/exact_commit/README.md",
        "configs/exact_commit/README.md",
    ):
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in import_replacements.items():
            text = text.replace(old.replace(".", "/") + ".py", new.replace(".", "/") + ".py")
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def add_backend_boundary() -> None:
    write(
        "src/mwpc_exact/backend.py",
        '''"""Parser backend selection shared by reference and production orchestration."""\n\nfrom enum import StrEnum\n\n\nclass ExactBackend(StrEnum):\n    """Available finite-lattice parser implementations."""\n\n    PYTHON = "python"\n    RUST = "rust"\n\n\n__all__ = ["ExactBackend"]\n''',
    )

    finite = read("src/mwpc_exact/finite_solver.py")
    finite = finite.replace(
        '"""Bridge from finite token support to an independently validated solve.',
        '"""Frozen M6 ordinary-token reference bridge over finite support.',
        1,
    )
    finite = finite.replace("from enum import StrEnum\n", "")
    finite = finite.replace(
        "from mwpc_exact.byte_lattice import ByteLattice, build_byte_lattice\n",
        "from mwpc_exact.backend import ExactBackend\nfrom mwpc_exact.byte_lattice import ByteLattice, build_byte_lattice\n",
        1,
    )
    finite, count = re.subn(
        r'\nclass ExactBackend\(StrEnum\):\n    """Available finite-lattice parser implementations\."""\n\n    PYTHON = "python"\n    RUST = "rust"\n',
        "",
        finite,
        count=1,
    )
    if count != 1:
        raise RuntimeError("could not remove legacy ExactBackend definition")
    finite = finite.replace(
        '__all__ = ["ExactBackend", "solve_exact_commit"]',
        'solve_ordinary_support_reference = solve_exact_commit\n\n\n__all__ = ["solve_ordinary_support_reference"]',
    )
    write("src/mwpc_exact/finite_solver.py", finite)

    for relative in ("src/mwpc_exact/solver.py", "src/mwpc_exact/adaptive.py"):
        text = read(relative)
        text = text.replace(
            "from mwpc_exact.finite_solver import ExactBackend\n",
            "from mwpc_exact.backend import ExactBackend\n",
        )
        write(relative, text)

    package = read("src/mwpc_exact/__init__.py")
    package = package.replace(
        "from mwpc_exact.finite_solver import ExactBackend\n"
        "from mwpc_exact.finite_solver import solve_exact_commit as solve_ordinary_exact_commit\n",
        "from mwpc_exact.backend import ExactBackend\n"
        "from mwpc_exact.finite_solver import solve_ordinary_support_reference\n",
    )
    package = package.replace('    "solve_ordinary_exact_commit",\n', '    "solve_ordinary_support_reference",\n')
    write("src/mwpc_exact/__init__.py", package)


def split_eos_policy() -> None:
    lattice_path = "src/mwpc_exact/eos_lattice.py"
    text = read(lattice_path)
    start = text.index("def _non_negative_id")
    end = text.index("@dataclass(frozen=True, slots=True)\nclass EOSArc")
    policy_block = text[start:end]
    policy_header = '''"""Explicit EOS/PAD policy contracts independent of lattice construction."""\n\nfrom __future__ import annotations\n\nfrom collections.abc import Iterable\nfrom dataclasses import dataclass\nfrom enum import StrEnum\n\n\n'''
    policy_footer = '''\n\n__all__ = [\n    "EOSMode",\n    "EOSPolicy",\n    "EOSPolicyViolation",\n    "EOSState",\n    "TokenRole",\n]\n'''
    write("src/mwpc_exact/eos_policy.py", policy_header + policy_block + policy_footer)

    text = text[:start] + text[end:]
    text = text.replace("from enum import StrEnum\n", "")
    insertion = '''from mwpc_exact.eos_policy import (\n    EOSMode,\n    EOSPolicy,\n    EOSPolicyViolation,\n    EOSState,\n    TokenRole,\n    _id_tuple,\n    _non_negative_id,\n)\n'''
    marker = "from mwpc_exact.reference.epsilon import (\n"
    text = text.replace(marker, insertion + marker, 1)
    write(lattice_path, text)

    for relative in ("src/mwpc_exact/validator.py", "src/mwpc_exact/adaptive.py", "src/mwpc_exact/solver.py"):
        current = read(relative)
        current = current.replace(
            "from mwpc_exact.eos_lattice import EOSMode, EOSPolicy\n",
            "from mwpc_exact.eos_policy import EOSMode, EOSPolicy\n",
        )
        write(relative, current)

    package = read("src/mwpc_exact/__init__.py")
    package = package.replace(
        "from mwpc_exact.eos_lattice import (\n"
        "    EOSArc,\n"
        "    EOSLattice,\n"
        "    EOSLatticePath,\n"
        "    EOSMode,\n"
        "    EOSPolicy,\n"
        "    EOSPolicyViolation,\n"
        "    EOSState,\n"
        "    TokenRole,\n"
        "    build_eos_lattice,\n"
        ")\n",
        "from mwpc_exact.eos_lattice import (\n"
        "    EOSArc,\n"
        "    EOSLattice,\n"
        "    EOSLatticePath,\n"
        "    build_eos_lattice,\n"
        ")\n"
        "from mwpc_exact.eos_policy import (\n"
        "    EOSMode,\n"
        "    EOSPolicy,\n"
        "    EOSPolicyViolation,\n"
        "    EOSState,\n"
        "    TokenRole,\n"
        ")\n",
    )
    write("src/mwpc_exact/__init__.py", package)


def split_decoder_types() -> None:
    path = "src/mwpc_exact/decoder.py"
    text = read(path)
    marker = "def _prepare_proposals(\n"
    split = text.index(marker)
    prefix = text[:split]
    remainder = text[split:]

    prefix = prefix.replace(
        '"""Model-independent commit decisions and explicit decoder fallbacks.',
        '"""Immutable decoder commit and fallback contracts.',
        1,
    )
    prefix = prefix.replace(
        "from mwpc_exact.profiling import ComponentProfiler, ProfilingComponent\n",
        "",
    )
    alias = '\n\nFailureFallbackCallable = Callable[[FailureFallbackRequest], FallbackSelection]\n'
    prefix += alias
    prefix += '''\n\n__all__ = [\n    "CommitGuarantee",\n    "CommitSource",\n    "DecoderStepResult",\n    "FailureFallbackCallable",\n    "FailureFallbackHandler",\n    "FailureFallbackRequest",\n    "FailureFallbackStrategy",\n    "FallbackSelection",\n    "FallbackToken",\n    "TokenCommit",\n]\n'''
    write("src/mwpc_exact/decoder_types.py", prefix)

    bottom_marker = "\n\nFailureFallbackCallable = Callable[[FailureFallbackRequest], FallbackSelection]"
    if bottom_marker not in remainder:
        raise RuntimeError("could not find decoder alias/footer")
    remainder = remainder[: remainder.index(bottom_marker)]
    header = '''"""Apply certified exact results or explicit non-exact decoder fallbacks."""\n\nfrom __future__ import annotations\n\nfrom collections import Counter\nfrom collections.abc import Iterable, Mapping, Sequence\nfrom math import fsum, isclose, isfinite\n\nfrom mwpc_exact.decoder_types import (\n    CommitGuarantee,\n    CommitSource,\n    DecoderStepResult,\n    FailureFallbackCallable,\n    FailureFallbackHandler,\n    FailureFallbackRequest,\n    FailureFallbackStrategy,\n    FallbackSelection,\n    FallbackToken,\n    TokenCommit,\n    _normalize_canvas,\n)\nfrom mwpc_exact.profiling import ComponentProfiler, ProfilingComponent\nfrom mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, aggregate_proposals\nfrom mwpc_exact.validated import ValidatedExactCommit\n\n\n'''
    footer = '''\n\n__all__ = [\n    "CommitGuarantee",\n    "CommitSource",\n    "DecoderStepResult",\n    "FailureFallbackCallable",\n    "FailureFallbackHandler",\n    "FailureFallbackRequest",\n    "FailureFallbackStrategy",\n    "FallbackSelection",\n    "FallbackToken",\n    "TokenCommit",\n    "apply_exact_commit_result",\n]\n'''
    write(path, header + remainder.rstrip() + footer)


def add_typed_validation_boundary() -> None:
    validator_path = "src/mwpc_exact/validator.py"
    validator = read(validator_path)
    marker = "\n\ndef _validate_canvas(canvas: Sequence[int | None])"
    if marker not in validator:
        raise RuntimeError("validator insertion marker missing")
    method = '''\n\n    @classmethod\n    def from_dict(cls, data: Mapping[str, object]) -> ValidationReport:\n        """Reconstruct a typed report from its JSON-compatible representation."""\n\n        if not isinstance(data, Mapping):\n            raise TypeError("validation report data must be a mapping")\n        raw_issues = data.get("issues", ())\n        if isinstance(raw_issues, (str, bytes)) or not isinstance(raw_issues, Sequence):\n            raise TypeError("validation report issues must be a finite sequence")\n        issues: list[ValidationIssue] = []\n        for index, raw_issue in enumerate(raw_issues):\n            if not isinstance(raw_issue, Mapping):\n                raise TypeError(f"validation issue {index} must be a mapping")\n            raw_code = raw_issue.get("code")\n            raw_message = raw_issue.get("message")\n            raw_context = raw_issue.get("context", {})\n            if not isinstance(raw_code, str):\n                raise TypeError(f"validation issue {index} code must be a string")\n            if not isinstance(raw_message, str):\n                raise TypeError(f"validation issue {index} message must be a string")\n            if not isinstance(raw_context, Mapping):\n                raise TypeError(f"validation issue {index} context must be a mapping")\n            try:\n                code = ValidationCode(raw_code)\n            except ValueError as exc:\n                raise ValueError(f"unknown validation issue code: {raw_code!r}") from exc\n            issues.append(ValidationIssue(code=code, message=raw_message, context=raw_context))\n\n        raw_skipped = data.get("skipped_checks", ())\n        if isinstance(raw_skipped, (str, bytes)) or not isinstance(raw_skipped, Sequence):\n            raise TypeError("skipped_checks must be a finite sequence")\n        skipped = tuple(raw_skipped)\n        if not all(isinstance(item, str) and item for item in skipped):\n            raise TypeError("skipped_checks must contain non-empty strings")\n\n        raw_objective = data.get("recomputed_objective")\n        if raw_objective is None:\n            objective = None\n        elif isinstance(raw_objective, bool) or not isinstance(raw_objective, (int, float)):\n            raise TypeError("recomputed_objective must be a real number or None")\n        else:\n            objective = float(raw_objective)\n            if not isfinite(objective):\n                raise ValueError("recomputed_objective must be finite")\n\n        raw_ids = data.get("recomputed_selected_proposal_ids", ())\n        if isinstance(raw_ids, (str, bytes)) or not isinstance(raw_ids, Sequence):\n            raise TypeError("recomputed_selected_proposal_ids must be a finite sequence")\n        recomputed_ids: list[int] = []\n        for item in raw_ids:\n            if isinstance(item, bool) or not isinstance(item, int) or item < 0:\n                raise ValueError("recomputed selected proposal IDs must be non-negative integers")\n            recomputed_ids.append(item)\n\n        report = cls(\n            issues=tuple(issues),\n            skipped_checks=skipped,\n            recomputed_objective=objective,\n            recomputed_selected_proposal_ids=tuple(recomputed_ids),\n        )\n        declared_valid = data.get("is_valid")\n        if declared_valid is not None:\n            if not isinstance(declared_valid, bool):\n                raise TypeError("is_valid must be a boolean when provided")\n            if declared_valid is not report.is_valid:\n                raise ValueError("serialized is_valid disagrees with reconstructed report")\n        return report\n'''
    validator = validator.replace(marker, method + marker, 1)
    write(validator_path, validator)

    write(
        "src/mwpc_exact/validated.py",
        '''"""Typed boundary between independently validated solves and physical commits."""\n\nfrom __future__ import annotations\n\nfrom collections import Counter\nfrom collections.abc import Mapping\nfrom dataclasses import dataclass\nfrom math import isclose\n\nfrom mwpc_exact.types import ExactCommitResult, SolveStatus\nfrom mwpc_exact.validator import ValidationReport\n\n\n@dataclass(frozen=True, slots=True)\nclass ValidatedExactCommit:\n    """An optimal result paired with its typed independent validation report."""\n\n    result: ExactCommitResult\n    validation_report: ValidationReport\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.result, ExactCommitResult):\n            raise TypeError("result must be an ExactCommitResult")\n        if not isinstance(self.validation_report, ValidationReport):\n            raise TypeError("validation_report must be a ValidationReport")\n        if self.result.status is not SolveStatus.OPTIMAL:\n            raise ValueError("ValidatedExactCommit requires an OPTIMAL result")\n        if not self.validation_report.is_valid:\n            raise ValueError("ValidatedExactCommit requires a fully valid report")\n        if Counter(self.result.selected_proposal_ids) != Counter(\n            self.validation_report.recomputed_selected_proposal_ids\n        ):\n            raise ValueError("validation report proposal IDs disagree with the result")\n        recomputed = self.validation_report.recomputed_objective\n        if recomputed is None or self.result.objective_value is None or not isclose(\n            self.result.objective_value, recomputed, rel_tol=1e-12, abs_tol=1e-12\n        ):\n            raise ValueError("validation report objective disagrees with the result")\n\n    @property\n    def status(self) -> SolveStatus:\n        return self.result.status\n\n    @property\n    def exactness_scope(self):  # type: ignore[no-untyped-def]\n        return self.result.exactness_scope\n\n    @property\n    def objective_value(self) -> float:\n        assert self.result.objective_value is not None\n        return self.result.objective_value\n\n    @property\n    def selected_proposal_ids(self) -> tuple[int, ...]:\n        return self.result.selected_proposal_ids\n\n    @property\n    def witness_token_ids(self) -> tuple[int, ...]:\n        return self.result.witness_token_ids\n\n    @property\n    def witness_terminal_labels(self):  # type: ignore[no-untyped-def]\n        return self.result.witness_terminal_labels\n\n    @property\n    def witness_graph_edge_ids(self) -> tuple[int, ...]:\n        return self.result.witness_graph_edge_ids\n\n    @property\n    def witness_eos_position(self) -> int | None:\n        return self.result.witness_eos_position\n\n    @property\n    def witness_content_endpoint_slot(self) -> int | None:\n        return self.result.witness_content_endpoint_slot\n\n    @property\n    def diagnostics(self) -> Mapping[str, object]:\n        return self.result.diagnostics\n\n    def to_dict(self) -> dict[str, object]:\n        return self.result.to_dict()\n\n\ndef validated_exact_commit(result: ExactCommitResult) -> ValidatedExactCommit:\n    """Create the typed commit boundary from the orchestrator's recorded report."""\n\n    if not isinstance(result, ExactCommitResult):\n        raise TypeError("result must be an ExactCommitResult")\n    raw_report = result.diagnostics.get("certificate_validation")\n    if not isinstance(raw_report, Mapping):\n        raise ValueError("optimal result omitted typed certificate-validation evidence")\n    return ValidatedExactCommit(\n        result=result,\n        validation_report=ValidationReport.from_dict(raw_report),\n    )\n\n\n__all__ = ["ValidatedExactCommit", "validated_exact_commit"]\n''',
    )

    solver = read("src/mwpc_exact/solver.py")
    solver = solver.replace(
        "from mwpc_exact.validator import validate_exact_commit_certificate\n",
        "from mwpc_exact.validated import ValidatedExactCommit, validated_exact_commit\n"
        "from mwpc_exact.validator import validate_exact_commit_certificate\n",
        1,
    )
    wrapper = '''\n\ndef solve_validated_exact_commit(\n    grammar: CnfGrammar,\n    *,\n    canvas: Sequence[int | None],\n    support: PerPositionSupport,\n    proposals: Iterable[Proposal],\n    tokenizer_adapter: CompositionalByteLevelAdapter,\n    eos_policy: EOSPolicy,\n    backend: ExactBackend = ExactBackend.RUST,\n    timeout_seconds: float | None = None,\n    deadline_check_interval: int = 1_024,\n    deterministic_work_limit: int | None = None,\n    profiler: ComponentProfiler | None = None,\n) -> ValidatedExactCommit | ExactCommitResult:\n    """Return a typed validated wrapper for optimal outcomes and raw failures otherwise."""\n\n    result = solve_exact_commit(\n        grammar,\n        canvas=canvas,\n        support=support,\n        proposals=proposals,\n        tokenizer_adapter=tokenizer_adapter,\n        eos_policy=eos_policy,\n        backend=backend,\n        timeout_seconds=timeout_seconds,\n        deadline_check_interval=deadline_check_interval,\n        deterministic_work_limit=deterministic_work_limit,\n        profiler=profiler,\n    )\n    return validated_exact_commit(result) if result.status is SolveStatus.OPTIMAL else result\n'''
    solver = solver.replace('\n\n__all__ = ["ExactBackend", "solve_exact_commit"]', wrapper + '\n\n__all__ = ["solve_exact_commit", "solve_validated_exact_commit"]')
    write("src/mwpc_exact/solver.py", solver)

    package = read("src/mwpc_exact/__init__.py")
    package = package.replace(
        "from mwpc_exact.solver import solve_exact_commit\n",
        "from mwpc_exact.solver import solve_exact_commit, solve_validated_exact_commit\n",
    )
    package = package.replace(
        "from mwpc_exact.validator import (\n",
        "from mwpc_exact.validated import ValidatedExactCommit\n"
        "from mwpc_exact.validator import (\n",
    )
    package = package.replace('    "ValidationCode",\n', '    "ValidatedExactCommit",\n    "ValidationCode",\n')
    package = package.replace('    "solve_exact_commit_adaptive",\n', '    "solve_exact_commit_adaptive",\n    "solve_exact_commit_adaptive_validated",\n')
    package = package.replace('    "solve_exact_commit",\n', '    "solve_exact_commit",\n    "solve_validated_exact_commit",\n')
    write("src/mwpc_exact/__init__.py", package)


def harden_adaptive_timeout_and_naming() -> None:
    path = "src/mwpc_exact/adaptive.py"
    text = read(path)
    text = text.replace(
        "from collections.abc import Iterable, Mapping, Sequence\n",
        "from collections.abc import Callable, Iterable, Mapping, Sequence\n",
        1,
    )
    text = text.replace(
        "from mwpc_exact.solver import solve_exact_commit\n",
        "from mwpc_exact.solver import solve_exact_commit\n"
        "from mwpc_exact.validated import ValidatedExactCommit, validated_exact_commit\n",
        1,
    )
    text = text.replace(
        '        "orchestrator": "adaptive_support_v1",\n',
        '        "orchestrator": "feasibility_driven_support_expansion_v2",\n'
        '        "stopping_policy": "first_feasible",\n',
    )
    text = text.replace(
        '        "objective_monotonicity_basis": (\n',
        '        "observed_objective_monotonicity_basis": (\n',
    )
    text = text.replace(
        '        "optimal_objective_non_decreasing": all(\n',
        '        "observed_optimal_objectives_non_decreasing": all(\n',
    )
    text = text.replace(
        "    profiler: ComponentProfiler | None = None,\n) -> ExactCommitResult:\n",
        "    profiler: ComponentProfiler | None = None,\n    clock: Callable[[], float] | None = None,\n) -> ExactCommitResult:\n",
        1,
    )
    text = text.replace(
        "    if not isinstance(config, AdaptiveSupportConfig):\n",
        "    if clock is None:\n        clock = monotonic\n    elif not callable(clock):\n        raise TypeError(\"clock must be callable or None\")\n    if not isinstance(config, AdaptiveSupportConfig):\n",
        1,
    )
    text = text.replace("    started_at = monotonic()\n", "    started_at = clock()\n", 1)
    text = text.replace("        support_finished_at = monotonic()\n", "        support_finished_at = clock()\n")
    text = text.replace("        latest_time = monotonic()\n", "        latest_time = clock()\n")

    marker = '''        if profiler is not None and profiler.enabled:\n            profiler.set_counter("support_attempt_count", len(attempts))\n            profiler.set_counter("support_expansion_count", max(0, len(attempts) - 1))\n\n        if result.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:\n'''
    replacement = '''        if profiler is not None and profiler.enabled:\n            profiler.set_counter("support_attempt_count", len(attempts))\n            profiler.set_counter("support_expansion_count", max(0, len(attempts) - 1))\n\n        total_elapsed = max(0.0, latest_time - started_at)\n        if (\n            config.total_timeout_seconds is not None\n            and total_elapsed >= config.total_timeout_seconds\n            and result.status is not SolveStatus.TIMEOUT\n        ):\n            timeout_result = ExactCommitResult(\n                status=SolveStatus.TIMEOUT,\n                exactness_scope=result.exactness_scope,\n                diagnostics=result.diagnostics,\n            )\n            attempts[-1] = _AttemptRecord(\n                attempt_index=attempt.attempt_index,\n                requested_k=attempt.requested_k,\n                support=attempt.support,\n                result=timeout_result,\n                support_construction_seconds=attempt.support_construction_seconds,\n                solve_seconds=attempt.solve_seconds,\n                cumulative_elapsed_seconds=attempt.cumulative_elapsed_seconds,\n                backend_timeout_seconds=attempt.backend_timeout_seconds,\n                superset_of_previous=attempt.superset_of_previous,\n            )\n            return _finalize(\n                timeout_result,\n                config=config,\n                configured_widths=widths,\n                attempts=attempts,\n                backend=backend,\n                stopped_reason="total_timeout_after_attempt",\n                resource_limit_prevented_expansion=True,\n                total_elapsed_seconds=total_elapsed,\n            )\n\n        if result.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:\n'''
    if marker not in text:
        raise RuntimeError("adaptive timeout insertion marker missing")
    text = text.replace(marker, replacement, 1)

    wrapper = '''\n\ndef solve_exact_commit_adaptive_validated(\n    grammar: CnfGrammar,\n    *,\n    canvas: Sequence[int | None],\n    logits: Sequence[Sequence[float]],\n    proposals: Iterable[Proposal],\n    tokenizer_adapter: CompositionalByteLevelAdapter,\n    eos_policy: EOSPolicy,\n    config: AdaptiveSupportConfig,\n    backend: ExactBackend = ExactBackend.RUST,\n    permitted_token_ids: Sequence[int] | None = None,\n    include_proposal_tokens: bool = False,\n    pruning_description: str | None = None,\n    deadline_check_interval: int = 1_024,\n    deterministic_work_limit: int | None = None,\n    profiler: ComponentProfiler | None = None,\n    clock: Callable[[], float] | None = None,\n) -> ValidatedExactCommit | ExactCommitResult:\n    """Return a typed validated optimum under feasibility-driven support expansion."""\n\n    result = solve_exact_commit_adaptive(\n        grammar,\n        canvas=canvas,\n        logits=logits,\n        proposals=proposals,\n        tokenizer_adapter=tokenizer_adapter,\n        eos_policy=eos_policy,\n        config=config,\n        backend=backend,\n        permitted_token_ids=permitted_token_ids,\n        include_proposal_tokens=include_proposal_tokens,\n        pruning_description=pruning_description,\n        deadline_check_interval=deadline_check_interval,\n        deterministic_work_limit=deterministic_work_limit,\n        profiler=profiler,\n        clock=clock,\n    )\n    return validated_exact_commit(result) if result.status is SolveStatus.OPTIMAL else result\n'''
    text = text.replace(
        '\n\n__all__ = [\n    "AdaptiveSupportConfig",',
        wrapper + '\n\n__all__ = [\n    "AdaptiveSupportConfig",',
        1,
    )
    text = text.replace(
        '    "solve_exact_commit_adaptive",\n]',
        '    "solve_exact_commit_adaptive",\n    "solve_exact_commit_adaptive_validated",\n]',
    )
    write(path, text)

    package = read("src/mwpc_exact/__init__.py")
    package = package.replace(
        "    solve_exact_commit_adaptive,\n",
        "    solve_exact_commit_adaptive,\n    solve_exact_commit_adaptive_validated,\n",
    )
    write("src/mwpc_exact/__init__.py", package)


def require_validated_decoder_input() -> None:
    path = "src/mwpc_exact/decoder.py"
    text = read(path)
    text = text.replace(
        '''    validation = result.diagnostics.get("certificate_validation")\n    if not isinstance(validation, Mapping) or validation.get("is_valid") is not True:\n        raise ValueError(\n            "OPTIMAL decoder input requires recorded independent certificate validation"\n        )\n''',
        "",
        1,
    )

    start = text.index("def apply_exact_commit_result(\n")
    end = text.index("\n\n__all__ =", start)
    function = text[start:end]
    function = re.sub(r"\bresult\b", "solver_result", function)
    function = function.replace(
        "def apply_exact_commit_result(\n    solver_result: ExactCommitResult,",
        "def apply_exact_commit_result(\n    result: ValidatedExactCommit | ExactCommitResult,",
        1,
    )
    old_validation = '''    if not isinstance(solver_result, ExactCommitResult):\n        raise TypeError("result must be an ExactCommitResult")\n'''
    new_validation = '''    if isinstance(result, ValidatedExactCommit):\n        solver_result = result.result\n    elif isinstance(result, ExactCommitResult):\n        solver_result = result\n    else:\n        raise TypeError("result must be a ValidatedExactCommit or ExactCommitResult")\n    if (\n        solver_result.status is SolveStatus.OPTIMAL\n        and not isinstance(result, ValidatedExactCommit)\n    ):\n        raise ValueError("OPTIMAL decoder input requires a ValidatedExactCommit")\n'''
    if old_validation not in function:
        raise RuntimeError("decoder result validation marker missing")
    function = function.replace(old_validation, new_validation, 1)
    text = text[:start] + function + text[end:]
    write(path, text)


def update_tests_for_typed_boundary_and_timeout() -> None:
    test_decoder = read("tests/exact_commit/test_decoder.py")
    test_decoder = test_decoder.replace(
        "    SupportKind,\n",
        "    SupportKind,\n    ValidatedExactCommit,\n    ValidationReport,\n",
        1,
    )
    old_helper = '''def optimal_result(\n    witness: tuple[int, ...],\n    *,\n    selected: tuple[int, ...] = (),\n    objective: float = 0.0,\n) -> ExactCommitResult:\n    return ExactCommitResult(\n        status=SolveStatus.OPTIMAL,\n        exactness_scope=SCOPE,\n        objective_value=objective,\n        selected_proposal_ids=selected,\n        witness_token_ids=witness,\n        witness_terminal_labels=(ord("a"),),\n        witness_graph_edge_ids=(100,),\n        witness_content_endpoint_slot=len(witness),\n        diagnostics={"certificate_validation": {"is_valid": True}},\n    )\n'''
    new_helper = '''def optimal_result(\n    witness: tuple[int, ...],\n    *,\n    selected: tuple[int, ...] = (),\n    objective: float = 0.0,\n) -> ValidatedExactCommit:\n    raw_result = ExactCommitResult(\n        status=SolveStatus.OPTIMAL,\n        exactness_scope=SCOPE,\n        objective_value=objective,\n        selected_proposal_ids=selected,\n        witness_token_ids=witness,\n        witness_terminal_labels=(ord("a"),),\n        witness_graph_edge_ids=(100,),\n        witness_content_endpoint_slot=len(witness),\n        diagnostics={\n            "certificate_validation": {\n                "is_valid": True,\n                "issues": [],\n                "skipped_checks": [],\n                "recomputed_objective": objective,\n                "recomputed_selected_proposal_ids": list(selected),\n            }\n        },\n    )\n    return ValidatedExactCommit(\n        result=raw_result,\n        validation_report=ValidationReport(\n            issues=(),\n            skipped_checks=(),\n            recomputed_objective=objective,\n            recomputed_selected_proposal_ids=selected,\n        ),\n    )\n'''
    if old_helper not in test_decoder:
        raise RuntimeError("decoder optimal_result helper changed unexpectedly")
    test_decoder = test_decoder.replace(old_helper, new_helper, 1)
    test_decoder = test_decoder.replace("assert step.solver_result is result\n", "assert step.solver_result is result.result\n", 1)
    test_decoder = test_decoder.replace(
        'with pytest.raises(ValueError, match="independent certificate validation"):',
        'with pytest.raises(ValueError, match="ValidatedExactCommit"):',
        1,
    )
    write("tests/exact_commit/test_decoder.py", test_decoder)

    offline = read("tests/exact_commit/test_offline_exact_step.py")
    offline = offline.replace(
        "    solve_exact_commit_adaptive,\n",
        "    ValidatedExactCommit,\n    solve_exact_commit_adaptive_validated,\n",
        1,
    )
    offline = offline.replace(
        "    solver_result = solve_exact_commit_adaptive(\n",
        "    validated_result = solve_exact_commit_adaptive_validated(\n",
        1,
    )
    marker = '''    decoder_step = apply_exact_commit_result(\n        solver_result,\n'''
    replacement = '''    if not isinstance(validated_result, ValidatedExactCommit):\n        raise AssertionError("offline exact fixture expected an optimal validated result")\n    solver_result = validated_result.result\n    decoder_step = apply_exact_commit_result(\n        validated_result,\n'''
    if marker not in offline:
        raise RuntimeError("offline integration decoder marker missing")
    offline = offline.replace(marker, replacement, 1)
    write("tests/exact_commit/test_offline_exact_step.py", offline)

    adaptive_test = read("tests/exact_commit/test_adaptive_support.py")
    adaptive_test = adaptive_test.replace(
        'assert diagnostics["optimal_objective_non_decreasing"] is True',
        'assert diagnostics["observed_optimal_objectives_non_decreasing"] is True',
    )
    adaptive_test = adaptive_test.replace(
        'assert diagnostics["stopped_reason"] == "total_timeout_before_next_expansion"',
        'assert diagnostics["stopped_reason"] == "total_timeout_after_attempt"',
    )
    adaptive_test += '''\n\ndef test_hard_total_timeout_overrides_a_late_optimal_reference_result(\n    monkeypatch: pytest.MonkeyPatch,\n) -> None:\n    times = iter((0.0, 0.1, 1.1))\n\n    def clock() -> float:\n        return next(times)\n\n    def late_optimal(*_args: object, **kwargs: object) -> ExactCommitResult:\n        support = kwargs["support"]\n        assert isinstance(support, PerPositionSupport)\n        return ExactCommitResult(\n            status=SolveStatus.OPTIMAL,\n            exactness_scope=support.exactness_scope,\n            objective_value=0.0,\n            witness_token_ids=(0,),\n            witness_terminal_labels=(ord("a"),),\n            witness_graph_edge_ids=(0,),\n            witness_content_endpoint_slot=1,\n            diagnostics={\n                "certificate_validation": {\n                    "is_valid": True,\n                    "issues": [],\n                    "skipped_checks": [],\n                    "recomputed_objective": 0.0,\n                    "recomputed_selected_proposal_ids": [],\n                }\n            },\n        )\n\n    monkeypatch.setattr(adaptive, "solve_exact_commit", late_optimal)\n    result = solve_exact_commit_adaptive(\n        one_byte_grammar(ord("a")),\n        canvas=(None,),\n        logits=((1.0,),),\n        proposals=(),\n        tokenizer_adapter=CompositionalByteLevelAdapter((b"a",)),\n        eos_policy=EOSPolicy(EOSMode.ABSENT),\n        config=AdaptiveSupportConfig(\n            initial_k=1,\n            k_max=1,\n            total_timeout_seconds=1.0,\n        ),\n        backend=ExactBackend.PYTHON,\n        clock=clock,\n    )\n\n    assert result.status is SolveStatus.TIMEOUT\n    assert result.objective_value is None\n    diagnostics = adaptive_diagnostics(result)\n    assert diagnostics["stopped_reason"] == "total_timeout_after_attempt"\n    assert diagnostics["resource_limit_prevented_expansion"] is True\n    attempts = diagnostics["attempts"]\n    assert isinstance(attempts, tuple)\n    assert attempts[0]["status"] == SolveStatus.TIMEOUT.value\n    assert attempts[0]["objective_value"] is None\n\n\ndef test_adaptive_diagnostics_name_first_feasible_stopping_policy() -> None:\n    result = solve_exact_commit_adaptive(\n        one_byte_grammar(ord("a")),\n        canvas=(None,),\n        logits=((2.0, 1.0),),\n        proposals=(),\n        tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b")),\n        eos_policy=EOSPolicy(EOSMode.ABSENT),\n        config=AdaptiveSupportConfig(initial_k=1, k_max=2),\n        backend=ExactBackend.PYTHON,\n    )\n\n    diagnostics = adaptive_diagnostics(result)\n    assert diagnostics["orchestrator"] == "feasibility_driven_support_expansion_v2"\n    assert diagnostics["stopping_policy"] == "first_feasible"\n    assert diagnostics["attempted_k"] == (1,)\n'''
    write("tests/exact_commit/test_adaptive_support.py", adaptive_test)

    write(
        "tests/exact_commit/test_validated_result.py",
        '''from __future__ import annotations\n\nimport pytest\n\nfrom mwpc_exact import (\n    ExactCommitResult,\n    ExactnessScope,\n    SolveStatus,\n    SupportKind,\n    ValidatedExactCommit,\n    ValidationReport,\n)\n\n\nSCOPE = ExactnessScope(\n    kind=SupportKind.EXPLICIT,\n    vocabulary_size=2,\n    pruning_description="typed validation boundary fixture",\n)\n\n\ndef result() -> ExactCommitResult:\n    return ExactCommitResult(\n        status=SolveStatus.OPTIMAL,\n        exactness_scope=SCOPE,\n        objective_value=1.0,\n        selected_proposal_ids=(7,),\n        witness_token_ids=(0,),\n        witness_terminal_labels=(97,),\n        witness_graph_edge_ids=(1,),\n        witness_content_endpoint_slot=1,\n    )\n\n\ndef test_validated_boundary_requires_a_fully_valid_typed_report() -> None:\n    validated = ValidatedExactCommit(\n        result=result(),\n        validation_report=ValidationReport(\n            issues=(),\n            skipped_checks=(),\n            recomputed_objective=1.0,\n            recomputed_selected_proposal_ids=(7,),\n        ),\n    )\n\n    assert validated.status is SolveStatus.OPTIMAL\n    assert validated.result.objective_value == 1.0\n\n\ndef test_validated_boundary_rejects_mismatched_objective() -> None:\n    with pytest.raises(ValueError, match="objective"):\n        ValidatedExactCommit(\n            result=result(),\n            validation_report=ValidationReport(\n                issues=(),\n                skipped_checks=(),\n                recomputed_objective=0.0,\n                recomputed_selected_proposal_ids=(7,),\n            ),\n        )\n''',
    )


def archive_tasks() -> None:
    original = read("TASKS.md")
    write("docs/history/TASKS-through-M8.md", original)
    active_marker = "# M9 — EPIC/dLLM integration"
    if active_marker not in original:
        raise RuntimeError("M9 marker missing from TASKS.md")
    active = original[original.index(active_marker):]
    concise = '''# TASKS.md — Exact MWPC for CFG-Constrained dLLMs\n\n## How to use this file\n\nThis is the authoritative checklist for current and future work. `AGENTS.md`\ndefines stable scientific invariants; `IMPLEMENTATION_PLAN.md` explains the\ndesign. Detailed M0--M8 task evidence is archived in\n[`docs/history/TASKS-through-M8.md`](docs/history/TASKS-through-M8.md).\n\nStatus convention:\n\n- `[ ]` not completed;\n- `[x]` completed and supported by immutable evidence;\n- `BLOCKED:` cannot proceed, with a concrete reason;\n- `OPTIONAL:` not required for the minimum TCC implementation.\n\nRules:\n\n1. Complete required tasks in dependency order.\n2. Close a task only after every acceptance criterion and required check passes.\n3. Record commands, outputs, artifacts, and relevant commits in its Evidence field.\n4. A correctness-gate failure blocks later integration and performance work.\n5. Never substitute measurements with estimates.\n6. Do not redo completed milestones unless a regression invalidates their evidence.\n\n## Current starting point\n\n**M9 / T900.** M0 through M8 are complete. The first incomplete required task\nis T900: configuration and strategy dispatch.\n\nRequired milestones: **M0 through M13**. Optional milestones: **O1 through O4**.\n\n## Completed milestone summary\n\n- **M0:** pinned EPIC baseline and reproducible Python/Rust environment.\n- **M1:** scientific contracts, statuses, scope metadata, and independent validation.\n- **M2:** token-aligned Python max-plus CKY with reconstructible certificates.\n- **M3:** exhaustive completion/subset oracles and deterministic differential gate.\n- **M4:** generic weighted terminal-DAG reference parser and epsilon semantics.\n- **M5:** independent Rust parser, PyO3 binding, timeouts, and differential gate.\n- **M6:** finite tokenizer-aware token/byte lattice exact on represented support.\n- **M7:** explicit EOS/PAD automaton, finite-slot validator, counterexamples, and gate.\n- **M8:** proposal policy, first-feasible adaptive support, typed solve/commit boundary, fallbacks, profiling, and offline exact-step integration.\n\n**Post-M8 corrections:** the production decoder now requires a typed\n`ValidatedExactCommit`; `total_timeout_seconds` is a hard returned-status\ndeadline even when a complete attempt finishes late; adaptive diagnostics name\nthe first-feasible stopping policy; campaign code lives in `mwpc_research`; and\nthe Rust CI path runs the complete current suite plus normal M6/M7 campaigns.\n\nSee the archived checklist and `docs/evidence/` for exact commits, commands,\nconfigured-case boundaries, and campaign counts.\n\n---\n\n'''
    write("TASKS.md", concise + active)


def add_decisions_and_cleanup_notes() -> None:
    write(
        "docs/decisions/0009-hard-total-timeout.md",
        '''# ADR 0009: Adaptive total timeout is a hard returned-status deadline\n\n- Status: Accepted\n- Date: 2026-08-25\n- Applies to: adaptive support orchestration and decoder fallback decisions\n\n`total_timeout_seconds` bounds the complete adaptive operation as observed by\nthe caller. A Python reference attempt cannot be interrupted safely, but if it\nfinishes after the deadline its result is discarded and the public status is\n`TIMEOUT`. The attempt history records no objective or certificate for that\nlate attempt. Rust continues to receive the remaining deadline before each\nsolve. Timeout is never converted to infeasibility.\n''',
    )
    write(
        "docs/decisions/0010-validated-commit-boundary.md",
        '''# ADR 0010: Physical commits require a typed validated result\n\n- Status: Accepted\n- Date: 2026-08-25\n- Applies to: exact orchestration, adaptive orchestration, and decoder updates\n\nAn `ExactCommitResult` is the serializable scientific result. A physical exact\ncommit additionally requires `ValidatedExactCommit`, which pairs an optimal\nresult with a typed `ValidationReport` whose recomputed objective and proposal\nIDs agree with the result. Non-optimal results remain raw because fallbacks\nmust preserve their original status without acquiring an exact guarantee.\n\nThe production M9 adapter must call the validated solve APIs before invoking\n`apply_exact_commit_result`. A JSON boolean in diagnostics is evidence for\nserialization, not by itself authorization to mutate the canvas.\n''',
    )
    write(
        "docs/decisions/0011-feasibility-driven-support-expansion.md",
        '''# ADR 0011: Adaptive support expansion stops at first feasibility\n\n- Status: Accepted\n- Date: 2026-08-25\n- Applies to: T802 and later exact-mode configuration\n\nAdaptive top-K expansion retries only after `INFEASIBLE_ON_SUPPORT` and stops\nat the first conclusive feasible support. It is therefore a\n**feasibility-driven first-feasible policy**, not an optimization over every\nconfigured width through `k_max`. Each returned optimum remains exact on its\nrepresented support. Diagnostics use `stopping_policy=first_feasible` and\n`observed_optimal_objectives_non_decreasing`; they do not imply that wider\nfeasible supports were evaluated.\n''',
    )
    write(
        "docs/post-m8-review-fixes.md",
        '''# Post-M8 review fixes\n\nThis focused change preserves all completed M7/M8 algorithms and immutable\nevidence while tightening the production boundary before M9.\n\n- complete Rust-backed CI now exercises the full suite and normal M6/M7 campaigns;\n- adaptive total timeout has hard returned-status semantics;\n- exact canvas mutation requires a typed validated result;\n- the legacy ordinary-support solver is no longer presented as a peer production API;\n- adaptive support is named as first-feasible rather than globally best across K;\n- randomized campaigns and evidence generators moved to `mwpc_research`;\n- completed M0--M8 details moved to the history archive;\n- EOS policy and decoder data contracts were split from their operational modules.\n\nBranch protection was intentionally not changed at the repository owner's request.\n''',
    )


def update_ci() -> None:
    write(
        ".github/workflows/ci.yml",
        '''name: project-checks\n\non:\n  push:\n    branches: ["main"]\n  pull_request:\n  workflow_dispatch:\n\npermissions:\n  contents: read\n\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          submodules: recursive\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - name: Install development environment\n        run: |\n          python -m pip install --upgrade pip\n          python -m pip install -e '.[dev]'\n      - name: Verify pinned EPIC provenance\n        run: ./scripts/verify_upstream.sh\n      - name: Lint\n        run: python -m ruff check src tests\n      - name: Type check\n        run: python -m mypy src\n      - name: Unit and exact-commit tests\n        run: python -m pytest -q tests/unit tests/exact_commit\n\n  rust-correctness:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          submodules: recursive\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - name: Bootstrap production Rust binding\n        run: make bootstrap-rust-parser\n      - name: Check Rust crates\n        run: make test-rust-parser\n      - name: Run complete suite with production binding\n        run: .venv/bin/python -m pytest -q tests/unit tests/exact_commit\n      - name: Run normal M6 finite-lattice campaign\n        run: |\n          .venv/bin/python scripts/exact_commit/run_m6_finite_lattice_differential.py \\\n            --campaign normal\n      - name: Run normal M7 EOS finite-slot campaign\n        run: |\n          .venv/bin/python scripts/exact_commit/run_m7_eos_finite_slot_differential.py \\\n            --campaign normal\n''',
    )


def main() -> None:
    move_research_campaigns()
    add_backend_boundary()
    split_eos_policy()
    add_typed_validation_boundary()
    split_decoder_types()
    harden_adaptive_timeout_and_naming()
    require_validated_decoder_input()
    update_tests_for_typed_boundary_and_timeout()
    archive_tasks()
    add_decisions_and_cleanup_notes()
    update_ci()


if __name__ == "__main__":
    main()
