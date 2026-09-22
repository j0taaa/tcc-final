#!/usr/bin/env python3
"""Generate a compact evidence report from immutable recursive-study raw rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mwpc_exact import BenchmarkInstance
from mwpc_research.branching_study import summarize_branching_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    arguments = parser.parse_args()
    raw = (arguments.run_directory / "rows.jsonl").read_bytes()
    recorded = json.loads((arguments.run_directory / "summary.json").read_text())
    if hashlib.sha256(raw).hexdigest() != recorded["raw_sha256"]:
        raise ValueError("raw SHA-256 differs from the recorded summary")
    rows = [json.loads(line) for line in raw.splitlines()]
    for row in rows:
        instance = BenchmarkInstance.from_dict(row["instance"])
        if instance.fingerprint != row["instance_sha256"]:
            raise ValueError("saved input changed")
    summary = summarize_branching_rows(rows)
    if any(recorded[key] != value for key, value in summary.items()):
        raise ValueError("recorded summary does not reproduce from raw rows")
    summary.update(
        {
            key: recorded[key]
            for key in (
                "raw_sha256",
                "expected_rows",
                "complete",
                "source_changed_during_run",
                "run_metadata",
            )
        }
    )
    directory = arguments.output_directory
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "summary.json").open("x") as output:
        json.dump(summary, output, allow_nan=False, indent=2)
    lines = [
        "# Recursive branching-support study",
        "",
        "Generated from immutable raw JSONL. This is synthetic, feasibility-conditioned,",
        "dirty-tree development evidence, not real-model or EPIC performance evidence.",
        "",
        f"- Unique family/seed states: {summary['generated_state_count']}.",
        f"- Shared seed clusters across families: {summary['seed_cluster_count']}.",
        f"- Repeated support/weight conditions: {summary['row_count']}.",
        f"- Correctness failure rows: {summary['correctness_failure_rows']}.",
        f"- Width objective improvements: {summary['width_objective_improvements']}/"
        f"{summary['width_pairs']} paired objectives.",
        f"- Width monotonicity violations: {summary['width_monotonicity_violations']}.",
        f"- Raw SHA-256: `{summary['raw_sha256']}`.",
        "",
        "| Family | Width | Weights | Multiple valid completions | Greedy loses | Mean / max gap |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for group in summary["groups"]:
        gap = group["absolute_gap"]
        lines.append(
            f"| {group['family']} | {group['width']} | {group['weight_mode']} | "
            f"{group['branching_valid_states']}/{group['state_count']} | "
            f"{group['positive_gap_count']}/{group['gap_pair_count']} | "
            f"{gap['mean']:.3f} / {gap['maximum']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Branching and loss are separate quantities: multiple valid completions need not",
            "make greedy selection suboptimal. These states test correctness and characterize",
            "this generator only. Exactness does not imply a typical real-model advantage.",
            "",
            "Whole-selector timings and all status counts are in summary.json. The greedy",
            "baseline repeatedly invokes the common finite-feasibility solver; it is not the",
            "upstream serial decoder. No ratio here is an EPIC or end-to-end speedup.",
            "",
            "Widths and weight modes share seeds. Do not treat the repeated conditions as",
            "independent samples or pool them into a population confidence interval.",
            "",
        ]
    )
    with (directory / "report.md").open("x") as output:
        output.write("\n".join(lines))
    print(
        json.dumps(
            {"output_directory": str(directory), "verified_raw_sha256": summary["raw_sha256"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
