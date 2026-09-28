from itertools import product
from random import Random

import pytest

from mwpc_research.commit_stability import stable_catalog_commit


def test_defer_near_tie_without_changing_optimizer_selected_set():
    result = stable_catalog_commit(
        ((1, 1, 7), (0, 0, 7)),
        (None,) * 3,
        ((0, 1, 6), (1, 0, 5), (2, 7, 3)),
        tolerance=1,
    )
    assert result.optimizer.selected_positions == (0, 2)
    assert result.optimizer.objective == 9
    assert result.certified_positions == result.committed_positions == (2,)
    assert result.stability[0].margin == 1
    assert result.stability[1].forced_on_support
    assert not result.progress_fallback


def test_tied_optima_and_fallback_are_not_certified():
    result = stable_catalog_commit(
        ((0, 0), (1, 1)), (None, None), ((0, 0, 1), (1, 1, 1)), tolerance=0
    )
    assert result.certified_positions == ()
    assert result.progress_fallback
    assert result.committed_positions == (0,)
    assert result.stability[0].margin == 0


def test_zero_weight_fallback_is_not_a_matched_proposal():
    result = stable_catalog_commit(((2,),), (None,), ((0, 2, 0),), tolerance=0)
    assert result.optimizer.selected_positions == ()
    assert result.certified_positions == ()
    assert result.progress_fallback and result.committed_positions == (0,)


def test_completed_canvas_has_no_fallback():
    result = stable_catalog_commit(((2,),), (2,), (), tolerance=0)
    assert not result.progress_fallback and result.committed_positions == ()


@pytest.mark.parametrize("seed", range(240000, 240040))
def test_gate_equals_independent_near_optimal_consensus(seed):
    rng = Random(seed)
    paths = rng.sample(list(product(range(3), repeat=4)), 16)
    canvas = (paths[0][0], None, None, None)
    proposals = tuple((p, rng.randrange(3), rng.randrange(6)) for p in range(1, 4))
    tolerance = rng.randrange(5)
    result = stable_catalog_commit(paths, canvas, proposals, tolerance=tolerance)
    feasible = [path for path in paths if path[0] == canvas[0]]
    scored = [(path, sum(w for p, t, w in proposals if path[p] == t)) for path in feasible]
    optimum = max(score for _, score in scored)
    near = [path for path, score in scored if score >= optimum - tolerance]
    expected = {
        p
        for p in result.optimizer.selected_positions
        if all(path[p] == result.optimizer.witness_token_ids[p] for path in near)
    }
    assert set(result.certified_positions) == expected, seed
    assert result.optimizer.objective == optimum, seed
    assert result.optimizer.witness_token_ids[0] == canvas[0], seed
    assert all(
        all(path[p] == result.optimizer.witness_token_ids[p] for p in expected) for path in near
    ), seed


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_tolerance_and_weights(value):
    with pytest.raises(ValueError):
        stable_catalog_commit(((0,),), (None,), (), tolerance=value)
    with pytest.raises(ValueError):
        stable_catalog_commit(((0,),), (None,), ((0, 0, value),), tolerance=0)
