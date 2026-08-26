"""Guarded common-result adapters for the independent exhaustive oracles.

The token-aligned adapter delegates optimization to the M3 completion oracle.
The graph adapter delegates to the M4 path oracle.  Both count their complete
search spaces before enumeration and return an explicit size-limit status when
the configured tiny-instance budget would be exceeded.
"""

from __future__ import annotations

from math import fsum, isclose, prod
from time import perf_counter

from mwpc_exact.byte_lattice import build_byte_lattice
from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    recompute_witness_selection,
)
from mwpc_exact.reference.brute_force import (
    SearchSpaceLimitExceeded,
    exhaustive_completion_oracle,
)
from mwpc_exact.reference.dag_parser import (
    DagParseCertificate,
    validate_dag_certificate,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.reference.graph_oracle import (
    PathEnumerationLimitExceeded,
    enumerate_best_cfg_path,
)
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.types import (
    ExactnessScope,
    SolveStatus,
    TerminalEdge,
    WeightedTerminalDAG,
)


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _limit_result(
    *,
    exactness_scope: ExactnessScope,
    started: float,
    diagnostics: dict[str, object],
) -> SelectionResult:
    return SelectionResult(
        selector=SelectorKind.BRUTE_FORCE,
        status=SelectionStatus.SIZE_LIMIT_EXCEEDED,
        exactness_scope=exactness_scope,
        runtime_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )


def _failure_result(
    *,
    status: SelectionStatus,
    exactness_scope: ExactnessScope,
    started: float,
    diagnostics: dict[str, object],
) -> SelectionResult:
    if status in {
        SelectionStatus.OPTIMAL,
        SelectionStatus.FEASIBLE_ON_SUPPORT,
        SelectionStatus.HEURISTIC,
    }:
        raise ValueError("failure conversion requires a non-success status")
    return SelectionResult(
        selector=SelectorKind.BRUTE_FORCE,
        status=status,
        exactness_scope=exactness_scope,
        runtime_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )


def _token_aligned_labels(
    selection_input: SelectionInput,
) -> tuple[dict[int, int] | None, str | None]:
    token_ids = tuple(
        dict.fromkeys(token_id for row in selection_input.support.rows for token_id in row)
    )
    labels: dict[int, int] = {}
    for token_id in token_ids:
        emission = selection_input.tokenizer_adapter.emissions[token_id]
        if emission is None or len(emission) != 1:
            return None, (
                "the completion oracle requires one unique grammar terminal per represented token"
            )
        labels[token_id] = emission[0]
    if len(set(labels.values())) != len(labels):
        return None, (
            "the completion oracle requires one unique grammar terminal per represented token"
        )
    unknown_labels = sorted(
        set(labels.values()) - set(selection_input.grammar.terminal_labels.values())
    )
    if unknown_labels:
        return None, (
            "the completion oracle requires every represented token terminal to "
            f"appear in the grammar (missing={unknown_labels})"
        )
    return labels, None


def select_brute_force(
    selection_input: SelectionInput,
    *,
    max_completions: int = 100_000,
) -> SelectionResult:
    """Exhaustively optimize one tiny token-aligned common selection input."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    maximum = _positive_integer(max_completions, "max_completions")
    started = perf_counter()
    scope = selection_input.support.exactness_scope
    base_diagnostics: dict[str, object] = {
        "implementation": "m3_exhaustive_completion_oracle",
        "instance_kind": "token_aligned",
        "optimization_guarantee": "exact_on_support",
        "maximum_completions": maximum,
        "input_support_sha256": selection_input.support.fingerprint,
    }

    if selection_input.eos_policy.mode is not EOSMode.ABSENT:
        return _failure_result(
            status=SelectionStatus.UNSUPPORTED,
            exactness_scope=scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "unsupported_reason": (
                    "the token-aligned completion oracle does not model EOS/PAD; "
                    "use the guarded graph oracle on an EOS lattice"
                ),
            },
        )
    labels_by_token_id, unsupported_reason = _token_aligned_labels(selection_input)
    if labels_by_token_id is None:
        assert unsupported_reason is not None
        return _failure_result(
            status=SelectionStatus.UNSUPPORTED,
            exactness_scope=scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "unsupported_reason": unsupported_reason,
            },
        )

    search_space_size = prod(len(row) for row in selection_input.support.rows)
    if search_space_size > maximum:
        return _limit_result(
            exactness_scope=scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "search_space_size": search_space_size,
                "enumeration_started": False,
                "limit_reason": "completion_search_space",
            },
        )

    try:
        oracle = exhaustive_completion_oracle(
            grammar=selection_input.grammar,
            per_position_support=selection_input.support.rows,
            canvas=selection_input.canvas,
            proposals=selection_input.proposals,
            terminal_labels_by_token_id=labels_by_token_id,
            max_completions=maximum,
        )
    except SearchSpaceLimitExceeded as error:
        return _limit_result(
            exactness_scope=scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "search_space_size": error.search_space_size,
                "enumeration_started": False,
                "limit_reason": "completion_search_space",
            },
        )

    enumeration_diagnostics = {
        **base_diagnostics,
        "search_space_size": oracle.search_space_size,
        "enumerated_completions": oracle.enumerated_completions,
        "fixed_compatible_completions": oracle.fixed_compatible_completions,
        "grammar_valid_completions": oracle.grammar_valid_completions,
        "enumeration_started": True,
    }
    if oracle.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        return _failure_result(
            status=SelectionStatus.INFEASIBLE_ON_SUPPORT,
            exactness_scope=scope,
            started=started,
            diagnostics=enumeration_diagnostics,
        )

    optimum = oracle.optima[0]
    selected_ids, score = recompute_witness_selection(
        selection_input,
        optimum.witness_token_ids,
    )
    if set(selected_ids) != set(optimum.selected_proposal_ids) or not isclose(
        score,
        optimum.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        return _failure_result(
            status=SelectionStatus.ERROR,
            exactness_scope=scope,
            started=started,
            diagnostics={
                **enumeration_diagnostics,
                "error_stage": "common_result_validation",
                "error_message": "completion oracle disagrees with witness score recomputation",
                "oracle_selected_proposal_ids": list(optimum.selected_proposal_ids),
                "recomputed_selected_proposal_ids": list(selected_ids),
                "oracle_score": optimum.objective_value,
                "recomputed_score": score,
            },
        )

    try:
        token_lattice = build_token_lattice(
            support=selection_input.support,
            proposals=selection_input.proposals,
        )
        token_path = next(
            path
            for path in token_lattice.iter_paths()
            if path.token_ids == optimum.witness_token_ids
        )
        byte_lattice = build_byte_lattice(
            token_lattice=token_lattice,
            adapter=selection_input.tokenizer_adapter,
        )
        byte_path = byte_lattice.expand_path(token_path)
        byte_lattice.validate_path(byte_path)
        if set(byte_path.matched_proposal_ids) != set(selected_ids) or not isclose(
            byte_path.objective_value,
            score,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("completion and byte-lattice proposal provenance disagree")
        certificate = DagParseCertificate(
            objective_value=score,
            selected_proposal_ids=byte_path.matched_proposal_ids,
            witness_terminal_labels=byte_path.terminal_labels,
            witness_graph_edge_ids=byte_path.graph_edge_ids,
        )
        if optimum.witness_terminal_labels != byte_path.terminal_labels:
            raise ValueError("completion and byte-lattice terminal witnesses disagree")
        if not validate_dag_certificate(
            selection_input.grammar,
            byte_lattice.graph,
            certificate,
        ):
            raise ValueError("completion witness failed independent graph validation")
    except (StopIteration, ValueError) as error:
        return _failure_result(
            status=SelectionStatus.ERROR,
            exactness_scope=scope,
            started=started,
            diagnostics={
                **enumeration_diagnostics,
                "error_stage": "certificate_reconstruction",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    return SelectionResult(
        selector=SelectorKind.BRUTE_FORCE,
        status=SelectionStatus.OPTIMAL,
        exactness_scope=scope,
        runtime_seconds=perf_counter() - started,
        selected_proposal_ids=selected_ids,
        score=score,
        witness_token_ids=optimum.witness_token_ids,
        witness_terminal_labels=byte_path.terminal_labels,
        witness_graph_edge_ids=byte_path.graph_edge_ids,
        witness_content_endpoint_slot=len(selection_input.canvas),
        diagnostics={
            **enumeration_diagnostics,
            "score_recomputed_from_witness": True,
            "certificate_independently_validated": True,
        },
    )


def _completed_path_count(graph: WeightedTerminalDAG) -> int:
    indexed = index_terminal_dag(graph)
    final_ids = set(graph.final_node_ids)
    counts: dict[int, int] = {}
    for node_id in reversed(indexed.topological_order):
        counts[node_id] = (1 if node_id in final_ids else 0) + sum(
            counts[edge.target_state] for edge in indexed.outgoing_edges[node_id]
        )
    return counts[graph.start_node_id]


def select_brute_force_graph(
    grammar: CnfGrammar,
    graph: WeightedTerminalDAG,
    *,
    exactness_scope: ExactnessScope,
    max_paths: int = 100_000,
) -> SelectionResult:
    """Exhaustively optimize one tiny weighted terminal-DAG instance.

    Generic T402 graphs do not encode physical token IDs, so this parser-local
    result carries only stable graph edges and terminal labels.  It is not a
    decoder certificate and never invents a token sequence.
    """

    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(graph, WeightedTerminalDAG):
        raise TypeError("graph must be a WeightedTerminalDAG")
    if not isinstance(exactness_scope, ExactnessScope):
        raise TypeError("exactness_scope must be an ExactnessScope")
    maximum = _positive_integer(max_paths, "max_paths")
    started = perf_counter()
    completed_path_count = _completed_path_count(graph)
    base_diagnostics: dict[str, object] = {
        "implementation": "m4_exhaustive_graph_path_oracle",
        "instance_kind": "terminal_dag",
        "optimization_guarantee": "exact_on_represented_graph",
        "maximum_paths": maximum,
        "completed_path_count": completed_path_count,
    }
    if completed_path_count > maximum:
        return _limit_result(
            exactness_scope=exactness_scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "enumeration_started": False,
                "limit_reason": "completed_graph_paths",
            },
        )

    try:
        oracle = enumerate_best_cfg_path(grammar, graph, max_paths=maximum)
    except PathEnumerationLimitExceeded:
        return _limit_result(
            exactness_scope=exactness_scope,
            started=started,
            diagnostics={
                **base_diagnostics,
                "enumeration_started": True,
                "limit_reason": "completed_graph_paths",
            },
        )

    diagnostics = {
        **base_diagnostics,
        "enumerated_paths": oracle.enumerated_path_count,
        "enumeration_started": True,
    }
    if oracle.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        return _failure_result(
            status=SelectionStatus.INFEASIBLE_ON_SUPPORT,
            exactness_scope=exactness_scope,
            started=started,
            diagnostics=diagnostics,
        )

    certificate = oracle.certificate
    if certificate is None:
        raise AssertionError("optimal graph oracle result omitted its certificate")
    if not certificate.witness_graph_edge_ids:
        return _failure_result(
            status=SelectionStatus.UNSUPPORTED,
            exactness_scope=exactness_scope,
            started=started,
            diagnostics={
                **diagnostics,
                "unsupported_reason": (
                    "the common graph witness requires at least one stable edge ID"
                ),
            },
        )

    edge_by_id = {edge.edge_id: edge for edge in graph.edges}
    edges = tuple(edge_by_id[edge_id] for edge_id in certificate.witness_graph_edge_ids)
    recomputed_score = fsum(edge.weight for edge in edges)
    recomputed_ids = tuple(
        proposal_id for edge in edges for proposal_id in edge.matched_proposal_ids
    )
    recomputed_labels = tuple(
        edge.terminal_label for edge in edges if isinstance(edge, TerminalEdge)
    )
    if (
        not validate_dag_certificate(grammar, graph, certificate)
        or not isclose(
            recomputed_score,
            certificate.objective_value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        or recomputed_ids != certificate.selected_proposal_ids
        or recomputed_labels != certificate.witness_terminal_labels
        or len(set(recomputed_ids)) != len(recomputed_ids)
    ):
        return _failure_result(
            status=SelectionStatus.ERROR,
            exactness_scope=exactness_scope,
            started=started,
            diagnostics={
                **diagnostics,
                "error_stage": "common_result_validation",
                "error_message": "graph oracle certificate failed independent recomputation",
            },
        )

    return SelectionResult(
        selector=SelectorKind.BRUTE_FORCE,
        status=SelectionStatus.OPTIMAL,
        exactness_scope=exactness_scope,
        runtime_seconds=perf_counter() - started,
        selected_proposal_ids=recomputed_ids,
        score=recomputed_score,
        witness_terminal_labels=recomputed_labels,
        witness_graph_edge_ids=certificate.witness_graph_edge_ids,
        diagnostics={
            **diagnostics,
            "score_recomputed_from_graph_edges": True,
            "certificate_independently_validated": True,
            "token_witness_available": False,
        },
    )


__all__ = ["select_brute_force", "select_brute_force_graph"]
