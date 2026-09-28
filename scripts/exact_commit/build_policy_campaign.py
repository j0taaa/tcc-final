#!/usr/bin/env python3
"""Validate every frozen M24 cohort and regenerate its complete report collection."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from compare_policy_repeats import build
from diagnose_policy_whitespace import diagnose
from summarize_policy_screen import read, summarize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m24_policy_v1"
OUT = ROOT / "docs/research/generated"
COHORTS = {
    "smoke": 40,
    "development": 600,
    "confirmation": 700,
    "repeat": 700,
    "secondary": 400,
    "secondary_repeat": 400,
    "bfcl": 160,
    "bfcl_repeat": 160,
    "epic_intermediate": 300,
    "epic_intermediate_repeat": 300,
    "bfcl_controls": 48,
    "bfcl_controls_repeat": 48,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    def write(path, value):
        text = value if isinstance(value, str) else json.dumps(value, indent=2) + "\n"
        if args.check:
            assert path.read_text() == text, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    all_rows, cohorts, whitespace = [], {}, {}
    for name, count in COHORTS.items():
        directory = RAW / name
        config, rows = read(directory)
        assert len(rows) == count
        summary, report = summarize(directory)
        write(OUT / f"m24-{name}-summary.json", summary)
        write(OUT / f"m24-{name}-results.md", report)
        all_rows += rows
        whitespace[name] = diagnose(config, rows)
        cohorts[name] = {
            "records": count,
            "producing_commits": sorted({r["git_commit"] for r in rows}),
            "manifest_sha256": hashlib.sha256(
                (directory / "manifest.json").read_bytes()
            ).hexdigest(),
            "producing_command": "PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python "
            "scripts/exact_commit/run_policy_screen.py --config "
            f"configs/experiments/{config['experiment_id']}.json",
        }
    for name, dirs in (
        (
            "confirmation-paired",
            (
                "confirmation",
                "repeat",
                "secondary",
                "secondary_repeat",
                "epic_intermediate",
                "epic_intermediate_repeat",
            ),
        ),
        ("external-paired", ("bfcl", "bfcl_repeat", "bfcl_controls", "bfcl_controls_repeat")),
    ):
        summary, report = build(*(RAW / d for d in dirs))
        write(OUT / f"m24-{name}-summary.json", summary)
        write(OUT / f"m24-{name}-results.md", report)
    inventory = {
        "cohorts": cohorts,
        "live_final_generations": len(all_rows),
        "additional_review_canvases": sum("draft" in r for r in all_rows),
        "unique_task_ids": len({r["task"]["id"] for r in all_rows}),
        "policies": sorted({r["method"] for r in all_rows}),
        "status_counts": dict(sorted(Counter(r["status"] for r in all_rows).items())),
        "total_model_forwards": sum(r["forwards"] for r in all_rows),
        "model_revisions": sorted({r["model_revision"] for r in all_rows}),
        "tokenizer_revisions": sorted({r["tokenizer_revision"] for r in all_rows}),
        "hardware": sorted({r["hardware"] for r in all_rows}),
        "limitations": [
            "repetitions are not independent tasks",
            "100 confirmation requests use the same synthetic templates as development",
            "eight external cases cover only 8/658 audited BFCL examples and four function names",
            "historical greedy row scope labels name the exact feasibility parser; "
            "their feasible_on_support status does not guarantee optimal proposal selection",
            "GPU allocation includes model weights; CPU peak memory was not measured",
        ],
    }
    write(OUT / "m24-campaign-inventory.json", inventory)
    write(OUT / "m24-whitespace-sensitivity.json", whitespace)
    print(json.dumps({k: v for k, v in inventory.items() if k != "cohorts"}, indent=2))


if __name__ == "__main__":
    main()
