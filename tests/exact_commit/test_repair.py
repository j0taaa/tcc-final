from itertools import product
from math import fsum
from random import Random

import pytest

from mwpc_exact import CompositionalByteLevelAdapter, ExactBackend, SelectionStatus
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.repair import (
    BYTE_ADAPTER,
    json_repair_grammar,
    prepare_repair,
    repair_json_text,
    repair_tokens,
    strict_json_loads,
    structural_byte_support,
    structural_token_support,
)


@pytest.fixture(scope="module")
def grammar():
    return json_repair_grammar()


def repair(text, grammar, backend, **kwargs):
    return repair_tokens(
        tuple(text.encode()),
        adapter=BYTE_ADAPTER,
        grammar=grammar,
        alternatives=structural_byte_support(text),
        backend=backend,
        **kwargs,
    )


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_minimum_substitution_preserves_an_object_that_order_greedy_flattens(grammar, backend):
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    text = '["a":1,"b":2}'
    exact = repair(text, grammar, backend)
    greedy = repair(text, grammar, backend, method="greedy")
    assert exact.status is SelectionStatus.OPTIMAL
    assert strict_json_loads(exact.output_text) == {"a": 1, "b": 2}
    assert exact.substitution_cost == 1
    assert greedy.substitution_cost == 3
    assert exact.selection.witness_graph_edge_ids
    assert exact.selection.diagnostics["optimization_guarantee"] == "exact_on_support"


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_random_weighted_repair_agrees_with_independent_enumeration(grammar, backend):
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    for seed in range(210000, 210025):
        rng = Random(seed)
        original = '{"a":1,"b":2}'
        rows = structural_byte_support(original)
        draft = bytes(rng.choice(row) for row in rows).decode()
        weights = tuple(float(rng.randrange(4)) for _ in draft)
        options = structural_byte_support(draft)
        valid = []
        for path in product(*options):
            try:
                strict_json_loads(bytes(path).decode())
            except ValueError:
                continue
            valid.append(
                fsum(
                    w
                    for old, new, w in zip(draft.encode(), path, weights, strict=True)
                    if old != new
                )
            )
        result = repair(draft, grammar, backend, weights=weights)
        assert result.status is SelectionStatus.OPTIMAL, seed
        assert result.substitution_cost == min(valid), seed
        assert recognizes_cnf(grammar, tuple(result.output_text.encode())), seed


@pytest.mark.parametrize(
    "text",
    [
        '{ "a" : -12, "b" : [ true, null, false ] }',
        '{"ID":"A\\u00e9\\n\\"","x":{}}',
        "[ ]",
        "{ }",
        "123",
        '"A,[]"',
    ],
)
def test_supported_grammar_and_independent_json_checker_agree(text, grammar):
    assert recognizes_cnf(grammar, tuple(text.encode()))
    result = repair(text, grammar, ExactBackend.PYTHON)
    assert result.status is SelectionStatus.OPTIMAL
    assert result.output_text == text
    assert result.substitution_cost == 0


def test_protected_byte_span_freezes_whole_multi_byte_token(grammar):
    adapter = CompositionalByteLevelAdapter((b'["a"', b'{"a"', b':1,"b":2}', b',1,"b",2]'))
    draft = (0, 2)
    options = ((0, 1), (2, 3))
    result = repair_tokens(
        draft,
        adapter=adapter,
        grammar=grammar,
        alternatives=options,
        protected_byte_spans=((2, 3),),
        backend=ExactBackend.PYTHON,
    )
    assert result.protected_positions == (0,)
    assert result.output_text == '["a",1,"b",2]'
    assert result.substitution_cost == 1
    unprotected = repair_tokens(
        draft, adapter=adapter, grammar=grammar, alternatives=options, backend=ExactBackend.PYTHON
    )
    assert unprotected.status is SelectionStatus.OPTIMAL
    state, _ = prepare_repair(
        draft,
        adapter=adapter,
        grammar=grammar,
        alternatives=options,
        protected_byte_spans=((2, 3),),
    )
    assert state.support.rows[0] == (0,)


def test_structural_support_respects_quotes_escapes_and_missing_vocabulary():
    text = '{"a":"[,\\"}"}'
    rows = structural_byte_support(text)
    assert sum(len(row) > 1 for row in rows) == 3
    adapter = CompositionalByteLevelAdapter((b'["a"', b'{"a"', b":1}", b",1]"))
    assert structural_token_support((0, 2), adapter) == ((0, 1), (2, 3))
    assert structural_token_support((0, 2), adapter, max_variants_per_token=1) == ((0,), (2,))


