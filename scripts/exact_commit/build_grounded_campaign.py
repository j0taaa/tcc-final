#!/usr/bin/env python3
"""Revalidate all M25 certificates, coverage and paired external comparisons."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from compare_policy_repeats import build
from diagnose_policy_whitespace import diagnose
from summarize_policy_screen import read, summarize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m25_grounded_v1"
OUT = ROOT / "docs/research/generated"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="Development-only progress report; never final evidence",
    )
    args = parser.parse_args()

    def write(name, value):
        path = OUT / name
        text = value if isinstance(value, str) else json.dumps(value, indent=2) + "\n"
        if args.check:
            assert path.read_text() == text, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    inventory, all_rows, whitespace = {}, [], {}
    names = ["interrupted_smoke", "smoke", "development", "confirmation", "repeat"]
    for name in names:
        directory = RAW / name
        if not directory.exists() and args.partial:
            continue
        interrupted = name == "interrupted_smoke"
        config, rows = read(directory, allow_incomplete=interrupted)
        manifest = json.loads((directory / "manifest.json").read_text())
        assert manifest["records"] == len(rows)
        all_rows += rows
        inventory[name] = {
            "records": len(rows),
            "planned_records": len(config["tasks"]) * len(config["policies"]),
            "interrupted": interrupted,
            "producing_commits": sorted({r["git_commit"] for r in rows}),
            "manifest_sha256": hashlib.sha256(
                (directory / "manifest.json").read_bytes()
            ).hexdigest(),
            "producing_command": "PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python "
            "scripts/exact_commit/run_policy_screen.py --config "
            + f"configs/experiments/{config['experiment_id']}.json",
        }
        whitespace[name] = diagnose(config, rows)
        if not interrupted:
            summary, report = summarize(directory)
            summary["scope"] = (
                "M25 question/schema-grounded scalar calls; own checker, not official BFCL"
            )
            write(f"m25-{name}-summary.json", summary)
            write(f"m25-{name}-results.md", report.replace("# M24", "# M25"))
    if all((RAW / d).exists() for d in ("confirmation", "repeat")):
        summary, report = build(RAW / "confirmation", RAW / "repeat")
        write("m25-confirmation-paired-summary.json", summary)
        write("m25-confirmation-paired-results.md", report)
        cfg, first = read(RAW / "confirmation")
        groups = defaultdict(list)
        for row in first:
            groups[row["method"]].append(row)
        coverage = {
            "cases": len(cfg["tasks"]),
            "answer_in_support": sum(r["answer_in_support"] for r in next(iter(groups.values()))),
            "methods": {
                method: {
                    "all_correct": sum(r["correct"] for r in rs),
                    "covered_correct": sum(r["correct"] and r["answer_in_support"] for r in rs),
                    "uncovered_correct": sum(
                        r["correct"] and not r["answer_in_support"] for r in rs
                    ),
                    "min_catalog_size": min(r["active_catalog_size"] for r in rs),
                    "max_catalog_size": max(r["active_catalog_size"] for r in rs),
                    "status_counts": dict(Counter(r["status"] for r in rs)),
                }
                for method, rs in sorted(groups.items())
            },
        }
        write("m25-confirmation-coverage.json", coverage)
    result = {
        "cohorts": inventory,
        "complete_campaign": len(inventory) == len(names),
        "recorded_generations": len(all_rows),
        "distinct_task_ids": len({r["task"]["id"] for r in all_rows}),
        "model_forwards": sum(r["forwards"] for r in all_rows),
        "statuses": dict(sorted(Counter(r["status"] for r in all_rows).items())),
        "source_commits": sorted({r["git_commit"] for r in all_rows}),
        "model_revisions": sorted({r["model_revision"] for r in all_rows}),
        "hardware": sorted({r["hardware"] for r in all_rows}),
        "limitations": [
            "own scalar AST grader; not official BFCL score",
            "schema/query-based eligibility is a restricted external subset",
            "family split separates function names, not every semantic domain",
            "answer-independent finite support can omit the correct value",
            "two timings per request are not independent samples",
            "secondary comparisons have no multiplicity adjustment",
            "partial interrupted smoke retained separately",
        ],
    }
    write("m25-campaign-inventory.json", result)
    write("m25-whitespace-sensitivity.json", whitespace)
    print(json.dumps({k: v for k, v in result.items() if k != "cohorts"}, indent=2))


if __name__ == "__main__":
    main()
