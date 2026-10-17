"""Exact fresh-stop/adaptive Markov audit; no model or numerical sampler imports."""

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
from math import prod
from pathlib import Path

from clock_reference_v2 import clock_cdf, stop_law

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]
CUTS = (F(1, 4), F(1, 2), F(3, 4))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def independent_masks(probabilities):
    return {
        mask: prod(p if mask >> i & 1 else 1 - p for i, p in enumerate(probabilities))
        for mask in range(1 << len(probabilities))
    }


def intersections(law, k):
    return {
        subset: sum(mass for mask, mass in law.items() if mask & subset == subset)
        for subset in range(1 << k)
    }


def recursive_native(row, family):
    """Independent per-request Markov recursion, no coordinator or joint states."""
    result = Counter()

    def step(word, mass):
        if not word:
            probability = F((row + family) % 3 + 1, 4)
        elif len(word) == 1:
            probability = F(1 if (word == "A") != bool(family % 2) else 3, 4)
        else:
            probability = F(1)
        result[word + "E"] += mass * probability
        if probability < 1:
            step(word + "A", mass * (1 - probability) / 2)
            step(word + "B", mass * (1 - probability) / 2)

    step("", F(1))
    return result


def joint_hazard(row, family, prefix):
    if len(prefix) == 0:
        return F(1 + (row + family) % 3, 4)
    if len(prefix) == 1:
        return F(1 + 2 * ((prefix == "B") ^ bool(family % 2)), 4)
    return F(1)


def choose_cut(policy, probabilities, state, depth):
    if policy == "fixed" or len(probabilities) < 3:
        return F(1, 2)
    if policy == "history":
        position = (
            sum(int(4 * p) for p in probabilities)
            + sum(w.count("A") for w in state)
            + depth
            + len(probabilities)
        )
        return CUTS[position % 3]
    if policy == "head_greedy":
        return min(CUTS, key=lambda q: (-clock_cdf(len(probabilities), q, probabilities), q))
    raise ValueError(policy)


