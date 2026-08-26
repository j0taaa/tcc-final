from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest

from mwpc_exact import ExactBackend, SolveStatus
from mwpc_exact.experiments import ExperimentKind, load_experiment_config
from mwpc_research.finite_differential import (
    RandomFiniteLatticeInstance,
    check_finite_lattice_instance,
)
from mwpc_research.q1_correctness import (
    Q1_RAW_FILENAME,
    Q1_SUMMARY_FILENAME,
    Q1CaseFamily,
    canonical_q1_cases,
    configured_q1_cases,
    exhaustive_q1_cases,
    run_q1_correctness_cases,
    write_q1_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
PYTHON_SOLVERS = ("exhaustive_oracle", "python_reference")
ALL_SOLVERS = (*PYTHON_SOLVERS, "rust_production")


def _rust_binding_available() -> bool:
    try:
        import_module("mwpc_parser_py")
    except ImportError:
        return False
    return True


requires_rust_binding = pytest.mark.skipif(
    not _rust_binding_available(),
    reason="build the production binding with `make bootstrap-rust-parser`",
)


def _python_checker(instance: RandomFiniteLatticeInstance):
    return check_finite_lattice_instance(instance, backends=(ExactBackend.PYTHON,))


def test_q1_config_freezes_all_case_families_and_solvers() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config.question is ExperimentKind.CORRECTNESS
    assert config.publication_mode is False
    assert config.exactness_scope == "exact_on_support"
    assert config.finite_slots is True
    assert config.parameters["campaigns"] == tuple(family.value for family in Q1CaseFamily)
    assert config.parameters["solvers"] == ALL_SOLVERS
    assert config.parameters["random_case_count"] == 100


def test_canonical_cases_cover_optimal_infeasible_duplicate_and_multibyte_paths() -> None:
    cases = canonical_q1_cases(seed_base=1_000_000)
    reports = {
        case.case_id: check_finite_lattice_instance(
            case.instance,
            backends=(ExactBackend.PYTHON,),
        )
        for case in cases
    }

    assert len(cases) == 5
    assert reports["canonical-all-compatible"].objective_value == 5.0
    assert reports["canonical-jointly-incompatible"].objective_value == 5.0
    assert reports["canonical-duplicate-proposals"].objective_value == 6.0
    assert reports["canonical-fixed-infeasible"].status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert reports["canonical-multibyte-token-provenance"].objective_value == 3.0
    for report in reports.values():
        assert set(report.solver_statuses) == set(PYTHON_SOLVERS)
        assert set(report.timings_seconds) >= {*PYTHON_SOLVERS, "total"}


def test_exhaustive_family_enumerates_every_valid_tiny_boundary_combination() -> None:
    cases = exhaustive_q1_cases(seed_base=2_000_000)

    assert len(cases) == 144
    assert len({case.case_id for case in cases}) == len(cases)
    assert any(case.instance.canvas == (0, 0) for case in cases)
    assert any(not case.instance.proposals for case in cases)
    assert any(len(case.instance.proposals) == 4 for case in cases)

    result = run_q1_correctness_cases(
        cases,
        checker=_python_checker,
        required_solvers=PYTHON_SOLVERS,
        run_metadata={"test": "exhaustive"},
    )
    assert result.failed_cases == 0, result.summary_dict()
    assert result.summary_dict()["case_count"] == 144


def test_configured_cases_have_recorded_disjoint_seed_ranges() -> None:
    cases = configured_q1_cases(seed_start=1101, random_case_count=100)
    counts = {
        family: sum(case.family is family for case in cases)
        for family in Q1CaseFamily
    }

    assert counts == {
        Q1CaseFamily.CANONICAL: 5,
        Q1CaseFamily.EXHAUSTIVE: 144,
        Q1CaseFamily.RANDOMIZED: 100,
    }
    assert len(cases) == 249
    assert len({case.instance.seed for case in cases}) == 249


def test_summary_agreement_is_computed_and_failures_are_replayable(tmp_path: Path) -> None:
    cases = canonical_q1_cases(seed_base=3_000_000)[:2]

    def injected_checker(instance: RandomFiniteLatticeInstance):
        if instance.seed == cases[1].instance.seed:
            raise AssertionError("injected solver disagreement")
        return _python_checker(instance)

    result = run_q1_correctness_cases(
        cases,
        checker=injected_checker,
        required_solvers=PYTHON_SOLVERS,
        run_metadata={"config_sha256": "test-hash"},
        failure_directory=tmp_path / "mismatches",
    )
    summary = result.summary_dict()

    assert summary["case_count"] == 2
    assert summary["passed_cases"] == 1
    assert summary["failed_cases"] == 1
    assert summary["agreement_rate"] == 0.5
    failure = summary["failures"][0]
    assert isinstance(failure, dict)
    fixture_path = tmp_path / "mismatches" / str(failure["fixture_file"])
    failure_path = tmp_path / "mismatches" / str(failure["failure_file"])
    assert RandomFiniteLatticeInstance.read_json(fixture_path).seed == cases[1].instance.seed
    assert json.loads(failure_path.read_text(encoding="utf-8"))["case_id"] == cases[1].case_id


def test_raw_and_summary_artifacts_are_separate_and_immutable(tmp_path: Path) -> None:
    result = run_q1_correctness_cases(
        canonical_q1_cases(seed_base=4_000_000)[:1],
        checker=_python_checker,
        required_solvers=PYTHON_SOLVERS,
        run_metadata={"config_sha256": "test-hash", "git_commit": "test-commit"},
    )

    raw_path, summary_path = write_q1_artifacts(result, tmp_path)

    assert raw_path.name == Q1_RAW_FILENAME
    assert summary_path.name == Q1_SUMMARY_FILENAME
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(raw_rows) == summary["case_count"] == 1
    assert raw_rows[0]["agreement"] is True
    assert raw_rows[0]["grammar_sha256"]
    assert raw_rows[0]["support_sha256"]
    assert raw_rows[0]["support_specification"]["kind"] == "explicit"
    assert set(raw_rows[0]["solver_statuses"]) == set(PYTHON_SOLVERS)
    assert summary["agreement_rate"] == 1.0

    with pytest.raises(FileExistsError):
        write_q1_artifacts(result, tmp_path)


def test_missing_configured_solver_is_a_replayable_failure(tmp_path: Path) -> None:
    cases = canonical_q1_cases(seed_base=5_000_000)[:1]
    result = run_q1_correctness_cases(
        cases,
        checker=_python_checker,
        required_solvers=ALL_SOLVERS,
        run_metadata={"test": "missing-rust"},
        failure_directory=tmp_path,
    )

    assert result.failed_cases == 1
    assert result.records[0].error_type == "ValueError"
    assert "configured solvers" in (result.records[0].error_message or "")
    assert (tmp_path / "canonical-all-compatible.json").is_file()


@requires_rust_binding
def test_canonical_cases_compare_oracle_python_and_rust() -> None:
    result = run_q1_correctness_cases(
        canonical_q1_cases(seed_base=6_000_000),
        checker=check_finite_lattice_instance,
        required_solvers=ALL_SOLVERS,
        run_metadata={"test": "cross-language"},
    )

    assert result.failed_cases == 0, result.summary_dict()
    assert result.summary_dict()["solver_status_counts"].keys() == set(ALL_SOLVERS)
