"""FAKE-head capture/analysis regression; no pretrained model or real auxiliary data."""

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import conditional_capture_v18 as driver
from .actor_coordinates import actor_vector, state_features
from .conditional_analyze_v18 import run as analyze
from .consumer_resource import serial, sha, write_json
from .llada_suffix_v10 import NumericSuffixJSON
from .numeric_proxy import IntegerProxy
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .proxy_floating import ProxyPlanner


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    emissions = (b"1}", b"1e" + b"9" * 1000 + b"}", b" ", b"", b"", b"0}", b"<MASK>", b"<EOT>")
    plan = PrefixFloatPlan(NumericSuffixJSON(emissions, 7, 7))
    planner = PrefixPlanner(plan, np.full((2, 8), 1 / 8), {}, 0.0)
    capture, analysis = output / "FAKE-capture", output / "FAKE-analysis"
    (capture / "heads").mkdir(parents=True)
    analysis.mkdir()
    head = capture / "heads/fake.npz"
    np.savez(head, logits_bf16=np.zeros((2, 8), dtype=np.uint16), positions=[0, 1])
    write_json(capture / "manifest.json", {"heads/fake.npz": {"sha256": sha(head)}})
    rows = []
    for index in range(16):
        case, replica = divmod(index, 2)
        token = int(case >= 4)
        action = ((0, token), (1, 7))
        logp = planner.statistics(action)["log_probability"]
        transitions = [
            {
                "head": "fake",
                "step": step,
                "fixed_before": [],
                "action": action,
                "queried_positions": [0, 1],
                "prefix_extent": 2,
                "log_probability": logp,
            }
            for step in range(5 if index < 6 else 4)
        ]
        rows.append(
            {"case": case, "replica": replica, "root_feature": 0.0, "transitions": transitions}
        )
    (capture / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    write_json(analysis / "known-labels-provenance.json", {"labels": [{"answer": "1"}] * 8})
    rewards = [
        {"case": r["case"], "replica": r["replica"], "candidate_correct": r["case"] < 4}
        for r in rows
    ]
    write_json(analysis / "reward-rows.json", rewards)
    state = state_features(planner.weights, {}, 7)
    proxy = ProxyPlanner(planner, PrefixFloatPlan(IntegerProxy(emissions, 7, 7, "1")))
    features = []
    for r in rows:
        for t in r["transitions"]:
            c = proxy.statistics(tuple(map(tuple, t["action"])))
            features.append(
                {
                    "case": r["case"],
                    "replica": r["replica"],
                    "step": t["step"],
                    "head": t["head"],
                    "features": serial(state),
                    "baselines": [0.0, 0.5, 1 / 3, 1 / 3],
                    "controls": [
                        serial(actor_vector(c["correction"], state)),
                        [0.0] * 9,
                        [0.0] * 9,
                    ],
                }
            )
    feature_path = output / "FAKE-features.jsonl"
    feature_path.write_text("".join(json.dumps(r) + "\n" for r in features))
    protocol = {
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        },
        "source_sha256": {},
        "old_features_path": str(feature_path),
        "input_sha256": {
            "rows": sha(capture / "rows.jsonl"),
            "manifest": sha(capture / "manifest.json"),
            "features": sha(feature_path),
            "rewards": sha(analysis / "reward-rows.json"),
            "labels": sha(analysis / "known-labels-provenance.json"),
        },
    }
    write_json(output / "FAKE-protocol.json", protocol)

    class FakeTokenizer:
        def decode(self, ids, skip_special_tokens=False):
            assert ids[:3] == [12657, 31113, 2275] and not skip_special_tokens
            return '{"answer":' + b"".join(emissions[v] for v in ids[3:]).decode()

    with (
        patch.object(driver, "VOCABULARY", 8),
        patch.object(driver, "EOS", 7),
        patch.object(driver, "emissions", return_value=emissions),
        patch.object(driver, "verify_files", return_value={}),
        patch.object(driver, "tokenizer_from", return_value=FakeTokenizer()),
    ):
        driver.run(
            Path("unused-FAKE-model"),
            capture,
            analysis,
            output / "FAKE-protocol.json",
            output / "FAKE-replay",
        )
    report = json.loads((output / "FAKE-replay/summary.json").read_text())
    assert report["status"] == "PASS" and report["status_counts"]["PASS"] == 8960
    assert report["auxiliary_word_attempts"] == report["raw_completed_auxiliary_words"] == 8960
    recorded = [
        json.loads(r) for r in (output / "FAKE-replay/records.jsonl").read_text().splitlines()
    ]
    assert sum(r["secondary_Decimal_representable"] is False for r in recorded) == 4096
    analyze(output / "FAKE-replay", output / "FAKE-analysis-tables")
    result = json.loads((output / "FAKE-analysis-tables/summary.json").read_text())
    assert result["table_entries"] == 2268
    assert result["family_A"]["status"] != "ZERO_OVERHEAD_NECESSITY_PASS"
    assert result["family_B"]["status"] != "ZERO_OVERHEAD_NECESSITY_PASS"
    assert report["global_Python_NumPy_RNG_unchanged"]
    write_json(
        output / "scope.json",
        {
            "status": "PASS",
            "FAKE_states": 70,
            "FAKE_auxiliary_words": 8960,
            "FAKE_Decimal_unrepresentable_legal_words": 4096,
            "pretrained_heads": 0,
            "real_old_head_auxiliary_words": 0,
            "model_forwards": 0,
            "note": "IO/status regression; repeated fake states do not form a decoder path",
        },
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
