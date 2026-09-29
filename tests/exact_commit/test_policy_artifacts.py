import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location(
        "policy_summary", ROOT / "scripts/exact_commit/summarize_policy_screen.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_smoke_has_every_policy_and_valid_certificates():
    config, rows = load().read(ROOT / "docs/artifacts/raw/m24_policy_v1/smoke")
    assert len(rows) == 40 and len(config["policies"]) == 20
    assert any(row["method"] == "exact_review" and "draft" in row for row in rows)
    assert any(row["method"].startswith("margin") for row in rows)


@pytest.mark.parametrize("mutation", ["success", "fixed", "score", "forced", "missing"])
def test_semantic_corruption_is_rejected(tmp_path, mutation):
    shutil.copytree(ROOT / "docs/artifacts/raw/m24_policy_v1/smoke", tmp_path / "data")
    directory = tmp_path / "data"
    (directory / "manifest.json").unlink()
    path = directory / "results.jsonl.gz"
    rows = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    if mutation == "success":
        rows[0]["correct"] = not rows[0]["correct"]
    elif mutation == "fixed":
        row = next(r for r in rows if r["method"] == "exact_b24")
        row["trace"][1]["canvas_before"][0] = -1
    elif mutation == "score":
        row = next(r for r in rows if r["method"] == "exact_b24")
        row["trace"][0]["production_result"]["score"] += 1
    elif mutation == "forced":
        row = next(r for r in rows if r["method"] == "margin_0")
        query = row["trace"][0]["gate"]["queries"][0]
        query["forced"] = not query["forced"]
    else:
        rows.pop()
    path.write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))
    with pytest.raises((AssertionError, ValueError)):
        load().read(directory)


def test_confidence_filter_also_applies_to_matched_greedy(monkeypatch):
    from types import SimpleNamespace

    import torch

    from mwpc_exact import CompositionalByteLevelAdapter
    from mwpc_research.tool_parser import catalog_byte_grammar

    spec = importlib.util.spec_from_file_location(
        "policy_driver", ROOT / "scripts/exact_commit/run_policy_screen.py"
    )
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    # The exact feasibility subroutine does not make greedy selection optimal.
    assert driver.policy_scope({"kind": "confidence", "selector": "greedy"}).startswith(
        "feasible_on_support; no optimal-selection guarantee"
    )
    assert driver.policy_scope({"kind": "greedy"}).startswith("feasible_on_support")
    assert driver.policy_scope({"kind": "confidence"}).startswith("exact_on_support")
    original_tensor = torch.tensor
    monkeypatch.setattr(
        torch, "tensor", lambda *a, **kw: original_tensor(*a, **{**kw, "device": "cpu"})
    )
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda: 0)

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [2]

        def decode(self, ids, **kwargs):
            return "".join({0: "a", 1: "b"}.get(t, "") for t in ids)

    def model(tokens):
        logits = torch.full((1, 4, 126337), -100.0)
        logits[0, 1:3, :2] = torch.tensor([[0.4, 0.0], [0.0, 0.4]])
        logits[0, 3, 126081] = 100.0
        return SimpleNamespace(logits=logits)

    adapter = CompositionalByteLevelAdapter(tuple({0: b"a", 1: b"b"}.get(t) for t in range(126337)))
    result = driver.decode(
        model=model,
        tokenizer=Tokenizer(),
        request="arbitrary",
        calls=["aa", "bb"],
        paths=[[0, 0, 126081], [1, 1, 126081]],
        grammar=catalog_byte_grammar(["aa", "bb"]),
        rows=[[0, 1, 126081], [0, 1, 126081], [126081]],
        adapter=adapter,
        policy={"name": "test", "kind": "confidence", "selector": "greedy", "threshold": 0.8},
        config={
            "slots": 3,
            "max_forwards": 3,
            "max_generation_seconds": 30,
            "selection_timeout_seconds": 10,
        },
    )
    assert result["status"] == "complete"
    assert result["trace"][0]["committed_positions"] == [2]
    assert all(t["production_result"]["status"] == "feasible_on_support" for t in result["trace"])
    assert result["forwards"] > 1


def test_interrupted_external_smoke_is_not_a_complete_cohort():
    directory = ROOT / "docs/artifacts/raw/m25_grounded_v1/interrupted_smoke"
    with pytest.raises(AssertionError):
        load().read(directory)
    config, rows = load().read(directory, allow_incomplete=True)
    assert len(rows) == 4 < len(config["tasks"]) * len(config["policies"])
    assert all(row["git_commit"].startswith("b71e3c6") for row in rows)
