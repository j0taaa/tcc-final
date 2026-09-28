#!/usr/bin/env python3
"""Recheck catalog certificates and summarize complete live screening cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from mwpc_research.tool_screen import screen_tasks, select_catalog, tool_catalog


def summarize(directory: Path) -> dict:
    config = json.loads((directory / "config.json").read_text())
    support = json.loads((directory / "support.json").read_text())
    records = [json.loads(line) for line in (directory / "results.jsonl").read_text().splitlines()]
    family = config.get("family", "simple")
    assert support["catalog"] == list(tool_catalog(family))
    tasks = {t["id"]: t for t in screen_tasks(config["seed"], config["task_count"], family)}
    paths = support["paths"]
    support_hash = hashlib.sha256(json.dumps(paths).encode()).hexdigest()
    groups = defaultdict(list)
    paired = defaultdict(dict)
    seen = set()
    gaps = []
    for row in records:
        key = (row["task"]["id"], row["method"], row["budget"])
        assert key not in seen
        seen.add(key)
        assert row["task"] == tasks[key[0]]
        assert row["support_sha256"] == support_hash
        assert (
            row["config_sha256"]
            == hashlib.sha256((directory / "config.json").read_bytes()).hexdigest()
        )
        canvas = [None] * config["slots"]
        assert row["forwards"] == len(row["trace"])
        for trace in row["trace"]:
            assert trace["canvas_before"] == canvas
            result = select_catalog(paths, canvas, trace["proposals"], method=row["method"])
            assert result.witness_index == trace["witness_index"]
            assert list(result.selected_positions) == trace["selected_positions"]
            assert abs(result.objective - trace["objective"]) < 1e-10
            other = select_catalog(
                paths,
                canvas,
                trace["proposals"],
                method="greedy" if row["method"] == "exact" else "exact",
            )
            assert abs(other.objective - trace["other_objective"]) < 1e-10
            if abs(result.objective - other.objective) > 1e-10:
                gaps.append(
                    {
                        "task": key[0],
                        "method": row["method"],
                        "budget": row["budget"],
                        "step": trace["step"],
                        "score": result.objective,
                        "other_score": other.objective,
                    }
                )
            assert trace["fallback"] == (not result.selected_positions)
            expected_commits = list(result.selected_positions) or [canvas.index(None)]
            assert expected_commits == trace["committed_positions"]
            for p in expected_commits:
                assert canvas[p] is None
                canvas[p] = paths[result.witness_index][p]
        complete = all(t is not None for t in canvas)
        assert complete == (row["status"] == "complete")
        if complete:
            assert canvas in paths
            assert row["output"] == support["catalog"][paths.index(canvas)]
        assert row["correct"] == (complete and row["output"] == row["task"]["expected"])
        groups[(row["budget"], row["method"])].append(row)
        paired[(row["budget"], key[0])][row["method"]] = row
    assert len(records) == len(tasks) * len(config["methods"]) * len(config["proposal_budgets"])
    cells = []
    comparisons = []
    for (budget, method), rows in sorted(groups.items()):
        cells.append(
            {
                "budget": budget,
                "method": method,
                "n": len(rows),
                "correct": sum(r["correct"] for r in rows),
                "forwards": sum(r["forwards"] for r in rows),
            }
        )
    for budget in config["proposal_budgets"]:
        pairs = [pair for (b, _), pair in paired.items() if b == budget]
        wins = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"] and not p["greedy"]["correct"]
        ]
        losses = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["greedy"]["correct"] and not p["exact"]["correct"]
        ]
        fewer = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"]
            and p["greedy"]["correct"]
            and p["exact"]["forwards"] < p["greedy"]["forwards"]
        ]
        more = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"]
            and p["greedy"]["correct"]
            and p["exact"]["forwards"] > p["greedy"]["forwards"]
        ]
        comparisons.append(
            {
                "budget": budget,
                "exact_only_correct": wins,
                "greedy_only_correct": losses,
                "both_correct_exact_fewer_forwards": fewer,
                "both_correct_exact_more_forwards": more,
            }
        )
    return {
        "experiment": config["experiment_id"],
        "records": len(records),
        "unique_tasks": len(tasks),
        "cells": cells,
        "comparisons": comparisons,
        "score_gap_states": gaps,
        "producing_commits": sorted({r["git_commit"] for r in records}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = [summarize(directory) for directory in args.directories]
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
