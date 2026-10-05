from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from itertools import product
from random import Random

import pytest
from scripts.exact_commit.build_probability_audit_results import check_capture
from scripts.exact_commit.capture_mdlm_probability import planned_case_ids
from scripts.exact_commit.probability_audit_controls import (
    ACCEPT,
    START,
    array_step,
    compile_array_plan,
)
from scripts.exact_commit.run_conflict_real import write
from scripts.exact_commit.run_probability_audit import (
    decode_input,
    encode_input,
    prepare_input,
    reference,
    validate_partition,
)
from tests.exact_commit.test_budget_bounds import state_for

from mwpc_exact import ExactBackend
from mwpc_exact.mass_certificate import (
    PosteriorScope,
    ProbabilityInput,
    verify_mass_proof,
)
from mwpc_exact.mass_solver import probability_partition
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf


def json_arrays(raw, one_child):
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return False
    pending = [value]
    while pending:
        item = pending.pop()
        if not isinstance(item, list) or (one_child and len(item) > 1):
            return False
        pending.extend(item)
    return bool(raw) and all(byte in b"[]," for byte in raw)


def array_grammar(one_child):
    builder = _SourceGrammarBuilder(("S", "L"), start="S")
    builder.rule("S", b"[]")
    builder.rule("S", b"[", "S" if one_child else "L", b"]")
    if not one_child:
        builder.rule("L", "S")
        builder.rule("L", "S", b",", "L")
    return normalize_to_cnf(builder.build()).grammar


@pytest.mark.parametrize("one_child", (False, True))
def test_streaming_array_control_agrees_with_independent_json_for_all_short_byte_strings(one_child):
    for length in range(1, 9):
        for word in product(b"[],", repeat=length):
            raw = bytes(word)
            assert (array_step(START, raw, one_child=one_child) == ACCEPT) == json_arrays(
                raw, one_child
            ), raw
    for raw in (b"", b"[ ]", b"[0]", b"null", b"[[],]", b"[][[]]"):
        assert array_step(START, raw, one_child=one_child) is None


@pytest.mark.parametrize("seed", range(310000, 310032))
def test_original_token_bruteforce_and_exact_transfer_bound_partial_cfg_inference(seed):
    rng = Random(seed)
    one_child = bool(seed % 2)
    emissions = (b"[", b"]", b",", b"[]", b"[[]]", b"[]", b"x")
    slots = 2 + seed % 2
    full_rows = (tuple(range(len(emissions))),) * slots
    weights = []
    for _ in full_rows:
        row = [rng.randrange(8) for _ in emissions]
        row[-1] += 1  # each full row has positive total, including invalid mass
        weights.append(tuple(Fraction(w, sum(row)) for w in row))
    full_probabilities = tuple(weights)
    exact = {}
    for tokens in product(*full_rows):
        raw = b"".join(emissions[t] for t in tokens)
        if json_arrays(raw, one_child):
            mass = Fraction(1)
            for row, token in zip(weights, tokens, strict=True):
                mass *= row[token]
            if mass:
                exact[tokens] = mass
    z = sum(exact.values(), Fraction())
    plan = compile_array_plan(emissions, full_rows, one_child=one_child)
    assert plan.forward(full_probabilities) == (z, len(exact)), seed
    suffix = plan.backward(full_probabilities)
    assert suffix[0][START] == z, seed
    if z:
        for _ in range(8):
            assert plan.sample(full_probabilities, suffix, rng) in exact, seed

    rows = tuple(tuple(sorted(rng.sample(range(len(emissions)), 3))) for _ in full_rows)
    base = state_for((b"[]",), emissions, rows, ())
    state = replace(base, grammar=array_grammar(one_child))
    predictive = ProbabilityInput(
        state, tuple(tuple(weights[i][t] for t in row) for i, row in enumerate(rows))
    )
    represented = {
        t: m
        for t, m in exact.items()
        if all(token in row for token, row in zip(t, rows, strict=True))
    }
    zs = sum(represented.values(), Fraction())
    last_lower, last_upper = Fraction(), Fraction(1)
    for limit in (0, 1, 4, 128):
        proof = probability_partition(
            predictive, max_oracle_calls=limit, requested_tv=Fraction(), backend=ExactBackend.PYTHON
        )
        result = verify_mass_proof(proof, expected_input=predictive)
        assert (
            last_lower
            <= result.lower
            <= zs
            <= result.upper(PosteriorScope.REPRESENTED)
            <= last_upper
        ), seed
        assert result.lower <= z <= result.upper(PosteriorScope.FULL), seed
        assert result.omitted == 1 - predictive.box_mass(rows), seed
        last_lower, last_upper = result.lower, result.upper(PosteriorScope.REPRESENTED)
        if result.lower:
            assert 1 - result.lower / zs <= result.tv_bound(PosteriorScope.REPRESENTED), seed
            assert 1 - result.lower / z <= result.tv_bound(PosteriorScope.FULL), seed
            for event_token in range(len(emissions)):
                lo, hi = result.event_interval(
                    lambda t, token=event_token: t[0] == token, PosteriorScope.FULL
                )
                event_mass = sum(
                    (m / z for t, m in exact.items() if t[0] == event_token), Fraction()
                )
                assert lo <= event_mass <= hi, seed
        if limit == 128:
            assert result.lower == zs and result.unresolved == 0, seed


