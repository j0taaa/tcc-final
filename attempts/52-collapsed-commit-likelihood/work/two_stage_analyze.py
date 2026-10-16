"""Post-capture labels and frozen necessary variance gate. No model execution."""

import argparse
import json
from pathlib import Path

import numpy as np

from .consumer_resource import HERE, sha, write_json
from .two_stage import answer_equal

DATA_SHA = "17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465"
METHODS = ("full_triple", "anchor_integrated", "known_anchor", "collapsed")
BASELINES = ("zero", "pilot", "rloo")


def fit_baseline(rewards, scores):
    norm = np.sum(scores * scores, axis=1)
    return float(np.dot(rewards, norm) / norm.sum()) if norm.sum() else 0.0


def group_gradients(rewards, scores, baseline, kind, group_size=8):
    r = np.asarray(rewards).reshape(-1, group_size)
    s = np.asarray(scores).reshape(-1, group_size, scores.shape[-1])
    if kind == "rloo":
        b = (r.sum(axis=1, keepdims=True) - r) / (group_size - 1)
    elif kind == "pilot":
        b = baseline
    elif kind == "zero":
        b = 0.0
    else:
        raise ValueError("unknown frozen baseline")
    return np.mean((r - b)[:, :, None] * s, axis=1)


def trace(groups):
    return np.sum((groups - groups.mean(axis=-2, keepdims=True)) ** 2, axis=(-2, -1)) / (
        groups.shape[-2] - 1
    )


