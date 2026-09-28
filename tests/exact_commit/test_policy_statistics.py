import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    spec = importlib.util.spec_from_file_location(
        "policy_statistics", ROOT / "scripts/exact_commit/compare_policy_repeats.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_binomial_bounds_do_not_collapse_with_zero_discordant_pairs(monkeypatch):
    module = load(monkeypatch)
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


def test_secondary_pairs_require_matching_methods_and_both_repetitions(monkeypatch):
    module = load(monkeypatch)
    configs = {
        "a": {"tasks": [], "policies": [{"name": "primary"}]},
        "b": {"tasks": [], "policies": [{"name": "primary"}]},
        "c": {"tasks": [], "policies": [{"name": "extra"}]},
        "d": {"tasks": [], "policies": [{"name": "different"}]},
    }
    monkeypatch.setattr(module, "read", lambda path: (configs[path], []))
    with pytest.raises(ValueError, match="Both repetitions"):
        module.build("a", "b", controls_first="c")
    with pytest.raises(AssertionError):
        module.build("a", "b", controls_first="c", controls_second="d")
    with pytest.raises(AssertionError):
        module.build("a", "b", secondary_first="a", secondary_second="b")


def test_whitespace_sensitivity_handles_indentation_without_changing_strings(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    from diagnose_policy_whitespace import normalize_lexical_whitespace

    from mwpc_research.schema_calls import normalize_schema_call

    output = "\n    get_service_id\n\n (service_id = 2)\n"
    assert normalize_schema_call(output) is None
    assert (
        normalize_schema_call(normalize_lexical_whitespace(output))
        == "get_service_id(service_id=2)"
    )
    output = "f\n (x='a  b\\nc')"
    assert normalize_schema_call(normalize_lexical_whitespace(output)) == "f(x='a  b\\nc')"
    assert normalize_lexical_whitespace("f(") == "f("
