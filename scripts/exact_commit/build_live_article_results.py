#!/usr/bin/env python3
"""Generate article tables from independently regenerated live-study summaries."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "docs/research/generated"
OUTPUT = ROOT / "paper/generated/m25_live_v1"
LABELS = {
    "confidence_0.8": r"MWPC, $\tau=0.8$",
    "confidence_0.2": r"MWPC, $\tau=0.2$",
    "greedy_confidence_0.8": r"Greedy, $\tau=0.8$",
    "greedy_confidence_0.2": r"Greedy, $\tau=0.2$",
    "exact_multi3": r"MWPC, three proposals/slot",
}


def label(name):
    if name in LABELS:
        return LABELS[name]
    if name.startswith("epic_lexical_"):
        return "EPIC, " + name.rsplit("_", 1)[1] + " steps"
    if name.startswith("exact_b"):
        return "MWPC, budget " + name.removeprefix("exact_b")
    if name.startswith("catalog_map"):
        return "MAP, cap " + name.removeprefix("catalog_map")
    raise ValueError(name)


def table(summary, *, external):
    name = "grounded" if external else "synthetic"
    caption = (
        "External scalar queries, disjoint function-name families. "
        "Own AST grading; not an official BFCL score."
        if external
        else "Synthetic tool-call confirmation with real LLaDA. "
        "Strict call accuracy preserves the requested operations."
    )
    lines = [
        r"\begin{table}[ht]",
        r"\centering\small",
        r"\caption{"
        + caption
        + f" There are {summary['unique_requests']} requests. Correct calls are shown "
        "separately for two repetitions; total latency includes "
        "setup and upstream recovery, with repeats aggregated within each request. "
        "Forwards are summed over the first repetition.}",
        r"\label{tab:live-" + name + "}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Method & Correct 1/2 & Valid 1/2 & Median ms & Forwards \\",
        r"\midrule",
    ]
    for row in summary["table"]:
        a, b = row["correct"]
        va, vb = row["valid"]
        lines.append(
            f"{label(row['method'])} & {a}/{b} & {va}/{vb} & "
            f"{row['median_total_ms']:.0f} & {row['forwards'][0]} " + r"\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(lines)


def build(*, grounded):
    sources = {}

    def read(name):
        raw = (INPUT / name).read_bytes()
        sources[name] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    synthetic = read("m24-confirmation-paired-summary.json")
    secondary = read("m24-secondary-vs-epic_lexical_8.json")
    values = {}

    def numbers(prefix, summary):
        suffixes = {
            "confidence_0.8": "Confidence",
            "exact_b4": "BudgetFour",
            "exact_b64": "BudgetFull",
            "epic_lexical_8": "EpicEight",
            "epic_lexical_24": "EpicFull",
            "epic_lexical_32": "EpicThirtyTwo",
            "epic_lexical_64": "EpicSixtyFour",
            "catalog_map8": "MapEight",
            "catalog_map64": "MapFull",
            "greedy_confidence_0.8": "Greedy",
        }
        for row in summary["table"]:
            if row["method"] in suffixes:
                suffix = suffixes[row["method"]]
                values[prefix + suffix + "Correct"] = str(row["correct"][0])
                values[prefix + suffix + "Ms"] = f"{row['median_total_ms']:.0f}"

    numbers("MLive", synthetic)
    primary = synthetic["paired_comparisons"]["confidence_0.8"]
    values["MLivePrimarySpeed"] = f"{primary['median_paired_speed_ratio']:.2f}"
    values["MLivePrimaryLower"] = f"{primary['paired_accuracy_conservative95_pp'][0]:.2f}"
    values["MLivePrimaryUpper"] = f"{primary['paired_accuracy_conservative95_pp'][1]:.2f}"
    values["MLiveSecondaryP"] = (
        f"{secondary['paired_comparisons']['exact_b4']['mcnemar_exact_two_sided']:.5f}"
    )
    output = {"synthetic-results.tex": table(synthetic, external=False)}
    if grounded:
        external = read("m25-confirmation-paired-summary.json")
        coverage = read("m25-confirmation-coverage.json")
        output["grounded-results.tex"] = table(external, external=True)
        values["MGroundedCases"] = str(external["unique_requests"])
        values["MGroundedCovered"] = str(coverage["answer_in_support"])
        numbers("MGrounded", external)
        primary = external["paired_comparisons"][external["primary_method"]]
        values["MGroundedPrimarySpeed"] = f"{primary['median_paired_speed_ratio']:.2f}"
        values["MGroundedPrimaryDifference"] = f"{primary['accuracy_difference_pp']:.2f}"
        values["MGroundedPrimaryLower"] = f"{primary['paired_accuracy_conservative95_pp'][0]:.2f}"
        values["MGroundedPrimaryUpper"] = f"{primary['paired_accuracy_conservative95_pp'][1]:.2f}"
    output["live-values.tex"] = (
        "\n".join("\\newcommand{\\" + name + "}{" + value + "}" for name, value in values.items())
        + "\n"
    )
    output["sources.json"] = (
        json.dumps(
            {
                "summary_sha256": sources,
                "validation_commands": ["scripts/exact_commit/build_policy_campaign.py --check"]
                + (["scripts/exact_commit/build_grounded_campaign.py --check"] if grounded else []),
            },
            indent=2,
        )
        + "\n"
    )
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    p.add_argument("--grounded", action="store_true")
    args = p.parse_args()
    for name, text in build(grounded=args.grounded).items():
        path = OUTPUT / name
        if args.check:
            assert path.read_text() == text, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(
        "Live article derivatives verified" if args.check else "Live article derivatives generated"
    )


if __name__ == "__main__":
    main()
