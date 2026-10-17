"""Independent Fraction enumeration versus original native control and reference."""

import hashlib
import itertools
import json
import math
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

from native_replay import EXPECTED, NativeReplay
from reference import aggregate_auto

HERE = Path(__file__).resolve().parent


def entropy(packet):
    return max(-sum(float(p) * math.log(float(p)) for p in (x, 1 - x)) for x in packet)


def vector(packet):
    return tuple(p for x in packet for p in (x, 1 - x))


def average(rows):
    return tuple(sum(col, F()) / len(rows) for col in zip(*rows, strict=True))


def outer(row):
    return tuple(tuple(x * y for y in row) for x in row)


def moments(weighted):
    width = len(weighted[0][1])
    mean = tuple(sum((p * x[j] for p, x in weighted), F()) for j in range(width))
    cov = tuple(
        tuple(
            sum((p * x[j] * x[k] for p, x in weighted), F()) - mean[j] * mean[k]
            for k in range(width)
        )
        for j in range(width)
    )
    return mean, cov


def mse(weighted, target):
    return sum(
        (p * sum((u - v) ** 2 for u, v in zip(x, target, strict=True)) for p, x in weighted), F()
    )


def conditional_order(rows, high):
    if len(rows) == 1:
        return rows[0]
    possible_first = [
        rows[order[0]] for order in itertools.permutations(range(len(rows))) if high[order[0]]
    ]
    return average(possible_first)


