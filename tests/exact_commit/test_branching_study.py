from __future__ import annotations

import pytest

import mwpc_research.branching_study as study
from mwpc_exact import BenchmarkInstance
from mwpc_research.branching_study import (
    build_branching_instance,
    evaluate_branching_instance,
    exhaustive_completions,
    summarize_branching_rows,
)
from mwpc_research.recursive_tasks import FAMILIES


@pytest.mark.parametrize("family", FAMILIES)
def test_support_widths_are_nested_without_changing_proposals(family: str) -> None:
    for seed in range(160100, 160110):
        narrow = build_branching_instance(family, seed, 2, "integer_utility")
        wide = build_branching_instance(family, seed, 4, "integer_utility")
        assert narrow.selection_input.proposals == wide.selection_input.proposals, seed
        assert narrow.selection_input.canvas == wide.selection_input.canvas, seed
        for left, right in zip(
            narrow.selection_input.support.rows, wide.selection_input.support.rows, strict=True
        ):
            assert set(left) <= set(right), seed
        assert exhaustive_completions(narrow), seed
        assert BenchmarkInstance.from_dict(wide.to_dict()).fingerprint == wide.fingerprint


@pytest.mark.integration
@pytest.mark.parametrize("family", FAMILIES)
def test_branching_study_differential_gate(family: str) -> None:
    pytest.importorskip("mwpc_parser_py")
    rows = []
    for width in (2, 4):
        instance = build_branching_instance(family, 160100, width, "integer_utility")
        row = evaluate_branching_instance(instance)
        assert not row["failures"], row
        assert row["valid_paths"] >= 1
        assert all(result["independently_valid"] for result in row["selectors"].values()), row
        rows.append(row)
    summary = summarize_branching_rows(rows)
    assert summary["generated_state_count"] == 1
    assert summary["seed_cluster_count"] == 1
    assert summary["width_pairs"] == 1
    assert summary["width_monotonicity_violations"] == 0
    with pytest.raises(ValueError, match="duplicate"):
        summarize_branching_rows([rows[0], rows[0]])


def test_exhaustive_oracle_has_a_hard_path_limit() -> None:
    instance = build_branching_instance("brackets", 160100, 4, "unit")
    with pytest.raises(ValueError, match="budget exceeded"):
        exhaustive_completions(instance, maximum_paths=10)


def test_rejects_unconfigured_generator_controls() -> None:
    with pytest.raises(ValueError, match="width"):
        build_branching_instance("brackets", 1, 3, "unit")


@pytest.mark.integration
def test_independent_study_gate_rejects_corrupted_solver_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    pytest.importorskip("mwpc_parser_py")
    original = study.solve_exact_commit

    def corrupted(*args: object, **kwargs: object) -> object:
        result = original(*args, **kwargs)
        assert result.objective_value is not None
        return replace(result, objective_value=result.objective_value + 1.0)

    monkeypatch.setattr(study, "solve_exact_commit", corrupted)
    row = evaluate_branching_instance(build_branching_instance("brackets", 160100, 4, "unit"))
    assert len(row["failures"]) == 2
    assert row["selectors"]["rust_exact"]["independently_valid"] is False
    assert summarize_branching_rows([row])["correctness_failure_rows"] == 1
