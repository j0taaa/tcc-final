#!/usr/bin/env python3
"""Recheck catalog certificates and summarize complete live screening cohorts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from math import fsum
from pathlib import Path
from statistics import median

from mwpc_research.tool_screen import (
    CatalogSelection,
    operand_preserving_indices,
    screen_tasks,
    select_catalog,
    tool_catalog,
)


def summarize(directory: Path) -> dict:
    config = json.loads((directory / "config.json").read_text())
    support = json.loads((directory / "support.json").read_text())
    records = [json.loads(line) for line in (directory / "results.jsonl").read_text().splitlines()]
    family = config.get("family", "simple")
    assert support["catalog"] == list(tool_catalog(family))
    task_list = config.get("tasks") or screen_tasks(config["seed"], config["task_count"], family)
    tasks = {t["id"]: t for t in task_list}
    production = config.get("backend") == "rust"
    emissions = (
        {
            int(t): bytes(b)
            for t, b in json.loads((directory / "token_emissions.json").read_text()).items()
        }
        if production
        else {}
    )

    def decode_witness(witness):
        endpoint = witness.index(126081)
        assert all(t == 126081 for t in witness[endpoint:])
        return b"".join(emissions[t] for t in witness[:endpoint]).decode()

    paths = support["paths"]
    support_hash = hashlib.sha256(json.dumps(paths).encode()).hexdigest()
    groups = defaultdict(list)
    paired = defaultdict(dict)
    seen = set()
    gaps = []
    for row in records:
        active_indices = list(range(len(support["catalog"])))
        if config.get("preserve_operands", False):
            active_indices = list(
                operand_preserving_indices(support["catalog"], row["task"]["instruction"])
            )
        assert row.get("active_catalog_indices", active_indices) == active_indices
        paths = [support["paths"][i] for i in active_indices]
        calls = [support["catalog"][i] for i in active_indices]
        domains = [{path[p] for path in paths} for p in range(config["slots"])]
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
        assert row["forwards"] == len(row["trace"]) + bool(row.get("failure"))
        for trace in row["trace"]:
            assert trace["canvas_before"] == canvas
            if production:
                witness = tuple(trace["witness_token_ids"])
                assert len(witness) == config["slots"]
                assert all(t in domains[p] for p, t in enumerate(witness))
                assert all(t is None or t == witness[p] for p, t in enumerate(canvas))
                assert decode_witness(witness) in calls
                matched = tuple(p for p, t, w in trace["proposals"] if w > 0 and witness[p] == t)
                score = fsum(w for p, t, w in trace["proposals"] if witness[p] == t)
                result = CatalogSelection(trace["witness_index"], matched, score, witness)
                native = trace["production_result"]
                assert native["status"] == (
                    "optimal" if row["method"] == "exact" else "feasible_on_support"
                )
                assert native["witness_token_ids"] == list(witness)
                assert abs(native["score"] - score) < 1e-10
                other_score = trace["other_objective"]
                if other_score is not None:
                    assert (
                        (score + 1e-10 >= other_score)
                        if row["method"] == "exact"
                        else (other_score + 1e-10 >= score)
                    )
            else:
                result = select_catalog(paths, canvas, trace["proposals"], method=row["method"])
                assert result.witness_index == trace["witness_index"]
                other = select_catalog(
                    paths,
                    canvas,
                    trace["proposals"],
                    method="greedy" if row["method"] == "exact" else "exact",
                )
                other_score = other.objective
                assert abs(other_score - trace["other_objective"]) < 1e-10
            assert list(result.selected_positions) == trace["selected_positions"]
            assert abs(result.objective - trace["objective"]) < 1e-10
            if other_score is not None and abs(result.objective - other_score) > 1e-10:
                gaps.append(
                    {
                        "task": key[0],
                        "method": row["method"],
                        "budget": row["budget"],
                        "step": trace["step"],
                        "score": result.objective,
                        "other_score": other_score,
                    }
                )
            assert trace["fallback"] == (not result.selected_positions)
            expected_commits = list(result.selected_positions) or [canvas.index(None)]
            assert expected_commits == trace["committed_positions"]
            for p in expected_commits:
                assert canvas[p] is None
                canvas[p] = result.witness_token_ids[p]
        complete = all(t is not None for t in canvas)
        assert complete == (row["status"] == "complete")
        if complete:
            if production:
                assert row["output"] == decode_witness(canvas)
                assert row["output"] in calls
            else:
                assert canvas in paths
                assert row["output"] == support["catalog"][active_indices[paths.index(canvas)]]
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
                "median_seconds_including_grammar_setup": median(
                    r["elapsed_excluding_shadow_seconds"] + r.get("grammar_setup_seconds", 0)
                    for r in rows
                ),
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
                "both_correct_median_speed_ratio_greedy_over_exact": median(
                    [
                        (
                            p["greedy"]["elapsed_excluding_shadow_seconds"]
                            + p["greedy"].get("grammar_setup_seconds", 0)
                        )
                        / (
                            p["exact"]["elapsed_excluding_shadow_seconds"]
                            + p["exact"].get("grammar_setup_seconds", 0)
                        )
                        for p in pairs
                        if p["exact"]["correct"] and p["greedy"]["correct"]
                    ]
                )
                if any(p["exact"]["correct"] and p["greedy"]["correct"] for p in pairs)
                else None,
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
