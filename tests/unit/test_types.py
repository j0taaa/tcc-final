from math import inf, nan

import pytest

from mwpc_exact import ExactCommitResult, ExactnessScope, Proposal, SolveStatus, SupportKind


def finite_scope() -> ExactnessScope:
    return ExactnessScope(
        kind=SupportKind.TOP_K,
        vocabulary_size=128,
        included_special_tokens=(0, 127),
        top_k=8,
        pruning_description="top-8 per masked slot",
    )


@pytest.mark.parametrize("weight", [-1.0, inf, -inf, nan])
def test_proposal_rejects_invalid_weight(weight: float) -> None:
    with pytest.raises(ValueError):
        Proposal(0, position=0, token_id=1, weight=weight)


def test_scope_records_top_k() -> None:
    scope = finite_scope()
    assert scope.kind is SupportKind.TOP_K
    assert scope.top_k == 8


def test_optimal_requires_certificate() -> None:
    with pytest.raises(ValueError):
        ExactCommitResult(
            status=SolveStatus.OPTIMAL,
            exactness_scope=finite_scope(),
            objective_value=1.0,
        )


def test_valid_optimal_result() -> None:
    result = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=finite_scope(),
        objective_value=2.5,
        selected_proposal_ids=("p0",),
        witness_token_ids=(10, 11),
        witness_terminal_labels=("a", "b"),
        witness_graph_edge_ids=("e0", "e1"),
    )
    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 2.5


def test_timeout_cannot_claim_selected_proposals() -> None:
    with pytest.raises(ValueError):
        ExactCommitResult(
            status=SolveStatus.TIMEOUT,
            exactness_scope=finite_scope(),
            selected_proposal_ids=("p0",),
        )
