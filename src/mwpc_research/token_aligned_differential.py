"""Three-way randomized correctness checks for token-aligned MWPC."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import fsum, isclose
from pathlib import Path
from types import MappingProxyType
from typing import NoReturn

from mwpc_exact.reference.brute_force import (
    CompletionOracleResult,
    SubsetOracleResult,
    exhaustive_completion_oracle,
    exhaustive_subset_oracle,
)
from mwpc_exact.reference.random_instances import (
    RandomTokenAlignedInstance,
    generate_random_instance,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.reference.token_aligned import solve_token_aligned
from mwpc_exact.types import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    SupportKind,
    TerminalLabel,
)


class DifferentialMismatch(AssertionError):
    """One replayable seed violated a named correctness property."""

    def __init__(self, *, seed: int, property_name: str, details: str) -> None:
        self.seed = seed
        self.property_name = property_name
        self.details = details
        super().__init__(f"seed={seed} property={property_name}: {details}")


@dataclass(frozen=True, slots=True)
class DifferentialCaseReport:
    """Checks completed for one generated seed."""

    seed: int
    base_status: SolveStatus
    property_checks: Mapping[str, int]

    def __post_init__(self) -> None:
        checks = dict(self.property_checks)
        if any(
            not isinstance(name, str)
            or not name
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            for name, count in checks.items()
        ):
            raise ValueError("property check counts must have names and non-negative integers")
        object.__setattr__(self, "property_checks", MappingProxyType(checks))


@dataclass(frozen=True, slots=True)
class DifferentialFailure:
    seed: int
    error_type: str
    message: str
    fixture_file: str | None
    failure_file: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "error_type": self.error_type,
            "message": self.message,
            "fixture_file": self.fixture_file,
            "failure_file": self.failure_file,
        }


@dataclass(frozen=True, slots=True)
class DifferentialCampaignSummary:
    """Deterministic aggregate plus replay pointers for any failures."""

    seed_start: int
    case_count: int
    passed_cases: int
    failed_cases: int
    status_counts: Mapping[str, int]
    property_checks: Mapping[str, int]
    failures: tuple[DifferentialFailure, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.passed_cases + self.failed_cases != self.case_count:
            raise ValueError("campaign passed/failed counts must equal case_count")
        object.__setattr__(self, "status_counts", MappingProxyType(dict(self.status_counts)))
        object.__setattr__(self, "property_checks", MappingProxyType(dict(self.property_checks)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "campaign": "m3_token_aligned_differential",
            "seed_start": self.seed_start,
            "case_count": self.case_count,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "status_counts": dict(self.status_counts),
            "property_checks": dict(self.property_checks),
            "failures": [failure.to_dict() for failure in self.failures],
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")


@dataclass(frozen=True, slots=True)
class _ThreeWayOutcome:
    status: SolveStatus
    objective_value: float | None
    completion: CompletionOracleResult
    subset: SubsetOracleResult
    cky: ExactCommitResult


def check_differential_instance(
    instance: RandomTokenAlignedInstance,
) -> DifferentialCaseReport:
    """Check three-way agreement and three theorem-level monotonicities."""
    if not isinstance(instance, RandomTokenAlignedInstance):
        raise TypeError("instance must be a RandomTokenAlignedInstance")
    checks: dict[str, int] = {}

    base = _compare_three(
        instance,
        supports=instance.per_position_support,
        canvas=instance.canvas,
        proposals=instance.proposals,
        variant="base",
        checks=checks,
    )

    all_tokens = tuple(sorted(instance.terminal_labels_by_token_id))
    expanded_support = tuple(all_tokens for _ in instance.per_position_support)
    expanded = _compare_three(
        instance,
        supports=expanded_support,
        canvas=instance.canvas,
        proposals=instance.proposals,
        variant="expanded_support",
        checks=checks,
    )
    if base.status is SolveStatus.OPTIMAL:
        if expanded.status is not SolveStatus.OPTIMAL:
            _mismatch(instance, "support_monotonicity", "expansion lost feasibility")
        assert base.objective_value is not None
        assert expanded.objective_value is not None
        if expanded.objective_value < base.objective_value:
            _mismatch(
                instance,
                "support_monotonicity",
                f"expanded objective {expanded.objective_value} < {base.objective_value}",
            )
    _increment(checks, "support_monotonicity")

    removal_index = instance.seed % len(instance.proposals)
    reduced_proposals = tuple(
        proposal for index, proposal in enumerate(instance.proposals) if index != removal_index
    )
    removed = _compare_three(
        instance,
        supports=instance.per_position_support,
        canvas=instance.canvas,
        proposals=reduced_proposals,
        variant="proposal_removed",
        checks=checks,
    )
    if removed.status is not base.status:
        _mismatch(instance, "proposal_removal", "proposal removal changed feasibility")
    if base.status is SolveStatus.OPTIMAL:
        assert base.objective_value is not None
        assert removed.objective_value is not None
        if removed.objective_value > base.objective_value:
            _mismatch(
                instance,
                "proposal_removal",
                f"removed objective {removed.objective_value} > {base.objective_value}",
            )
    _increment(checks, "proposal_removal")

    free_canvas = tuple(None for _ in instance.canvas)
    free = _compare_three(
        instance,
        supports=instance.per_position_support,
        canvas=free_canvas,
        proposals=instance.proposals,
        variant="unfixed_canvas",
        checks=checks,
    )
    fixed_position = instance.seed % len(instance.canvas)
    support = instance.per_position_support[fixed_position]
    fixed_token = support[instance.seed % len(support)]
    fixed_canvas = tuple(
        fixed_token if position == fixed_position else None
        for position in range(len(instance.canvas))
    )
    fixed = _compare_three(
        instance,
        supports=instance.per_position_support,
        canvas=fixed_canvas,
        proposals=instance.proposals,
        variant="one_fixed_position",
        checks=checks,
    )
    if free.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        if fixed.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:
            _mismatch(instance, "fixed_position", "fixing restored infeasible support")
    elif fixed.status is SolveStatus.OPTIMAL:
        assert free.objective_value is not None
        assert fixed.objective_value is not None
        if fixed.objective_value > free.objective_value:
            _mismatch(
                instance,
                "fixed_position",
                f"fixed objective {fixed.objective_value} > {free.objective_value}",
            )
    _increment(checks, "fixed_position")

    return DifferentialCaseReport(instance.seed, base.status, checks)


def run_differential_campaign(
    *,
    seed_start: int,
    case_count: int,
    failure_directory: str | Path | None = None,
    metadata: Mapping[str, str] | None = None,
    checker: Callable[[RandomTokenAlignedInstance], DifferentialCaseReport] = (
        check_differential_instance
    ),
) -> DifferentialCampaignSummary:
    """Run a replayable seed range and persist any failing instances."""
    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    if isinstance(case_count, bool) or not isinstance(case_count, int) or case_count <= 0:
        raise ValueError("case_count must be a positive integer")
    failure_path = None if failure_directory is None else Path(failure_directory)
    if failure_path is not None:
        failure_path.mkdir(parents=True, exist_ok=True)

    passed = 0
    status_counts: dict[str, int] = {}
    property_counts: dict[str, int] = {}
    failures: list[DifferentialFailure] = []
    for seed in range(seed_start, seed_start + case_count):
        instance = generate_random_instance(seed)
        try:
            report = checker(instance)
        except Exception as exc:  # each unexpected error must remain replayable
            fixture_file: str | None = None
            failure_file: str | None = None
            if failure_path is not None:
                fixture_name = f"seed-{seed}.json"
                failure_name = f"seed-{seed}.failure.json"
                instance.write_json(failure_path / fixture_name)
                (failure_path / failure_name).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "seed": seed,
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                            "fixture_file": fixture_name,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                fixture_file = fixture_name
                failure_file = failure_name
            failures.append(
                DifferentialFailure(
                    seed=seed,
                    error_type=type(exc).__name__,
                    message=str(exc),
                    fixture_file=fixture_file,
                    failure_file=failure_file,
                )
            )
            continue
        passed += 1
        status_counts[report.base_status.value] = status_counts.get(report.base_status.value, 0) + 1
        for property_name, count in report.property_checks.items():
            property_counts[property_name] = property_counts.get(property_name, 0) + count

    return DifferentialCampaignSummary(
        seed_start=seed_start,
        case_count=case_count,
        passed_cases=passed,
        failed_cases=len(failures),
        status_counts=status_counts,
        property_checks=property_counts,
        failures=tuple(failures),
        metadata={} if metadata is None else metadata,
    )


def _compare_three(
    instance: RandomTokenAlignedInstance,
    *,
    supports: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    variant: str,
    checks: dict[str, int],
) -> _ThreeWayOutcome:
    proposal_items = tuple(proposals)
    completion = exhaustive_completion_oracle(
        grammar=instance.grammar,
        per_position_support=supports,
        canvas=canvas,
        proposals=proposal_items,
        terminal_labels_by_token_id=instance.terminal_labels_by_token_id,
    )
    subset = exhaustive_subset_oracle(
        grammar=instance.grammar,
        per_position_support=supports,
        canvas=canvas,
        proposals=proposal_items,
        terminal_labels_by_token_id=instance.terminal_labels_by_token_id,
    )
    scope = ExactnessScope(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=instance.vocabulary_size,
        pruning_description=f"generated seed {instance.seed} variant {variant}",
    )
    cky = solve_token_aligned(
        grammar=instance.grammar,
        canvas=canvas,
        proposals=proposal_items,
        exactness_scope=scope,
        terminal_token_ids=instance.terminal_token_ids,
        per_position_support=supports,
    )
    statuses = (completion.status, subset.status, cky.status)
    if not statuses[0] is statuses[1] is statuses[2]:
        _mismatch(
            instance,
            "three_way_status",
            f"variant={variant} completion/subset/cky={statuses!r}",
        )
    objectives = (
        completion.objective_value,
        subset.objective_value,
        cky.objective_value,
    )
    if completion.status is SolveStatus.OPTIMAL:
        if any(item is None for item in objectives):
            _mismatch(instance, "three_way_objective", f"variant={variant} missing objective")
        first, second, third = objectives
        assert first is not None and second is not None and third is not None
        if not (
            isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)
            and isclose(first, third, rel_tol=1e-12, abs_tol=1e-12)
        ):
            _mismatch(
                instance,
                "three_way_objective",
                f"variant={variant} completion/subset/cky={objectives!r}",
            )
        _check_completion_certificate(instance, completion, proposal_items, supports, canvas)
        _check_subset_certificate(instance, subset, proposal_items, supports, canvas)
        _check_cky_certificate(instance, cky, proposal_items, supports, canvas)
        _increment(checks, "certificate_validation", 3)
    elif any(item is not None for item in objectives):
        _mismatch(
            instance,
            "three_way_objective",
            f"variant={variant} infeasible result exposed objective {objectives!r}",
        )
    _increment(checks, "three_way_agreement")
    return _ThreeWayOutcome(
        status=completion.status,
        objective_value=completion.objective_value,
        completion=completion,
        subset=subset,
        cky=cky,
    )


def _check_completion_certificate(
    instance: RandomTokenAlignedInstance,
    result: CompletionOracleResult,
    proposals: tuple[Proposal, ...],
    supports: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
) -> None:
    optimum = result.optima[0]
    _check_witness(
        instance,
        witness=optimum.witness_token_ids,
        labels=optimum.witness_terminal_labels,
        selected_ids=optimum.selected_proposal_ids,
        objective=optimum.objective_value,
        proposals=proposals,
        supports=supports,
        canvas=canvas,
        source="completion",
    )


def _check_subset_certificate(
    instance: RandomTokenAlignedInstance,
    result: SubsetOracleResult,
    proposals: tuple[Proposal, ...],
    supports: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
) -> None:
    assert result.objective_value is not None
    _check_witness(
        instance,
        witness=result.witness_token_ids,
        labels=result.witness_terminal_labels,
        selected_ids=result.selected_proposal_ids,
        objective=result.objective_value,
        proposals=proposals,
        supports=supports,
        canvas=canvas,
        source="subset",
    )


def _check_cky_certificate(
    instance: RandomTokenAlignedInstance,
    result: ExactCommitResult,
    proposals: tuple[Proposal, ...],
    supports: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
) -> None:
    assert result.objective_value is not None
    _check_witness(
        instance,
        witness=result.witness_token_ids,
        labels=result.witness_terminal_labels,
        selected_ids=result.selected_proposal_ids,
        objective=result.objective_value,
        proposals=proposals,
        supports=supports,
        canvas=canvas,
        source="cky",
    )
    diagnostics = result.to_dict()["diagnostics"]
    if not isinstance(diagnostics, Mapping):
        _mismatch(instance, "cky_certificate", "diagnostics are not a mapping")
    validation = diagnostics.get("certificate_validation")
    if not isinstance(validation, Mapping) or validation.get("is_valid") is not True:
        _mismatch(instance, "cky_certificate", "independent validator did not accept")


def _check_witness(
    instance: RandomTokenAlignedInstance,
    *,
    witness: tuple[int, ...],
    labels: tuple[TerminalLabel, ...],
    selected_ids: tuple[int, ...],
    objective: float,
    proposals: tuple[Proposal, ...],
    supports: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    source: str,
) -> None:
    if len(witness) != len(supports) or len(labels) != len(witness):
        _mismatch(instance, f"{source}_certificate", "witness length mismatch")
    if any(token_id not in supports[position] for position, token_id in enumerate(witness)):
        _mismatch(instance, f"{source}_certificate", "witness left represented support")
    if any(
        fixed is not None and witness[position] != fixed for position, fixed in enumerate(canvas)
    ):
        _mismatch(instance, f"{source}_certificate", "witness changed fixed canvas")
    expected_labels = tuple(instance.terminal_labels_by_token_id[token_id] for token_id in witness)
    if labels != expected_labels:
        _mismatch(
            instance,
            f"{source}_certificate",
            "terminal labels do not match witness token IDs",
        )
    if not recognizes_cnf(instance.grammar, labels):
        _mismatch(instance, f"{source}_certificate", "Boolean recognizer rejected witness")
    matched = tuple(
        proposal
        for proposal in proposals
        if proposal.weight > 0 and witness[proposal.position] == proposal.token_id
    )
    expected_ids = {proposal.proposal_id for proposal in matched}
    if set(selected_ids) != expected_ids:
        _mismatch(
            instance,
            f"{source}_certificate",
            f"selected IDs {selected_ids!r} != {sorted(expected_ids)!r}",
        )
    recomputed = fsum(proposal.weight for proposal in matched)
    if not isclose(recomputed, objective, rel_tol=1e-12, abs_tol=1e-12):
        _mismatch(
            instance,
            f"{source}_certificate",
            f"objective {objective} != recomputed {recomputed}",
        )


def _mismatch(instance: RandomTokenAlignedInstance, property_name: str, details: str) -> NoReturn:
    raise DifferentialMismatch(
        seed=instance.seed,
        property_name=property_name,
        details=details,
    )


def _increment(counts: dict[str, int], name: str, amount: int = 1) -> None:
    counts[name] = counts.get(name, 0) + amount
