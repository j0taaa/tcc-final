"""AFTER-data scalar recomputation of ALL old-path diagnostic configurations."""

import argparse
import json
from pathlib import Path

import numpy as np


def run(capture, proxy, diagnostic):
    rows = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    states = [json.loads(x) for x in (diagnostic / "state-features.jsonl").read_text().splitlines()]
    proxy_rows = [json.loads(x) for x in (proxy / "records.jsonl").read_text().splitlines()]
    stored = json.loads((diagnostic / "path-sufficient-statistics.json").read_text())
    table = json.loads((diagnostic / "ALL756-fixed-configurations.json").read_text())
    assert len(rows) == len(stored) == 16 and len(states) == len(proxy_rows) == 70
    methods = tuple(stored[0]["scores"])
    computed, ordinal = {}, 0
    maximum, coordinates, rloo_checks = 0.0, 0, 0

    def check(a, b):
        nonlocal maximum, coordinates
        a, b = np.asarray(a), np.asarray(b)
        assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
        delta = float(np.max(np.abs(a - b)))
        maximum = max(maximum, delta)
        coordinates += a.size
        assert delta <= 2e-12

    def project(score, f):
        n = len(f["x"])
        a = [float(x) for x in score["alpha"][:n]]
        r = [float(x) for x in score["anchor"][:n]]
        ax, ah, rx, rh = (
            sum(f[k][i] * v[i] for i in range(n))
            for k, v in (("x", a), ("h", a), ("x", r), ("h", r))
        )
        return np.asarray(
            [sum(a), ax, ah, f["m"] * sum(a), f["e"] * sum(a), rx, rh, f["m"] * rx, score["beta"]]
        )

    for row, saved in zip(rows, stored, strict=True):
        scores = {m: np.zeros(9) for m in methods}
        baselines = {m: np.zeros((4, 9)) for m in methods}
        controls = np.zeros((3, 9))
        for transition in row["transitions"]:
            state, previous = states[ordinal], proxy_rows[ordinal]
            assert state["ordinal"] == ordinal
            for k, source in (
                ("case", row),
                ("replica", row),
                ("step", transition),
                ("head", transition),
            ):
                assert state[k] == previous[k] == source[k]
            f = state["features"]
            check(f["x"], [(2 * i + 1) / 64 - 1 for i in range(transition["prefix_extent"])])
            check(f["m"], (transition["prefix_extent"] - len(transition["fixed_before"])) / 64)
            vec = {m: project(transition["scores"][m], f) for m in methods}
            cv = np.stack(
                (
                    project(previous["proxy"]["correction"], f),
                    previous["proposal_semantic_correct"] * vec["full_triple"],
                    previous["proposal_semantic_correct"] * vec["anchor_integrated"],
                )
            )
            check(cv, state["controls"])
            for m in methods:
                scores[m] += vec[m]
                for b in range(4):
                    baselines[m][b] += state["baselines"][b] * vec[m]
            controls += cv
            ordinal += 1
        for m in methods:
            check(scores[m], saved["scores"][m])
            check(baselines[m], saved["baseline_scores"][m])
        check(controls, saved["controls"])
        computed[row["case"], row["replica"]] = {
            "scores": scores,
            "baselines": baselines,
            "controls": controls,
            "reward": saved["reward"],
        }
    for entry in table:
        m, b = (
            entry["method"],
            ("zero", "half", "proxy_state", "proxy_root").index(entry["baseline"]),
        )
        coef = entry["coefficients_C_Wfull_Wanchor"]
        gradients = {}
        for key, p in computed.items():
            g = np.asarray(
                [
                    p["reward"] * p["scores"][m][j]
                    - p["baselines"][m][b][j]
                    - sum(coef[k] * p["controls"][k][j] for k in range(3))
                    for j in range(9)
                ]
            )
            saved = next(
                x for x in entry["individual_gradients"] if (x["case"], x["replica"]) == key
            )
            check(g, saved["gradient"])
            gradients[key] = g
        blocks = dict.fromkeys(("total", "gate", "anchor", "confidence"), 0.0)
        for q in range(8):
            d = gradients[q, 0] - gradients[q, 1]
            values = {
                "total": sum(v * v for v in d) / 2,
                "gate": sum(v * v for v in d[:5]) / 2,
                "anchor": sum(v * v for v in d[5:8]) / 2,
                "confidence": d[8] ** 2 / 2,
            }
            for block, value in values.items():
                check(value, entry["paired_single_path_trace_by_question"][str(q)][block])
                blocks[block] += value / 64
        for block, value in blocks.items():
            check(value, entry["equal8_question_mean_trace_estimate"][block])
    assert len(table) == 756
    for entry in json.loads((diagnostic / "RLOO-one-group-variance-unavailable.json").read_text()):
        assert entry["variance"] is None and entry["independent_groups_per_question"] == 1
        for group in entry["groups"]:
            q = group["case"]
            a, b = computed[q, 0], computed[q, 1]
            m, c = entry["method"], entry["coefficients_C_Wfull_Wanchor"]
            g = (
                (a["reward"] - b["reward"]) * (a["scores"][m] - b["scores"][m])
                - np.asarray(c) @ (a["controls"] + b["controls"])
            ) / 2
            check(g, group["group_gradient"])
            rloo_checks += 1
    report = {
        "status": "PASS",
        "scope": "AFTER-data arithmetic consistency, not independent evaluation",
        "old_transitions": ordinal,
        "fixed_configurations": len(table),
        "scalar_coordinate_checks": coordinates,
        "RLOO_group_checks": rloo_checks,
        "maximum_absolute_difference": maximum,
        "new_model_forwards": 0,
        "updates": 0,
    }
    (diagnostic / "post-capture-scalar-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "proxy", "diagnostic"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    run(a.capture, a.proxy, a.diagnostic)
