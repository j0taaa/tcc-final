"""Public model-independent orchestration for one exact MWPC step.

This layer freezes already constructed proposals and finite support, composes
the token choices with explicit byte/EOS semantics, dispatches to the selected
parser backend, reconstructs every physical token slot, and independently
validates an optimal public certificate before returning it.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import isclose, isfinite

from mwpc_exact.eos_lattice import EOSLattice, EOSLatticePath, EOSMode, EOSPolicy, build_eos_lattice
from mwpc_exact.finite_solver import ExactBackend
from mwpc_exact.reference.dag_parser import (
    DagParseCertificate,
    reconstruct_dag_certificate,
    run_dag_cky,
    validate_dag_certificate,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.rust_solver import RustBindingUnavailable, solve_rust_dag
from mwpc_exact.support import PerPositionSupport
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, TerminalEdge
from mwpc_exact.validator import validate_exact_commit_certificate


class _CertificateValidationError(ValueError):
    """A backend or reconstructed certificate violated the public contract."""


@dataclass(frozen=True, slots=True)
class _BackendOutcome:
    status: SolveStatus
    certificate: DagParseCertificate | None
    witness_token_edge_ids: tuple[int | None, ...] | None
    diagnostics: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _PathCandidate:
    path: EOSLatticePath
    source: str


def _normalize_canvas(canvas: Sequence[int | None]) -> tuple[int | None, ...]:
    if isinstance(canvas, (str, bytes)) or not isinstance(canvas, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    normalized: list[int | None] = []
    for position, token_id in enumerate(canvas):
        if token_id is None:
            normalized.append(None)
        elif isinstance(token_id, bool) or not isinstance(token_id, int):
            raise TypeError(f"canvas token at position {position} must be an integer or None")
        elif token_id < 0:
            raise ValueError(f"canvas token at position {position} must be non-negative")
        else:
            normalized.append(token_id)
    if not normalized:
        raise ValueError("exact-commit orchestration requires at least one physical slot")
    return tuple(normalized)


def _validate_byte_grammar(grammar: CnfGrammar) -> None:
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    for terminal_id, label in grammar.terminal_labels.items():
        if isinstance(label, bool) or not isinstance(label, int):
            raise ValueError(
                "exact-commit orchestration requires integer byte grammar terminals "
                f"(terminal_id={terminal_id}, label={label!r})"
            )


def _validate_solver_controls(
    *,
    backend: ExactBackend,
    timeout_seconds: float | None,
    deadline_check_interval: int,
    deterministic_work_limit: int | None,
) -> None:
    if not isinstance(backend, ExactBackend):
        raise TypeError("backend must be an ExactBackend")
    if timeout_seconds is not None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise TypeError("timeout_seconds must be a real number or None")
        if not isfinite(float(timeout_seconds)) or timeout_seconds < 0.0:
            raise ValueError("timeout_seconds must be finite and non-negative")
    if (
        isinstance(deadline_check_interval, bool)
        or not isinstance(deadline_check_interval, int)
        or deadline_check_interval <= 0
    ):
        raise ValueError("deadline_check_interval must be a positive integer")
    if deterministic_work_limit is not None and (
        isinstance(deterministic_work_limit, bool)
        or not isinstance(deterministic_work_limit, int)
        or deterministic_work_limit < 0
    ):
        raise ValueError("deterministic_work_limit must be a non-negative integer or None")
    if backend is ExactBackend.PYTHON and (
        timeout_seconds is not None
        or deterministic_work_limit is not None
        or deadline_check_interval != 1_024
    ):
        raise ValueError("Rust timeout/work controls are unsupported by the Python backend")


def _validate_input_consistency(
    *,
    canvas: tuple[int | None, ...],
    support: PerPositionSupport,
    adapter: CompositionalByteLevelAdapter,
    eos_policy: EOSPolicy,
) -> None:
    if canvas != support.canvas:
        raise ValueError("canvas must exactly match the validated per-position support canvas")
    scope = support.exactness_scope
    if adapter.vocabulary_size != scope.vocabulary_size:
        raise ValueError("tokenizer adapter and exactness scope must have equal vocabularies")
    configured_specials = set(eos_policy.termination_token_ids)
    if eos_policy.pad_token_id is not None:
        configured_specials.add(eos_policy.pad_token_id)
    missing_specials = sorted(configured_specials - set(scope.included_special_tokens))
    if missing_specials:
        raise ValueError(
            "EOS/PAD policy token IDs must be listed in exactness-scope special tokens: "
            f"{missing_specials}"
        )
    if eos_policy.mode is EOSMode.ABSENT and configured_specials:
        raise AssertionError("validated ABSENT EOS policy unexpectedly configured special IDs")


def _run_python_backend(grammar: CnfGrammar, lattice: EOSLattice) -> _BackendOutcome:
    solve = run_dag_cky(grammar, lattice.normalized_graph)
    certificate = (
        reconstruct_dag_certificate(solve) if solve.status is SolveStatus.OPTIMAL else None
    )
    return _BackendOutcome(
        status=solve.status,
        certificate=certificate,
        witness_token_edge_ids=None,
        diagnostics={
            "chart_entries": len(solve.chart.entries),
            "final_node_id": solve.final_node_id,
        },
    )


def _run_rust_backend(
    grammar: CnfGrammar,
    lattice: EOSLattice,
    *,
    timeout_seconds: float | None,
    deadline_check_interval: int,
    deterministic_work_limit: int | None,
) -> _BackendOutcome:
    solve = solve_rust_dag(
        grammar,
        lattice.normalized_graph,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    return _BackendOutcome(
        status=solve.status,
        certificate=solve.certificate,
        witness_token_edge_ids=solve.witness_token_edge_ids,
        diagnostics=dict(solve.diagnostics),
    )


def _validate_reported_normalized_provenance(
    lattice: EOSLattice,
    certificate: DagParseCertificate,
    reported_token_edge_ids: tuple[int | None, ...] | None,
) -> None:
    if reported_token_edge_ids is None:
        return
    if len(reported_token_edge_ids) != len(certificate.witness_graph_edge_ids):
        raise _CertificateValidationError(
            "backend token-edge provenance does not align with normalized witness edges"
        )
    edge_by_id = {edge.edge_id: edge for edge in lattice.normalized_graph.edges}
    expected_items: list[int | None] = []
    for edge_id in certificate.witness_graph_edge_ids:
        edge = edge_by_id.get(edge_id)
        if not isinstance(edge, TerminalEdge):
            raise _CertificateValidationError(
                "normalized witness references a missing or non-terminal edge"
            )
        expected_items.append(edge.provenance_token_edge_id)
    expected = tuple(expected_items)
    if reported_token_edge_ids != expected:
        raise _CertificateValidationError(
            "backend token-edge provenance disagrees with the normalized byte graph"
        )


def _reconstruct_normalized_candidate(
    grammar: CnfGrammar,
    lattice: EOSLattice,
    certificate: DagParseCertificate,
    *,
    reported_token_edge_ids: tuple[int | None, ...] | None,
) -> EOSLatticePath:
    if not validate_dag_certificate(grammar, lattice.normalized_graph, certificate):
        raise _CertificateValidationError(
            "normalized terminal-DAG certificate failed independent validation"
        )
    _validate_reported_normalized_provenance(
        lattice,
        certificate,
        reported_token_edge_ids,
    )
    path = lattice.reconstruct_normalized_path(certificate.witness_graph_edge_ids)
    lattice.validate_path(path)
    if path.terminal_labels != certificate.witness_terminal_labels:
        raise _CertificateValidationError(
            "restored full-slot path does not reproduce normalized terminal labels"
        )
    if Counter(path.matched_proposal_ids) != Counter(certificate.selected_proposal_ids):
        raise _CertificateValidationError(
            "restored full-slot path does not reproduce normalized proposal provenance"
        )
    if not isclose(
        path.objective_value,
        certificate.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise _CertificateValidationError(
            "restored full-slot objective differs from normalized parser objective"
        )
    return path


def _select_conclusive_path(
    grammar: CnfGrammar,
    lattice: EOSLattice,
    outcome: _BackendOutcome,
) -> _PathCandidate | None:
    candidates: list[_PathCandidate] = []
    if outcome.status is SolveStatus.OPTIMAL:
        if outcome.certificate is None:
            raise _CertificateValidationError("OPTIMAL backend outcome omitted its certificate")
        candidates.append(
            _PathCandidate(
                path=_reconstruct_normalized_candidate(
                    grammar,
                    lattice,
                    outcome.certificate,
                    reported_token_edge_ids=outcome.witness_token_edge_ids,
                ),
                source="normalized_parser",
            )
        )
    elif outcome.certificate is not None or outcome.witness_token_edge_ids not in {None, ()}:
        raise _CertificateValidationError(
            "a non-optimal backend outcome exposed partial certificate data"
        )

    if grammar.accepts_empty and lattice.normalization.best_epsilon_only_path is not None:
        epsilon_path = lattice.reconstruct_epsilon_only_path()
        lattice.validate_path(epsilon_path)
        candidates.append(_PathCandidate(epsilon_path, "epsilon_only"))

    if not candidates:
        return None
    return min(
        candidates,
        key=lambda candidate: (
            -candidate.path.objective_value,
            candidate.path.graph_edge_ids,
        ),
    )


def _support_accepts(support: PerPositionSupport, token_ids: tuple[int, ...]) -> bool:
    return len(token_ids) == len(support.rows) and all(
        token_id in support.rows[position] for position, token_id in enumerate(token_ids)
    )


def _base_diagnostics(
    *,
    backend: ExactBackend,
    support: PerPositionSupport,
    lattice: EOSLattice,
) -> dict[str, object]:
    return {
        "orchestrator": "exact_commit_step_v1",
        "backend": backend.value,
        "exactness_name": (
            "exact_declared_full_finite_slot_instance"
            if support.exactness_scope.kind.value == "full"
            else "exact_on_support"
        ),
        "finite_slot_policy": "all_physical_slots_consumed_with_explicit_eos_pad",
        "represented_support_sha256": support.fingerprint,
        "support_diagnostics": support.diagnostics,
        "token_lattice_diagnostics": lattice.token_lattice.diagnostics,
        "byte_eos_lattice_diagnostics": lattice.diagnostics,
    }


def _error_result(
    *,
    support: PerPositionSupport,
    diagnostics: Mapping[str, object],
    stage: str,
    error: Exception,
) -> ExactCommitResult:
    return ExactCommitResult(
        status=SolveStatus.ERROR,
        exactness_scope=support.exactness_scope,
        diagnostics={
            **diagnostics,
            "error_stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def solve_exact_commit(
    grammar: CnfGrammar,
    *,
    canvas: Sequence[int | None],
    support: PerPositionSupport,
    proposals: Iterable[Proposal],
    tokenizer_adapter: CompositionalByteLevelAdapter,
    eos_policy: EOSPolicy,
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
) -> ExactCommitResult:
    """Solve one frozen exact-commit instance without loading a model.

    Malformed public inputs raise explicit validation errors. Once backend
    execution begins, unavailable functionality and inconclusive statuses are
    preserved; a malformed or independently rejected certificate is returned
    as ``ERROR`` with no public objective or witness fields.
    """

    _validate_byte_grammar(grammar)
    if not isinstance(support, PerPositionSupport):
        raise TypeError("support must be a PerPositionSupport")
    if not isinstance(tokenizer_adapter, CompositionalByteLevelAdapter):
        raise TypeError("tokenizer_adapter must be a CompositionalByteLevelAdapter")
    if not isinstance(eos_policy, EOSPolicy):
        raise TypeError("eos_policy must be an EOSPolicy")
    _validate_solver_controls(
        backend=backend,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    canvas_tokens = _normalize_canvas(canvas)
    _validate_input_consistency(
        canvas=canvas_tokens,
        support=support,
        adapter=tokenizer_adapter,
        eos_policy=eos_policy,
    )
    proposal_items = tuple(proposals)
    token_lattice = build_token_lattice(support=support, proposals=proposal_items)
    byte_eos_lattice = build_eos_lattice(
        token_lattice=token_lattice,
        adapter=tokenizer_adapter,
        policy=eos_policy,
    )
    diagnostics = _base_diagnostics(
        backend=backend,
        support=support,
        lattice=byte_eos_lattice,
    )

    try:
        if backend is ExactBackend.PYTHON:
            outcome = _run_python_backend(grammar, byte_eos_lattice)
        else:
            outcome = _run_rust_backend(
                grammar,
                byte_eos_lattice,
                timeout_seconds=timeout_seconds,
                deadline_check_interval=deadline_check_interval,
                deterministic_work_limit=deterministic_work_limit,
            )
    except RustBindingUnavailable as error:
        return ExactCommitResult(
            status=SolveStatus.UNSUPPORTED,
            exactness_scope=support.exactness_scope,
            diagnostics={
                **diagnostics,
                "error_stage": "backend_availability",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
    except Exception as error:
        return _error_result(
            support=support,
            diagnostics=diagnostics,
            stage="backend_solve",
            error=error,
        )

    diagnostics["backend_diagnostics"] = dict(outcome.diagnostics)
    if outcome.status not in {SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE_ON_SUPPORT}:
        if outcome.certificate is not None or outcome.witness_token_edge_ids not in {None, ()}:
            return _error_result(
                support=support,
                diagnostics=diagnostics,
                stage="non_optimal_partial_certificate",
                error=_CertificateValidationError(
                    "a non-optimal backend outcome exposed partial certificate data"
                ),
            )
        return ExactCommitResult(
            status=outcome.status,
            exactness_scope=support.exactness_scope,
            diagnostics=diagnostics,
        )

    try:
        candidate = _select_conclusive_path(grammar, byte_eos_lattice, outcome)
        if candidate is None:
            return ExactCommitResult(
                status=SolveStatus.INFEASIBLE_ON_SUPPORT,
                exactness_scope=support.exactness_scope,
                diagnostics=diagnostics,
            )
        path = candidate.path
        diagnostics["certificate_source"] = candidate.source
        preliminary_result = ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=support.exactness_scope,
            objective_value=path.objective_value,
            selected_proposal_ids=path.matched_proposal_ids,
            witness_token_ids=path.token_path.token_ids,
            witness_terminal_labels=path.terminal_labels,
            witness_graph_edge_ids=path.graph_edge_ids,
            witness_eos_position=path.eos_position,
            witness_content_endpoint_slot=path.content_endpoint_slot,
            diagnostics=diagnostics,
        )
        validation = validate_exact_commit_certificate(
            preliminary_result,
            expected_scope=support.exactness_scope,
            canvas=canvas_tokens,
            proposals=proposal_items,
            graph=byte_eos_lattice.graph,
            grammar_recognizer=lambda labels: recognizes_cnf(grammar, labels),
            support_validator=lambda token_ids: _support_accepts(support, token_ids),
            eos_policy=eos_policy,
            eos_adapter=tokenizer_adapter,
        )
        diagnostics["certificate_validation"] = validation.to_dict()
        if not validation.is_valid:
            raise _CertificateValidationError(
                "public exact-commit certificate failed independent validation"
            )
    except Exception as error:
        return _error_result(
            support=support,
            diagnostics=diagnostics,
            stage="certificate_validation",
            error=error,
        )

    return ExactCommitResult(
        status=preliminary_result.status,
        exactness_scope=preliminary_result.exactness_scope,
        objective_value=preliminary_result.objective_value,
        selected_proposal_ids=preliminary_result.selected_proposal_ids,
        witness_token_ids=preliminary_result.witness_token_ids,
        witness_terminal_labels=preliminary_result.witness_terminal_labels,
        witness_graph_edge_ids=preliminary_result.witness_graph_edge_ids,
        witness_eos_position=preliminary_result.witness_eos_position,
        witness_content_endpoint_slot=preliminary_result.witness_content_endpoint_slot,
        diagnostics=diagnostics,
    )


__all__ = ["ExactBackend", "solve_exact_commit"]
