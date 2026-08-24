"""Bridge from finite token support to an independently validated solve.

This module intentionally accepts an already constructed
:class:`~mwpc_exact.support.PerPositionSupport`.  Proposal policy, adaptive
support expansion, EOS/PAD composition, and decoder fallbacks belong to later
milestones.  The bridge here preserves one ordinary grammar-emitting token per
physical canvas slot.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isclose, isfinite
from typing import cast

from mwpc_exact.byte_lattice import ByteLattice, build_byte_lattice
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
from mwpc_exact.token_lattice import TokenLatticePath, build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import (
    ExactCommitResult,
    Proposal,
    SolveStatus,
    TerminalLabel,
)
from mwpc_exact.validator import validate_exact_commit_certificate


class ExactBackend(StrEnum):
    """Available finite-lattice parser implementations."""

    PYTHON = "python"
    RUST = "rust"


@dataclass(frozen=True, slots=True)
class _BackendOutcome:
    status: SolveStatus
    certificate: DagParseCertificate | None
    witness_token_edge_ids: tuple[int | None, ...] | None
    diagnostics: Mapping[str, object]


class _CertificateValidationError(ValueError):
    """A backend certificate failed parser-independent lattice checks."""


def _normalize_canvas(canvas: Sequence[int | None]) -> tuple[int | None, ...]:
    if isinstance(canvas, (str, bytes)) or not isinstance(canvas, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    result: list[int | None] = []
    for position, token_id in enumerate(canvas):
        if token_id is None:
            result.append(None)
        elif isinstance(token_id, bool) or not isinstance(token_id, int):
            raise TypeError(f"canvas token at position {position} must be an integer or None")
        elif token_id < 0:
            raise ValueError(f"canvas token at position {position} must be non-negative")
        else:
            result.append(token_id)
    if not result:
        raise ValueError("the T605 finite-lattice bridge requires a non-empty canvas")
    return tuple(result)


def _validate_byte_grammar(grammar: CnfGrammar) -> None:
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    for terminal_id, label in grammar.terminal_labels.items():
        if isinstance(label, bool) or not isinstance(label, int):
            raise ValueError(
                "the finite byte-lattice solver requires integer byte grammar terminals "
                f"(terminal_id={terminal_id}, label={label!r})"
            )


def _validate_solver_controls(
    *,
    backend: ExactBackend,
    timeout_seconds: float | None,
    deadline_check_interval: int,
    deterministic_work_limit: int | None,
) -> None:
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


def _base_diagnostics(
    *,
    backend: ExactBackend,
    support: PerPositionSupport,
    byte_lattice: ByteLattice,
) -> dict[str, object]:
    return {
        "backend": backend.value,
        "finite_slot_policy": "one_ordinary_token_per_canvas_slot_no_eos_pad",
        "slot_count": byte_lattice.token_lattice.slot_count,
        "token_choice_count": len(byte_lattice.token_arcs),
        "terminal_node_count": len(byte_lattice.graph.node_ids),
        "terminal_edge_count": len(byte_lattice.terminal_edges),
        "represented_support_sha256": support.fingerprint,
        "support_kind": support.exactness_scope.kind.value,
    }


def _run_python_backend(grammar: CnfGrammar, byte_lattice: ByteLattice) -> _BackendOutcome:
    solve = run_dag_cky(grammar, byte_lattice.graph)
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
    byte_lattice: ByteLattice,
    *,
    timeout_seconds: float | None,
    deadline_check_interval: int,
    deterministic_work_limit: int | None,
) -> _BackendOutcome:
    solve = solve_rust_dag(
        grammar,
        byte_lattice.graph,
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


def _reconstruct_token_path(
    grammar: CnfGrammar,
    byte_lattice: ByteLattice,
    certificate: DagParseCertificate,
    *,
    reported_token_edge_ids: tuple[int | None, ...] | None,
) -> TokenLatticePath:
    """Recover token choices from complete private byte-path provenance."""

    if not validate_dag_certificate(grammar, byte_lattice.graph, certificate):
        raise _CertificateValidationError(
            "the generic terminal-DAG certificate failed independent validation"
        )

    edge_by_id = {edge.edge_id: edge for edge in byte_lattice.terminal_edges}
    graph_edge_ids = certificate.witness_graph_edge_ids
    if reported_token_edge_ids is not None and len(reported_token_edge_ids) != len(graph_edge_ids):
        raise _CertificateValidationError(
            "backend token-edge provenance does not align with terminal witness edges"
        )

    token_edge_ids: list[int] = []
    cursor = 0
    while cursor < len(graph_edge_ids):
        first_edge_id = graph_edge_ids[cursor]
        first_edge = edge_by_id.get(first_edge_id)
        if first_edge is None:
            raise _CertificateValidationError(
                f"terminal witness references unknown edge ID {first_edge_id}"
            )
        token_edge_id = first_edge.provenance_token_edge_id
        if token_edge_id is None or token_edge_id >= len(byte_lattice.token_arcs):
            raise _CertificateValidationError(
                "every terminal witness edge must identify a known token edge"
            )
        expected_edge_ids = byte_lattice.terminal_edge_ids_by_token_edge[token_edge_id]
        end = cursor + len(expected_edge_ids)
        if graph_edge_ids[cursor:end] != expected_edge_ids:
            raise _CertificateValidationError(
                "terminal witness does not contain one token's complete private byte path"
            )
        if reported_token_edge_ids is not None and reported_token_edge_ids[cursor:end] != (
            token_edge_id,
        ) * len(expected_edge_ids):
            raise _CertificateValidationError(
                "backend token-edge provenance disagrees with the byte lattice"
            )
        if any(
            edge_by_id[edge_id].provenance_token_edge_id != token_edge_id
            for edge_id in expected_edge_ids
        ):
            raise _CertificateValidationError(
                "one private byte path contains inconsistent token provenance"
            )
        token_edge_ids.append(token_edge_id)
        cursor = end

    token_lattice = byte_lattice.token_lattice
    if len(token_edge_ids) != token_lattice.slot_count:
        raise _CertificateValidationError(
            "terminal witness does not recover exactly one token per physical slot"
        )
    choices = tuple(token_lattice.choices[token_edge_id] for token_edge_id in token_edge_ids)
    path = TokenLatticePath(
        token_edge_ids=tuple(token_edge_ids),
        token_ids=tuple(choice.token_id for choice in choices),
        objective_value=fsum(choice.weight for choice in choices),
        matched_proposal_ids=tuple(
            proposal_id for choice in choices for proposal_id in choice.matched_proposal_ids
        ),
    )
    expanded = byte_lattice.expand_path(path)
    byte_lattice.validate_path(expanded)
    if expanded.graph_edge_ids != certificate.witness_graph_edge_ids:
        raise _CertificateValidationError(
            "reconstructed token path does not reproduce the terminal witness edges"
        )
    if expanded.terminal_labels != certificate.witness_terminal_labels:
        raise _CertificateValidationError(
            "reconstructed token bytes do not reproduce the terminal witness labels"
        )
    if expanded.matched_proposal_ids != certificate.selected_proposal_ids:
        raise _CertificateValidationError(
            "reconstructed token proposals do not reproduce terminal-edge provenance"
        )
    if not isclose(
        expanded.objective_value,
        certificate.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise _CertificateValidationError(
            "reconstructed token objective does not equal the terminal certificate"
        )
    return path


def _tokenizer_witness_is_exact(
    adapter: CompositionalByteLevelAdapter,
    token_ids: tuple[int, ...],
    terminal_labels: tuple[TerminalLabel, ...],
) -> bool:
    if any(isinstance(label, bool) or not isinstance(label, int) for label in terminal_labels):
        return False
    byte_labels = cast(tuple[int, ...], terminal_labels)
    return adapter.detokenize_bytes(token_ids) == bytes(byte_labels)


def _finite_support_witness_is_exact(
    support: PerPositionSupport,
    token_ids: tuple[int, ...],
) -> bool:
    return len(token_ids) == len(support.rows) and all(
        token_id in support.rows[position] for position, token_id in enumerate(token_ids)
    )



def _absent_eos_witness_is_exact(
    adapter: CompositionalByteLevelAdapter,
    token_ids: tuple[int, ...],
) -> bool:
    """Validate the completed M6 profile in which every slot is ordinary content."""

    unsupported = frozenset(adapter.unsupported_token_ids)
    return not any(token_id in unsupported for token_id in token_ids)


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
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
) -> ExactCommitResult:
    """Solve one finite ordinary-token support and validate any optimal witness.

    ``OPTIMAL`` is scoped exactly by ``support.exactness_scope``.  The Python
    backend is an independent debugging implementation; Rust is the production
    default.  Timeout controls apply only to Rust in this milestone.
    """

    _validate_byte_grammar(grammar)
    if not isinstance(support, PerPositionSupport):
        raise TypeError("support must be a PerPositionSupport")
    if not isinstance(tokenizer_adapter, CompositionalByteLevelAdapter):
        raise TypeError("tokenizer_adapter must be a CompositionalByteLevelAdapter")
    if not isinstance(backend, ExactBackend):
        raise TypeError("backend must be an ExactBackend")
    _validate_solver_controls(
        backend=backend,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    canvas_tokens = _normalize_canvas(canvas)
    if canvas_tokens != support.canvas:
        raise ValueError("canvas must exactly match the validated per-position support canvas")
    proposal_items = tuple(proposals)

    token_lattice = build_token_lattice(support=support, proposals=proposal_items)
    byte_lattice = build_byte_lattice(
        token_lattice=token_lattice,
        adapter=tokenizer_adapter,
    )
    diagnostics = _base_diagnostics(
        backend=backend,
        support=support,
        byte_lattice=byte_lattice,
    )

    try:
        if backend is ExactBackend.PYTHON:
            outcome = _run_python_backend(grammar, byte_lattice)
        else:
            outcome = _run_rust_backend(
                grammar,
                byte_lattice,
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
    if outcome.status is not SolveStatus.OPTIMAL:
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
    if outcome.certificate is None:
        return _error_result(
            support=support,
            diagnostics=diagnostics,
            stage="certificate_reconstruction",
            error=_CertificateValidationError("OPTIMAL backend outcome omitted its certificate"),
        )

    try:
        token_path = _reconstruct_token_path(
            grammar,
            byte_lattice,
            outcome.certificate,
            reported_token_edge_ids=outcome.witness_token_edge_ids,
        )
        if not _finite_support_witness_is_exact(support, token_path.token_ids):
            raise _CertificateValidationError(
                "reconstructed witness is outside the represented finite support"
            )
        preliminary_result = ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=support.exactness_scope,
            objective_value=token_path.objective_value,
            selected_proposal_ids=token_path.matched_proposal_ids,
            witness_token_ids=token_path.token_ids,
            witness_terminal_labels=outcome.certificate.witness_terminal_labels,
            witness_graph_edge_ids=outcome.certificate.witness_graph_edge_ids,
            diagnostics=diagnostics,
        )
        validation = validate_exact_commit_certificate(
            preliminary_result,
            expected_scope=support.exactness_scope,
            canvas=canvas_tokens,
            proposals=proposal_items,
            graph=byte_lattice.graph,
            grammar_recognizer=lambda labels: recognizes_cnf(grammar, labels),
            tokenizer_validator=lambda token_ids, labels: _tokenizer_witness_is_exact(
                tokenizer_adapter,
                token_ids,
                labels,
            ),
            support_validator=lambda token_ids: _finite_support_witness_is_exact(
                support,
                token_ids,
            ),
            eos_validator=lambda token_ids: _absent_eos_witness_is_exact(
                tokenizer_adapter,
                token_ids,
            ),
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
        diagnostics=diagnostics,
    )


__all__ = ["ExactBackend", "solve_exact_commit"]
