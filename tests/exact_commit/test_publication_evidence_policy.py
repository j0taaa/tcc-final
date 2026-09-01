from __future__ import annotations

import tomllib
from pathlib import Path

from mwpc_exact.experiments import load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PUBLICATION_CONFIGS = {
    "q2": REPOSITORY_ROOT / "configs/experiments/q2_real_state_publication_v1.toml",
    "q4": REPOSITORY_ROOT / "configs/experiments/q4_scaling_publication_v1.toml",
    "q5": REPOSITORY_ROOT / "configs/experiments/q5_structured_publication_v4.toml",
}
LEGACY_FULL_CONFIGS = tuple(
    REPOSITORY_ROOT / "configs/experiments" / name
    for name in (
        "q1_correctness_v1.toml",
        "q2_heuristic_gap_v1.toml",
        "q3_finite_slots_v1.toml",
        "q4_scaling_v1.toml",
        "q5_end_to_end_v1.toml",
        "q5_timing_v1.toml",
    )
)


def test_existing_full_runs_remain_diagnostic() -> None:
    assert all(
        load_experiment_config(path).publication_mode is False for path in LEGACY_FULL_CONFIGS
    )


def test_publication_campaigns_are_predeclared_with_a_new_bundle() -> None:
    configs = {name: load_experiment_config(path) for name, path in PUBLICATION_CONFIGS.items()}

    assert all(config.publication_mode is True for config in configs.values())
    assert {config.parameters["publication_bundle_id"] for config in configs.values()} == {
        "m125_publication_results_v1"
    }
    assert "t1203_final_results_v1" not in {
        config.parameters["publication_bundle_id"] for config in configs.values()
    }

    q2 = configs["q2"]
    assert q2.parameters["expected_snapshot_count"] == 30
    assert q2.parameters["snapshots_per_task_seed"] == 5
    assert q2.parameters["require_common_snapshot_hash"] is True

    q4 = configs["q4"]
    assert q4.repetitions == 10
    assert q4.parameters["minimum_repetitions_for_distribution"] == 10
    assert (
        q4.parameters["graph_size_scale_interpretation"]
        == "compound_support_width_and_token_byte_length"
    )

    q5 = configs["q5"]
    assert q5.repetitions == 10
    assert len(q5.seeds) == 3
    assert q5.parameters["require_regular_cover_selector_call"] is True
    assert q5.parameters["require_epic_batch_larger_than_one"] is True
    assert q5.parameters["snapshot_capture_steps_per_task_seed"] == 5


def test_structured_task_manifest_freezes_two_nontrivial_targets() -> None:
    manifest_path = REPOSITORY_ROOT / "configs/experiments/q5_structured_tasks_v4.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    tasks = manifest["tasks"]

    assert manifest["schema_version"] == 1
    assert manifest["task_set_id"] == "q5_structured_tasks_v4"
    assert [task["task_id"] for task in tasks] == ["json_x_zero", "fenced_add_dsl"]
    assert all(len(task["target_utf8"]) >= 3 for task in tasks)
    assert all(task["grammar_kind"] == "literal_utf8_cfg" for task in tasks)
    assert [(task["generation_length"], task["steps"]) for task in tasks] == [
        (16, 8),
        (12, 6),
    ]


def test_decision_records_claim_boundaries_and_resource_rules() -> None:
    decision = (REPOSITORY_ROOT / "docs/decisions/0016-publication-evidence-tier.md").read_text(
        encoding="utf-8"
    )

    for question in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        assert f"| {question} |" in decision
    for required in (
        "publication_mode=false",
        "publication_mode=true",
        "m125_publication_results_v1",
        "TIMEOUT",
        "INFEASIBLE_ON_SUPPORT",
        "exact_on_support",
        "2 GiB",
        "local-only",
    ):
        assert required in decision


def test_q5_amendment_records_rejected_pilot_without_weakening_gates() -> None:
    amendment = (
        REPOSITORY_ROOT / "docs/decisions/0017-q5-publication-pilot-amendment.md"
    ).read_text(encoding="utf-8")

    for required in (
        "50 times",
        "34 constrained",
        "q5_structured_publication_v2.toml",
        "regular_cover_selector_calls > 0",
        "cardinality greater than one",
        "independently valid certificate",
        "exact_on_support",
    ):
        assert required in amendment

    task_schedule = (
        REPOSITORY_ROOT / "docs/decisions/0018-q5-task-specific-schedules.md"
    ).read_text(encoding="utf-8")
    for required in (
        "70 EPIC selector",
        "24",
        "no ordinary regular-cover selector call",
        "stratified by task",
        "exact_on_support",
    ):
        assert required in task_schedule

    model_aligned = (
        REPOSITORY_ROOT / "docs/decisions/0019-q5-model-aligned-dsl-task.md"
    ).read_text(encoding="utf-8")
    for required in (
        "initial-logit probe",
        "ten aligned ordinary token proposals",
        "12-slot",
        "real EPIC selector call",
        "exact_on_support",
    ):
        assert required in model_aligned
