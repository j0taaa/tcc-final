from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from test_compact_budget_graph import make_state

from mwpc_exact import Proposal
from mwpc_exact.budget_certificate import check_budget_commit_certificate, check_budget_graph
from mwpc_exact.budget_graph import BudgetGraphLayout, BudgetGraphNode, TokenClosing
from mwpc_exact.budgeted_commit import budgeted_commit_frontier, budgeted_progress_update
from mwpc_exact.eos_policy import TokenRole
from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budgeted_parser import budgeted_frontier


def fixture():
    state = make_state(
        (b"a", b"ab", b"ac"),
        (b"a", b"ab", b"ac", b"a"),
        ((0, 1, 2, 3),),
        (
            Proposal(0, 0, 0, 1),
            Proposal(1, 0, 1, 3),
        ),
    )
    return state, budgeted_commit_frontier(state, 1)[1]


@pytest.mark.parametrize("layout", tuple(BudgetGraphLayout))
def test_original_checker_accepts_both_complete_representations(layout):
    state, _ = fixture()
    for result in budgeted_commit_frontier(state, 2, graph_layout=layout):
        assert check_budget_commit_certificate(state, result).accepted


def test_a_valid_optimality_proof_for_altered_rewards_is_not_a_proof_for_original_input():
    state, result = fixture()
    graph = result.proof_graph
    changed = tuple(replace(a, reward=a.reward + 1) if a.cost else a for a in graph.arcs)
    foreign_graph = replace(graph, arcs=changed)
    foreign_path = budgeted_frontier(state.grammar, foreign_graph, 1)[1]
    assert check_budget_certificate(state.grammar, foreign_graph, foreign_path).accepted
    forged = replace(
        result,
        objective_value=foreign_path.objective_value,
        path_result=foreign_path,
        proof_graph=foreign_graph,
        compiled_graph=replace(result.compiled_graph, graph=foreign_graph),
    )
    report = check_budget_commit_certificate(state, forged)
    assert not report.accepted
    assert "token closures do not exactly represent original choices and rewards" in report.errors


def test_even_removing_an_unrewarded_choice_invalidates_input_correspondence():
    state, result = fixture()
    remove = next(c.arc_id for c in result.compiled_graph.closings if c.token_id == 3)
    graph = replace(
        result.proof_graph, arcs=tuple(a for a in result.proof_graph.arcs if a.arc_id != remove)
    )
    compiled = replace(
        result.compiled_graph,
        graph=graph,
        closings=tuple(c for c in result.compiled_graph.closings if c.arc_id != remove),
    )
    assert not check_budget_graph(state, compiled).accepted


@pytest.mark.parametrize(
    "field,value",
    (
        ("committed_positions", ()),
        ("committed_proposal_ids", ()),
        ("matched_proposal_ids", ()),
        ("witness_token_ids", (3,)),
        ("witness_terminal_labels", (97,)),
        ("objective_value", Fraction(99)),
        ("input_fingerprint", "0" * 64),
    ),
)
def test_original_checker_rejects_tampered_result_metadata(field, value):
    state, result = fixture()
    forged = replace(result, **{field: value})
    assert not check_budget_commit_certificate(state, forged).accepted
    with pytest.raises(ValueError):
        budgeted_progress_update(state, forged)


def test_closing_token_alias_cannot_be_relabelled_even_if_visible_bytes_match():
    state, result = fixture()
    ends = tuple(
        replace(c, token_id=3) if c.token_id == 0 else c for c in result.compiled_graph.closings
    )
    compiled = replace(result.compiled_graph, closings=ends)
    assert not check_budget_graph(state, compiled).accepted


def test_node_prefix_and_eos_role_are_independently_checked():
    state, result = fixture()
    compiled = result.compiled_graph
    for forged in (
        replace(
            compiled,
            nodes=tuple(replace(n, prefix=b"x") if n.prefix else n for n in compiled.nodes),
        ),
        replace(
            compiled, closings=tuple(replace(c, role=TokenRole.PAD) for c in compiled.closings)
        ),
        replace(compiled, private_node_count=compiled.private_node_count + 1),
    ):
        assert not check_budget_graph(state, forged).accepted


def test_boolean_ids_are_not_valid_node_or_closing_metadata():
    with pytest.raises(ValueError):
        BudgetGraphNode(False, 0, False)
    with pytest.raises(ValueError):
        TokenClosing(0, True, 0, TokenRole.ORDINARY)
    _, result = fixture()
    with pytest.raises(ValueError):
        replace(result.path_result, witness_arc_ids=(True,))
    with pytest.raises(ValueError):
        replace(result.path_result, witness_terminal_labels=(True,))


@pytest.mark.parametrize(
    "field,value",
    (
        ("committed_proposal_ids", (True,)),
        ("matched_proposal_ids", (True,)),
        ("committed_proposal_ids", (1.0,)),
        ("matched_proposal_ids", (1.0,)),
        ("committed_positions", (False,)),
        ("witness_token_ids", (True,)),
        ("witness_terminal_labels", (True,)),
        ("budget", True),
    ),
)
def test_result_boundary_rejects_boolean_and_float_aliases_of_integer_metadata(field, value):
    _, result = fixture()
    with pytest.raises(ValueError):
        replace(result, **{field: value})
