import json
from itertools import product
from pathlib import Path
from random import Random

import pytest

from mwpc_exact import CompositionalByteLevelAdapter, ExactBackend, select_exact_mwpc
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_research.tool_parser import catalog_byte_grammar, production_input
from mwpc_research.tool_screen import screen_tasks, select_catalog, tool_catalog


def test_confirmation_requests_are_frozen_unique_and_unseen():
    path = (
        Path(__file__).resolve().parents[2]
        / "configs/experiments/m22_tool_parser_confirmation_v1.json"
    )
    config = json.loads(path.read_text())
    requests = [t["instruction"] for t in config["tasks"]]
    assert len(requests) == len(set(requests)) == 100
    prior = set()
    for seed, count in ((220002, 30), (220003, 60), (220004, 60)):
        prior.update(t["instruction"] for t in screen_tasks(seed, count, "nested"))
    assert not set(requests) & prior
    generated = {t["id"]: t for t in screen_tasks(220104, 1000, "nested")}
    assert all(task == generated[task["id"]] for task in config["tasks"])


def test_suffix_merging_preserves_exact_language_exhaustively():
    calls = ("aa", "aba", "bba", "b", "bbb")
    grammar = catalog_byte_grammar(calls)
    for n in range(5):
        for word in product("ab", repeat=n):
            text = "".join(word)
            assert recognizes_cnf(grammar, tuple(text.encode())) == (text in calls)


def test_full_nested_catalog_and_out_of_language_calls():
    calls = tool_catalog("nested")
    grammar = catalog_byte_grammar(calls)
    for call in calls:
        assert recognizes_cnf(grammar, tuple(call.encode()))
    for wrong in ("", "add(1)", "neg(1,2)", "mul(add(1,2),4)", "add(add(1,2),neg(3))"):
        assert not recognizes_cnf(grammar, tuple(wrong.encode()))


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_production_solver_matches_catalog_for_exhaustive_byte_paths(backend):
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    adapter = CompositionalByteLevelAdapter((b"a", b"b", None))
    paths = ((0, 0, 0, 2), (1, 1, 1, 2))
    grammar = catalog_byte_grammar(("aaa", "bbb"))
    rows = ((0, 1), (0, 1), (0, 1), (2,))
    for seed in range(220100, 220120):
        rng = Random(seed)
        proposals = tuple((p, rng.randrange(2), rng.random()) for p in range(3))
        inputs = production_input(grammar, (None,) * 4, proposals, rows, adapter, 2)
        result = select_exact_mwpc(inputs, backend=backend)
        oracle = select_catalog(paths, (None,) * 4, proposals, method="exact")
        assert result.score == pytest.approx(oracle.objective), seed
        assert result.witness_token_ids in paths, seed
