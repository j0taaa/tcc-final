"""FAKE16-path70-transition IO screen; no real old-path certificates."""

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from unittest.mock import patch

from . import old_path_screen as driver


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    table = (b"0", b"1", b"}", b" ", b"", b"", b"EOS")
    capture = output / "FAKE-input"
    capture.mkdir()
    rows = []
    for i in range(16):
        word = [1, 3, 3, 2, 6] if i < 6 else [1, 3, 2, 6]
        transitions = []
        fixed = {}
        for step, token in enumerate(word):
            transitions.append(
                {
                    "fixed_before": sorted(fixed.items()),
                    "head": f"FAKE-{i}-{step}",
                    "proposal_prefix": word,
                }
            )
            fixed[step] = token
        rows.append(
            {
                "case": i // 2,
                "replica": i % 2,
                "status": "COMPLETE",
                "transitions": transitions,
                "fixed_terminal": sorted(fixed.items()),
                "terminal_ids": word,
            }
        )
    (capture / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    protocol = {
        "runtime": {
            "python": platform.python_version(),
            "tokenizers": importlib.metadata.version("tokenizers"),
        },
        "source_sha256": {},
        "input_sha256": {"rows": driver.sha(capture / "rows.jsonl")},
    }
    path = output / "FAKE-protocol.json"
    path.write_text(json.dumps(protocol, indent=2) + "\n")
    with (
        patch.object(driver, "EOS", 6),
        patch.object(driver, "emissions", return_value=table),
        patch.object(driver, "verify_files", return_value={}),
    ):
        driver.run(Path("unused-model"), capture, path, output / "FAKE-results")
    result = json.loads((output / "FAKE-results/summary.json").read_text())
    assert result["status"] == "NECESSITY_NEGATIVE"
    assert (
        result["logical_forward_requests"]["cheap_prefix"]
        == result["logical_forward_requests"]["projected_singleton"]
    )
    assert len((output / "FAKE-results/states.jsonl").read_text().splitlines()) == 86
    summary = {
        "status": "PASS",
        "FAKE_paths": 16,
        "FAKE_states": 86,
        "pretrained_heads": 0,
        "real_old_path_certificates": 0,
        "new_model_forwards": 0,
    }
    (output / "scope.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    run(p.parse_args().output)
