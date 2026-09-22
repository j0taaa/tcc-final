#!/usr/bin/env python3
"""Verify archived review evidence and regenerate the manuscript's new results."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path
from statistics import median

from mwpc_research.live_evidence import summarize_live_rows

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m17_review_v1"
OUTPUT = ROOT / "paper/generated/m17_review_v1"
BUNDLES = ("branching", "pilot-v1", "pilot-v2", "confirmation", "scaling", "replay-v1", "replay")


def verified_rows(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        if hashlib.sha256((directory / relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"archive hash mismatch: {directory.name}/{relative}")
    raw = gzip.decompress((directory / "rows.jsonl.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest["raw_rows_sha256"]:
        raise ValueError("uncompressed row hash mismatch")
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != manifest["row_count"]:
        raise ValueError("row count mismatch")
    if any(row["run_metadata"]["git_dirty"] for row in rows):
        raise ValueError("review measurements must name a clean producing commit")
    return rows


def live_table(rows):
    groups = summarize_live_rows(rows)["groups"]
    lines = [
        r"\begin{table}[ht]",
        r"\centering\small",
        r"\caption{Nonliteral confirmation: four tasks per family, two repetitions per task. "
        r"C: complete; S: syntactically valid; F: functionally successful. Counts use all eight "
        r"attempts. Time is the median of observed attempts, including incomplete outputs.}",
        r"\label{tab:review-live}",
        r"\begin{tabular}{llrrrrr}\toprule",
        r"Family & Strategy & C & S & F & Forwards & Seconds\\ \midrule",
    ]
    for group in groups:
        items = [
            r
            for r in rows
            if r["strategy"] == group["strategy"] and r["task"]["family"] == group["family"]
        ]
        times = [r["runtime_seconds"] for r in items if r.get("runtime_seconds") is not None]
        forwards = [
            r["model_forward_count"] for r in items if r.get("model_forward_count") is not None
        ]
        # Missing/censored attempts stay visible; do not report only successes.
        timing = f"{median(times):.2f}" if len(times) == len(items) else "--"
        forward = f"{min(forwards)}--{max(forwards)}" if len(forwards) == len(items) else "--"
        name = {"nested_json": "JSON", "arithmetic": "Arithmetic", "brackets": "Brackets"}[
            group["family"]
        ]
        lines.append(
            f"{name} & {group['strategy']} & {group['statuses'].get('complete', 0)} & "
            f"{group['syntax_valid']} & {group['functional_success']} & {forward} & {timing}"
            + r" \\"
        )
    return "\n".join([*lines, r"\bottomrule\end{tabular}", r"\end{table}", ""])


def derive(all_rows):
    branching = all_rows["branching"]
    if any(row["failures"] for row in branching):
        raise ValueError("branching correctness gate failed")
    replay = all_rows["replay"]
    pairs = defaultdict(dict)
    for row in replay:
        pairs[row["instance"]["instance_id"]][row["method"]] = row
    gaps = []
    zero_scores = 0
    positive_scores = 0
    nested = defaultdict(list)
    for pair in pairs.values():
        exact, greedy = pair["rust_exact"], pair["greedy_exact_feasibility"]
        if exact["status"] == "optimal":
            zero_scores += exact["score"] == 0
            positive_scores += exact["score"] > 0
            info = exact["instance"]["metadata"]
            nested[info["snapshot_id"]].append((info["width"], exact["score"]))
        if exact["status"] == "optimal" and greedy["status"] == "feasible_on_support":
            gap = exact["score"] - greedy["score"]
            if gap < -1e-12:
                raise ValueError("heuristic score exceeded exact on the same saved instance")
            gaps.append(gap)
    for values in nested.values():
        scores = [score for _, score in sorted(values)]
        if any(right < left for left, right in pairwise(scores)):
            raise ValueError("score decreased under nested support expansion")
    scaling = all_rows["scaling"]
    counters = [row.get("profile", {}).get("sizes", {}).get("counters", {}) for row in scaling]
    stats = {
        "producing_commits": {
            name: sorted({r["run_metadata"]["git_commit"] for r in rows})
            for name, rows in all_rows.items()
        },
        "branching": {
            "cases": len(branching),
            "failures": 0,
            "positive_gap_cases": sum(r["absolute_gap"] > 0 for r in branching),
            "multiple_valid_paths_cases": sum(r["valid_paths"] > 1 for r in branching),
        },
        "replay": {
            "rows": len(replay),
            "paired_conditions": len(pairs),
            "paired_feasible_conditions": len(gaps),
            "positive_gaps": sum(g > 0 for g in gaps),
            "zero_score_optima": zero_scores,
            "positive_score_optima": positive_scores,
            "statuses": dict(Counter(f"{r['method']}:{r['status']}" for r in replay)),
        },
        "scaling": {
            "rows": len(scaling),
            "statuses": dict(Counter(r["status"] for r in scaling)),
            "max_nodes": max(c.get("terminal_graph_node_count", 0) for c in counters),
            "max_edges": max(c.get("terminal_graph_edge_count", 0) for c in counters),
            "max_rss_bytes": max(r.get("peak_rss_bytes", 0) for r in scaling),
        },
        "pilot": summarize_live_rows(all_rows["pilot-v2"]),
        "confirmation": summarize_live_rows(all_rows["confirmation"]),
        "pilot_v1_errors": sum(r["execution_status"] == "error" for r in all_rows["pilot-v1"]),
    }
    stats["scaling"]["settings"] = []
    grouped = defaultdict(list)
    for row in scaling:
        info = row["instance"]["metadata"]
        grouped[info["slots"], info["width"], info["fixed_depth"]].append(row)
    for (slots, width, depth), rows in sorted(grouped.items()):
        times = [r["runtime_seconds"] for r in rows if r["status"] == "optimal"]
        stats["scaling"]["settings"].append(
            {
                "slots": slots,
                "width": width,
                "fixed_depth": depth,
                "statuses": dict(Counter(r["status"] for r in rows)),
                "optimal_runtime_median_seconds": median(times) if times else None,
                "optimal_runtime_count": len(times),
                "max_rss_bytes": max(r.get("peak_rss_bytes", 0) for r in rows),
            }
        )
    return stats


def outputs():
    all_rows = {name: verified_rows(RAW / name) for name in BUNDLES}
    stats = derive(all_rows)
    numbers = {
        "BranchingCases": stats["branching"]["cases"],
        "BranchingGaps": stats["branching"]["positive_gap_cases"],
        "BranchingMultiple": stats["branching"]["multiple_valid_paths_cases"],
        "ReplayPairs": stats["replay"]["paired_conditions"],
        "ReplayFeasible": stats["replay"]["paired_feasible_conditions"],
        "ReplayPositiveGaps": stats["replay"]["positive_gaps"],
        "ReplayZeroScores": stats["replay"]["zero_score_optima"],
        "ScalingCases": stats["scaling"]["rows"],
        "ScalingTimeouts": stats["scaling"]["statuses"].get("timeout", 0),
        "ScalingMaxNodes": stats["scaling"]["max_nodes"],
        "ScalingMaxEdges": stats["scaling"]["max_edges"],
        "ScalingMaxMiB": round(stats["scaling"]["max_rss_bytes"] / 1024**2, 1),
    }
    result = {
        "summary.json": json.dumps(stats, indent=2, sort_keys=True) + "\n",
        "review-values.tex": "".join(
            f"\\newcommand{{\\MReview{key}}}{{{value}}}\n" for key, value in numbers.items()
        ),
        "confirmation.tex": live_table(all_rows["confirmation"]),
        "provenance.json": json.dumps(
            {
                name: hashlib.sha256((RAW / name / "manifest.json").read_bytes()).hexdigest()
                for name in BUNDLES
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = outputs()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, content in result.items():
        path = OUTPUT / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"stale generated review result: {path}")
        else:
            path.write_text(content)
    print("Review evidence hashes and generated results verified.")


if __name__ == "__main__":
    main()
