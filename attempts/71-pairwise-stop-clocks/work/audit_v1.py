"""Frozen finite rational oracles for A71; no neural imports or benchmarks."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
import sys
import time
import traceback
from collections import Counter
from fractions import Fraction as F
from math import comb, prod
from pathlib import Path

from clock_reference_v1 import avoidance, clock_cdf, coarse_law, count_law

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def save(path, data):
    path.write_text(json.dumps(data, indent=2, default=str) + "\n")


def solve(matrix, target):
    n = len(target)
    rows = [[F(x) for x in row] + [F(b)] for row, b in zip(matrix, target, strict=True)]
    for col in range(n):
        pivot = next((i for i in range(col, n) if rows[i][col]), None)
        if pivot is None:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [x / scale for x in rows[col]]
        for i in range(n):
            if i != col:
                scale = rows[i][col]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[col], strict=True)]
    return [row[-1] for row in rows]


def vertices(k, q):
    """Independent ALL-support LP vertex enumeration, not the candidate formula."""
    target = [F(1), k * q, k * (k - 1) * q * q]
    found = set()
    for size in range(1, 4):
        for support in itertools.combinations(range(k + 1), size):
            full = [[F(1) for _ in support], list(support), [n * (n - 1) for n in support]]
            weights = solve(full[:size], target[:size])
            if weights is None or any(w < 0 for w in weights):
                continue
            if any(
                sum(a * w for a, w in zip(row, weights, strict=True)) != b
                for row, b in zip(full, target, strict=True)
            ):
                continue
            found.add(tuple((n, w) for n, w in zip(support, weights, strict=True) if w))
    return [dict(row) for row in sorted(found)]


def full_cdf(k, q, thresholds, subsets):
    """Separate full-subset integration; no coefficient recursion."""
    result = F(0)
    for subset, mass in subsets:
        factors = []
        for index, threshold in enumerate(thresholds):
            if index in subset:
                factors.append(max(F(0), (threshold - (1 - q)) / q))
            else:
                factors.append(min(F(1), threshold / (1 - q)))
        result += mass * prod(factors)
    return result


def markov_words(row, family):
    """Recursive per-step native oracle, with NO root clock or count law."""
    result = Counter()

    def visit(prefix, mass):
        if len(prefix) == 0:
            stop = F(1 + (row + family) % 3, 4)
        elif len(prefix) == 1:
            letter_is_a = prefix == "A"
            if family % 2:
                letter_is_a = not letter_is_a
            stop = F(1 if letter_is_a else 3, 4)
        else:
            stop = F(1)
        result[prefix + "E"] += mass * stop
        if stop != 1:
            for letter in "AB":
                visit(prefix + letter, mass * (1 - stop) / 2)

    visit("", F(1))
    return result


def clock_word(row, family, private, root):
    """Integer cumulative clock implementation; independently expressed p's."""
    first_numerator = (row + family) % 3 + 1
    if root < 4 * first_numerator:
        return "E"
    bit0, bit1 = private // 2, private % 2
    second_numerator = 1 + 2 * (bit0 ^ (family % 2))
    cutoff = 16 - (4 - first_numerator) * (4 - second_numerator)
    letter0 = "AB"[bit0]
    if root < cutoff:
        return letter0 + "E"
    return letter0 + "AB"[bit1] + "E"