def test_timeout_infeasibility_and_unsupported_are_separate(grammar):
    late = repair("[1}", grammar, ExactBackend.PYTHON, timeout_seconds=0)
    impossible = repair('{"a":}', grammar, ExactBackend.PYTHON)
    duplicate = repair('{"a":1,"a":2}', grammar, ExactBackend.PYTHON)
    assert late.status is SelectionStatus.TIMEOUT
    assert impossible.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert duplicate.status is SelectionStatus.UNSUPPORTED
    for result in (late, impossible, duplicate):
        assert result.output_text is None and result.selection is None
        assert result.substitution_cost is None


@pytest.mark.parametrize("weights", [(float("nan"),), (-1,), (float("inf"),), (True,)])
def test_invalid_weights_rejected(grammar, weights):
    with pytest.raises((ValueError, TypeError)):
        repair("1", grammar, ExactBackend.PYTHON, weights=weights)


@pytest.mark.parametrize("span", [(-1, 1), (0, 10), (1, 1), (False, 1)])
def test_invalid_protection_is_rejected(grammar, span):
    with pytest.raises((ValueError, TypeError)):
        repair("1", grammar, ExactBackend.PYTHON, protected_byte_spans=(span,))


def test_protected_rows_do_not_hide_invalid_alternatives(grammar):
    with pytest.raises((ValueError, TypeError)):
        prepare_repair(
            (49,),
            adapter=BYTE_ADAPTER,
            grammar=grammar,
            alternatives=((999,),),
            protected_byte_spans=((0, 1),),
        )


def test_cli_convenience_profile():
    assert repair_json_text('["a":1}', backend=ExactBackend.PYTHON).output_text == '{"a":1}'


def test_shared_record_schema_repairs_without_answer_literals():
    grammar = json_repair_grammar(record_schema=True)
    for text in ['{"id":7,"payload":[["a":1,"b":2}]}', '{"id":9,"payload":[["a":8,"b":3}]}']:
        result = repair(text, grammar, ExactBackend.PYTHON)
        assert result.status is SelectionStatus.OPTIMAL
        assert result.substitution_cost == 1
        assert isinstance(strict_json_loads(result.output_text)["payload"][0], dict)


@pytest.mark.parametrize("budget", [-1, float("nan"), float("inf"), True])
def test_text_api_rejects_invalid_deadline(budget):
    with pytest.raises((TypeError, ValueError)):
        repair_json_text("1", timeout_seconds=budget)


def test_late_final_json_validation_discards_certificate(grammar, monkeypatch):
    import mwpc_exact.repair as module

    clock = 0.0
    original = module.strict_json_loads

    def validate(text):
        nonlocal clock
        value = original(text)
        clock = 2.0
        return value

    monkeypatch.setattr(module, "perf_counter", lambda: clock)
    monkeypatch.setattr(module, "strict_json_loads", validate)
    result = repair("1", grammar, ExactBackend.PYTHON, timeout_seconds=1)
    assert result.status is SelectionStatus.TIMEOUT
    assert result.selection is None and result.output_text is None
    assert result.support_specification["rows"] == [[49]]


def test_unreachable_grammar_removal_preserves_exhaustive_small_language():
    from dataclasses import replace

    from mwpc_exact.reference.byte_grammars import lower_ascii_json_value_subset_v1_source
    from mwpc_exact.reference.normalization import normalize_to_cnf
    from mwpc_exact.repair import reachable_source

    full = lower_ascii_json_value_subset_v1_source()
    integer = next(n.symbol_id for n in full.nonterminals if n.name == "Integer")
    full = replace(full, start_nonterminal_id=integer)
    reduced = reachable_source(full)
    assert len(reduced.productions) < len(full.productions)
    old, new = normalize_to_cnf(full).grammar, normalize_to_cnf(reduced).grammar
    for length in range(4):
        for word in product(b"01[]", repeat=length):
            assert recognizes_cnf(old, word) == recognizes_cnf(new, word)


@pytest.mark.parametrize("method", ["exact", "greedy"])
def test_component_profiling_does_not_change_repair(grammar, method):
    from mwpc_exact import ComponentProfiler

    profile = ComponentProfiler(enabled=True)
    plain = repair('["a":1}', grammar, ExactBackend.PYTHON, method=method)
    timed = repair('["a":1}', grammar, ExactBackend.PYTHON, method=method, profiler=profile)
    assert timed.status == plain.status
    assert timed.substitution_cost == plain.substitution_cost
    assert profile.snapshot().measured_component_seconds > 0


def test_unrepresentable_total_weights_are_rejected_at_solver_boundary(grammar):
    with pytest.raises(ValueError, match="maximum complete token-path objective must be finite"):
        repair_tokens(
            (125, 123),
            adapter=BYTE_ADAPTER,
            grammar=grammar,
            alternatives=((125, 91), (123, 93)),
            weights=(1e308, 1e308),
            backend=ExactBackend.PYTHON,
        )
