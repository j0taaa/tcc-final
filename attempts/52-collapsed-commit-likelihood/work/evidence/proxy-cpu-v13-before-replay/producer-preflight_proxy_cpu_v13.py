"""FAKE-head end-to-end CPU driver regression; no pretrained head/model."""

import argparse
import ast
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import proxy_replay_v13 as driver
from .consumer_resource import sha, write_json
from .llada_capture_v10 import padded_score
from .llada_suffix_v10 import NumericSuffixJSON
from .prefix_floating import PrefixFloatPlan, PrefixPlanner


def run(output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    source = Path(driver.__file__).read_text()
    tree = ast.parse(source)
    assert not any(isinstance(n, ast.Attribute) and n.attr == "cuda" for n in ast.walk(tree))
    assert not any(
        isinstance(n, ast.keyword)
        and n.arg == "device"
        and isinstance(n.value, ast.Constant)
        and n.value.value != "cpu"
        for n in ast.walk(tree)
    )
    assert "CaptureOccupancy" not in source and "observer." not in source
    torch.set_num_threads(4)
    assert not torch.cuda.is_initialized()
    emissions = (b"1}", b"2}", b" ", b"", b"", b"0}", b"<MASK>", b"<EOT>")
    weights = np.full((2, 8), 1 / 8)
    plan = PrefixFloatPlan(NumericSuffixJSON(emissions, 7, 7))
    base = PrefixPlanner(plan, weights, {}, 0.0)
    action = ((0, 0), (1, 7))
    score = base.statistics(action)
    capture, analysis = output / "FAKE-capture", output / "FAKE-analysis"
    (capture / "heads").mkdir(parents=True)
    analysis.mkdir()
    head = capture / "heads/fake.npz"
    np.savez(head, logits_bf16=np.zeros((2, 8), dtype=np.uint16), positions=[0, 1])
    write_json(capture / "manifest.json", {"heads/fake.npz": {"sha256": sha(head)}})
    transition = {
        "head": "fake",
        "step": 0,
        "fixed_before": [],
        "action": action,
        "queried_positions": [0, 1],
        "prefix_extent": 2,
        "proposal_prefix": [0, 7],
        "log_probability": score["log_probability"],
        "scores": {
            "collapsed": {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in padded_score(score).items()
            }
        },
    }
    row = {"case": 0, "replica": 0, "root_feature": 0.0, "transitions": [transition] * 70}
    (capture / "rows.jsonl").write_text(json.dumps(row) + "\n")
    write_json(analysis / "known-labels-provenance.json", {"labels": [{"answer": "1"}]})
    protocol = {
        "runtime": {"torch": torch.__version__, "numpy": np.__version__},
        "source_sha256": {},
        "input_sha256": {
            "capture_manifest": sha(capture / "manifest.json"),
            "rows": sha(capture / "rows.jsonl"),
            "labels": sha(analysis / "known-labels-provenance.json"),
        },
    }
    write_json(output / "FAKE-protocol.json", protocol)
    with (
        patch.object(driver, "VOCABULARY", 8),
        patch.object(driver, "EOS", 7),
        patch.object(driver, "emissions", return_value=emissions),
        patch.object(driver, "verify_files", return_value={}),
    ):
        driver.run(
            Path("unused-FAKE-model"),
            capture,
            analysis,
            output / "FAKE-protocol.json",
            output / "FAKE-replay",
        )
    result = json.loads((output / "FAKE-replay/summary.json").read_text())
    assert result["status"] == "PASS" and result["records"] == 70
    assert not torch.cuda.is_initialized()
    write_json(
        output / "scope.json",
        {
            "status": "PASS",
            "FAKE_HEAD_records": 70,
            "actual_neural_heads": 0,
            "model_forwards": 0,
            "CUDA_initialized": False,
            "CPU_driver_serialization_caps_and_compares": True,
        },
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
