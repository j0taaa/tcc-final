"""Read-only independent audit of frozen A72 V2 data, without new timings."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def inputs(capture: list[dict]) -> dict[str, list[list[int]]]:
    result = {}
    for n in (33, 129, 513, 2049):
        for radius in (0.25, 0.75, 0.99):
            for seed in (720201, 720202, 720203):
                rng = random.Random(seed)
                rows = []
                for _ in range(n):
                    a, c, marker = [rng.randrange(1, 17) for _ in range(3)]
                    x = rng.randint(-int(256 * radius), int(256 * radius))
                    y = rng.randint(-int(256 * radius), int(256 * radius))
                    rows.append(
                        [a * (256 + x), c * (256 + y), a * (256 - x), c * (256 - y), marker * 512]
                    )
                result[f"synthetic-n{n}-r{radius}-s{seed}"] = rows
    for frame in capture:
        if frame.get("type") != "frame":
            continue
        rows = []
        for row in frame["probabilities_hex"]:
            probabilities = [Fraction.from_float(float.fromhex(v)) for v in row]
            denominator = math.lcm(*(v.denominator for v in probabilities))
            rows.append([v.numerator * (denominator // v.denominator) for v in probabilities])
        result[frame["case"]] = rows
    return result


def syntax_context_masses(rows: list[list[int]]) -> list[int]:
    """Peel matching delimiters from both ends of each grammar block."""
    result = []
    for separator in range(0, len(rows), 2):
        value = rows[separator][4]
        for start, stop in ((0, separator), (separator + 1, len(rows))):
            while start < stop:
                stop -= 1
                value *= sum(
                    rows[start][opening] * rows[stop][closing]
                    for opening, closing in ((0, 1), (2, 3))
                )
                start += 1
        result.append(value)
    return result


def valid_witness(word: str, length: int) -> bool:
    if len(word) != length or word.count("#") != 1:
        return False
    for block in word.split("#"):
        stack = []
        closing_started = False
        for c in block:
            if c in "([" and not closing_started:
                stack.append(")" if c == "(" else "]")
            elif c in ")]" and stack:
                closing_started = True
                if stack.pop() != c:
                    return False
            else:
                return False
        if stack:
            return False
    return True


def main() -> None:
    capture_path, result_path = HERE / "capture-v2.jsonl", HERE / "results-v2.jsonl"
    capture, saved = load(capture_path), load(result_path)
    assert saved[0]["capture_sha256"] == hashlib.sha256(capture_path.read_bytes()).hexdigest()
    assert capture[-1] == {"type": "exit", "returncode": 0}
    frames = [r for r in capture if r.get("type") == "frame"]
    assert {r["case"] for r in frames} == set(capture[0]["expected_cases"])
    assert capture_path.stat().st_size <= 2 * 2**20
    rows = [r for r in saved if r.get("type") == "result"]
    cases = inputs(capture)
    assert len(rows) == len(cases) == 42
    assert {r["case"] for r in rows} == set(cases)
    audited = witnesses = refused_verified = 0
    for record in rows:
        weights = cases[record["case"]]
        p = syntax_context_masses(weights)
        assert max(v.bit_length() for v in p) == record["max_context_mass_bits"]
        convolution = record["convolution"]
        if convolution["status"] == "refused_degree":
            x = max(abs(Fraction(row[0] - row[2], row[0] + row[2])) for row in weights)
            y = max(abs(Fraction(row[1] - row[3], row[1] + row[3])) for row in weights)
            rho = x * y
            # ln(1.01)/4 < 1/400, so this proves that K=64 cannot suffice.
            assert ((len(weights) - 1) // 2) * rho**65 / (65 * (1 - rho)) > Fraction(1, 400)
            refused_verified += 1
        for name in ("contextual_circuit", "orientation_only", "convolution"):
            method = record[name]
            if "marker_weights_hex" not in method:
                continue
            q = [int(v, 16) for v in method["marker_weights_hex"]]
            distance = Fraction(
                sum(abs(a * sum(q) - b * sum(p)) for a, b in zip(p, q, strict=True)),
                2 * sum(p) * sum(q),
            )
            assert distance == Fraction(
                int(method["tv_exact_numerator_hex"], 16),
                int(method["tv_exact_denominator_hex"], 16),
            )
            assert method["tv_pass"] == (distance <= Fraction(1, 100))
            audited += 1
            if "sample_word" in method:
                word = method["sample_word"]
                assert valid_witness(word, record["slots"])
                assert hashlib.sha256(word.encode()).hexdigest() == method["sample_sha256"]
                witnesses += 1
        if "sample_word" in record["integer_conditioning"]:
            assert valid_witness(record["integer_conditioning"]["sample_word"], record["slots"])
            witnesses += 1
    neural = [r for r in rows if r["kind"] == "neural"]
    proposed = [r for r in rows if r["convolution"]["status"] == "proposed"]
    low_bias_large = [r for r in proposed if "n2049-r0.25" in r["case"]]
    gate_passes = [
        r
        for r in neural
        if r["convolution"].get("tv_pass", False)
        and r["convolution"]["certified_total_median_ms"]
        < min(
            r[name]["certified_total_median_ms"]
            for name in ("integer_conditioning", "contextual_circuit", "orientation_only")
            if name == "integer_conditioning" or r[name]["tv_pass"]
        )
    ]
    model = next(r for r in capture if r.get("type") == "model")
    print(
        json.dumps(
            {
                "cases": len(rows),
                "exact_joint_tv_audits": audited,
                "independently_verified_degree_refusals": refused_verified,
                "neural_valid_witnesses": witnesses,
                "outcomes": dict(Counter(r["convolution"]["status"] for r in rows)),
                "neural_outcomes": dict(Counter(r["convolution"]["status"] for r in neural)),
                "neural_gate_passes": len(gate_passes),
                "neural_gate_total": len(neural),
                "proposed_tv_max": max(r["convolution"]["tv_float"] for r in proposed),
                "proposal_wins_over_full_vectorized": sum(
                    r["convolution"]["median_ms"] < r["contextual_circuit"]["median_ms"]
                    for r in proposed
                ),
                "certified_wins_over_integer_control": sum(
                    r["convolution"]["certified_total_median_ms"]
                    < r["integer_conditioning"]["certified_total_median_ms"]
                    for r in proposed
                ),
                "n2049_r025_median_ms": {
                    name: statistics.median(r[name]["median_ms"] for r in low_bias_large)
                    for name in ("integer_conditioning", "contextual_circuit", "convolution")
                },
                "n2049_r025_certified_convolution_median_ms": statistics.median(
                    r["convolution"]["certified_total_median_ms"] for r in low_bias_large
                ),
                "model_load_seconds": model["load_seconds"],
                "model_forward_total_seconds": sum(r["forward_seconds"] for r in frames),
                "model_normalize_transfer_total_seconds": sum(
                    r["transfer_normalization_seconds"] for r in frames
                ),
                "model_peak_allocated_bytes": max(r["gpu_peak_allocated_bytes"] for r in frames),
                "original_token_ids": model["token_ids"],
                "neural_rho_range": [
                    min(r["convolution"]["rho"] for r in neural),
                    max(r["convolution"]["rho"] for r in neural),
                ],
                "selected_support_mass_range": [
                    min(r["selected_support_mass_min"] for r in frames),
                    max(r["selected_support_mass_max"] for r in frames),
                ],
                "files_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (capture_path, result_path)
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
