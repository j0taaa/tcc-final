"""Evaluate the predeclared gate; retain every conclusive, zero and refused case."""

import argparse
import gzip
import itertools
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    path = args.input / "rows.jsonl"
    data = (
        path.read_text()
        if path.exists()
        else gzip.decompress((args.input / "rows.jsonl.gz").read_bytes()).decode()
    )
    rows = [json.loads(line) for line in data.splitlines()]
    metadata = json.loads((args.input / "metadata.json").read_text())
    protocol = metadata["protocol"]
    expected = (
        len(metadata["capture"]["selected"])
        * len(protocol["mask_counts"])
        * len(protocol["methods"])
        * (
            protocol["independent_repetitions"]
            if metadata["capture"]["phase"] == "independent"
            else protocol["fresh_repetitions"]
            if metadata["capture"]["phase"] == "fresh"
            else protocol["repetitions"]
        )
    )
    repeats_required = (
        protocol["independent_repetitions"]
        if metadata["capture"]["phase"] == "independent"
        else protocol["fresh_repetitions"]
        if metadata["capture"]["phase"] == "fresh"
        else protocol["repetitions"]
    )
    keys = [(r["case"], r["mask_count"], r["method"], r["repeat"]) for r in rows]
    allowed = set(
        itertools.product(
            [d["key"] for d in metadata["capture"]["selected"]],
            protocol["mask_counts"],
            protocol["methods"],
            range(repeats_required),
        )
    )
    if len(keys) != len(set(keys)) or not set(keys) <= allowed:
        raise ValueError("duplicate or unexpected measurement row")
    candidates = protocol.get("candidates", ["local"])
    primary = protocol.get("selected_candidate", candidates[0])
    controls_expected = protocol.get("exact_controls", ["raw", "global", "position"])
    candidate_wins = {name: [] for name in candidates}
    candidate_sampling = {name: [] for name in candidates}
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["case"], row["mask_count"]][row["method"]].append(row)
    cases = []
    for (case, masks), methods in grouped.items():
        item = dict(case=case, mask_count=masks, methods={}, comparisons=[], sampling={})
        for method, repeats in methods.items():
            record = dict(statuses=dict(Counter(r["status"] for r in repeats)))
            completed = [r for r in repeats if r["status"] == "complete"]
            for field in (
                "prepared_total",
                "cold_total",
                "sampling_total",
                "operation",
                "startup",
                "conversion",
                "compilation",
                "inside",
                "outside_and_original_marginals",
            ):
                measured = [r[field] for r in completed if field in r]
                if measured:
                    record[field] = {u: median(r[u] for r in measured) for u in ("wall", "cpu")}
            if completed:
                for field in (
                    "valid_mass",
                    "integer_bits",
                    "graph_edges",
                    "cells",
                    "alternatives",
                    "peak_rss_kib",
                    "trials",
                ):
                    if field in completed[0]:
                        record[field] = completed[0][field]
            item["methods"][method] = record
        exact = [
            r
            for method, repeats in methods.items()
            if method != "rejection"
            for r in repeats
            if r["status"] in ("complete", "zero_valid_mass")
        ]
        for field in ("exact_total", "exact_denominator", "matrix_sha256"):
            if len({r[field] for r in exact if field in r}) > 1:
                raise ValueError(f"unequal exact {field} for {case}/{masks}")
        item["candidate_decisions"] = {}
        for candidate in candidates:
            chosen = dict(comparisons=[], sampling={})
            all_local = methods.get(candidate, [])
            required_repeats = (
                protocol["independent_repetitions"]
                if metadata["capture"]["phase"] == "independent"
                else protocol["fresh_repetitions"]
                if metadata["capture"]["phase"] == "fresh"
                else protocol["repetitions"]
            )
            conclusive = len(all_local) == required_repeats and all(
                r["status"] == "complete" for r in all_local
            )
            benefit = conclusive
            for comparator in controls_expected:
                controls = methods.get(comparator, [])
                comparison = dict(comparator=comparator)
                if len(controls) != required_repeats or not conclusive:
                    comparison["utility"] = False
                elif all(r["status"] == "resource_refusal" and "operation" in r for r in controls):
                    comparison.update(utility=True, reason="capacity_at_equal_predeclared_limits")
                elif all(r["status"] == "complete" for r in controls):
                    local_by_rep = {r["repeat"]: r for r in all_local}
                    ratios = {
                        u: [
                            local_by_rep[r["repeat"]]["prepared_total"][u] / r["prepared_total"][u]
                            for r in controls
                        ]
                        for u in ("wall", "cpu")
                    }
                    comparison.update(
                        ratio_medians={u: median(v) for u, v in ratios.items()},
                        favorable_every_repeat=all(x < 1 for v in ratios.values() for x in v),
                    )
                    comparison["utility"] = (
                        all(median(v) <= 0.8 for v in ratios.values())
                        and comparison["favorable_every_repeat"]
                    )
                else:
                    comparison["utility"] = False
                benefit &= comparison["utility"]
                chosen["comparisons"].append(comparison)
            chosen["strong_benefit"] = benefit
            if benefit:
                candidate_wins[candidate].append([case, masks])
            rejection_rows = methods.get("rejection", [])
            if conclusive and rejection_rows:
                if all(
                    r["status"] == "resource_refusal" and "operation" in r for r in rejection_rows
                ):
                    chosen["sampling"] = dict(useful=True, reason="all_rejection_runs_exhausted")
                elif all(r["status"] == "complete" for r in rejection_rows):
                    local_by_rep = {r["repeat"]: r for r in all_local}
                    ratios = {
                        u: [
                            local_by_rep[r["repeat"]]["sampling_total"][u] / r["sampling_total"][u]
                            for r in rejection_rows
                        ]
                        for u in ("wall", "cpu")
                    }
                    chosen["sampling"] = dict(
                        ratio_medians={u: median(v) for u, v in ratios.items()},
                        useful=all(median(v) <= 0.8 and max(v) < 1 for v in ratios.values()),
                    )
                if chosen["sampling"].get("useful"):
                    candidate_sampling[candidate].append([case, masks])
            item["candidate_decisions"][candidate] = chosen
        item["comparisons"] = item["candidate_decisions"][primary]["comparisons"]
        item["sampling"] = item["candidate_decisions"][primary]["sampling"]
        item["strong_local_benefit"] = item["candidate_decisions"][primary]["strong_benefit"]
        for method in ("raw", "global", "position", "local"):
            mass = item["methods"].get(method, {}).get("valid_mass")
            if mass is not None and Fraction(mass) > 0:
                item["expected_rejection_attempts"] = float(1 / Fraction(mass))
                break
        cases.append(item)
    wins, sampling_wins = candidate_wins[primary], candidate_sampling[primary]
    report = dict(
        primary_candidate=primary,
        candidate_benefits=candidate_wins,
        candidate_sampling_benefits=candidate_sampling,
        rows=len(rows),
        expected_rows=expected,
        campaign_complete=set(keys) == allowed,
        statuses=dict(Counter(r["status"] for r in rows)),
        producer_commit=metadata["producer_commit"],
        strong_local_benefit=wins,
        sampling_benefit=sampling_wins,
        cases=cases,
        scope="Full frozen vocabulary posterior, not whole-generation speed or semantic accuracy",
        priority="Known lexer/semiring/quotient principles; world novelty unconfirmed",
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "decision.json").write_text(json.dumps(report, indent=2) + "\n")
    text = [
        f"# Full vocabulary posterior — {metadata['capture']['phase']}",
        "",
        f"Rows: {len(rows)}/{expected}. Statuses: {report['statuses']}.",
        f"Default/frozen candidate: {primary}. Strong benefits: {len(wins)}/{len(cases)}; "
        f"sampling: {len(sampling_wins)}.",
        "Candidate benefit counts: " + str({k: len(v) for k, v in candidate_wins.items()}),
        "",
        "Prepared service costs include frame compilation, full marginals "
        "and shared actual forward.",
        "| Case / masks | "
        + " | ".join(
            method + " wall / CPU"
            for method in (
                ("bidir_global", "bidir_position", "stack", primary, "rejection")
                if "stack" in protocol["methods"]
                else ("global", "position", primary, "rejection")
            )
        )
        + " | Strong |",
        "|---|" + "---:|" * (5 if "stack" in protocol["methods"] else 4) + "---|",
    ]
    for item in cases:
        columns = []
        for method in (
            ("bidir_global", "bidir_position", "stack", primary, "rejection")
            if "stack" in protocol["methods"]
            else ("global", "position", primary, "rejection")
        ):
            record = item["methods"].get(method, {})
            costs = record.get("prepared_total")
            columns.append(
                f"{costs['wall']:.3f} / {costs['cpu']:.3f}"
                if costs
                else str(record.get("statuses"))
            )
        text.append(
            f"| {item['case'][:8]} / {item['mask_count']} | "
            + " | ".join(columns)
            + f" | {item['strong_local_benefit']} |"
        )
    text.extend(
        [
            "",
            report["scope"],
            report["priority"],
            "",
            "All startup/cold costs, refusals and exact mass retained in decision.json.",
        ]
    )
    (args.output / "decision.md").write_text("\n".join(text) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "rows",
                    "expected_rows",
                    "statuses",
                    "candidate_benefits",
                    "strong_local_benefit",
                    "sampling_benefit",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
