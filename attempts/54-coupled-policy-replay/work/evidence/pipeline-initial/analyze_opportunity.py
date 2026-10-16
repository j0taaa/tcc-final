"""Frozen local first-order LOSS coefficients, not finite coupling performance."""

import argparse
import json
import random
from pathlib import Path

import numpy as np

CONTROLS = ("full_triple", "anchor_integrated", "class_integrated", "proper_length", "known_anchor")


def directions():
    values = np.eye(9).tolist()
    rng = random.Random(54001)
    values.extend([[rng.choice((-1, 1)) / 3 for _ in range(9)] for _ in range(16)])
    return values


def run(capture, auxiliary, output):
    output.mkdir(parents=True, exist_ok=False)
    summary = json.loads((capture / "summary.json").read_text())
    if summary["status"] != "PASS":
        (output / "summary.json").write_text(
            json.dumps({"status": "NO_CREDIT_INCOMPLETE", "capture": summary}, indent=2) + "\n"
        )
        return
    states = [json.loads(s) for s in (capture / "records.jsonl").read_text().splitlines()]
    aux_summary = json.loads((auxiliary / "summary.json").read_text())
    assert aux_summary["status"] == "PASS"
    records = [json.loads(s) for s in (auxiliary / "records.jsonl").read_text().splitlines()]
    assert len(records) == 8960
    groups = {}
    for r in records:
        assert r["status"] == "PASS"
        key = (r["case"], r["replica"], r["step"], r["method"])
        groups.setdefault(key, {})[r["draw_index"]] = r
    table = []
    with (output / "ALL25-directions-ALL70-states.jsonl").open("x") as stream:
        for index, d in enumerate(directions()):
            d = np.asarray(d)
            totals = {
                mode: {m: 0.0 for m in (*CONTROLS, "observed")}
                for mode in ("iid", "prefix_stratified")
            }
            by_question = {
                mode: [{m: 0.0 for m in (*CONTROLS, "observed")} for _ in range(8)]
                for mode in totals
            }
            for state in states:
                key = state["case"], state["replica"], state["step"]
                v = state["readout"]
                weight = state["remaining_requests_after_action"]
                common = {
                    "observed": float(abs(np.dot(v["collapsed_actor"], d))),
                    "proper_length": sum(
                        r["probability_given_action"] * abs(float(np.dot(r["actor"], d)))
                        for r in v["lengths"]
                    ),
                    "known_anchor": sum(
                        r["probability_given_action"] * abs(float(np.dot(r["actor"], d)))
                        for r in v["anchors"]
                    ),
                }
                values = {}
                for mode in totals:
                    subset = groups[*key, mode]
                    assert set(subset) == set(range(64))
                    assert all(r["head"] == state["head"] for r in subset.values())
                    current = {**common}
                    for method in CONTROLS[:3]:
                        current[method] = float(
                            np.mean(
                                [abs(np.dot(r["actor_scores"][method], d)) for r in subset.values()]
                            )
                        )
                    values[mode] = current
                    for m, value in current.items():
                        totals[mode][m] += weight * value / 16
                        by_question[mode][state["case"]][m] += weight * value / 16
                stream.write(
                    json.dumps(
                        {
                            "direction_index": index,
                            "case": state["case"],
                            "replica": state["replica"],
                            "step": state["step"],
                            "remaining_weight": weight,
                            "absolute_scores": values,
                        }
                    )
                    + "\n"
                )
            candidate = totals["iid"]["observed"]
            controls = [totals["iid"][m] for m in CONTROLS]
            if (
                not np.isfinite(candidate)
                or candidate <= 0
                or any(not np.isfinite(c) or c <= 0 for c in controls)
            ):
                status = "INCONCLUSIVE_NONPOSITIVE"
                ratio = None
            else:
                ratio = candidate / min(controls)
                status = (
                    "LOCAL_FIRST_ORDER_OPPORTUNITY_ONLY"
                    if ratio <= 0.8
                    else "NO_LOCAL_20PCT_OPPORTUNITY"
                )
            table.append(
                {
                    "direction_index": index,
                    "direction": d.tolist(),
                    "totals": totals,
                    "by_question": by_question,
                    "primary_ratio_to_strongest_control": ratio,
                    "status": status,
                }
            )
    (output / "ALL25-direction-table.json").write_text(json.dumps(table, indent=2) + "\n")
    winners = [r for r in table if r["status"] == "LOCAL_FIRST_ORDER_OPPORTUNITY_ONLY"]
    valid = [r for r in table if r["primary_ratio_to_strongest_control"] is not None]
    result = {
        "status": "LOCAL_OPPORTUNITY_ONLY"
        if winners
        else "NO_LOCAL_20PCT_OPPORTUNITY_IN_FIXED_DIRECTIONS",
        "promising_direction_indices": [r["direction_index"] for r in winners],
        "best_valid": min(valid, key=lambda r: r["primary_ratio_to_strongest_control"])
        if valid
        else None,
        "all_directions": 25,
        "states": 70,
        "old_paths": 16,
        "old_auxiliary_words": 8960,
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
        "updates": 0,
        "exact_native_coupler_implemented": False,
        "finite_parameter_or_latency_or_variance_claim": False,
        "neural_campaign_triggered": False,
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "auxiliary", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.auxiliary, a.output)