def run(capture, dataset, output):
    output.mkdir(parents=True, exist_ok=False)
    status = json.loads((capture / "summary.json").read_text())
    if status["status"] != "CAPTURE_COMPLETE" or status["records"] != 640 or status["errors"]:
        write_json(
            output / "summary.json", {"status": "NEGATIVE_CAPTURE_INCOMPLETE", "capture": status}
        )
        return
    records = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    if len(records) != 640 or any(r["status"] != "COMPLETE" for r in records):
        raise ValueError("capture status/rows mismatch")
    # This is the FIRST answer-label access in the V5 program, after closed capture.
    if sha(dataset) != DATA_SHA:
        raise ValueError("external dataset pin mismatch")
    lines = dataset.read_text().splitlines()
    inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
    labels = []
    for item in inputs:
        raw = json.loads(lines[int(item["id"].split(":")[1])])
        if raw["question"] != item["question"]:
            raise ValueError("external question mismatch")
        label = raw["answer"].split("####")[-1].strip().replace(",", "")
        labels.append({"id": item["id"], "answer": label})
    write_json(
        output / "labels-after-capture.json",
        {
            "dataset_sha256": DATA_SHA,
            "capture_rows_sha256": sha(capture / "rows.jsonl"),
            "capture_summary_sha256": sha(capture / "summary.json"),
            "labels": labels,
        },
    )
    names = [f"{m}:{b}" for m in METHODS for b in BASELINES]
    groups = []
    per_case = []
    baselines = []
    reward_rows = []
    for case in range(8):
        ordered = []
        for phase, count in (("pilot", 16), ("eval", 64)):
            rows = sorted(
                (r for r in records if r["case"] == case and r["phase"] == phase),
                key=lambda r: r["draw"],
            )
            if len(rows) != count or [r["draw"] for r in rows] != list(range(count)):
                raise ValueError("missing/duplicate fixed draw")
            ordered.extend(rows)
        reward = np.asarray(
            [answer_equal(r["json"], labels[case]["answer"]) for r in ordered], dtype=np.float64
        )
        reward_rows.extend(
            {"case": case, "phase": r["phase"], "draw": r["draw"], "reward": int(v)}
            for r, v in zip(ordered, reward, strict=True)
        )
        outputs = []
        for method in METHODS:
            score = np.asarray([r["scores"][method] for r in ordered], dtype=np.float64)
            if score.shape != (80, 65) or not np.isfinite(score).all():
                raise ValueError("declared65-coordinate planner score mismatch")
            baseline = fit_baseline(reward[:16], score[:16])
            baselines.append({"case": case, "method": method, "pilot_baseline": baseline})
            outputs.extend(group_gradients(reward[16:], score[16:], baseline, b) for b in BASELINES)
        outputs = np.asarray(outputs)
        variances = trace(outputs)
        per_case.append(
            {
                "case": case,
                "input_id": inputs[case]["id"],
                "pilot_correct": int(reward[:16].sum()),
                "evaluation_correct": int(reward[16:].sum()),
                "reward_varies": bool(reward[16:].min() != reward[16:].max()),
                "variance": dict(zip(names, variances.tolist(), strict=True)),
                "block_variance": {
                    block: dict(zip(names, trace(outputs[..., indices]).tolist(), strict=True))
                    for block, indices in (
                        ("alpha", slice(0, 32)),
                        ("beta", slice(32, 33)),
                        ("anchor", slice(33, 65)),
                    )
                },
            }
        )
        groups.append(outputs)
    groups = np.asarray(groups)
    aggregate = trace(groups).sum(axis=0) / 64
    candidate = names.index("collapsed:pilot")
    controls = tuple(i for i, n in enumerate(names) if not n.startswith("collapsed:"))
    cheap = names.index("anchor_integrated:pilot")
    variation = sum(r["reward_varies"] for r in per_case)
    favorable = sum(r["variance"][names[candidate]] < r["variance"][names[cheap]] for r in per_case)
    positive = bool(aggregate[candidate] > 0 and all(aggregate[i] > 0 for i in controls))
    gate = bool(
        positive
        and variation >= 6
        and favorable >= 6
        and all(aggregate[candidate] <= 0.8 * aggregate[i] for i in controls)
    )
    rng = np.random.default_rng(52051)
    boot = []
    for _ in range(2000):
        indices = rng.integers(8, size=(8, 8))
        sample = np.take_along_axis(groups, indices[:, None, :, None], axis=2)
        values = trace(sample).sum(axis=0) / 64
        boot.append([values[candidate] / values[i] if values[i] > 0 else np.nan for i in controls])
    boot = np.asarray(boot)
    ratios = {
        names[i]: float(aggregate[candidate] / aggregate[i]) if aggregate[i] > 0 else None
        for i in controls
    }
    intervals = {
        names[i]: np.quantile(boot[np.isfinite(boot[:, j]), j], [0.025, 0.975]).tolist()
        if np.isfinite(boot[:, j]).any()
        else None
        for j, i in enumerate(controls)
    }
    report = {
        "status": "NECESSARY_VARIANCE_PASS" if gate else "NEGATIVE_NECESSARY_VARIANCE",
        "producer_capture": json.loads((capture / "provenance.json").read_text())[
            "producer_commit"
        ],
        "records": 640,
        "reward_variation_cases": variation,
        "favorable_vs_cheap_pilot_cases": favorable,
        "aggregate_trace_covariance": dict(zip(names, aggregate.tolist(), strict=True)),
        "candidate": "collapsed:pilot",
        "candidate_to_control_ratio": ratios,
        "diagnostic_group_bootstrap_ratio_intervals": intervals,
        "complete_cost_gate_executed": False,
        "updates": 0,
        "independent_confirmation": False,
        "per_case": per_case,
        "next_phase": "separate complete-cost protocol MAY be considered"
        if gate
        else "this application is closed; no timing/training campaign",
    }
    write_json(output / "summary.json", report)
    write_json(output / "pilot-baselines.json", baselines)
    write_json(output / "reward-rows.json", reward_rows)
    np.savez_compressed(
        output / "group-gradients.npz", groups=groups, configuration=np.asarray(names)
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("per_case", "diagnostic_group_bootstrap_ratio_intervals")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.capture, args.dataset, args.output)
