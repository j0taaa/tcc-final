from __future__ import annotations

import json
from math import nan

import pytest

from mwpc_exact import (
    ExactCommitResult,
    ExactnessScope,
    SolveStatus,
    SupportKind,
    TerminalEdge,
    TokenArc,
    WeightedTerminalDAG,
)


def explicit_scope() -> ExactnessScope:
    return ExactnessScope(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=128,
        included_special_tokens=(0, 127),
        pruning_description="support IDs recorded in the fixture",
    )


def test_token_arc_canonicalizes_immutable_provenance() -> None:
    matched_ids = [4, 9]
    emitted = bytearray(b"ab")
    arc = TokenArc(
        token_edge_id=3,
        slot=1,
        token_id=42,
        source_boundary=1,
        target_boundary=2,
        emitted_bytes=emitted,  # type: ignore[arg-type]
        weight=2,
        matched_proposal_ids=matched_ids,  # type: ignore[arg-type]
    )
    matched_ids.append(12)
    emitted.append(99)

    assert arc.emitted_bytes == b"ab"
    assert arc.weight == 2.0
    assert arc.matched_proposal_ids == (4, 9)


def test_terminal_graph_rejects_missing_edge_endpoint() -> None:
    edge = TerminalEdge(edge_id=7, source_state=0, target_state=2, terminal_label="a")

    with pytest.raises(ValueError, match="edge endpoint"):
        WeightedTerminalDAG(
            node_ids=(0, 1),
            start_node_id=0,
            final_node_ids=(1,),
            edges=(edge,),
        )


def test_terminal_graph_rejects_duplicate_stable_ids() -> None:
    first = TerminalEdge(edge_id=7, source_state=0, target_state=1, terminal_label=97)
    second = TerminalEdge(edge_id=7, source_state=1, target_state=2, terminal_label="b")

    with pytest.raises(ValueError, match="edge IDs must be unique"):
        WeightedTerminalDAG(
            node_ids=(0, 1, 2),
            start_node_id=0,
            final_node_ids=(2,),
            edges=(first, second),
        )


def test_valid_terminal_graph_keeps_stable_ids() -> None:
    edges = (
        TerminalEdge(
            edge_id=7,
            source_state=10,
            target_state=20,
            terminal_label=97,
            weight=1.5,
            provenance_token_edge_id=3,
            matched_proposal_ids=(4,),
        ),
        TerminalEdge(edge_id=8, source_state=20, target_state=30, terminal_label="b"),
    )

    graph = WeightedTerminalDAG(
        node_ids=(10, 20, 30),
        start_node_id=10,
        final_node_ids=(30,),
        edges=edges,
    )

    assert tuple(edge.edge_id for edge in graph.edges) == (7, 8)


@pytest.mark.parametrize(
    "missing_field",
    ["objective_value", "witness_token_ids", "witness_terminal_labels", "witness_graph_edge_ids"],
)
def test_optimal_result_requires_complete_certificate(missing_field: str) -> None:
    values: dict[str, object] = {
        "status": SolveStatus.OPTIMAL,
        "exactness_scope": explicit_scope(),
        "objective_value": 3.0,
        "selected_proposal_ids": (4, 9),
        "witness_token_ids": (42,),
        "witness_terminal_labels": (97, 98),
        "witness_graph_edge_ids": (7, 8),
    }
    values.pop(missing_field)

    with pytest.raises(ValueError, match="OPTIMAL requires"):
        ExactCommitResult(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", list(SolveStatus)[1:])
def test_non_optimal_result_rejects_objective_and_certificate(status: SolveStatus) -> None:
    with pytest.raises(ValueError, match="cannot expose an objective or certificate"):
        ExactCommitResult(
            status=status,
            exactness_scope=explicit_scope(),
            objective_value=0.0,
        )


def test_result_rejects_non_finite_diagnostics() -> None:
    with pytest.raises(ValueError, match="NaN or infinity"):
        ExactCommitResult(
            status=SolveStatus.TIMEOUT,
            exactness_scope=explicit_scope(),
            diagnostics={"elapsed_seconds": nan},
        )


def test_optimal_result_json_round_trip_preserves_status_and_ids() -> None:
    result = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=explicit_scope(),
        objective_value=3.0,
        selected_proposal_ids=(4, 9),
        witness_token_ids=(42,),
        witness_terminal_labels=(97, "b"),
        witness_graph_edge_ids=(7, 8),
        diagnostics={"chart": {"entries": 12}, "tie_break": [7, 8]},
    )

    serialized = json.loads(json.dumps(result.to_dict()))
    restored = ExactCommitResult.from_dict(serialized)

    assert restored == result
    assert restored.status is SolveStatus.OPTIMAL
    assert restored.selected_proposal_ids == (4, 9)
    assert restored.witness_graph_edge_ids == (7, 8)


def test_optimal_result_preserves_repeated_proposal_id_occurrences() -> None:
    result = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=explicit_scope(),
        objective_value=3.0,
        selected_proposal_ids=(4, 4),
        witness_token_ids=(42,),
        witness_terminal_labels=(97,),
        witness_graph_edge_ids=(7,),
    )

    assert ExactCommitResult.from_dict(result.to_dict()).selected_proposal_ids == (4, 4)


def test_result_diagnostics_are_deeply_immutable() -> None:
    diagnostics = {"chart": {"entries": 12}, "edge_ids": [7, 8]}
    result = ExactCommitResult(
        status=SolveStatus.TIMEOUT,
        exactness_scope=explicit_scope(),
        diagnostics=diagnostics,
    )
    diagnostics["chart"]["entries"] = 99  # type: ignore[index]
    diagnostics["edge_ids"].append(9)  # type: ignore[union-attr]

    assert result.to_dict()["diagnostics"] == {
        "chart": {"entries": 12},
        "edge_ids": [7, 8],
    }
