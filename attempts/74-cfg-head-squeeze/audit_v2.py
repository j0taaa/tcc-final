"""Independent stdlib auditor of A74 V2 integer class masses and frozen gate."""

from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path
from statistics import median


def mass(rows):
    """Forward polynomial coefficients, independent from the suffix sampler DP."""
    total = 0
    for mode in (0, 1):
        coefficients = [1]
        for row in rows:
            a, b = (int(v) for v in row[2 * mode : 2 * mode + 2])
            next_coefficients = [0] * (len(coefficients) + 1)
            for k, value in enumerate(coefficients):
                next_coefficients[k] += b * value
                next_coefficients[k + 1] += a * value
            coefficients = next_coefficients
        total += coefficients[len(rows) // 2]
    return total


def audit(directory):
    rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
    if not rows or rows[-1]["type"] != "complete":
        raise ValueError("incomplete/failed capture; cannot decide operational gate")
    assert not any(row["type"] in ("error", "resource", "interruption") for row in rows)
    targets = {row["case"]: row for row in rows if row["type"] == "target_mass"}
    states = {row["case"]: row for row in rows if row["type"] == "state"}
    assert set(targets) == set(states) == set(range(6))
    for row in targets.values():
        assert mass(row["class_masses"]) == int(row["Zw"])
    probabilities = []
    for row in rows:
        if row["type"] != "mass":
            continue
        zw, zl, zu = (int(row[k]) for k in ("Zw", "ZL", "ZU"))
        assert zw == int(targets[row["case"]]["Zw"])
        assert mass(row["lower_class_masses"]) == zl
        assert mass(row["upper_class_masses"]) == zu
        assert 0 < zl <= zw <= zu
        p, q = Fraction(zw, zu), 1 - Fraction(zl, zu)
        fallback = (1 - p) ** 4
        attempts = sum((1 - p) ** j for j in range(4))
        probabilities.append(
            {
                "case": row["case"],
                "n": row["n"],
                "proxy": row["proxy"],
                "log_acceptance": math.log(zw) - math.log(zu),
                "acceptance_display": float(p),
                "fallback_probability_display": float(fallback),
                "expected_attempts_cap4": float(attempts),
                "expected_reference_rows_cap4": float(q * attempts) * row["n"],
            }
        )
    assert len(probabilities) == 24
    draws = [row for row in rows if row["type"] == "draw"]
    assert len(draws) == 660
    for row in draws:
        word = row["ids"]
        assert len(word) == row["n"] and all(type(v) is int and 0 <= v < 50256 for v in word)
        assert len({(v % 4) // 2 for v in word}) == 1
        assert sum(v % 2 == 0 for v in word) * 2 == len(word)
        assert 0 <= row["proposals"] <= 4
        assert row["reference_rows"] <= row["n"] * row["proposals"]
        assert row["rng_bits"] >= 0 and row["peak_chart_integer_bits"] > 0
    comparisons = []
    for case in range(6):
        local = [row for row in draws if row["case"] == case]
        by_method = {}
        for row in local:
            by_method.setdefault(row["method"], {})[row["rep"]] = row
        assert len(by_method) == 10
        assert all(set(reps) == set(range(11)) for reps in by_method.values())
        baselines = ("dense:split", "dense:double")
        fastest = min(
            baselines, key=lambda b: median(row["seconds"] for row in by_method[b].values())
        )
        for method, candidate in by_method.items():
            if method.startswith("dense:"):
                continue
            paired_all = all(
                candidate[rep]["seconds"] < by_method[base][rep]["seconds"]
                for base in baselines
                for rep in range(11)
            )
            raw = median(
                row["seconds"] + row["hidden_quantize_seconds"] for row in candidate.values()
            )
            base_raw = median(
                row["seconds"] + row["hidden_quantize_seconds"]
                for row in by_method[fastest].values()
            )
            full = {}
            for amort in (1, 32):
                candidate_total = median(
                    row["seconds"]
                    + row["hidden_quantize_seconds"]
                    + row["backbone_seconds"]
                    + (row["common_setup_seconds"] + row["proxy_setup_seconds"]) / amort
                    for row in candidate.values()
                )
                base_total = median(
                    row["seconds"]
                    + row["hidden_quantize_seconds"]
                    + row["backbone_seconds"]
                    + row["common_setup_seconds"] / amort
                    for row in by_method[fastest].values()
                )
                full[f"speedup_total_T{amort}"] = base_total / candidate_total
            passed = paired_all and base_raw / raw >= 1.10 and full["speedup_total_T32"] >= 1.10
            comparisons.append(
                {
                    "case": case,
                    "n": states[case]["n"],
                    "method": method,
                    "best_dense": fastest,
                    "head_sampler_speedup": base_raw / raw,
                    "paired_wins_against_both": sum(
                        all(
                            candidate[rep]["seconds"] < by_method[b][rep]["seconds"]
                            for b in baselines
                        )
                        for rep in range(11)
                    ),
                    "candidate_median_seconds": raw,
                    "baseline_median_seconds": base_raw,
                    "observed_fallbacks": sum(row["fallback"] for row in candidate.values()),
                    "passed_frozen_gate": passed,
                    **full,
                }
            )
    return {
        "status": "PASS",
        "states": 6,
        "draws": 660,
        "class_mass_certificates": 54,
        "gate_passes": sum(row["passed_frozen_gate"] for row in comparisons),
        "decision_scope": (
            "A74 V2, four fixed proxies, declared integer reference, constructed full-ID CFG"
        ),
        "probabilities": probabilities,
        "comparisons": comparisons,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory), indent=2))
