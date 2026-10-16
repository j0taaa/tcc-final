"""FAKE pipeline: repeated toy states, not real adaptive decoder trajectories."""

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import capture_support as driver
from .actor_coordinates import actor_vector, state_features
from .analyze_opportunity import run as analyze
from .length_readout import NumericSuffix
from .prefix_floating import PrefixFloatPlan, PrefixPlanner


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return list(map(serial, value))
    return value


def save(path, value):
    path.write_text(json.dumps(serial(value), indent=2) + "\n")


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    capture = output / "FAKE-input"
    (capture / "heads").mkdir(parents=True)
    auxiliary = output / "FAKE-auxiliary"
    auxiliary.mkdir()
    table = (b"1", b"}", b"", b"0", b"EOS")
    plan = PrefixFloatPlan(NumericSuffix(table, 4, 4))
    weights = np.full((4, 5), 1 / 5)
    planner = PrefixPlanner(plan, weights, {}, -2.0)
    features = state_features(weights, {}, 4)
    action = ((0, 0), (2, 4))
    word = (0, 1, 4)
    scores = planner.statistics(action)
    np.savez(
        capture / "heads/FAKE.npz",
        logits_bf16=np.zeros((4, 5), dtype=np.uint16),
        positions=np.arange(4),
    )
    save(
        capture / "manifest.json",
        {"heads/FAKE.npz": {"sha256": driver.sha(capture / "heads/FAKE.npz")}},
    )
    rows = []
    old_features = []
    records = []
    for index in range(16):
        case, replica = divmod(index, 2)
        transitions = []
        for step in range(5 if index < 6 else 4):
            transitions.append(
                {
                    "step": step,
                    "head": "FAKE",
                    "prefix_extent": 4,
                    "fixed_before": [],
                    "action": action,
                    "log_probability": scores["log_probability"],
                    "scores": {"collapsed": scores},
                }
            )
            old_features.append(
                {
                    "case": case,
                    "replica": replica,
                    "step": step,
                    "head": "FAKE",
                    "features": features,
                }
            )
            for mode in ("iid", "prefix_stratified"):
                for r in range(64):
                    anchor = action[r % 2][0]
                    controls = {
                        "collapsed": scores,
                        **planner.controls(word, anchor, action, scores),
                    }
                    records.append(
                        {
                            "case": case,
                            "replica": replica,
                            "step": step,
                            "head": "FAKE",
                            "method": mode,
                            "draw_index": r,
                            "status": "PASS",
                            "actor_scores": {
                                m: actor_vector(s, features) for m, s in controls.items()
                            },
                        }
                    )
        rows.append(
            {"case": case, "replica": replica, "root_feature": -2.0, "transitions": transitions}
        )
    (capture / "rows.jsonl").write_text("".join(json.dumps(serial(r)) + "\n" for r in rows))
    f = output / "FAKE-features.jsonl"
    f.write_text("".join(json.dumps(serial(r)) + "\n" for r in old_features))
    (auxiliary / "records.jsonl").write_text("".join(json.dumps(serial(r)) + "\n" for r in records))
    save(auxiliary / "summary.json", {"status": "PASS"})
    protocol = {
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        },
        "source_sha256": {},
        "input_sha256": {
            k: driver.sha(p)
            for k, p in {
                "rows": capture / "rows.jsonl",
                "manifest": capture / "manifest.json",
                "features": f,
                "auxiliary": auxiliary / "records.jsonl",
                "auxiliary_summary": auxiliary / "summary.json",
            }.items()
        },
    }
    save(output / "FAKE-protocol.json", protocol)
    with (
        patch.object(driver, "EOS", 4),
        patch.object(driver, "VOCABULARY", 5),
        patch.object(driver, "emissions", return_value=table),
        patch.object(driver, "verify_files", return_value={}),
    ):
        driver.run(
            Path("unused-model"),
            capture,
            f,
            auxiliary,
            output / "FAKE-protocol.json",
            output / "FAKE-readouts",
        )
    status = json.loads((output / "FAKE-readouts/summary.json").read_text())
    assert status["status"] == "PASS"
    analyze(output / "FAKE-readouts", auxiliary, output / "FAKE-analysis")
    result = json.loads((output / "FAKE-analysis/summary.json").read_text())
    assert not result["promising_direction_indices"] and result["all_directions"] == 25
    save(
        output / "scope.json",
        {
            "status": "PASS",
            "FAKE_states": 70,
            "FAKE_preexisting_auxiliary_vectors": 8960,
            "real_old_head_queries": 0,
            "new_model_forwards": 0,
            "note": "repeated fake states, not a decoder/posterior study",
        },
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    run(p.parse_args().output)
