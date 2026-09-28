from itertools import product
from random import Random

import pytest

from mwpc_research.tool_screen import screen_tasks, select_catalog, tool_catalog


def test_catalog_is_prompt_independent_and_tasks_are_nonliteral():
    catalog = tool_catalog()
    assert len(catalog) == len(set(catalog)) == 320
    for seed in (220001, 220002):
        assert all(t["expected"] in catalog for t in screen_tasks(seed, 100))
    assert screen_tasks(220001, 24) != screen_tasks(220002, 24)


def test_exact_can_reject_one_confident_proposal_for_two_joint_matches():
    paths = ((0, 0, 0), (1, 1, 1))
    proposals = ((0, 0, 0.9), (1, 1, 0.6), (2, 1, 0.6))
    exact = select_catalog(paths, (None,) * 3, proposals, method="exact")
    greedy = select_catalog(paths, (None,) * 3, proposals, method="greedy")
    assert exact.witness_index == 1 and exact.objective == 1.2
    assert exact.selected_positions == (1, 2)
    assert greedy.witness_index == 0 and greedy.objective == 0.9


def test_random_optima_and_fixed_positions_against_independent_enumeration():
    for seed in range(220000, 220050):
        rng = Random(seed)
        paths = rng.sample(list(product(range(3), repeat=4)), 12)
        canvas = (paths[0][0], None, None, None)
        proposals = tuple(
            sorted(
                ((p, rng.randrange(3), rng.randrange(1, 10)) for p in range(1, 4)),
                key=lambda item: -item[2],
            )
        )
        result = select_catalog(paths, canvas, proposals, method="exact")
        scores = [
            sum(w for p, t, w in proposals if path[p] == t)
            for path in paths
            if path[0] == canvas[0]
        ]
        assert result.objective == max(scores), seed
        assert paths[result.witness_index][0] == canvas[0], seed
        greedy = select_catalog(paths, canvas, proposals, method="greedy")
        assert greedy.objective <= result.objective, seed


@pytest.mark.parametrize("weight", [-1, float("nan"), float("inf")])
def test_invalid_weights_rejected(weight):
    with pytest.raises(ValueError):
        select_catalog(((0,),), (None,), ((0, 0, weight),), method="exact")
