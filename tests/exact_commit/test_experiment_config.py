from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from mwpc_exact.experiments import (
    RESOLVED_CONFIG_ARTIFACT_KIND,
    RESOLVED_CONFIG_FILENAME,
    ExperimentConfig,
    ExperimentKind,
    load_experiment_config,
    save_resolved_config,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRECTORY = REPOSITORY_ROOT / "configs/experiments"
CONFIGS = {
    ExperimentKind.CORRECTNESS: CONFIG_DIRECTORY / "q1_correctness_smoke_v1.toml",
    ExperimentKind.HEURISTIC_GAP: CONFIG_DIRECTORY / "q2_heuristic_gap_smoke_v1.toml",
    ExperimentKind.FINITE_SLOTS: CONFIG_DIRECTORY / "q3_finite_slots_smoke_v1.toml",
    ExperimentKind.SCALING: CONFIG_DIRECTORY / "q4_scaling_smoke_v1.toml",
    ExperimentKind.END_TO_END: CONFIG_DIRECTORY / "q5_end_to_end_smoke_v1.toml",
}


@pytest.mark.parametrize(("question", "path"), CONFIGS.items())
def test_all_research_questions_have_complete_immutable_configs(
    question: ExperimentKind,
    path: Path,
) -> None:
    config = load_experiment_config(path)

    assert config.question is question
    assert config.publication_mode is False
    assert config.exactness_scope == "exact_on_support"
    assert config.exactness_guarantee == "per_step"
    assert config.require_independent_certificate is True
    assert config.finite_slots is True
    assert config.support_top_k <= config.support_k_max
    assert config.model_id
    assert config.model_revision
    assert config.tokenizer_id
    assert config.tokenizer_revision
    assert config.grammar_id
    assert config.grammar_source
    assert config.grammar_revision
    assert config.grammar_hash_policy.startswith("sha256_")
    assert config.seeds
    assert config.solver_timeout_seconds > 0.0
    assert config.run_timeout_seconds >= config.solver_timeout_seconds
    assert config.cpu_threads >= 1
    assert config.parameters["raw_output_root"] == (
        f"results/raw/{config.experiment_id}"
    )
    assert len(config.config_sha256) == 64


def test_normalized_hash_ignores_mapping_order_and_toml_representation() -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])
    normalized = config.to_dict()
    reordered = dict(reversed(tuple(normalized.items())))
    reparsed = ExperimentConfig.from_dict(reordered)

    assert reparsed == config
    assert reparsed.config_sha256 == config.config_sha256
    assert reparsed.to_dict()["hardware"] == {
        "device": "cpu",
        "dtype": "float64",
        "cpu_threads": 1,
        "cuda_device": None,
        "synchronize_cuda": False,
    }


def test_rerun_saves_byte_identical_comparable_resolved_metadata(tmp_path: Path) -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])

    first = save_resolved_config(config, tmp_path / "run-1")
    second = save_resolved_config(config, tmp_path / "run-2")
    repeated = save_resolved_config(config, tmp_path / "run-1")

    assert first.name == second.name == repeated.name == RESOLVED_CONFIG_FILENAME
    assert first.read_bytes() == second.read_bytes() == repeated.read_bytes()
    artifact = json.loads(first.read_text(encoding="utf-8"))
    assert artifact == {
        "artifact_kind": RESOLVED_CONFIG_ARTIFACT_KIND,
        "schema_version": 1,
        "config_sha256": config.config_sha256,
        "resolved_config": config.to_dict(),
    }


def test_resolved_config_refuses_conflicting_overwrite(tmp_path: Path) -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])
    save_resolved_config(config, tmp_path)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        save_resolved_config(replace(config, repetitions=2), tmp_path)


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    (
        ("exactness", "scope", "globally_exact", "exact_on_support"),
        ("exactness", "require_independent_certificate", False, "certificate"),
        ("support", "finite_slots", False, "finite token slots"),
        ("timeouts", "solver_seconds", 0.0, "finite and positive"),
    ),
)
def test_scientific_config_contract_fails_closed(
    section: str,
    field: str,
    value: object,
    message: str,
) -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])
    data = config.to_dict()
    nested = data[section]
    assert isinstance(nested, dict)
    nested[field] = value

    with pytest.raises(ValueError, match=message):
        ExperimentConfig.from_dict(data)


def test_unknown_fields_are_rejected_instead_of_silently_ignored() -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])
    data = config.to_dict()
    data["unversioned_override"] = True

    with pytest.raises(ValueError, match="unknown experiment config fields"):
        ExperimentConfig.from_dict(data)


def test_direct_construction_rejects_boolean_schema_version() -> None:
    config = load_experiment_config(CONFIGS[ExperimentKind.CORRECTNESS])

    with pytest.raises(TypeError, match="schema_version must be an integer"):
        replace(config, schema_version=True)
