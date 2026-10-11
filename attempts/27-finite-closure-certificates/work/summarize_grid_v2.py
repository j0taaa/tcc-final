"""Derive the complete feasibility audit; no selection or timing claims."""

import gzip
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

WORK = Path(__file__).resolve().parent


def main():
    evidence = WORK / "evidence" / "development-feasibility-v2"
    path = evidence / "rows.jsonl.gz"
    rows = [json.loads(s) for s in gzip.open(path, "rt")]
    protocol = json.loads((WORK / "grid-protocol-v2.json").read_text())
    previous = Path(
        "attempts/24-certified-depth-approximation/work/evidence/"
        "handoff-feasibility-v1/rows.jsonl.gz"
    )
    old = [json.loads(s) for s in gzip.open(previous, "rt")]
    lookup = {(r["case"], r["depth"]): r for r in old if r["status"] == "complete"}
    tolerance = Fraction(protocol["tolerance"])
    old_depths = {}
    for r in lookup.values():
        if Fraction(r["certificates"]["handoff"]["delta"]) <= tolerance:
            old_depths[r["case"]] = min(old_depths.get(r["case"], 999), r["depth"])
    keys = {(r["case"], r["depth"], r["method"], str(r["parameter"])) for r in rows}
    expected = (
        len(protocol["cases"])
        * len(protocol["depths"])
        * (len(protocol["moduli"]) + len(protocol["potential_exponents"]))
    )
    assert len(rows) == len(keys) == expected == 1080
    results = []
    for method, parameters in (
        ("residue", protocol["moduli"]),
        ("potential", protocol["potential_exponents"]),
    ):
        for parameter in parameters:
            subset = [r for r in rows if r["method"] == method and r["parameter"] == parameter]
            depth, comparison = {}, Counter()
            for r in subset:
                if r["certifies"]:
                    depth[r["case"]] = min(depth.get(r["case"], 999), r["depth"])
                if r["status"] != "complete" or (r["case"], r["depth"]) not in lookup:
                    continue
                other = lookup[r["case"], r["depth"]]
                assert Fraction(r["lower"]) == Fraction(other["lower_mass"])
                upper, prior = Fraction(r["upper"]), Fraction(other["bounds"]["handoff"]["mass"])
                comparison[
                    "tighter" if upper < prior else "equal" if upper == prior else "looser"
                ] += 1
            depths = Counter()
            for case, value in depth.items():
                prior = old_depths.get(case)
                depths[
                    "old_missing"
                    if prior is None
                    else "better"
                    if value < prior
                    else "equal"
                    if value == prior
                    else "worse"
                ] += 1
            results.append(
                dict(
                    method=method,
                    parameter=parameter,
                    statuses=dict(Counter(r["status"] for r in subset)),
                    certifying_cases=len(depth),
                    minimum_depth_by_case=depth,
                    active_frontier_certificates=sum(
                        r["certifies"] and r.get("frontier_states", 0) > 0 for r in subset
                    ),
                    handoff_bound_comparison=dict(comparison),
                    handoff_depth_comparison=dict(depths),
                )
            )
    checks = [r for r in rows if r.get("archived_full_mass") is not None]
    assert all(
        0 <= Fraction(r["archived_full_mass"]) - Fraction(r["lower"]) <= Fraction(r["upper"])
        for r in checks
    )
    summary = dict(
        rows_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        old_rows_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),
        records=len(rows),
        original_cases=len(protocol["cases"]),
        statuses=dict(Counter(r["status"] for r in rows)),
        exact_mass_checks=len(checks),
        old_handoff_minimum_depth_by_case=old_depths,
        variants=results,
        interpretation=(
            "Reused development feasibility only; no timing, "
            "independent confirmation or priority claim"
        ),
    )
    (evidence / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
