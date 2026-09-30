#!/usr/bin/env python3
"""Post-hoc gold-support diagnostics. Never used by the generation driver."""

import argparse
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from summarize_policy_screen import read

from mwpc_exact import CompositionalByteLevelAdapter, ExactBackend, Proposal, select_exact_mwpc
from mwpc_research.tool_parser import catalog_byte_grammar, production_input


def diagnose(directory: Path, *, backend: ExactBackend = ExactBackend.RUST):
    config, records = read(directory)
    support = json.loads((directory / "support.json").read_text())
    emissions = {
        int(t): bytes(b)
        for t, b in json.loads((directory / "token_emissions.json").read_text()).items()
    }
    adapter = CompositionalByteLevelAdapter(tuple(emissions.get(t) for t in range(126464)))
    details = []
    for row in records:
        if row["method"] != "exact_b24":
            continue
        calls = [support["catalog"][i] for i in row["active_catalog_indices"]]
        paths = [support["paths"][i] for i in row["active_catalog_indices"]]
        rows = [sorted({path[p] for path in paths}) for p in range(config["slots"])]
        expected = row["task"]["expected"]
        assert expected in calls
        gold = catalog_byte_grammar([expected])
        detail = {
            "task_id": row["task"]["id"],
            "correct": row["correct"],
            "gold_in_initial_support": True,
        }
        if not row["correct"]:
            for trace in row["trace"]:
                after = list(trace["canvas_before"])
                for p in trace["committed_positions"]:
                    after[p] = trace["witness_token_ids"][p]
                feasible = select_exact_mwpc(
                    production_input(gold, after, (), rows, adapter, 126081), backend=backend
                )
                if feasible.status.value == "infeasible_on_support":
                    before = production_input(
                        gold, trace["canvas_before"], (), rows, adapter, 126081
                    )
                    proposals = tuple(
                        Proposal(i, p, t, w) for i, (p, t, w) in enumerate(trace["proposals"])
                    )
                    gold_best = select_exact_mwpc(
                        replace(before, proposals=proposals), backend=backend
                    )
                    assert gold_best.score is not None
                    gap = trace["production_result"]["score"] - gold_best.score
                    detail.update(
                        first_gold_excluding_step=trace["step"],
                        score_gap=gap,
                        category="objective_prefers_wrong_completion"
                        if gap > 1e-9
                        else "tied_score_wrong_commit",
                        excluded_by_positions=trace["committed_positions"],
                    )
                    break
                assert feasible.status.value == "optimal"
        details.append(detail)
    result = {
        "source_commit": records[0]["git_commit"],
        "method": "exact_b24",
        "counts": dict(
            Counter(
                d.get("category", "correct" if d["correct"] else "other_failure") for d in details
            )
        ),
        "limitations": (
            "gold used only after generation; score mismatch does not establish "
            "a causal benefit of deferral"
        ),
        "details": details,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("python", "rust"), default="rust")
    args = parser.parse_args()
    result = diagnose(args.directory, backend=ExactBackend(args.backend))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