class ForcedTicket(Random):
    def __init__(self, ticket):
        self.ticket = ticket

    def randrange(self, stop):
        assert 0 <= self.ticket < stop
        return self.ticket


def test_exact_rational_certificate_sampling_preserves_every_integer_ticket_and_alias():
    state = state_for((b"a",), (b"a", b"a", b"b"), ((0, 1, 2),), ())
    predictive = ProbabilityInput(state, ((Fraction(1, 8), Fraction(3, 8), Fraction(1, 2)),))
    checked = verify_mass_proof(
        probability_partition(predictive, requested_tv=Fraction(), backend=ExactBackend.PYTHON)
    )
    samples = [
        checked.sample(ForcedTicket(k), scope=PosteriorScope.FULL, max_tv=Fraction())
        for k in range(4)
    ]
    assert samples.count((0,)) == 1 and samples.count((1,)) == 3


def test_reweighting_checks_actual_full_posterior_and_never_reuses_old_admission():
    state = state_for((b"ab", b"ba"), (b"a", b"b", b"x"), ((0, 1, 2),) * 2, ())
    original = ProbabilityInput(state, ((Fraction(9, 10), Fraction(1, 10), Fraction()),) * 2)
    proof = probability_partition(
        original, max_oracle_calls=1, requested_tv=Fraction(1), backend=ExactBackend.PYTHON
    )
    changed = ProbabilityInput(
        state,
        (
            (Fraction(1, 100), Fraction(98, 100), Fraction(1, 100)),
            (Fraction(98, 100), Fraction(1, 100), Fraction(1, 100)),
        ),
    )
    checked = verify_mass_proof(proof, reweight=changed)
    exact_mass = Fraction(1, 10000) + Fraction(9604, 10000)
    assert checked.lower <= exact_mass <= checked.upper(PosteriorScope.FULL)
    assert 1 - checked.lower / exact_mass <= checked.tv_bound(PosteriorScope.FULL)


def test_low_grammar_probability_and_structural_validity_do_not_certify_semantic_accuracy():
    state = state_for((b"wrong",), (b"wrong", b"right"), ((0, 1),), ())
    tiny = Fraction(1, 10**100)
    checked = verify_mass_proof(
        probability_partition(
            ProbabilityInput(state, ((tiny, 1 - tiny),)),
            requested_tv=Fraction(),
            backend=ExactBackend.PYTHON,
        )
    )
    assert checked.lower == tiny and checked.tv_bound(PosteriorScope.FULL) == 0
    assert checked.sample(Random(31), scope=PosteriorScope.FULL, max_tv=Fraction()) == (0,)
    # A zero conditional approximation error says nothing about the independent
    # task label (token 1). No enormous rejection-sampling trial is performed.


def test_capture_inventory_counts_actual_config_and_rejects_colliding_ids():
    config = {"slots": [4, 8, 16], "probes": [{"id": str(n)} for n in range(6)]}
    assert len(planned_case_ids(config)) == 18
    bad = deepcopy(config)
    bad["probes"].append({"id": "0"})
    with pytest.raises(ValueError, match="unique"):
        planned_case_ids(bad)
    for slots in ([1, 1], [True], [1.0], [0], []):
        with pytest.raises(ValueError, match="positive"):
            planned_case_ids({"slots": slots, "probes": [{"id": "a"}]})


