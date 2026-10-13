"""Frozen full-cost gate; partial campaigns can only support negative diagnosis."""

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    protocol = metadata["protocol"]
    rows = [json.loads(line) for line in (args.input / "rows.jsonl").read_text().splitlines()]
    cases = sorted(metadata["cases"])
    cases = [Path(c).stem for c in cases]
    repeats = range(protocol["repetitions"])
    configs = [(m, o) for m in protocol["methods"] for o in protocol["outside"]]
    index = {}
    for row in rows:
        key = row["case"], row["repeat"], row["method"], row["outside"], row["boundary"]
        if key in index:
            raise ValueError("duplicate operation record")
        index[key] = row
    expected = len(cases) * protocol["repetitions"] * (len(configs) + 2)
    complete = len(rows) == expected and not any(r["status"] == "error" for r in rows)
    controls = [(m, o) for m, o in configs if m not in protocol["candidate_family"]]
    candidates = [(m, o) for m, o in configs if m in protocol["candidate_family"]]
    outcomes = {}
    for method, outside in candidates:
        state_results = []
        for case in cases:
            candidate = [index.get((case, r, method, outside, "numpy")) for r in repeats]
            if any(row is None or row["status"] != "complete" for row in candidate):
                state_results.append(dict(case=case, strong=False, reason="candidate incomplete"))
                continue
            passed, comparisons = True, []
            for control, interface in controls:
                other = [index.get((case, r, control, interface, "numpy")) for r in repeats]
                if any(row is None or row["status"] != "complete" for row in other):
                    passed = False
                    comparisons.append(
                        dict(
                            method=control, outside=interface, status="incomplete; no speed credit"
                        )
                    )
                    continue
                ratios = {
                    unit: [
                        a["paid_total"][unit] / b["paid_total"][unit]
                        for a, b in zip(candidate, other, strict=True)
                    ]
                    for unit in ("wall", "cpu")
                }
                benefit = all(
                    median(values) <= 0.8 and all(x < 1 for x in values)
                    for values in ratios.values()
                )
                passed &= benefit
                comparisons.append(
                    dict(
                        method=control,
                        outside=interface,
                        strong=benefit,
                        median_ratios={u: median(v) for u, v in ratios.items()},
                    )
                )
            dense = [index.get((case, r, method, "dense", "python_dense")) for r in repeats]
            dense_ratios = None
            if all(row is not None and row["status"] == "complete" for row in dense):
                dense_ratios = {
                    u: median(
                        a["paid_total"][u] / b["paid_total"][u]
                        for a, b in zip(candidate, dense, strict=True)
                    )
                    for u in ("wall", "cpu")
                }
            state_results.append(
                dict(
                    case=case,
                    strong=passed,
                    comparisons=comparisons,
                    dense_ablation_median_ratios=dense_ratios,
                )
            )
        outcomes[method + "/" + outside] = dict(
            strong_states=sum(r["strong"] for r in state_results), states=state_results
        )
    # Frozen tie order: preserve handoff preference; no post hoc case selection.
    order = protocol["selection_tie_order"]
    selected = max(order, key=lambda name: outcomes[name]["strong_states"]) if complete else None
    gate = bool(complete and outcomes[selected]["strong_states"] >= 3)
    result = dict(
        records=len(rows),
        planned=expected,
        campaign_complete=complete,
        statuses=dict(Counter(r["status"] for r in rows)),
        practical_development_gate=gate,
        selected=selected,
        outcomes=outcomes,
        new_neural_forwards=0,
        scope=(
            "Known old heads; matched sparse CPU controls, "
            "not independent confirmation/native EPIC/publication"
        ),
    )
    (args.input / "decision.json").write_text(json.dumps(result, indent=2) + "\n")
    report = [
        "# A24 consumer V2 development",
        "",
        f"Records {len(rows)}/{expected}; complete {complete}.",
        f"Statuses: {result['statuses']}.",
        f"Development gate: {gate}; selected: {selected}.",
        "No new forwards or independent confirmation. Dense comparisons are ablations.",
        "",
    ]
    for name, outcome in outcomes.items():
        report.append(f"- {name}: {outcome['strong_states']}/{len(cases)} matched-control states.")
    (args.input / "decision.md").write_text("\n".join(report) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes"}, indent=2))


if __name__ == "__main__":
    main()