def run(output):
    start = time.perf_counter()
    producer = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = {}
    for name in ("audit_v2.py", "clock_reference_v2.py", "theory-v2-local.md", "protocol-v2.md"):
        path = WORK / name
        relative = str(path.relative_to(ROOT))
        original = subprocess.check_output(["git", "show", producer + ":" + relative], cwd=ROOT)
        assert original == path.read_bytes(), ("Unfrozen source", name)
        hashes[relative] = hashlib.sha256(original).hexdigest()
    save(
        output / "manifest.json",
        {
            "producer": producer,
            "sources": hashes,
            "python": sys.version,
            "platform": platform.platform(),
            "scope": (
                "Finite exact local-kernel and adaptive Markov oracle, no neural/latency study"
            ),
        },
    )
    counts = Counter()

    def record(kind, **fields):
        with (output / "records.jsonl").open("a") as stream:
            stream.write(json.dumps({"kind": kind, "status": "PASS", **fields}, default=str) + "\n")

    for k in (3, 4):
        for probabilities in itertools.product(CUTS, repeat=k):
            for q in CUTS:
                law = dict(stop_law(probabilities, q))
                assert all(mass >= 0 for mass in law.values()) and sum(law.values()) == 1
                all_stop = {}
                for subset in range(1 << k):
                    thresholds = [
                        p if subset >> i & 1 else F(1) for i, p in enumerate(probabilities)
                    ]
                    all_stop[subset] = clock_cdf(k, q, thresholds)
                    expected = prod(p for i, p in enumerate(probabilities) if subset >> i & 1)
                    assert all_stop[subset] >= expected
                    counts["stop_orthant_events"] += 1
                    if subset.bit_count() <= 2:
                        assert all_stop[subset] == expected
                        counts["stop_single_pair_intersections"] += 1
                for mask in range(1 << k):
                    zeros = ((1 << k) - 1) ^ mask
                    mobius = sum(
                        (-1) ** sub.bit_count() * all_stop[mask | sub]
                        for sub in range(1 << k)
                        if sub & zeros == sub
                    )
                    assert law.get(mask, 0) == mobius
                    counts["independent_mobius_mask_checks"] += 1
                counts["local_k_q_cells"] += 1
    for k in (0, 1, 2):
        for probabilities in itertools.product(CUTS, repeat=k):
            assert dict(stop_law(probabilities, F(1, 2))) == independent_masks(probabilities)
            counts["iid_fallback_cells"] += 1
    record("local-mask-oracles", counts=dict(counts))

    (output / "joint-laws").mkdir()
    adaptive = []
    for k, family, policy in itertools.product(
        (3, 4), range(4), ("fixed", "history", "head_greedy")
    ):
        distribution = {("",) * k: F(1)}
        native = [recursive_native(i, family) for i in range(k)]
        cdfs = []
        cuts_used = Counter()
        active_counts = Counter()
        for depth in range(3):
            following = Counter()
            for state, state_mass in distribution.items():
                live = [i for i, word in enumerate(state) if not word.endswith("E")]
                if not live:
                    following[state] += state_mass
                    continue
                probabilities = tuple(joint_hazard(i, family, state[i]) for i in live)
                q = choose_cut(policy, probabilities, state, depth)
                cuts_used[str(q)] += 1
                active_counts[len(live)] += 1
                for mask, stop_mass in stop_law(probabilities, q):
                    remaining = [j for j in range(len(live)) if not mask >> j & 1]
                    for letters in itertools.product("AB", repeat=len(remaining)):
                        next_state = list(state)
                        letter_map = dict(zip(remaining, letters, strict=True))
                        for j, i in enumerate(live):
                            next_state[i] += "E" if mask >> j & 1 else letter_map[j]
                        following[tuple(next_state)] += (
                            state_mass * stop_mass / (2 ** len(remaining))
                        )
                        counts["adaptive_transition_terms"] += 1
            distribution = dict(following)
            assert sum(distribution.values()) == 1
            actual = sum(
                mass
                for state, mass in distribution.items()
                if all(word.endswith("E") for word in state)
            )
            expected = prod(
                sum(mass for word, mass in row.items() if len(word) <= depth + 1) for row in native
            )
            assert actual >= expected, (k, family, policy, depth, actual, expected)
            cdfs.append({"t": depth + 1, "candidate": actual, "iid": expected})
            counts["adaptive_max_cdf_checks"] += 1
        assert all(all(word.endswith("E") for word in state) for state in distribution)
        for width in (1, 2):
            for ids in itertools.combinations(range(k), width):
                projected = Counter()
                for state, mass in distribution.items():
                    projected[tuple(state[i] for i in ids)] += mass
                for words in itertools.product(*(native[i] for i in ids)):
                    assert projected[words] == prod(
                        native[i][word] for i, word in zip(ids, words, strict=True)
                    )
                    counts["complete_word_single_pair_probabilities"] += 1
        first_difference = next(
            (
                state
                for state, mass in sorted(distribution.items())
                if mass != prod(native[i][word] for i, word in enumerate(state))
            ),
            None,
        )
        assert first_difference is not None
        stem = f"k{k}-family{family}-{policy}"
        save(
            output / "joint-laws" / (stem + ".json"),
            [[state, mass] for state, mass in sorted(distribution.items())],
        )
        info = {
            "k": k,
            "family": family,
            "policy": policy,
            "terminal_states": len(distribution),
            "cuts_used": dict(cuts_used),
            "active_counts": dict(active_counts),
            "cdf": cdfs,
            "first_non_iid_tuple": first_difference,
        }
        adaptive.append(info)
        counts["adaptive_policy_cases"] += 1
        record("adaptive-local", **info)

    # Independent finite characterization check for ALL 3-way pairwise laws' endpoints.
    failures_witnessed = []
    for probabilities in itertools.product(CUTS, repeat=3):
        base = independent_masks(probabilities)
        signs = {mask: 1 if (3 - mask.bit_count()) % 2 == 0 else -1 for mask in range(8)}
        lower = max(-mass for mask, mass in base.items() if signs[mask] == 1)
        upper = min(mass for mask, mass in base.items() if signs[mask] == -1)
        for delta in sorted({lower, F(0), upper}):
            law = {mask: mass + delta * signs[mask] for mask, mass in base.items()}
            assert min(law.values()) >= 0 and sum(law.values()) == 1
            inter = intersections(law, 3)
            native_inter = {
                subset: prod(p for i, p in enumerate(probabilities) if subset >> i & 1)
                for subset in range(8)
            }
            for subset in range(8):
                if subset.bit_count() <= 2:
                    assert inter[subset] == native_inter[subset]
            orthant = all(inter[s] >= native_inter[s] for s in range(8))
            witness = None
            for continuation in itertools.product((F(0), *CUTS, F(1)), repeat=3):
                actual = sum(
                    mass
                    * prod(
                        continuation[i] + (1 - continuation[i]) * ((mask >> i) & 1)
                        for i in range(3)
                    )
                    for mask, mass in law.items()
                )
                iid = prod(
                    r + (1 - r) * p for p, r in zip(probabilities, continuation, strict=True)
                )
                if orthant:
                    assert actual >= iid
                elif actual < iid and all(r in (0, 1) for r in continuation) and witness is None:
                    witness = {"R": continuation, "candidate": actual, "iid": iid}
                counts["continuation_comparisons"] += 1
            if not orthant:
                assert witness is not None
                failures_witnessed.append({"p": probabilities, "delta": delta, **witness})
            counts["characterization_kernels"] += 1
    record(
        "necessity-corners",
        kernels=counts["characterization_kernels"],
        nonorthant_witnesses=failures_witnessed,
    )

    probabilities = (F(1, 17), F(9, 17), F(2, 17))
    field = Counter()
    for a, b in itertools.product(range(17), repeat=2):
        mask = sum((1 << i) for i, tick in enumerate((1, 9, 2)) if (a + i * b) % 17 < tick)
        field[mask] += F(1, 289)
    inter = intersections(field, 3)
    for subset in range(8):
        if subset.bit_count() <= 2:
            assert inter[subset] == prod(p for i, p in enumerate(probabilities) if subset >> i & 1)
    assert inter[7] == F(1, 289) < prod(probabilities) == F(18, 4913)
    law = dict(stop_law((F(1, 2),) * 3, F(1, 2)))
    candidate_cost = sum(mass * min(3 - mask.bit_count(), 2) for mask, mass in law.items())
    iid_cost = sum(
        mass * min(3 - mask.bit_count(), 2)
        for mask, mass in independent_masks((F(1, 2),) * 3).items()
    )
    assert candidate_cost == F(3, 2) > iid_cost == F(11, 8)
    record(
        "required-adverse-controls",
        field_deadline=inter[7],
        iid_deadline=prod(probabilities),
        nonlinear_cost_candidate=candidate_cost,
        nonlinear_cost_iid=iid_cost,
        common_clock_bernoulli_variance_ratio=3,
    )
    result = {
        "status": "PASS",
        "producer": producer,
        "counts": dict(counts),
        "adaptive_cases": adaptive,
        "nonorthant_necessity_witnesses": failures_witnessed,
        "diagnostic_elapsed_seconds_NOT_timing": time.perf_counter() - start,
        "model_forwards": 0,
        "backwards": 0,
        "optimizer_updates": 0,
        "scope": (
            "Exact finite local/adaptive comparison only; "
            "no neural latency, priority or fulfilled goal"
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
