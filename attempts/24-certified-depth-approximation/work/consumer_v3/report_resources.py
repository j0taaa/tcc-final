"""Audit all45 frozen known-data rows; report resources, never a speed win."""

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path


def report(folder):
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
    decision = json.loads((folder / "decision.json").read_text())
    indexed = {(r["case"], r["depth"]): r for r in rows}
    cases = sorted({r["case"] for r in rows})
    if len(rows) != 45 or len(indexed) != 45 or len(cases) != 15:
        raise ValueError("partial/duplicated resource campaign cannot pass")
    if set(indexed) != {(c, d) for c in cases for d in (1, 3, None)}:
        raise ValueError("resource configurations changed")
    checks = 0
    for case in cases:
        full = Fraction(indexed[case, None]["true_mass"])
        if full <= 0:
            raise ValueError("full conditioned law is undefined")
        for depth in (1, 3):
            row = indexed[case, depth]
            shallow, upper = Fraction(row["true_mass"]), Fraction(row["upper_tail"])
            if not 0 <= shallow <= full or full - shallow > upper:
                raise ValueError("structural mass/tail bound failed against exact full mass")
            if shallow and 1 - shallow / full > Fraction(row["delta"]):
                raise ValueError("conditional TV bound failed")
            checks += 1
    native = [n for r in rows for n in r.get("native", [])]
    completed = [n for n in native if n["status"] == "complete"]
    plausible = {
        r["case"]
        for r in rows
        if r["depth"] is not None
        and r.get("delta") is not None
        and Fraction(r["delta"]) <= Fraction(1, 1000)
        and any(n.get("correctness_gate") for n in r.get("native", []))
    }
    if plausible != set(decision["plausible_states"]):
        raise ValueError("resource decision disagrees with raw rows")
    result = dict(
        **decision,
        record_statuses=dict(Counter(r["status"] for r in rows)),
        native_statuses=dict(Counter(n["status"] for n in native)),
        native_completed_correct=sum(bool(n.get("correctness_gate")) for n in completed),
        exact_full_mass_tail_checks=checks,
        max_observed_absolute_confidence_error=max(
            n["max_absolute_confidence_error"] for n in completed
        ),
        max_observed_fp64_error=max(
            n["max_absolute_confidence_error"] for n in completed if n["method"].endswith("fp64")
        ),
        source_data_sha256={
            name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
            for name in ("rows.jsonl", "metadata.json", "decision.json")
        },
        diagnostic_overlap=(
            "Isolated Torch2.13 venv creation/pip resolution/download overlapped the final part; "
            "no positive timing conclusion. Resource/correctness gate is independent of timing."
        ),
    )
    text = [
        "# A24 V3 — complete known-data resource screen",
        "",
        f"{len(rows)}/45 records; statuses:{result['record_statuses']}.",
        f"Native statuses:{result['native_statuses']}; "
        f"{result['native_completed_correct']} complete/correct.",
        f"Warnings:{sum(len(n.get('warnings', [])) for n in native)}.",
        f"{checks} tail/conditional checks against exact full masses pass. "
        f"Resource gate:{len(plausible)}/{len(cases)} states.",
        "",
        "These are OLD weights with an appended fixed EOT/PAD, not new neural outputs.",
        "The target is JSON EOT PAD* over all original IDs. "
        "Torch2.8/CUDA12.8 is the declared kernel port.",
        "An allocation guard is not a measured OOM or a general CFG lower bound.",
        "Single-run diagnostic clocks, partly overlapping dependency downloads, "
        "establish no latency advantage.",
        "The independent confirmation/cost/originality goals remain open.",
        "",
        "| Old case | d1 nodes | d1 bound | d3 nodes | d3 bound | "
        "Full nodes | Native full completed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for case in cases:
        a, b, c = (indexed[case, depth] for depth in (1, 3, None))

        def delta(row):
            return "zero L" if row.get("delta") is None else f"{float(Fraction(row['delta'])):.6g}"

        label = case[:8] + "-" + case.rsplit("-", 1)[1]
        complete = sum(n.get("status") == "complete" for n in c["native"])
        text.append(
            f"|{label}|{a['minimized_graph']['nodes']}|{delta(a)}|"
            f"{b['minimized_graph']['nodes']}|{delta(b)}|"
            f"{c['minimized_graph']['nodes']}|{complete}/5|"
        )
    text.extend(
        [
            "",
            "Observed maximum sampled-confidence absolute difference:"
            f"{result['max_observed_absolute_confidence_error']:.9g}; "
            f"fp64:{result['max_observed_fp64_error']:.9g}.",
            "These are observed errors, not certificates for the entire rounded sampling law.",
            "",
        ]
    )
    return result, "\n".join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result, markdown = report(args.input)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "report.md").write_text(markdown)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("plausible_states", "source_data_sha256")}
        )
    )


if __name__ == "__main__":
    main()
