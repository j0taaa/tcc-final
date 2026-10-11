"""All preregistered numerical-interface gates, including losses/refusals."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from statistics import median


def gate(index, case, size, scope, protocol):
    own = [index[case, "triton", size, r] for r in range(protocol["repetitions"])]
    if any(row["status"] != "complete" for row in own):
        return dict(pass_gate=False, reason="candidate_not_complete", comparisons=[])
    comparisons = []
    for method in ("numpy", "torch"):
        for other_size in protocol["blocks"]:
            control = [index[case, method, other_size, r] for r in range(protocol["repetitions"])]
            if any(row["status"] != "complete" for row in control):
                return dict(
                    pass_gate=False,
                    reason="control_not_complete_no_credit",
                    comparisons=comparisons,
                )
            metrics = {}
            for metric in ("wall", "cpu"):
                a, b = [row[scope][metric] for row in own], [row[scope][metric] for row in control]
                ratio = median(x / y for x, y in zip(a, b, strict=True))
                favorable = all(x < y for x, y in zip(a, b, strict=True))
                metrics[metric] = dict(
                    paired_median_ratio=ratio,
                    all_repetitions_favorable=favorable,
                    pass_metric=ratio <= 0.8 and favorable,
                )
            comparisons.append(
                dict(
                    control=method,
                    block_size=other_size,
                    metrics=metrics,
                    pass_pair=all(m["pass_metric"] for m in metrics.values()),
                )
            )
    return dict(
        pass_gate=all(c["pass_pair"] for c in comparisons),
        reason="all_controls_checked",
        comparisons=comparisons,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    protocol = metadata["protocol"]
    with gzip.open(args.input / "rows.jsonl.gz", "rt") as file:
        rows = [json.loads(line) for line in file]
    index = {(r["case"], r["method"], r["block_size"], r["repeat"]): r for r in rows}
    cases = sorted({r["case"] for r in rows})
    expected = 18 * len(protocol["methods"]) * len(protocol["blocks"]) * protocol["repetitions"]
    if len(index) != len(rows) or len(rows) != expected or len(cases) != 18:
        raise ValueError("missing/duplicate development observations; no positive gate")
    results = []
    counts = Counter()
    for case in cases:
        for size in protocol["blocks"]:
            scopes = {
                scope: gate(index, case, size, scope, protocol)
                for scope in ("first_sample", "total_step", "query", "boundary")
            }
            primary = scopes["first_sample"]["pass_gate"] and scopes["total_step"]["pass_gate"]
            counts["primary_" + str(size)] += primary
            counts["warm_query_" + str(size)] += scopes["query"]["pass_gate"]
            counts["boundary_" + str(size)] += scopes["boundary"]["pass_gate"]
            results.append(dict(case=case, block_size=size, primary=primary, scopes=scopes))
    audit = dict(
        schema=1,
        records=len(rows),
        status_counts=Counter(r["status"] for r in rows),
        candidate_state_pairs=len(results),
        gate_counts=counts,
        cases=results,
        scope=(
            "Development numerical boundary with paired new neural step costs; "
            "not independent or whole-generation/publication confirmation"
        ),
    )
    (args.input / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(dict(records=len(rows), statuses=audit["status_counts"], gates=counts)))


if __name__ == "__main__":
    main()