def run(output):
    start = time.perf_counter()
    producer = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = {}
    for name in (
        "clock_reference_v1.py",
        "audit_v1.py",
        "theory-v1.md",
        "protocol-v1.md",
        "primary-v1.json",
    ):
        path = WORK / name
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(["git", "show", producer + ":" + relative], cwd=ROOT)
        assert committed == path.read_bytes(), ("Source not frozen", name)
        hashes[relative] = hashlib.sha256(committed).hexdigest()
    save(
        output / "manifest.json",
        {
            "producer": producer,
            "sources": hashes,
            "python": sys.version,
            "platform": platform.platform(),
            "scope": "Exact constructed rational oracles; no model/training/timing study",
        },
    )
    counts = Counter()

    def record(kind, **fields):
        with (output / "records.jsonl").open("a") as stream:
            stream.write(json.dumps({"kind": kind, "status": "PASS", **fields}, default=str) + "\n")

    for k in range(3, 9):
        grid = sorted(
            {F(1, k - 1), F(2, k - 1), F(1, 4), F(1, 2), F(3, 4), F(2 * k - 3, 2 * k - 2)} - {F(1)}
        )
        for q in grid:
            counts["k_q_cells"] += 1
            subsets = list(coarse_law(k, q))
            assert all(mass >= 0 for _, mass in subsets)
            assert sum(mass for _, mass in subsets) == 1
            for width in (1, 2):
                for ids in itertools.combinations(range(k), width):
                    for flags in itertools.product((False, True), repeat=width):
                        observed = sum(
                            mass
                            for subset, mass in subsets
                            if all(
                                (i in subset) == flag for i, flag in zip(ids, flags, strict=True)
                            )
                        )
                        assert observed == prod(q if flag else 1 - q for flag in flags)
                        counts["coarse_marginal_events"] += 1
            feasible = vertices(k, q)
            assert feasible
            counts["feasible_count_vertices"] += len(feasible)
            for j in range(k + 1):
                oracle = max(
                    sum(w * F(comb(k - n, j), comb(k, j)) for n, w in vertex.items() if j <= k - n)
                    for vertex in feasible
                )
                direct = sum(mass for subset, mass in subsets if not subset.intersection(range(j)))
                assert avoidance(k, q, j) == direct == oracle
                assert direct >= (1 - q) ** j
                counts["all_vertex_avoidance_optima"] += 1
            points = [F(0), F(1, 8), (1 - q) / 2, 1 - q, (2 - q) / 2, F(7, 8), F(1)]
            for vector in range(32):
                u = [points[((vector + 1) * (i + 2) + i * i + vector // 7) % 7] for i in range(k)]
                declared = clock_cdf(k, q, u)
                assert declared == full_cdf(k, q, u, subsets)
                assert declared >= prod(u)
                counts["cdf_vectors"] += 1
                if declared > prod(u):
                    counts["cdf_strict_vectors"] += 1
            for width in (1, 2):
                for ids in itertools.combinations(range(k), width):
                    u = [F(1)] * k
                    for index, i in enumerate(ids):
                        u[i] = F(index + 1, 3)
                    assert clock_cdf(k, q, u) == prod(u)
                    counts["uniform_clock_pair_projections"] += 1
            record(
                "moment-and-cdf", k=k, q=q, subset_states=len(subsets), count_vertices=len(feasible)
            )

    # Complete finite adaptive trajectory laws: 4 * 131072 equiprobable scenarios.
    adaptive = []
    for family in range(4):
        lookup = [
            [[clock_word(i, family, private, root) for root in range(16)] for private in range(4)]
            for i in range(3)
        ]
        joint = Counter()
        for subset in ((), (0, 1), (0, 2), (1, 2)):
            ranges = [range(8, 16) if i in subset else range(8) for i in range(3)]
            for roots in itertools.product(*ranges):
                for private in itertools.product(range(4), repeat=3):
                    words = tuple(lookup[i][private[i]][roots[i]] for i in range(3))
                    joint[words] += 1
        total = sum(joint.values())
        assert total == 131072
        counts["adaptive_joint_scenarios"] += total
        native = [markov_words(i, family) for i in range(3)]
        for width in (1, 2):
            for ids in itertools.combinations(range(3), width):
                projected = Counter()
                for words, mass in joint.items():
                    projected[tuple(words[i] for i in ids)] += mass
                support = itertools.product(*(native[i] for i in ids))
                for words in support:
                    assert F(projected[words], total) == prod(
                        native[i][word] for i, word in zip(ids, words, strict=True)
                    )
                    counts["complete_word_single_pair_probabilities"] += 1
        cdfs = []
        for t in (1, 2, 3):
            observed = F(sum(n for words, n in joint.items() if max(map(len, words)) <= t), total)
            iid = prod(sum(mass for word, mass in law.items() if len(word) <= t) for law in native)
            assert observed >= iid
            cdfs.append({"t": t, "candidate": observed, "iid": iid})
            counts["adaptive_max_cdf_checks"] += 1
        difference = next(
            (
                words
                for words, mass in sorted(joint.items())
                if F(mass, total) != prod(native[i][word] for i, word in enumerate(words))
            ),
            None,
        )
        assert difference is not None
        adaptive.append({"family": family, "cdf": cdfs, "first_non_iid_word_triple": difference})
        record(
            "adaptive-words",
            family=family,
            joint_scenarios=total,
            distinct_word_triples=len(joint),
            cdf=cdfs,
            first_non_iid_word_triple=difference,
        )

    constructed = []
    for k in (3, 4, 8, 16, 32, 64):
        for r in (2, 3):
            if r >= k:
                continue
            q = F(r - 1, k - 1)
            law = count_law(k, q)
            assert set(law) == {0, r}
            assert sum(n * p for n, p in law.items()) == k * q
            assert sum(n * (n - 1) * p for n, p in law.items()) == k * (k - 1) * q * q
            for horizon in (2, 32, 1024):
                iid = 1 + (horizon - 1) * (1 - (1 - q) ** k)
                coordinated = 1 + (horizon - 1) * (1 - law[0])
                assert coordinated < iid
                row = {
                    "k": k,
                    "r": r,
                    "horizon": horizon,
                    "q": q,
                    "expected_iid": iid,
                    "expected_candidate": coordinated,
                    "ratio": coordinated / iid,
                    "ratio_float_diagnostic": float(coordinated / iid),
                }
                constructed.append(row)
                counts["constructed_two_point_cases"] += 1
                record("constructed-two-point-NOT-neural", **row)
        q = F(1, k - 1)
        survival = [q * F(i + 1, k + 1) for i in range(k)]
        union = sum(survival) - sum(a * b for a, b in itertools.combinations(survival, 2))
        assert 1 - clock_cdf(k, q, [1 - x for x in survival]) == union
        counts["heterogeneous_rare_tail_sharp_checks"] += 1

    candidate_cost = sum(mass * min(n, 2) for n, mass in count_law(3, F(1, 2)).items())
    iid_cost = sum(F(comb(3, n), 8) * min(n, 2) for n in range(4))
    assert candidate_cost == F(3, 2) > iid_cost == F(11, 8)
    variance_independent, variance_common = F(1, 12), F(1, 4)
    assert variance_common / variance_independent == 3
    record(
        "required-adverse-limits",
        candidate_concave_cost=candidate_cost,
        iid_concave_cost=iid_cost,
        common_clock_variance_ratio=3,
    )

    # Strong same-contract classic control, including its favorable cases.
    roots = [
        ((a + 0 * b) % 17, (a + b) % 17, (a + 2 * b) % 17) for a in range(17) for b in range(17)
    ]
    for i, j in itertools.combinations(range(3), 2):
        assert Counter((row[i], row[j]) for row in roots) == Counter(
            itertools.product(range(17), repeat=2)
        )
    witnesses = {}
    for ticks in itertools.product(range(18), repeat=3):
        observed = F(sum(all(root[i] < ticks[i] for i in range(3)) for root in roots), 289)
        u = [F(tick, 17) for tick in ticks]
        iid = prod(u)
        candidate = clock_cdf(3, F(1, 2), u)
        conditions = {
            "field_below_iid": observed < iid,
            "field_above_iid": observed > iid,
            "field_above_candidate": observed > candidate,
        }
        for name, condition in conditions.items():
            if condition and name not in witnesses:
                witnesses[name] = {
                    "threshold_ticks": ticks,
                    "field": observed,
                    "iid": iid,
                    "candidate": candidate,
                }
        counts["affine_control_grid_points"] += 1
    assert len(witnesses) == 3
    record("classic-field-control", witnesses=witnesses)
    result = {
        "status": "PASS",
        "producer": producer,
        "counts": dict(counts),
        "adaptive": adaptive,
        "constructed": constructed,
        "affine_control_witnesses": witnesses,
        "adverse_compact_cost": {"candidate": candidate_cost, "iid": iid_cost},
        "diagnostic_elapsed_seconds_NOT_timing_comparison": time.perf_counter() - start,
        "model_forwards": 0,
        "backwards": 0,
        "optimizer_updates": 0,
        "scope": (
            "Finite exact correctness/benefit/counterexample instances; "
            "no real latency, new count law, priority or fulfilled goal"
        ),
    }
    save(output / "summary.json", result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("status", "producer", "counts", "model_forwards", "scope")
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        run(args.output)
    except BaseException as error:
        save(
            args.output / "error.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
