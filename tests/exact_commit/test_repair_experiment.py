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


def test_metadata_mapping_proxy_serializes_without_deepcopy():
    from dataclasses import dataclass
    from types import MappingProxyType

    from scripts.exact_commit.run_json_repair import system_metadata_dict

    @dataclass
    class System:
        python_version: str
        thread_environment: object

    system = System("3.11", MappingProxyType({"OMP_NUM_THREADS": None}))
    assert system_metadata_dict(system) == {
        "python_version": "3.11",
        "thread_environment": {"OMP_NUM_THREADS": None},
    }


def test_offline_schema_checker_matches_jsonschema_on_valid_and_invalid_values():
    from scripts.exact_commit.run_json_repair import record_schema_valid

    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(SCHEMA)
    values = [None, [], {}, {"id": 1}, {"id": 1, "payload": [], "extra": 0}]
    for number in (True, False, None, "1", 1, -4, 1.0, 1.5):
        for payload in ([], None, [{"a": number, "b": 1}], [{"a": 1}], [3]):
            values.append({"id": number, "payload": payload})
    for value in values:
        assert record_schema_valid(value) == validator.is_valid(value), value


def test_repair_derivatives_match_all_archived_runs():
    from scripts.exact_commit.build_json_repair_results import OUT, outputs

    for name, content in outputs().items():
        assert (OUT / name).read_bytes() == content.encode(), name


@pytest.mark.parametrize("mutation", ["hash", "missing", "duplicate", "support", "evaluation"])
def test_archive_audit_rejects_corruption_and_incomplete_cohorts(tmp_path, mutation):
    import gzip
    import hashlib
    import json
    import shutil

    from scripts.exact_commit.run_json_repair import read_archive

    source = ROOT / "docs/artifacts/raw/m21_repair_v1/pilot"
    for name in ("metadata.json", "manifest.json", "rows.jsonl.gz"):
        shutil.copyfile(source / name, tmp_path / name)
    archive = tmp_path / "rows.jsonl.gz"
    with gzip.open(archive, "rt") as file:
        rows = [json.loads(line) for line in file]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = rows[0]
    elif mutation == "support":
        rows[0]["support_rows"][0].append(255)
    else:
        rows[0]["evaluation"]["semantic_success"] = not rows[0]["evaluation"]["semantic_success"]
    with gzip.open(archive, "wt") as file:
        file.writelines(json.dumps(row) + "\n" for row in rows)
    if mutation != "hash":
        manifest_path = tmp_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.update(
            rows=len(rows), rows_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()
        )
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        read_archive(tmp_path)
