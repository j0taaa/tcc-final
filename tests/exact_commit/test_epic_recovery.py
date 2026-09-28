import importlib.util
from pathlib import Path

import pytest

from mwpc_research.tool_parser import catalog_byte_grammar, epic_byte_grammar, epic_lexical_grammar

ROOT = Path(__file__).resolve().parents[2]


def runner():
    spec = importlib.util.spec_from_file_location(
        "run_epic_recovery", ROOT / "scripts/exact_commit/run_epic_recovery.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("method", ["epic_native_1", "epic_lexical_1"])
def test_official_recovery_fills_a_saved_mask_without_model_or_answer(method):
    pytest.importorskip("rustformlang")
    calls = ["neg(1)", "abs(1)"]
    _, _, rules = (
        epic_lexical_grammar(calls)
        if "lexical" in method
        else epic_byte_grammar(catalog_byte_grammar(calls))
    )
    row = {
        "method": method,
        "status": "incomplete",
        "epic_lex_rules": rules,
        "token_ids": [0, 126336, 1, 126081],
        "token_emissions": {"0": list(b"neg("), "1": list(b")")},
    }
    result = runner().recover(row, calls, 10)
    assert result["recovery_status"] == "recovered", result
    assert result["fixed_fragments_preserved"]
    assert result["recovery_output"] == "neg(1)"


def test_complete_decoder_output_is_not_repaired():
    result = runner().recover({"status": "complete"}, [])
    assert result["recovery_status"] == "not_needed"
    assert result["recovery_output"] is None
    assert result["recovery_seconds"] == 0


@pytest.mark.parametrize(
    "failure,status",
    [(None, "no_completion"), (TimeoutError("late"), "timeout"), (ValueError("broken"), "error")],
)
def test_recovery_failures_keep_distinct_statuses(monkeypatch, failure, status):
    pytest.importorskip("rustformlang")
    from constrained_diffusion import constrain_utils

    def injected(**kwargs):
        if failure is not None:
            raise failure
        return None

    monkeypatch.setattr(constrain_utils, "autocomplete_valid", injected)
    calls = ["neg(1)"]
    _, _, rules = epic_lexical_grammar(calls)
    result = runner().recover(
        {
            "method": "epic_lexical_1",
            "status": "incomplete",
            "epic_lex_rules": rules,
            "token_ids": [0, 126336, 1, 126081],
            "token_emissions": {"0": list(b"neg("), "1": list(b")")},
        },
        calls,
    )
    assert result["recovery_status"] == status
    assert result["recovery_output"] is None


def test_official_recovery_keeps_an_open_tail_without_eos():
    pytest.importorskip("rustformlang")
    calls = ["neg(1)"]
    _, _, rules = epic_lexical_grammar(calls)
    result = runner().recover(
        {
            "method": "epic_lexical_1",
            "status": "incomplete",
            "epic_lex_rules": rules,
            "token_ids": [0],
            "token_emissions": {"0": list(b"neg(1")},
        },
        calls,
    )
    assert result["recovery_output"] == "neg(1)"
    assert result["fixed_fragments_preserved"]
