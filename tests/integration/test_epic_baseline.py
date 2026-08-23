# ruff: noqa: E402
from __future__ import annotations

import sys

import pytest

sys.dont_write_bytecode = True

from mwpc_exact.epic_adapter.baseline_graph import baseline_graph_intersection_is_empty

rustformlang_cfg = pytest.importorskip("rustformlang.cfg")
CFG = rustformlang_cfg.CFG
TerminalGraph = rustformlang_cfg.TerminalGraph


@pytest.mark.integration
def test_parent_adapter_normalizes_before_epic_graph_check() -> None:
    cfg = CFG.from_text("S -> A B\nA -> a\nB -> b", "S")
    valid_graph = TerminalGraph(3, 0, [2], [(0, "a", 1), (1, "b", 2)])
    invalid_graph = TerminalGraph(3, 0, [2], [(0, "a", 1), (1, "a", 2)])

    assert not baseline_graph_intersection_is_empty(cfg, valid_graph, 1.0)
    assert baseline_graph_intersection_is_empty(cfg, invalid_graph, 1.0)
