from dataclasses import replace
from itertools import product
from random import Random

import pytest

import mwpc_exact.commit_gate as gate_module
from mwpc_exact import CompositionalByteLevelAdapter, ExactBackend, SelectionStatus
from mwpc_exact.commit_gate import select_stable_commit
from mwpc_research.commit_stability import stable_catalog_commit
from mwpc_research.tool_parser import catalog_byte_grammar, production_input


def state_for(calls, proposals, canvas=(None, None, None)):
    return production_input(
        catalog_byte_grammar(calls),
        canvas,
        proposals,
        ((0, 1, 2),) * 3,
        CompositionalByteLevelAdapter((b"a", b"b", None)),
        2,
    )


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
@pytest.mark.parametrize("seed", range(241000, 241030))
def test_production_margins_match_independent_catalog_with_eos(backend, seed):
    rng = Random(seed)
    paths = rng.sample([(a, b, 2) for a, b in product(range(2), repeat=2)], 3)
    calls = ["".join("ab"[t] for t in path[:2]) for path in paths]
    proposals = tuple((p, rng.randrange(3), rng.randrange(1, 9)) for p in range(3))
    tolerance = rng.randrange(4)
    state = state_for(calls, proposals)
    reference = stable_catalog_commit(paths, state.canvas, proposals, tolerance=tolerance)
    result = select_stable_commit(state, tolerance=tolerance, backend=backend)
    assert result.status is SelectionStatus.OPTIMAL, seed
    assert result.optimizer.score == reference.optimizer.objective, seed
    # Witness ties need not be equal; test consensus from all near-optimal paths.
    scored = [(path, sum(w for p, t, w in proposals if path[p] == t)) for path in paths]
    near = [path for path, score in scored if score >= result.optimizer.score - tolerance]
    selected = result.optimizer.selected_proposal_ids
    expected = {
        p
        for p in selected
        if all(path[p] == result.optimizer.witness_token_ids[p] for path in near)
    }
    assert set(result.certified_positions) == expected, seed
    for query in result.queries:
        alternatives = [
            score
            for path, score in scored
            if path[query.position] != result.optimizer.witness_token_ids[query.position]
        ]
        assert query.forced_on_support == (not alternatives), seed
        if alternatives:
            assert query.alternative_score == max(alternatives), seed
    assert state.support.rows == ((0, 1, 2),) * 3


def test_fixed_position_duplicate_matches_and_zero_weight_preserved():
    from mwpc_exact import Proposal

    state = state_for(("aa", "ab"), ((1, 0, 1), (2, 2, 0)), canvas=(0, None, None))
    state = replace(state, proposals=(*state.proposals, Proposal(99, 1, 0, 2)))
    result = select_stable_commit(state, tolerance=0)
    assert result.optimizer.selected_proposal_ids == (1, 99)
    assert result.optimizer.witness_token_ids[0] == 0
    assert result.certified_positions == (1,)


def test_query_timeout_is_unknown_not_forced(monkeypatch):
    original = gate_module.select_exact_mwpc
    calls = 0

    def fail_second(state, **kwargs):
        nonlocal calls
        calls += 1
        result = original(state, **kwargs)
        if calls == 2:
            return gate_module.SelectionResult(
                result.selector, SelectionStatus.TIMEOUT, result.exactness_scope, 0
            )
        return result

    monkeypatch.setattr(gate_module, "select_exact_mwpc", fail_second)
    result = select_stable_commit(state_for(("aa", "bb"), ((0, 0, 2),)), tolerance=0)
    assert result.status is SelectionStatus.TIMEOUT
    assert not result.certified_positions and not result.committed_positions
    assert not result.queries[0].forced_on_support


def test_total_deadline_checks_late_results_and_zero_budget():
    ticks = iter([0, 0, 2, 2, 2, 2])
    state = state_for(("aa",), ((0, 0, 1),))
    result = select_stable_commit(
        state, tolerance=0, total_timeout_seconds=1, clock=lambda: next(ticks)
    )
    assert result.status is SelectionStatus.TIMEOUT and not result.committed_positions
    result = select_stable_commit(state, tolerance=0, total_timeout_seconds=0)
    assert result.status is SelectionStatus.TIMEOUT and result.optimizer is None


def test_numerical_boundary_is_conservative():
    state = state_for(("aa", "bb"), ((0, 0, 1), (1, 1, 1 - 1e-12)))
    result = select_stable_commit(state, tolerance=0)
    assert result.certified_positions == () and result.progress_fallback


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_controls(value):
    state = state_for(("aa",), ())
    for key in ("tolerance", "total_timeout_seconds", "numerical_guard"):
        with pytest.raises(ValueError):
            select_stable_commit(state, **{"tolerance": 0, key: value})
