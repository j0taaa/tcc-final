"""AFTER-data scalar mixture/L1/count audit, no new head query or draw."""

import argparse
import json
import math
import random
from pathlib import Path


def run(capture, auxiliary, analysis, original):
    states = [json.loads(s) for s in (capture / "records.jsonl").read_text().splitlines()]
    aux = [json.loads(s) for s in (auxiliary / "records.jsonl").read_text().splitlines()]
    rows = [json.loads(s) for s in (original / "rows.jsonl").read_text().splitlines()]
    inputs = [(r, t) for r in rows for t in r["transitions"]]
    table = json.loads((analysis / "ALL25-direction-table.json").read_text())
    summary = json.loads((analysis / "summary.json").read_text())
    assert len(states) == len(inputs) == 70 and len(aux) == 8960 and len(table) == 25
    groups = {}
    for r in aux:
        key = r["case"], r["replica"], r["step"], r["method"]
        group = groups.setdefault(key, {})
        assert r["draw_index"] not in group
        group[r["draw_index"]] = r
    maximum, checks = 0.0, 0

    def compare(a, b):
        nonlocal maximum, checks
        assert math.isfinite(a) and math.isfinite(b)
        maximum = max(maximum, abs(a - b))
        checks += 1
        assert abs(a - b) < 1e-9, (a, b)

    for state, (row, t) in zip(states, inputs, strict=True):
        assert state["status"] == "PASS" and all(
            state[k] == source[k]
            for k, source in (("case", row), ("replica", row), ("step", t), ("head", t))
        )
        assert state["remaining_requests_after_action"] == len(row["transitions"]) - t["step"] - 1
        v = state["readout"]
        lengths = v["lengths"]
        anchors = v["anchors"]
        assert len({r["length"] for r in lengths}) == len(lengths)
        assert set(v["structural_zero_lengths"]).isdisjoint(r["length"] for r in lengths)
        assert set(v["structural_zero_lengths"]) | {r["length"] for r in lengths} == set(
            range(1, t["prefix_extent"] + 1)
        )
        compare(sum(r["probability_given_action"] for r in lengths), 1.0)
        compare(sum(r["probability_given_action"] for r in anchors), 1.0)
        fixed = dict(t["fixed_before"])
        action = dict(t["action"])
        assert {r["anchor"] for r in anchors} == set(action)
        stops = [i + 1 for i, token in (*fixed.items(), *action.items()) if token == 126081]
        if stops:
            assert [r["length"] for r in lengths] == [min(stops)]
        for j in range(9):
            for group in (lengths, anchors):
                compare(
                    sum(r["probability_given_action"] * r["actor"][j] for r in group),
                    v["collapsed_actor"][j],
                )
    rng = random.Random(54001)
    directions = [[float(i == j) for j in range(9)] for i in range(9)] + [
        [rng.choice((-1, 1)) / 3 for _ in range(9)] for _ in range(16)
    ]
    controls = (
        "full_triple",
        "anchor_integrated",
        "class_integrated",
        "proper_length",
        "known_anchor",
    )
    negative_empirical_gaps = 0
    for entry, d in zip(table, directions, strict=True):
        assert entry["direction"] == d
        results = {
            mode: {m: 0.0 for m in (*controls, "observed")} for mode in ("iid", "prefix_stratified")
        }
        question = {
            mode: [dict.fromkeys((*controls, "observed"), 0.0) for _ in range(8)]
            for mode in results
        }
        for state in states:
            v = state["readout"]
            key = state["case"], state["replica"], state["step"]
            weight = state["remaining_requests_after_action"] / 16
            observed = abs(sum(x * y for x, y in zip(v["collapsed_actor"], d, strict=True)))
            length = sum(
                r["probability_given_action"]
                * abs(sum(x * y for x, y in zip(r["actor"], d, strict=True)))
                for r in v["lengths"]
            )
            anchor = sum(
                r["probability_given_action"]
                * abs(sum(x * y for x, y in zip(r["actor"], d, strict=True)))
                for r in v["anchors"]
            )
            assert min(length, anchor) >= observed - 1e-7
            for mode in results:
                current = {"observed": observed, "proper_length": length, "known_anchor": anchor}
                group = groups[*key, mode]
                assert set(group) == set(range(64))
                for m in controls[:3]:
                    current[m] = (
                        sum(
                            abs(sum(r["actor_scores"][m][j] * d[j] for j in range(9)))
                            for r in group.values()
                        )
                        / 64
                    )
                    negative_empirical_gaps += current[m] < observed - 1e-12
                for m, val in current.items():
                    results[mode][m] += weight * val
                    question[mode][state["case"]][m] += weight * val
        for mode in results:
            for m, val in results[mode].items():
                compare(val, entry["totals"][mode][m])
                for q in range(8):
                    compare(question[mode][q][m], entry["by_question"][mode][q][m])
        candidate = results["iid"]["observed"]
        denominators = [results["iid"][m] for m in controls]
        if candidate > 0 and min(denominators) > 0:
            ratio = candidate / min(denominators)
            compare(ratio, entry["primary_ratio_to_strongest_control"])
            assert ratio > 0.8 and entry["status"] == "NO_LOCAL_20PCT_OPPORTUNITY"
        else:
            assert entry["status"] == "INCONCLUSIVE_NONPOSITIVE"
    assert not summary["promising_direction_indices"] and not summary["neural_campaign_triggered"]
    result = {
        "status": "PASS",
        "scope": "AFTER-data arithmetic/source-state audit, not independent evaluation",
        "states": 70,
        "directions": 25,
        "old_auxiliary_vectors": 8960,
        "scalar_checks": checks,
        "maximum_absolute_difference": maximum,
        "negative_MC_conditional_Jensen_gaps_retained": negative_empirical_gaps,
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
    }
    (analysis / "post-analysis-independent-audit.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "auxiliary", "analysis", "original"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.auxiliary, a.analysis, a.original)