def test_full_reference_refuses_missing_alias_even_when_emitted_bytes_are_retained():
    state = replace(
        state_for((b"[]",), (b"[]", b"[]"), ((0,),), ()),
        grammar=array_grammar(True),
    )
    with pytest.raises(ValueError, match="compatible original token"):
        reference(ProbabilityInput(state, ((Fraction(1, 2),),)), True, 31, 1)


def test_saved_audit_input_rejects_boolean_and_float_rational_aliases():
    state = state_for((b"a",), (b"a",), ((0,),), ())
    packet = encode_input(ProbabilityInput(state, ((Fraction(1),),)))
    assert decode_input(packet).fingerprint == packet["input_fingerprint"]
    for alias in (True, 1.0):
        for column in (0, 1):
            bad = deepcopy(packet)
            bad["probabilities"][0][0][column] = alias
            with pytest.raises((ValueError, TypeError)):
                decode_input(bad)


def test_audit_capture_preserves_original_probabilities_and_rejects_fabricated_softmax(tmp_path):
    import numpy as np

    write(tmp_path / "tokenizer-pieces.json.gz", ["[", "]", ",", "x", None])
    logits = np.array([[0, 1, -1, 2, 3]] * 4, dtype=np.float32)
    scores = logits.astype(np.float64)
    scores[:, 4] = -np.inf
    probabilities = np.exp(scores - scores.max(axis=1, keepdims=True))
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    np.savez(tmp_path / "case.npz", logits=logits, probabilities=probabilities)
    config = {"mask_token_id": 4, "top_k": 1}
    case = {
        "slots": 4,
        "array_file": "case.npz",
        "canvas": [0, None, None, None, None],
        "masked_positions": [1, 2, 3, 4],
        "probe": {"grammar": "recursive_one_child_arrays", "prefix": "[", "suffix": ""},
    }
    inputs, _ = prepare_input(tmp_path, case, config)
    full = [Fraction(float(p)) for p in probabilities[0]]
    for row, values in zip(inputs.state.support.rows[1:], inputs.probabilities[1:], strict=True):
        assert row == (0, 1, 3)
        assert values == tuple(full[t] / sum(full) for t in row)
        assert sum(values) < 1
    exact = reference(inputs, True, 31, 1)
    proof = probability_partition(
        inputs, requested_tv=Fraction(1), max_oracle_calls=4, backend=ExactBackend.PYTHON
    )
    checked = validate_partition(
        inputs, proof, Fraction(*exact["valid_mass"]), True, 31, Fraction(1)
    )
    # Five one-byte brackets cannot form a balanced array: preserve refusal.
    assert exact["valid_mass"] == [0, 1] and not checked["admitted"]
    assert proof["status"] == "zero_valid_probability_on_support"
    case["canvas"] = [0, 0, None, None, None, None]
    case["masked_positions"] = [2, 3, 4, 5]
    case["probe"]["prefix"] = "[["
    inputs, normalization = prepare_input(tmp_path, case, config)
    packet = {
        **encode_input(inputs),
        "case": case,
        "normalization": normalization,
        "source_array_sha256": sha256((tmp_path / "case.npz").read_bytes()).hexdigest(),
    }
    check_capture(tmp_path, packet, inputs, config)
    changed_adapter = replace(
        inputs.state.tokenizer_adapter, emissions=(b"[", b"]", b",", b"y", None)
    )
    changed_input = ProbabilityInput(
        replace(inputs.state, tokenizer_adapter=changed_adapter), inputs.probabilities
    )
    with pytest.raises(ValueError, match="tokenizer bytes"):
        check_capture(tmp_path, packet, changed_input, config)
    exact = reference(inputs, True, 31, 1)
    proof = probability_partition(
        inputs, requested_tv=Fraction(1), max_oracle_calls=4, backend=ExactBackend.PYTHON
    )
    checked = validate_partition(
        inputs, proof, Fraction(*exact["valid_mass"]), True, 31, Fraction(1)
    )
    assert checked["admitted"]
    forged = deepcopy(proof)
    forged["envelope"]["lower"] = [1, 1]
    with pytest.raises(ValueError):
        validate_partition(inputs, forged, Fraction(*exact["valid_mass"]), True, 31, Fraction(1))
    probabilities[:, 0] += 0.01
    np.savez(tmp_path / "case.npz", logits=logits, probabilities=probabilities)
    with pytest.raises(ValueError, match="softmax"):
        prepare_input(tmp_path, case, config)
