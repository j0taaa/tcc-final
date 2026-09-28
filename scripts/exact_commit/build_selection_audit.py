#!/usr/bin/env python3
"""Regenerate/check every M19 manuscript derivative from verified archived rows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m19_selection_audit_v1"
OUTPUT = ROOT / "paper/generated/m19_selection_audit_v1"


def render_timing_table(summary: dict) -> str:
    rows = [
        row for row in summary["comparisons"] if row.get("comparator") == "greedy_witness_reuse"
    ]
    counts = {(row["paired_feasible_states"], row["paired_feasible_repetitions"]) for row in rows}
    if len(counts) != 1:
        raise ValueError("timing table requires equal paired sample sizes in every row")
    states, observations = counts.pop()
    if states <= 0 or observations % states:
        raise ValueError("invalid paired sample size")
    repetitions = observations // states
    lines = [
        r"\begin{table}[ht]",
        r"\centering\small",
        r"\caption{Saved-state selection against witness-reusing greedy. Absolute times "
        r"are medians of state medians; ratios are medians of paired within-state ratios, "
        f"not ratios of the absolute columns. Each row has {states} feasible states and "
        f"{repetitions} repetitions. Model inference and top-$K$ preparation are excluded." + "}",
        r"\label{tab:selection-audit}",
        r"\begin{tabular}{rrrrr}\toprule",
        r"$K$ & Budget & Exact (ms) & Greedy (ms) & Greedy/exact\\ \midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['width']} & {row['proposal_budget']} & "
            f"{1000 * row['paired_median_exact_seconds']:.1f} & "
            f"{1000 * row['paired_median_comparator_seconds']:.1f} & "
            f"{row['median_state_speedup']:.2f}" + r" \\"
        )
    return "\n".join([*lines, r"\bottomrule\end{tabular}", r"\end{table}", ""])


def expected_outputs() -> dict[str, str]:
    outputs = {}
    for filename, options in (("summary.json", ()), ("audit-values.tex", ("--latex",))):
        outputs[filename] = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.exact_commit.run_review_offline",
                "--analyze-directory",
                str(RAW),
                *options,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
    outputs["audit-timing.tex"] = render_timing_table(json.loads(outputs["summary.json"]))
    return outputs


def verify_outputs(directory: Path, expected: dict[str, str]) -> None:
    for filename, content in expected.items():
        path = directory / filename
        if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
            raise ValueError(f"selection audit derivative differs or is missing: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = expected_outputs()
    if args.check:
        verify_outputs(OUTPUT, expected)
        print("M19 summary, manuscript values and timing table verified")
    else:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for filename, content in expected.items():
            (OUTPUT / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
