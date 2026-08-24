from __future__ import annotations

from types import SimpleNamespace

import pytest

mwpc_parser_py = pytest.importorskip("mwpc_parser_py")

from mwpc_exact.reference.dag_parser import validate_dag_certificate  # noqa: E402
from mwpc_exact.reference.grammar import (  # noqa: E402
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.rust_solver import solve_rust_dag  # noqa: E402
from mwpc_exact.types import (  # noqa: E402
    EpsilonEdge,
    SolveStatus,
    TerminalEdge,
    WeightedTerminalDAG,
)


def single_terminal_grammar(label: int | str) -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, label),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(20, 0, 10),),
    )


@pytest.mark.parametrize("label", [b"x"[0], "terminal-x"])
def test_binding_round_trips_labels_ids_status_and_provenance(label: int | str) -> None:
    grammar = single_terminal_grammar(label)
    graph = WeightedTerminalDAG(
        node_ids=(10, 20),
        start_node_id=10,
        final_node_ids=(20,),
        edges=(TerminalEdge(7, 10, 20, label, 2.5, 70, (100, 101)),),
    )

    result = solve_rust_dag(grammar, graph)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 2.5
    assert result.certificate is not None
    assert result.certificate.witness_terminal_labels == (label,)
    assert result.certificate.witness_graph_edge_ids == (7,)
    assert result.certificate.selected_proposal_ids == (100, 101)
    assert result.witness_token_edge_ids == (70,)
    assert validate_dag_certificate(grammar, graph, result.certificate)


def test_binding_timeout_is_not_infeasible_and_exposes_no_partial_data() -> None:
    grammar = single_terminal_grammar("x")
    graph = WeightedTerminalDAG(
        (0, 1),
        0,
        (1,),
        (TerminalEdge(0, 0, 1, "x", 1.0),),
    )

    result = solve_rust_dag(grammar, graph, deterministic_work_limit=0)

    assert result.status is SolveStatus.TIMEOUT
    assert result.objective_value is None
    assert result.certificate is None
    assert result.witness_token_edge_ids == ()
    assert result.diagnostics["deadline_checks"] == 1


def test_binding_preserves_repeated_proposal_id_occurrences() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "X")),
        terminals=(Terminal(10, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 1, 10),),
        binary_productions=(BinaryProduction(1, 0, 1, 1),),
    )
    graph = WeightedTerminalDAG(
        (0, 1, 2),
        0,
        (2,),
        (
            TerminalEdge(0, 0, 1, "x", 2, matched_proposal_ids=(7,)),
            TerminalEdge(1, 1, 2, "x", 3, matched_proposal_ids=(7,)),
        ),
    )

    result = solve_rust_dag(grammar, graph)

    assert result.certificate is not None
    assert result.certificate.selected_proposal_ids == (7, 7)
    assert validate_dag_certificate(grammar, graph, result.certificate)


def test_binding_rejects_external_epsilon_edges_clearly() -> None:
    grammar = single_terminal_grammar("x")
    graph = WeightedTerminalDAG((0, 1), 0, (1,), (EpsilonEdge(0, 0, 1),))

    with pytest.raises(ValueError, match="normalize epsilon edges first"):
        mwpc_parser_py.solve(grammar, graph)


@pytest.mark.parametrize(
    ("field", "value", "error", "message"),
    [
        ("edge_id", True, TypeError, "not bool"),
        ("edge_id", -1, TypeError, "non-negative integer"),
        ("weight", float("nan"), ValueError, "finite"),
        ("weight", -1.0, ValueError, "non-negative"),
    ],
)
def test_binding_rejects_malformed_python_edge_fields(
    field: str,
    value: object,
    error: type[Exception],
    message: str,
) -> None:
    grammar = single_terminal_grammar("x")
    edge_fields: dict[str, object] = {
        "edge_id": 0,
        "source_state": 0,
        "target_state": 1,
        "terminal_label": "x",
        "weight": 1.0,
        "provenance_token_edge_id": None,
        "matched_proposal_ids": (),
    }
    edge_fields[field] = value
    graph = SimpleNamespace(
        node_ids=(0, 1),
        start_node_id=0,
        final_node_ids=(1,),
        edges=(SimpleNamespace(**edge_fields),),
    )

    with pytest.raises(error, match=message):
        mwpc_parser_py.solve(grammar, graph)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"timeout_seconds": float("inf")}, "finite and non-negative"),
        ({"deadline_check_interval": 0}, "positive integer"),
        ({"deterministic_work_limit": -1}, "non-negative integer"),
    ],
)
def test_python_boundary_validates_solver_controls(kwargs: dict[str, object], message: str) -> None:
    grammar = single_terminal_grammar("x")
    graph = WeightedTerminalDAG((0, 1), 0, (1,), ())

    with pytest.raises(ValueError, match=message):
        solve_rust_dag(grammar, graph, **kwargs)  # type: ignore[arg-type]
