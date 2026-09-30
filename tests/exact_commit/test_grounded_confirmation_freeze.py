import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    spec = importlib.util.spec_from_file_location(
        "grounded_freeze", ROOT / "scripts/exact_commit/freeze_grounded_confirmation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_development_budget_choice_prioritizes_correctness_then_total_cost(monkeypatch):
    module = load(monkeypatch)
    rows = [
        {"method": "exact_b4", "n": 26, "correct": 5, "median_total_ms": 100},
        {"method": "exact_b64", "n": 26, "correct": 6, "median_total_ms": 1000},
        {"method": "confidence_0.8", "n": 26, "correct": 20, "median_total_ms": 1},
    ]
    assert module.selected_budget(rows) == "exact_b64"
    rows[1]["correct"] = 5
    assert module.selected_budget(rows) == "exact_b4"
    rows[1]["n"] = 25
    with pytest.raises(ValueError, match="complete"):
        module.selected_budget(rows)
