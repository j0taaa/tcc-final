"""FAKE-head IO/status regression, including legal Decimal-unrepresentable words."""

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import conditional_capture_v17 as driver
from .consumer_resource import sha, write_json
from .llada_suffix_v10 import NumericSuffixJSON
from .prefix_floating import PrefixFloatPlan, PrefixPlanner


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
    protocol = {
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        },
        "source_sha256": {},
        "input_sha256": {
            "rows": sha(capture / "rows.jsonl"),
            "manifest": sha(capture / "manifest.json"),
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
    assert report["status"] == "PASS" and report["status_counts"]["PASS"] == 560
    assert report["auxiliary_word_attempts"] == report["raw_completed_auxiliary_words"] == 560
    assert report["secondary_Decimal_unrepresentable_words"] == 256
    assert report["global_Python_NumPy_RNG_unchanged"]
    write_json(
        output / "scope.json",
        {
            "status": "PASS",
            "FAKE_states": 70,
            "FAKE_auxiliary_words": 560,
            "FAKE_Decimal_unrepresentable_legal_words": 256,
            "pretrained_heads": 0,
            "real_old_head_auxiliary_words": 0,
            "model_forwards": 0,
            "note": "IO/status regression; repeated fake states are not a real adaptive decoder path",
        },
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
