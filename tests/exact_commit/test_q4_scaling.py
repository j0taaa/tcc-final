from __future__ import annotations

import json
from pathlib import Path

import pytest

from mwpc_exact.backend import ExactBackend
from mwpc_exact.experiments import ExperimentKind, load_experiment_config
from mwpc_exact.types import SolveStatus, SupportKind
from mwpc_research.q4_scaling import (
    Q4_AXES,
    Q4Measurement,
    ScalingPoint,
    make_scaling_points,
    measure_scaling_point,
    run_bounded_measurement,
    run_q4_scaling,
    write_q4_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q4_scaling_v1.toml"


def _small_point() -> ScalingPoint:
    return ScalingPoint(
        case_id="slot_count-0001",
        axis="slot_count",
        axis_value=1,
        slot_count=1,
        support_kind=SupportKind.TOP_K,
        support_width=1,
        top_k=1,
        grammar_production_count=4,
        token_byte_length=1,
        proposal_count=1,
        vocabulary_size=3,
        seed=1104,
    )


def _timeout_row(point: ScalingPoint, backend: ExactBackend, repetition: int) -> Q4Measurement:
    return Q4Measurement(
        point=point,
        backend=backend,
        repetition=repetition,
        status=SolveStatus.TIMEOUT,
        censored=True,
        censor_reason="injected_timeout",
        successful_runtime_seconds=None,
        observed_profile=None,
        worker_wall_seconds=0.01,
        peak_rss_bytes=None,
        address_space_limit_bytes=1024,
        grammar_sha256="grammar",
        represented_support_sha256=None,
        exactness_scope=None,
        objective_value=None,
        selected_proposal_ids=None,
        witness_token_ids=None,
        witness_terminal_labels=None,
        witness_graph_edge_ids=None,
        certificate_valid=None,
        error_type="TimeoutError",
        error_message="injected",
    )


def test_q4_config_freezes_all_required_scaling_axes_and_limits() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config.question is ExperimentKind.SCALING
    assert config.publication_mode is False
    assert config.exactness_scope == "exact_on_support"
    assert config.parameters["backends"] == ("python", "rust")
    assert config.parameters["max_address_space_mib"] == 2048
    assert config.parameters["record_chart_size"] is True
    assert config.parameters["record_graph_size"] is True
    assert set(Q4_AXES) == {
        "slot_count",
        "top_k",
        "graph_size_scale",
        "grammar_production_count",
        "token_byte_length",
        "proposal_count",
    }


def test_scaling_points_change_one_axis_and_graph_size_is_explicit() -> None:
    points = make_scaling_points(
        seed=1104,
        vocabulary_size=5,
        baseline_slot_count=2,
        baseline_top_k=2,
        baseline_grammar_production_count=4,
        baseline_token_byte_length=1,
        baseline_proposal_count=2,
        slot_counts=(1, 3),
        top_k_values=(1, 3),
        graph_size_scales=(1, 3),
        grammar_production_counts=(4, 8),
        token_byte_lengths=(1, 3),
        proposal_counts=(1, 3),
    )

    assert len(points) == 12
    assert set(point.axis for point in points) == set(Q4_AXES)
    graph_points = [point for point in points if point.axis == "graph_size_scale"]
    assert all(point.support_kind.value == "explicit" for point in graph_points)
    assert [(point.support_width, point.token_byte_length) for point in graph_points] == [
        (1, 1),
        (3, 3),
    ]
    assert all(point.top_k is None for point in graph_points)


def test_python_measurement_records_breakdown_sizes_ram_and_certificate() -> None:
    row = measure_scaling_point(
        _small_point(),
        ExactBackend.PYTHON,
        0,
        solver_timeout_seconds=1.0,
        address_space_limit_bytes=2 * 1024**3,
    )

    assert row.status is SolveStatus.OPTIMAL
    assert row.censored is False
    assert row.successful_runtime_seconds is not None
    assert row.peak_rss_bytes is not None and row.peak_rss_bytes > 0
    assert row.certificate_valid is True
    assert row.objective_value == 1.0
    assert row.witness_token_ids is not None
    assert row.witness_terminal_labels is not None
    assert row.witness_graph_edge_ids is not None
    assert row.observed_profile is not None
    timings = row.observed_profile["timings_seconds"]
    sizes = row.observed_profile["sizes"]
    assert isinstance(timings, dict)
    assert isinstance(sizes, dict)
    components = timings["components"]
    counters = sizes["counters"]
    assert isinstance(components, dict)
    assert isinstance(counters, dict)
    for name in (
        "support_construction",
        "token_lattice_construction",
        "byte_lattice_expansion",
        "parser",
        "backtracking",
        "validation",
    ):
        assert components[name] >= 0.0
    for name in (
        "chart_entries",
        "token_lattice_node_count",
        "token_lattice_edge_count",
        "terminal_graph_node_count",
        "terminal_graph_edge_count",
    ):
        assert counters[name] > 0


def test_isolated_worker_round_trips_nested_profile_and_scope() -> None:
    row = run_bounded_measurement(
        _small_point(),
        ExactBackend.PYTHON,
        0,
        5.0,
        2 * 1024**3,
    )

    assert row.status is SolveStatus.OPTIMAL
    assert row.error_type is None
    assert row.observed_profile is not None
    assert row.exactness_scope is not None
    assert row.exactness_scope["kind"] == "top_k"
    assert row.worker_wall_seconds >= row.successful_runtime_seconds


def test_timeouts_remain_censored_and_never_enter_plot_artifact(tmp_path: Path) -> None:
    point = _small_point()

    def timeout_runner(
        requested_point: ScalingPoint,
        backend: ExactBackend,
        repetition: int,
        _timeout_seconds: float,
        _address_space_limit_bytes: int,
    ) -> Q4Measurement:
        return _timeout_row(requested_point, backend, repetition)

    result = run_q4_scaling(
        (point,),
        backends=(ExactBackend.PYTHON, ExactBackend.RUST),
        repetitions=1,
        solver_timeout_seconds=1.0,
        run_timeout_seconds=10.0,
        address_space_limit_bytes=1024,
        run_metadata={"test": "censoring"},
        bounded_runner=timeout_runner,
    )
    raw_path, plot_path, summary_path = write_q4_artifacts(result, tmp_path)
    raw_rows = [json.loads(line) for line in raw_path.read_text().splitlines()]
    summary = json.loads(summary_path.read_text())

    assert len(raw_rows) == 2
    assert all(row["status"] == "timeout" for row in raw_rows)
    assert all(row["censored"] is True for row in raw_rows)
    assert all(row["successful_runtime_seconds"] is None for row in raw_rows)
    assert plot_path.read_text() == ""
    assert summary["timeout_count"] == 2
    assert summary["plot_ready_runtime_count"] == 0
    assert summary["timeout_plot_runtime_count"] == 0
    assert summary["censoring_integrity"] is True

    with pytest.raises(FileExistsError):
        write_q4_artifacts(result, tmp_path)


def test_optimal_row_cannot_omit_independently_validated_witness() -> None:
    point = _small_point()

    with pytest.raises(ValueError, match="validated complete witness"):
        Q4Measurement(
            point=point,
            backend=ExactBackend.PYTHON,
            repetition=0,
            status=SolveStatus.OPTIMAL,
            censored=False,
            censor_reason=None,
            successful_runtime_seconds=0.1,
            observed_profile={},
            worker_wall_seconds=0.2,
            peak_rss_bytes=1,
            address_space_limit_bytes=1024,
            grammar_sha256="grammar",
            represented_support_sha256="support",
            exactness_scope={"kind": "top_k"},
            objective_value=1.0,
            selected_proposal_ids=None,
            witness_token_ids=None,
            witness_terminal_labels=None,
            witness_graph_edge_ids=None,
            certificate_valid=None,
        )
