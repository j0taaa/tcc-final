import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_reference_rebuild_preserves_historical_development_diagnosis(monkeypatch):
    from mwpc_exact import ExactBackend

    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    spec = importlib.util.spec_from_file_location(
        "development_diagnosis", ROOT / "scripts/exact_commit/diagnose_policy_errors.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = module.diagnose(
        ROOT / "docs/artifacts/raw/m24_policy_v1/development", backend=ExactBackend.PYTHON
    )
    expected = json.loads(
        (ROOT / "docs/research/generated/m24-development-diagnosis.json").read_text()
    )
    assert actual == expected


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


def test_failed_first_selection_is_counted_and_has_stage_timings(monkeypatch):
    from types import SimpleNamespace

    import torch

    from mwpc_exact import CompositionalByteLevelAdapter, SelectionStatus
    from mwpc_research.tool_parser import catalog_byte_grammar

    spec = importlib.util.spec_from_file_location(
        "policy_driver_failure", ROOT / "scripts/exact_commit/run_policy_screen.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tensor = torch.tensor
    monkeypatch.setattr(torch, "tensor", lambda *a, **kw: tensor(*a, **{**kw, "device": "cpu"}))
    monkeypatch.setattr(torch.cuda, "synchronize", lambda: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda: 0)
    monkeypatch.setattr(
        module,
        "select_exact_mwpc",
        lambda *a, **kw: SimpleNamespace(
            score=None,
            status=SelectionStatus.TIMEOUT,
            to_dict=lambda: {"status": "timeout", "score": None, "witness_available": False},
        ),
    )

    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return [2]

        def decode(self, *args, **kwargs):
            return ""

    def model(tokens):
        return SimpleNamespace(logits=torch.zeros((1, 3, 126337)))

    adapter = CompositionalByteLevelAdapter(tuple(b"a" if i == 0 else None for i in range(126337)))
    result = module.decode(
        model=model,
        tokenizer=Tokenizer(),
        request="arbitrary",
        calls=["a"],
        paths=[[0, 126081]],
        grammar=catalog_byte_grammar(["a"]),
        rows=[[0], [126081]],
        adapter=adapter,
        policy={"kind": "exact"},
        config={
            "slots": 2,
            "max_forwards": 2,
            "max_generation_seconds": 30,
            "selection_timeout_seconds": 10,
        },
    )
    assert result["status"] == "timeout" and result["forwards"] == 1 and result["trace"] == []
    assert result["token_ids"] == [None, None]
    assert result["solver_status_counts"] == {"timeout": 1}
    assert not result["failure"]["witness_available"]
    assert all(t >= 0 for t in result["failure"]["timings"].values())
    assert set(result["failure"]["timings"]) == {
        "forward_seconds",
        "candidate_seconds",
        "support_seconds",
        "selector_seconds",
    }
