import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def driver():
    spec = importlib.util.spec_from_file_location(
        "policy_driver_resume", ROOT / "scripts/exact_commit/run_policy_screen.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resume_only_accepts_intact_ordered_prefix_and_identical_config(tmp_path):
    cfg = {"tasks": [{"id": "a"}, {"id": "b"}], "policies": [{"name": "x"}, {"name": "y"}]}
    raw = json.dumps(cfg).encode()
    (tmp_path / "config.json").write_bytes(raw)

    def save(keys):
        (tmp_path / "results.jsonl").write_text(
            "".join(
                json.dumps(
                    {
                        "task": {"id": t},
                        "method": m,
                        "config_sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
                + "\n"
                for t, m in keys
            )
        )

    save([("a", "x"), ("a", "y"), ("b", "y")])
    assert driver().resume_keys(tmp_path, raw) == {("a", "x"), ("a", "y"), ("b", "y")}
    for keys in [[("a", "y")], [("a", "x"), ("a", "x")], [("a", "x"), ("a", "y"), ("b", "x")]]:
        save(keys)
        with pytest.raises(ValueError, match="prefix"):
            driver().resume_keys(tmp_path, raw)
    with pytest.raises(ValueError, match="configuration differs"):
        driver().resume_keys(tmp_path, raw + b" ")
    save([("a", "x")])
    path = tmp_path / "results.jsonl"
    path.write_text(path.read_text().replace(hashlib.sha256(raw).hexdigest(), "wrong"))
    with pytest.raises(ValueError, match="hash"):
        driver().resume_keys(tmp_path, raw)
    path.write_text(path.read_text() + '{"unfinished":')
    with pytest.raises(ValueError):
        driver().resume_keys(tmp_path, raw)
