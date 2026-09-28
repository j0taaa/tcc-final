"""CPU gates for using the real EPIC path on the tool language."""

import importlib.util
import json
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from mwpc_research.tool_parser import catalog_byte_grammar, epic_byte_grammar

ROOT = Path(__file__).resolve().parents[2]


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "epic_tool_runner", ROOT / "scripts/exact_commit/epic_tool_runner.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_epic_byte_grammar_preserves_language(monkeypatch):
    pytest.importorskip("rustformlang")
    from constrained_diffusion.constrain_utils import EOS, compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada.generate_constrained import check_valid
    from rustformlang.cfg import CFG

    monkeypatch.setenv("CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER", "1")
    calls = ("aa", "aba", "bba", "b", "bbb")
    text, start, rules = epic_byte_grammar(catalog_byte_grammar(calls))
    grammar = CFG.from_text(text, start).to_normal_form()
    lex_map = compile_lex_map(rules)
    for n in range(1, 5):
        for chars in product("ab", repeat=n):
            word = "".join(chars)
            assert (not check_valid([word, EOS], grammar, lex_map, grammar.get_terminals())) == (
                word in calls
            ), word


@pytest.mark.parametrize("method", ["epic_native_1", "epic_domains_1"])
def test_real_upstream_batch_executes_and_hooks_are_restored(method, monkeypatch):
    torch = pytest.importorskip("torch")
    from constrained_diffusion.eval.dllm.models.llada import generate_constrained as upstream

    class Tokenizer:
        special_tokens_map: ClassVar = {"eos_token": "<eos>"}

        def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
            if isinstance(ids, torch.Tensor):
                ids = ids.tolist()
            if isinstance(ids, int):
                ids = [ids]
            words = {0: "a", 1: "b", 2: "prompt", 126081: "<eos>", 126336: "<mask>"}
            return "".join(words[t] for t in ids if not skip_special_tokens or t < 126081)

        def batch_decode(self, rows):
            return [self.decode(row) for row in rows]

    class Model:
        device = "cpu"
        config = SimpleNamespace(vocab_size=126337)

        def __call__(self, tokens):
            logits = torch.full((*tokens.shape, 126337), -100.0)
            for p, token in enumerate([2, 0, 1, 126081, 126081]):
                logits[0, p, token] = 20.0
            return SimpleNamespace(logits=logits)

    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH", "0")
    original = upstream.select_batch_with_regular_cover
    result = load_runner().run_epic(
        model=Model(),
        tokenizer=Tokenizer(),
        prompt=[2],
        grammar=catalog_byte_grammar(("ab", "ba")),
        rows=[[0, 1], [0, 1], [126081], [126081]],
        calls=["ab", "ba"],
        config={
            "max_forwards": 4,
            "slots": 4,
            "max_generation_seconds": 20,
            "epic_max_resamples": 100,
        },
        method=method,
    )
    assert result["status"] == "complete", result
    assert result["output"] == "ab"
    assert result["forwards"] == 1
    assert result["epic_counters"]["batch_calls"] == 1
    assert result["epic_counters"]["batch_selected"] == 2
    assert not result["epic_batch_errors"]
    assert upstream.select_batch_with_regular_cover is original
    import os

    assert os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH"] == "0"


def test_comparison_uses_all_frozen_requests_and_two_schedules():
    old = json.loads(
        (ROOT / "configs/experiments/m22_tool_parser_confirmation_v1.json").read_text()
    )
    new = json.loads((ROOT / "configs/experiments/m23_epic_confirmation_v1.json").read_text())
    repeat = json.loads((ROOT / "configs/experiments/m23_epic_repeat_v1.json").read_text())
    assert new["tasks"] == repeat["tasks"] == old["tasks"]
    assert new["methods"] == list(reversed(repeat["methods"]))
    assert set(new["methods"]) == {
        "exact",
        "epic_native_1",
        "epic_native_4",
        "epic_domains_1",
        "epic_domains_4",
        "epic_native_24",
        "epic_domains_24",
    }
    for key in ("model_id", "revision", "seed", "slots", "max_forwards", "quantization"):
        assert new[key] == repeat[key] == old[key]


def test_structural_evaluation_allows_whitespace_without_repair_or_execution():
    from mwpc_research.tool_screen import normalize_tool_call

    assert normalize_tool_call(" sub( mul(3,\n 1), 1 ) ") == "sub(mul(3,1),1)"
    for invalid in (
        "sub(mul(3,1),1",
        "s ub(1,2)",
        "add(True,1)",
        "add(x,1)",
        "__import__('os')",
        "add(a=1,b=2)",
        "1",
        "add(1,2); exit()",
    ):
        assert normalize_tool_call(invalid) is None
