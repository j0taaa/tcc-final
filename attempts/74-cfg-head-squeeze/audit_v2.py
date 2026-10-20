"""Independent stdlib auditor of A74 V2 integer class masses and frozen gate."""

from __future__ import annotations

import argparse
import hashlib
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


def audit(directory, vocab=None):
    rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
    if not rows or rows[-1]["type"] != "complete":
        raise ValueError("incomplete/failed capture; cannot decide operational gate")
    assert not any(row["type"] in ("error", "resource", "interruption") for row in rows)
    environment = next(row for row in rows if row["type"] == "environment")
    resident = {
        int(line.split(",", 1)[0]) for line in environment["resident_processes"].splitlines()
    }
    final_processes = rows[-1]["final_processes"].splitlines()
    own = {int(line.split(",", 1)[0]) for line in final_processes if "python" in line} - resident
    assert len(own) == 1
    own_pid = own.pop()
    monitor = (directory / "pmon.txt").read_text().splitlines()
    valid_blocks = [
        row for row in rows if row["type"] == "measurement_block" and row["timing_valid"]
    ]
    assert len(valid_blocks) == 66
    assert len({(row["case"], row["rep"]) for row in valid_blocks}) == 66
    for block in valid_blocks:
        start, end = block["monitor_start_line"], block["monitor_end_line"]
        assert 0 <= start < end <= len(monitor)
        assert not block["foreign_activity"]
        for line in monitor[start:end]:
            columns = line.split()
            if len(columns) > 4 and columns[0].isdigit() and "C" in columns[2]:
                if int(columns[1]) != own_pid and columns[3].isdigit():
                    assert int(columns[3]) == 0
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
                "expected_reference_rows_uncapped_exceed_dense": q > 50256 * p,
                "expected_matching_gemm_work_factor_lower_bound": float((2 + 4 * fallback) / 4)
                if row["proxy"] == "int8"
                else float(fallback) + int(row["proxy"][3:]) * (768 + 50256) / (768 * 50256),
                "matching_gemm_work_control": "dense:split"
                if row["proxy"] == "int8"
                else "dense:double",
            }
        )
    assert len(probabilities) == 24
    all_draws = [row for row in rows if row["type"] == "draw"]
    draws = [row for row in all_draws if row.get("timing_valid", True)]
    assert len(draws) == 660
    byte_decoder = None
    if vocab is not None:
        pieces = {value: key for key, value in json.loads(vocab.read_text()).items()}
        direct = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
        extra = [value for value in range(256) if value not in direct]
        alphabet = {chr(value): value for value in direct}
        alphabet.update({chr(256 + i): value for i, value in enumerate(extra)})
        byte_decoder = {v: bytes(alphabet[c] for c in pieces[v]) for v in range(50256)}
    for row in draws:
        word = row["ids"]
        assert len(word) == row["n"] and all(type(v) is int and 0 <= v < 50256 for v in word)
        assert len({(v % 4) // 2 for v in word}) == 1
        assert sum(v % 2 == 0 for v in word) * 2 == len(word)
        assert 0 <= row["proposals"] <= 4
        assert row["reference_rows"] <= row["n"] * row["proposals"]
        assert row["rng_bits"] >= 0 and row["peak_chart_integer_bits"] > 0
        if byte_decoder is not None:
            raw = b"".join(byte_decoder[v] for v in word)
            assert hashlib.sha256(raw).hexdigest() == row["bytes_sha256"]
            assert len(raw) == row["output_byte_count"]
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
            proxy = method.split(":")[0]
            probability = next(
                r for r in probabilities if r["case"] == case and r["proxy"] == proxy
            )
            minimum_attempt = min(
                (r["stages"]["rng_proposals"] + r["stages"]["reference_queries"]) / r["proposals"]
                for r in candidate.values()
            )
            # Post-hoc optimistic cost diagnostics, not a new gate or an uncapped run.
            uncapped_log = math.log(minimum_attempt) - probability["log_acceptance"]
            free_preparation = median(
                r["seconds"]
                - sum(
                    r["stages"][k] for k in ("proxy_bounds_transfer", "inside_cdf", "lower_inside")
                )
                for r in candidate.values()
            )
            free_projection = median(
                r["seconds"] - r["stages"]["proxy_bounds_transfer"] for r in candidate.values()
            )
            warm_total = median(
                r["seconds"] + r["hidden_quantize_seconds"] + r["backbone_seconds"]
                for r in candidate.values()
            )
            base_warm_total = median(
                r["seconds"] + r["hidden_quantize_seconds"] + r["backbone_seconds"]
                for r in by_method[fastest].values()
            )
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
                    "full_cost_timing_valid": all(
                        r["setup_timing_valid"] and r["backbone_timing_valid"]
                        for r in candidate.values()
                    ),
                    "posthoc_free_proxy_and_proposal_prep_seconds": free_preparation,
                    "posthoc_free_prep_speedup": base_raw / free_preparation,
                    "posthoc_free_projection_speedup": base_raw / free_projection,
                    "speedup_warm_total_setup_free": base_warm_total / warm_total,
                    "posthoc_min_observed_attempt_seconds": minimum_attempt,
                    "posthoc_uncapped_estimated_log_seconds_free_setup": uncapped_log,
                    "posthoc_constant_attempt_cost_model_prefers_direct": uncapped_log
                    >= math.log(base_raw),
                    **full,
                }
            )
    return {
        "status": "PASS",
        "states": 6,
        "draws": 660,
        "invalid_resource_draws_preserved": len(all_draws) - len(draws),
        "valid_blocks_independently_checked": 66,
        "byte_outputs_checked": len(draws) if byte_decoder is not None else None,
        "vocab_sha256": hashlib.sha256(vocab.read_bytes()).hexdigest()
        if vocab is not None
        else None,
        "cold_setup_timings_are_diagnostic": not all(row["setup_timing_valid"] for row in draws),
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
    parser.add_argument("--vocab", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, args.vocab), indent=2))