def main(destination):
    protocol = json.loads((HERE / "protocol-v1.json").read_text())
    native = NativeReplay()
    cache = {}
    records = []
    tape_checks = permutation_checks = covariance_checks = 0
    vals = tuple(map(F, protocol["yes_values"]))
    for joint in (False, True):
        population = [(x,) for x in vals]
        if joint:
            population = [(vals[0] if i < 2 else vals[3], x) for i, x in enumerate(vals)]
        points = list(map(vector, population))
        high = [entropy(packet) > 0.1 for packet in population]
        assert high == [False, True, True, False]
        for law, raw_weights in protocol["laws"].items():
            weights = tuple(map(F, raw_weights))
            source = list(zip(weights, points, strict=True))
            target, source_cov = moments(source)
            a = sum((w for w, h in zip(weights, high, strict=True) if h), F())
            mu_h, sigma_h = (
                moments([(w / a, x) for w, x, h in zip(weights, points, high, strict=True) if h])
                if a
                else (target, outer((F(),) * len(target)))
            )
            mu_l = (
                average([target])
                if a == 1
                else moments(
                    [
                        (w / (1 - a), x)
                        for w, x, h in zip(weights, points, high, strict=True)
                        if not h
                    ]
                )[0]
            )
            for cap in protocol["caps"]:
                distributions = {name: [] for name in ("first", "native", "corrected", "fixed_cap")}
                cost = F()
                for tape in itertools.product(range(4), repeat=cap):
                    probability = math.prod(weights[i] for i in tape)
                    if not probability:
                        continue
                    n = cap if high[tape[0]] else 1
                    rows = [points[i] for i in tape[:n]]
                    flags = [high[i] for i in tape[:n]]
                    corrected = aggregate_auto(rows, flags, cap)
                    classical = conditional_order(rows, flags)
                    assert corrected == classical
                    permutation_checks += 1
                    key = joint, cap, tape
                    if key not in cache:
                        cache[key] = native.run([population[i] for i in tape], cap)
                    actual, actual_n, seeds = cache[key]
                    assert actual == average(rows) and actual_n == n
                    assert seeds == tuple(sorted([17] + [18 + 7919 * k for k in range(n - 1)]))
                    distributions["first"].append((probability, rows[0]))
                    distributions["native"].append((probability, actual))
                    distributions["corrected"].append((probability, corrected))
                    distributions["fixed_cap"].append(
                        (probability, average([points[i] for i in tape]))
                    )
                    cost += probability * n
                    tape_checks += 1
                assert cost == 1 + (cap - 1) * a
                native_mean, _ = moments(distributions["native"])
                corrected_mean, corrected_cov = moments(distributions["corrected"])
                fixed_mean, fixed_cov = moments(distributions["fixed_cap"])
                assert corrected_mean == fixed_mean == target
                factor = a - (1 - (1 - a) ** cap) / cap
                bias = tuple(
                    a * (1 - a) * F(cap - 1, cap) * (lo - hi)
                    for lo, hi in zip(mu_l, mu_h, strict=True)
                )
                assert tuple(b - t for b, t in zip(native_mean, target, strict=True)) == bias
                for j in range(len(target)):
                    for k in range(len(target)):
                        assert source_cov[j][k] - corrected_cov[j][k] == factor * sigma_h[j][k]
                        assert fixed_cov[j][k] == source_cov[j][k] / cap
                        covariance_checks += 1
                first_risk = mse(distributions["first"], target)
                corrected_risk = mse(distributions["corrected"], target)
                assert corrected_risk <= first_risk
                matched_risk = (1 - a + a / cap) * first_risk
                records.append(
                    {
                        "joint": joint,
                        "law": law,
                        "cap": cap,
                        "trigger_mass": str(a),
                        "expected_original_reads": str(cost),
                        "target": list(map(str, target)),
                        "native_mean": list(map(str, native_mean)),
                        "bias": list(map(str, bias)),
                        "first_mse": str(first_risk),
                        "native_mse": str(mse(distributions["native"], target)),
                        "corrected_mse": str(corrected_risk),
                        "fixed_cap_mse": str(mse(distributions["fixed_cap"], target)),
                        "oracle_matched_count_mse": str(matched_risk),
                        "split_pilot_mse": str(matched_risk),
                        "split_pilot_expected_reads": str(cost + 1),
                    }
                )

    counterexamples = []
    for mirror in (False, True):
        low = F(1023, 1024) if mirror else F(1, 1024)
        population = [(low,), (F(1, 2),)]
        target = ((low + F(1, 2)) / 2, 1 - (low + F(1, 2)) / 2)
        outcomes = []
        corrected_outcomes = []
        for tape in itertools.product(range(2), repeat=4):
            packets = [population[i] for i in tape]
            actual, n, _ = native.run(packets, 4)
            rows = [vector(z) for z in packets[:n]]
            corrected = aggregate_auto(rows, [entropy(z) > 0.1 for z in packets[:n]], 4)
            outcomes.append((F(1, 16), actual))
            corrected_outcomes.append((F(1, 16), corrected))
        bias = moments(outcomes)[0][0] - target[0]
        assert bias == (1 if mirror else -1) * F(1533, 16384)
        assert mse(outcomes, target) < mse(corrected_outcomes, target)
        counterexamples.append(
            {
                "mirrored": mirror,
                "native_yes_bias": str(bias),
                "native_mse": str(mse(outcomes, target)),
                "corrected_mse": str(mse(corrected_outcomes, target)),
            }
        )

    for cap in (1, 4):
        packet = [(F(1, 4),)] * cap
        _, n, _ = native.run(packet, cap, threshold=entropy(packet[0]))
        assert n == 1
    try:
        native.run([(F(1, 2),)] * 4, 4, fail_seed=18)
    except RuntimeError as error:
        assert str(error) == "Declared packet failure"
    else:
        raise AssertionError("Native read failure silently dropped")
    guards = 0
    for args in (
        ([], [], 4),
        ([(F(1),)], [True], 4),
        ([(F(1),)] * 2, [False, True], 2),
        ([(F(1),)], [False], 0),
        ([(F(1),), (F(1), F(0))], [True, True], 2),
    ):
        try:
            aggregate_auto(*args)
        except ValueError:
            guards += 1
        else:
            raise AssertionError("Invalid stopped input accepted")
    report = {
        "status": "PASS",
        "scope": (
            "Rational laws and original-body stub packets only; "
            "no server/model/tokenizer/head/forward/update/gold/latency benchmark."
        ),
        "producer_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "native_revision": protocol["native_revision"],
        "native_sha256": EXPECTED,
        "own_source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in (
                "reference.py",
                "native_replay.py",
                "audit.py",
                "protocol-v1.json",
                "theory-v1.md",
            )
        },
        "law_cap_question_cases": len(records),
        "weighted_tape_checks": tape_checks,
        "conditional_order_checks": permutation_checks,
        "exact_covariance_entries": covariance_checks,
        "unique_original_body_replays": native.runs,
        "stub_packet_calls_including_failure": native.packet_calls,
        "invalid_input_refusals": guards,
        "real_forwards": 0,
        "records": records,
        "counterexamples": counterexamples,
        "decision": (
            "Classical correction validated for declared iid packet target. "
            "Same-law classical control; sufficient own originality and real neural "
            "benefit remain open. No campaign triggered."
        ),
    }
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"records", "own_source_sha256"}}, indent=2
        )
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
