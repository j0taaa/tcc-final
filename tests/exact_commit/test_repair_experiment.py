import tomllib
from pathlib import Path
from time import perf_counter

import pytest
from scripts.exact_commit.run_json_repair import SCHEMA, cases, enumerate_min_edits, evaluate

from mwpc_exact.repair import BYTE_ADAPTER, structural_byte_support

ROOT = Path(__file__).resolve().parents[2]


def test_controlled_cohorts_are_disjoint_and_retain_all_error_families():
    configs = [
        tomllib.loads((ROOT / f"configs/experiments/m21_repair_{name}_v1.toml").read_text())
        for name in ("pilot", "confirmation")
    ]
    pilot, confirm = map(cases, configs)
    assert not {c["document_id"] for c in pilot} & {c["document_id"] for c in confirm}
    assert len(pilot) == 24 and len(confirm) == 120
    for cohort in (pilot, confirm):
        assert {c["family"] for c in cohort} == {
            "valid",
            "opening",
            "closing",
            "separator",
            "missing_suffix",
            "semantic",
        }
        assert all(c["draft"] == c["draft"].strip() for c in cohort)


def test_semantic_checker_ignores_object_key_order_but_not_type_or_missing_data():
    pytest.importorskip("jsonschema")
    target = {"id": 1, "payload": [{"a": 3, "b": 4}]}
    assert evaluate('{"payload":[{"b":4,"a":3}],"id":1}', target)["semantic_success"]
    for candidate in [
        '{"id":true,"payload":[{"a":3,"b":4}]}',
        '{"id":1,"payload":[]}',
        '{"id":1,"id":1,"payload":[{"a":3,"b":4}]}',
    ]:
        assert not evaluate(candidate, target)["semantic_success"]


def test_independent_enumerator_finds_the_minimum_without_cfg():
    jsonschema = pytest.importorskip("jsonschema")
    text = '{"id":7,"payload":[["a":1,"b":2}]}'
    result = enumerate_min_edits(
        tuple(text.encode()),
        structural_byte_support(text),
        BYTE_ADAPTER,
        jsonschema.Draft202012Validator(SCHEMA),
        perf_counter() + 2,
    )
    assert result["status"] == "optimal"
    assert result["substitution_cost"] == 1
    assert evaluate(result["output_text"], {"id": 7, "payload": [{"a": 1, "b": 2}]})[
        "semantic_success"
    ]
    expired = enumerate_min_edits(
        tuple(text.encode()),
        structural_byte_support(text),
        BYTE_ADAPTER,
        jsonschema.Draft202012Validator(SCHEMA),
        perf_counter() - 1,
    )
    assert expired["status"] == "timeout" and expired["output_text"] is None
