"""Versioned offline regression-fixture loading and verification."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import Self

from mwpc_exact.reference.brute_force import exhaustive_completion_oracle
from mwpc_exact.reference.differential import (
    DifferentialCaseReport,
    DifferentialMismatch,
    check_differential_instance,
)
from mwpc_exact.reference.random_instances import RandomTokenAlignedInstance
from mwpc_exact.types import SolveStatus

REGRESSION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RegressionFixture:
    """One minimized failure plus its corrected expected base outcome."""

    regression_id: str
    description: str
    discovered_in_task: str
    fixed_by_commit: str
    instance: RandomTokenAlignedInstance
    expected_status: SolveStatus
    expected_objective: float | None
    expected_selected_proposal_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "regression_id",
            "description",
            "discovered_in_task",
            "fixed_by_commit",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.expected_status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("regression status must be optimal or infeasible_on_support")
        if self.expected_status is SolveStatus.OPTIMAL:
            if self.expected_objective is None:
                raise ValueError("optimal regression fixture requires expected_objective")
        elif self.expected_objective is not None or self.expected_selected_proposal_ids:
            raise ValueError("infeasible regression fixture cannot expect an optimum")
        ids = tuple(self.expected_selected_proposal_ids)
        if len(set(ids)) != len(ids) or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in ids
        ):
            raise ValueError("expected selected proposal IDs must be unique and non-negative")
        object.__setattr__(self, "expected_selected_proposal_ids", ids)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        if not isinstance(data, Mapping):
            raise TypeError("regression fixture data must be a mapping")
        if data.get("schema_version") != REGRESSION_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported regression schema_version: {data.get('schema_version')!r}"
            )
        instance_data = data.get("instance")
        if not isinstance(instance_data, Mapping):
            raise TypeError("regression instance must be a mapping")
        status_value = data.get("expected_status")
        if not isinstance(status_value, str):
            raise TypeError("expected_status must be a string")
        try:
            status = SolveStatus(status_value)
        except ValueError as exc:
            raise ValueError(f"unknown expected_status: {status_value!r}") from exc
        objective_value = data.get("expected_objective")
        if objective_value is not None and (
            isinstance(objective_value, bool) or not isinstance(objective_value, (int, float))
        ):
            raise TypeError("expected_objective must be a real number or null")
        selected_value = data.get("expected_selected_proposal_ids")
        if not isinstance(selected_value, list):
            raise TypeError("expected_selected_proposal_ids must be a list")
        return cls(
            regression_id=_string(data.get("regression_id"), "regression_id"),
            description=_string(data.get("description"), "description"),
            discovered_in_task=_string(data.get("discovered_in_task"), "discovered_in_task"),
            fixed_by_commit=_string(data.get("fixed_by_commit"), "fixed_by_commit"),
            instance=RandomTokenAlignedInstance.from_dict(instance_data),
            expected_status=status,
            expected_objective=(None if objective_value is None else float(objective_value)),
            expected_selected_proposal_ids=tuple(
                _integer(item, "expected selected proposal ID") for item in selected_value
            ),
        )

    @classmethod
    def from_json(cls, text: str) -> Self:
        parsed = json.loads(text)
        if not isinstance(parsed, Mapping):
            raise TypeError("regression JSON root must be an object")
        return cls.from_dict(parsed)

    @classmethod
    def read_json(cls, path: str | Path) -> Self:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def load_regression_fixtures(directory: str | Path) -> tuple[RegressionFixture, ...]:
    """Load every ``*.json`` regression fixture in deterministic path order."""
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"regression directory does not exist: {root}")
    paths = tuple(sorted(root.glob("*.json"), key=lambda item: item.name))
    if not paths:
        raise ValueError(f"regression directory contains no JSON fixtures: {root}")
    fixtures = tuple(RegressionFixture.read_json(path) for path in paths)
    ids = tuple(item.regression_id for item in fixtures)
    if len(set(ids)) != len(ids):
        raise ValueError("regression IDs must be unique across the corpus")
    return fixtures


def verify_regression_fixture(fixture: RegressionFixture) -> DifferentialCaseReport:
    """Run the full differential checker and assert the recorded base result."""
    if not isinstance(fixture, RegressionFixture):
        raise TypeError("fixture must be a RegressionFixture")
    report = check_differential_instance(fixture.instance)
    completion = exhaustive_completion_oracle(
        grammar=fixture.instance.grammar,
        per_position_support=fixture.instance.per_position_support,
        canvas=fixture.instance.canvas,
        proposals=fixture.instance.proposals,
        terminal_labels_by_token_id=fixture.instance.terminal_labels_by_token_id,
    )
    if completion.status is not fixture.expected_status:
        raise DifferentialMismatch(
            seed=fixture.instance.seed,
            property_name="regression_expected_status",
            details=(
                f"fixture={fixture.regression_id} expected={fixture.expected_status.value} "
                f"actual={completion.status.value}"
            ),
        )
    if fixture.expected_status is SolveStatus.OPTIMAL:
        assert completion.objective_value is not None
        assert fixture.expected_objective is not None
        if not isclose(
            completion.objective_value,
            fixture.expected_objective,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise DifferentialMismatch(
                seed=fixture.instance.seed,
                property_name="regression_expected_objective",
                details=(
                    f"fixture={fixture.regression_id} "
                    f"expected={fixture.expected_objective} "
                    f"actual={completion.objective_value}"
                ),
            )
        actual_ids = set(completion.optima[0].selected_proposal_ids)
        if actual_ids != set(fixture.expected_selected_proposal_ids):
            raise DifferentialMismatch(
                seed=fixture.instance.seed,
                property_name="regression_expected_selected_ids",
                details=(
                    f"fixture={fixture.regression_id} "
                    f"expected={fixture.expected_selected_proposal_ids!r} "
                    f"actual={completion.optima[0].selected_proposal_ids!r}"
                ),
            )
    return report


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value
