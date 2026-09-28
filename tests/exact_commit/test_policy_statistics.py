import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_exact_binomial_bounds_do_not_collapse_with_zero_discordant_pairs(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    spec = importlib.util.spec_from_file_location(
        "policy_statistics", ROOT / "scripts/exact_commit/compare_policy_repeats.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    low, high = module.binomial_interval(0, 100)
    assert low == 0
    assert high == pytest.approx(1 - 0.0125**0.01)
    assert high > 0.02  # zero observed losses cannot establish this tight margin
    low, high = module.binomial_interval(100, 100)
    assert high == 1
    assert low == pytest.approx(0.0125**0.01)
    low, high = module.binomial_interval(50, 100)
    assert low < 0.5 < high
    assert low == pytest.approx(1 - high)
