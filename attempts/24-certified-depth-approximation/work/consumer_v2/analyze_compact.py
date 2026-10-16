"""Separate matched compact timings, explicit budget capacity, and law checks."""

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads((args.input / "metadata.json").read_text())
    rows = [json.loads(s) for s in (args.input / "rows.jsonl").read_text().splitlines()]
    initial = [json.loads(s) for s in (args.development / "rows.jsonl").read_text().splitlines()]
    exact = {
        (r["case"], r["repeat"]): r["sample_valid_mass"]
        for r in initial
        if r["method"] == "exact_stack" and r["outside"] == "cursor" and r["status"] == "complete"
    }
    by = {(r["case"], r["repeat"], r["method"]): r for r in rows}
    if len(by) != len(rows):
        raise ValueError("duplicated compact operation")
    law_errors = []
    for r in rows:
        if r["status"] == "complete" and r["method"] != "handoff":
            if r["sample_valid_mass"] != exact[r["case"], r["repeat"]]:
                law_errors.append((r["case"], r["repeat"], r["method"]))
    controls = [m for m in meta["protocol"]["methods"] if m != "handoff"]
    expected = (
        len(meta["cases"]) * len(meta["protocol"]["methods"]) * meta["protocol"]["repetitions"]
    )
    complete = (
        len(rows) == expected
        and not law_errors
        and all(r["status"] in ("complete", "resource_refusal", "zero_valid_mass") for r in rows)
    )
    states = []
    for case in meta["cases"]:
        repetitions = range(meta["protocol"]["repetitions"])
        candidate = [by.get((case, r, "handoff")) for r in repetitions]
        passed, capacity = True, False
        comparisons = []
        if any(r is None or r["status"] != "complete" for r in candidate):
            states.append(dict(case=case, survives=False, reason="candidate incomplete"))
            continue
        for method in controls:
            others = [by.get((case, r, method)) for r in repetitions]
            if all(r is not None and r["status"] == "complete" for r in others):
                ratios = {
                    u: [
                        a["paid_total"][u] / b["paid_total"][u]
                        for a, b in zip(candidate, others, strict=True)
                    ]
                    for u in ("wall", "cpu")
                }
                benefit = all(median(v) <= 0.8 and all(x < 1 for x in v) for v in ratios.values())
                passed &= benefit
                comparisons.append(
                    dict(
                        method=method,
                        kind="timing",
                        strong=benefit,
                        median_ratios={u: median(v) for u, v in ratios.items()},
                    )
                )
            elif all(
                r is not None
                and r["status"] == "resource_refusal"
                and r.get("reason", "").startswith(("MemoryError:", "CompilationLimit:"))
                for r in others
            ):
                capacity = True
                comparisons.append(
                    dict(
                        method=method,
                        kind="explicit-budget capacity",
                        reasons=[r["reason"] for r in others],
                        strong=True,
                    )
                )
            else:
                passed = False
                comparisons.append(
                    dict(method=method, kind="incomplete; no favorable credit", strong=False)
                )
        states.append(
            dict(case=case, survives=passed, capacity_involved=capacity, comparisons=comparisons)
        )
    selected = json.loads((args.development / "decision.json").read_text())
    prior = {r["case"] for r in selected["outcomes"][selected["selected"]]["states"] if r["strong"]}
    survived = [r["case"] for r in states if r["survives"] and r["case"] in prior]
    result = dict(
        records=len(rows),
        planned=expected,
        campaign_complete=complete,
        statuses=dict(Counter(r["status"] for r in rows)),
        exact_mass_law_checks=sum(
            r["status"] == "complete" and r["method"] != "handoff" for r in rows
        ),
        exact_mass_errors=law_errors,
        states=states,
        surviving_prior_states=survived,
        surviving_scoped_benefit=bool(complete and len(survived) >= 3),
        scope="Known-head development; capacity at3GiB/120s is NOT general latency superiority",
    )
    (args.input / "decision.json").write_text(json.dumps(result, indent=2) + "\n")
    report = [
        "# Matched compact-control supplement",
        "",
        f"Records {len(rows)}/{expected}; complete {complete}.",
        f"Statuses: {result['statuses']}.",
        f"Exact mass checks: {result['exact_mass_law_checks']}; errors: {law_errors}.",
        f"Surviving prior states: {len(survived)}/15.",
        "Internal memory/work refusals are explicit-budget capacity, not latency measurements.",
        "No new forwards, independent corpus confirmation, publication or semantic claim.",
    ]
    (args.input / "decision.md").write_text("\n".join(report) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "states"}, indent=2))


if __name__ == "__main__":
    main()
