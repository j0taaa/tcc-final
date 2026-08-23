#!/usr/bin/env python3
# ruff: noqa: E402
"""Run the deepest deterministic model-free EPIC baseline smoke path."""

from __future__ import annotations

import json
import sys

sys.dont_write_bytecode = True

from rustformlang.cfg import CFG, TerminalGraph

from mwpc_exact.epic_adapter.baseline_graph import baseline_graph_intersection_is_empty


def main() -> int:
    cfg = CFG.from_text("S -> A B\nA -> a\nB -> b", "S")
    valid_graph = TerminalGraph(3, 0, [2], [(0, "a", 1), (1, "b", 2)])
    invalid_graph = TerminalGraph(3, 0, [2], [(0, "a", 1), (1, "a", 2)])

    valid_completable = not baseline_graph_intersection_is_empty(cfg, valid_graph, 1.0)
    invalid_completable = not baseline_graph_intersection_is_empty(cfg, invalid_graph, 1.0)
    assert valid_completable
    assert not invalid_completable

    print(
        json.dumps(
            {
                "path": "EPIC rustformlang CFG-on-TerminalGraph",
                "model_free": True,
                "normalized_before_graph_check": True,
                "valid_path_completable": valid_completable,
                "invalid_path_completable": invalid_completable,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
