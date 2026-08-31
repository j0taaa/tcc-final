"""Q1 correctness cases and computed experiment artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import fsum
from pathlib import Path
from types import MappingProxyType

from mwpc_exact.experiments.artifacts import prepare_artifact_directories
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.types import Proposal, SolveStatus
from mwpc_research.finite_differential import (
    FiniteLatticeCaseReport,
    RandomFiniteLatticeInstance,
    generate_random_finite_lattice_instance,
)
from mwpc_research.statistical_summaries import summarize_proportion

Q1_ARTIFACT_SCHEMA_VERSION = 1
Q1_RAW_ARTIFACT_KIND = "mwpc_q1_correctness_case"
Q1_SUMMARY_ARTIFACT_KIND = "mwpc_q1_correctness_summary"
Q1_RAW_FILENAME = "q1-cases.jsonl"
Q1_SUMMARY_FILENAME = "q1-summary.json"

_SAFE_CASE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class Q1CaseFamily(StrEnum):
    """Configured Q1 input families."""

    CANONICAL = "canonical"
    EXHAUSTIVE = "exhaustive"
    RANDOMIZED = "randomized"


@dataclass(frozen=True, slots=True)
class Q1Case:
    """One named finite-lattice instance and its generation family."""

    case_id: str
    family: Q1CaseFamily
    instance: RandomFiniteLatticeInstance

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or _SAFE_CASE_ID.fullmatch(self.case_id) is None:
            raise ValueError("case_id must be a lowercase, hyphen-separated identifier")
        if not isinstance(self.family, Q1CaseFamily):
            raise TypeError("family must be a Q1CaseFamily")
        if not isinstance(self.instance, RandomFiniteLatticeInstance):
            raise TypeError("instance must be a RandomFiniteLatticeInstance")


@dataclass(frozen=True, slots=True)
class Q1CaseRecord:
    """Computed agreement, size, timing, and replay data for one Q1 case."""

    case_id: str
    family: Q1CaseFamily
    seed: int
    agreement: bool
    status: str
    objective_value: float | None
    solver_statuses: Mapping[str, str]
    property_checks: Mapping[str, int]
    timings_seconds: Mapping[str, float]
    sizes: Mapping[str, int]
    grammar_sha256: str
    support_sha256: str
    support_specification: Mapping[str, object]
    fixture_file: str | None = None
    failure_file: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if _SAFE_CASE_ID.fullmatch(self.case_id) is None:
            raise ValueError("case_id must be a lowercase, hyphen-separated identifier")
        if not isinstance(self.family, Q1CaseFamily):
            raise TypeError("family must be a Q1CaseFamily")
        if not isinstance(self.agreement, bool):
            raise TypeError("agreement must be a boolean")
        for field_name in (
            "solver_statuses",
            "property_checks",
            "timings_seconds",
            "sizes",
            "support_specification",
        ):
            object.__setattr__(
                self,
                field_name,
                MappingProxyType(dict(getattr(self, field_name))),
            )

    def to_dict(self, *, run_metadata: Mapping[str, object]) -> dict[str, object]:
        return {
            "artifact_kind": Q1_RAW_ARTIFACT_KIND,
            "schema_version": Q1_ARTIFACT_SCHEMA_VERSION,
            "case_id": self.case_id,
            "family": self.family.value,
            "seed": self.seed,
            "agreement": self.agreement,
            "status": self.status,
            "objective_value": self.objective_value,
            "solver_statuses": dict(self.solver_statuses),
            "property_checks": dict(self.property_checks),
            "timings_seconds": dict(self.timings_seconds),
            "sizes": dict(self.sizes),
            "grammar_sha256": self.grammar_sha256,
            "support_sha256": self.support_sha256,
            "support_specification": dict(self.support_specification),
            "fixture_file": self.fixture_file,
            "failure_file": self.failure_file,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "run_metadata": dict(run_metadata),
        }


@dataclass(frozen=True, slots=True)
class Q1ExperimentResult:
    """Case records plus a summary derived exclusively from those records."""

    records: tuple[Q1CaseRecord, ...]
    run_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        records = tuple(self.records)
        if not records:
            raise ValueError("Q1 experiment requires at least one case record")
        if len({record.case_id for record in records}) != len(records):
            raise ValueError("Q1 case IDs must be unique")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "run_metadata", MappingProxyType(dict(self.run_metadata)))

    @property
    def failed_cases(self) -> int:
        return sum(not record.agreement for record in self.records)

    def summary_dict(self) -> dict[str, object]:
        """Compute agreement and aggregates; no reported count is entered manually."""

        total = len(self.records)
        passed = sum(record.agreement for record in self.records)
        family_counts: dict[str, int] = {}
        family_passed: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        solver_status_counts: dict[str, dict[str, int]] = {}
        timing_totals: dict[str, float] = {}
        seeds_by_family: dict[str, list[int]] = {}
        size_values: dict[str, list[int]] = {}
        failures: list[dict[str, object]] = []

        for record in self.records:
            family = record.family.value
            family_counts[family] = family_counts.get(family, 0) + 1
            family_passed[family] = family_passed.get(family, 0) + int(record.agreement)
            status_counts[record.status] = status_counts.get(record.status, 0) + 1
            seeds_by_family.setdefault(family, []).append(record.seed)
            for solver, status in record.solver_statuses.items():
                counts = solver_status_counts.setdefault(solver, {})
                counts[status] = counts.get(status, 0) + 1
            for phase, seconds in record.timings_seconds.items():
                timing_totals[phase] = fsum((timing_totals.get(phase, 0.0), seconds))
            for size_name, value in record.sizes.items():
                size_values.setdefault(size_name, []).append(value)
            if not record.agreement:
                failures.append(
                    {
                        "case_id": record.case_id,
                        "seed": record.seed,
                        "error_type": record.error_type,
                        "error_message": record.error_message,
                        "fixture_file": record.fixture_file,
                        "failure_file": record.failure_file,
                    }
                )

        family_summaries = {
            family: {
                "case_count": count,
                "passed_cases": family_passed.get(family, 0),
                "failed_cases": count - family_passed.get(family, 0),
                "agreement": summarize_proportion(
                    family_passed.get(family, 0),
                    count,
                    analysis_unit="case",
                ).to_dict(),
            }
            for family, count in sorted(family_counts.items())
        }
        seed_ranges = {
            family: {
                "minimum": min(seeds),
                "maximum": max(seeds),
                "count": len(seeds),
            }
            for family, seeds in sorted(seeds_by_family.items())
        }
        size_ranges = {
            name: {"minimum": min(values), "maximum": max(values)}
            for name, values in sorted(size_values.items())
        }
        return {
            "artifact_kind": Q1_SUMMARY_ARTIFACT_KIND,
            "schema_version": Q1_ARTIFACT_SCHEMA_VERSION,
            "case_count": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "agreement_rate": passed / total,
            "agreement": summarize_proportion(
                passed,
                total,
                analysis_unit="case",
            ).to_dict(),
            "families": family_summaries,
            "seed_ranges": seed_ranges,
            "status_counts": dict(sorted(status_counts.items())),
            "solver_status_counts": {
                solver: dict(sorted(counts.items()))
                for solver, counts in sorted(solver_status_counts.items())
            },
            "timing_totals_seconds": dict(sorted(timing_totals.items())),
            "size_ranges": size_ranges,
            "failures": failures,
            "run_metadata": dict(self.run_metadata),
        }


def canonical_q1_cases(*, seed_base: int) -> tuple[Q1Case, ...]:
    """Return hand-written cases covering the main certificate corner cases."""

    grammar = _alternating_two_byte_grammar()
    emissions = (b"a", b"b")
    free_support_rows = ((0, 1), (0, 1))
    specifications = (
        (
            "canonical-all-compatible",
            (None, None),
            free_support_rows,
            (Proposal(0, 0, 0, 2), Proposal(1, 1, 1, 3)),
            ("all_proposals_compatible",),
        ),
        (
            "canonical-jointly-incompatible",
            (None, None),
            free_support_rows,
            (Proposal(0, 0, 0, 4), Proposal(1, 1, 0, 5)),
            ("jointly_incompatible_proposals",),
        ),
        (
            "canonical-duplicate-proposals",
            (None, None),
            free_support_rows,
            (
                Proposal(7, 0, 0, 2),
                Proposal(8, 0, 0, 3),
                Proposal(9, 1, 1, 1),
            ),
            ("duplicate_matching_proposals",),
        ),
        (
            "canonical-fixed-infeasible",
            (0, 0),
            ((0,), (0,)),
            (),
            ("fixed_infeasible_canvas",),
        ),
    )
    cases = [
        Q1Case(
            case_id=case_id,
            family=Q1CaseFamily.CANONICAL,
            instance=RandomFiniteLatticeInstance(
                seed=seed_base + index,
                grammar_kind="q1_alternating_two_byte",
                grammar=grammar,
                canvas=canvas,
                support_rows=support_rows,
                emissions=emissions,
                proposals=proposals,
                features=("canonical", *features),
            ),
        )
        for index, (case_id, canvas, support_rows, proposals, features) in enumerate(
            specifications
        )
    ]
    cases.append(
        Q1Case(
            case_id="canonical-multibyte-token-provenance",
            family=Q1CaseFamily.CANONICAL,
            instance=RandomFiniteLatticeInstance(
                seed=seed_base + len(cases),
                grammar_kind="q1_literal_ab",
                grammar=_literal_ab_grammar(),
                canvas=(None,),
                support_rows=((0, 1, 2),),
                emissions=(b"ab", b"ab", b"a"),
                proposals=(Proposal(0, 0, 0, 2), Proposal(1, 0, 1, 3)),
                features=(
                    "canonical",
                    "multi_byte_token",
                    "same_bytes_distinct_token_ids",
                    "token_provenance",
                ),
            ),
        )
    )
    return tuple(cases)


def exhaustive_q1_cases(*, seed_base: int) -> tuple[Q1Case, ...]:
    """Enumerate every tiny support, fixed canvas, and represented proposal subset."""

    grammar = _alternating_two_byte_grammar()
    position_options = (
        ((0,), None),
        ((1,), None),
        ((0, 1), None),
        ((0,), 0),
        ((1,), 1),
    )
    cases: list[Q1Case] = []
    for first_row, first_fixed in position_options:
        for second_row, second_fixed in position_options:
            rows = (first_row, second_row)
            proposal_choices = tuple(
                (position, token_id)
                for position, row in enumerate(rows)
                for token_id in row
            )
            for proposal_mask in range(1 << len(proposal_choices)):
                proposals = tuple(
                    Proposal(
                        proposal_id=index,
                        position=position,
                        token_id=token_id,
                        weight=(position + 1) * 10 + token_id + 1,
                    )
                    for index, (position, token_id) in enumerate(proposal_choices)
                    if proposal_mask & (1 << index)
                )
                case_index = len(cases)
                features = ["exhaustive_small_family"]
                if first_fixed is not None or second_fixed is not None:
                    features.append("fixed_position")
                if not proposals:
                    features.append("empty_proposal_set")
                cases.append(
                    Q1Case(
                        case_id=f"exhaustive-{case_index:04d}",
                        family=Q1CaseFamily.EXHAUSTIVE,
                        instance=RandomFiniteLatticeInstance(
                            seed=seed_base + case_index,
                            grammar_kind="q1_alternating_two_byte",
                            grammar=grammar,
                            canvas=(first_fixed, second_fixed),
                            support_rows=rows,
                            emissions=(b"a", b"b"),
                            proposals=proposals,
                            features=tuple(features),
                        ),
                    )
                )
    return tuple(cases)


def randomized_q1_cases(*, seed_start: int, case_count: int) -> tuple[Q1Case, ...]:
    """Generate a contiguous, replayable finite-lattice seed campaign."""

    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    if isinstance(case_count, bool) or not isinstance(case_count, int) or case_count <= 0:
        raise ValueError("case_count must be a positive integer")
    return tuple(
        Q1Case(
            case_id=f"randomized-seed-{seed}",
            family=Q1CaseFamily.RANDOMIZED,
            instance=generate_random_finite_lattice_instance(seed),
        )
        for seed in range(seed_start, seed_start + case_count)
    )


def configured_q1_cases(*, seed_start: int, random_case_count: int) -> tuple[Q1Case, ...]:
    """Build the complete canonical, exhaustive, and randomized Q1 input set."""

    return (
        *canonical_q1_cases(seed_base=seed_start + 1_000_000),
        *exhaustive_q1_cases(seed_base=seed_start + 2_000_000),
        *randomized_q1_cases(seed_start=seed_start, case_count=random_case_count),
    )


def run_q1_correctness_cases(
    cases: Iterable[Q1Case],
    *,
    checker: Callable[[RandomFiniteLatticeInstance], FiniteLatticeCaseReport],
    required_solvers: Iterable[str],
    run_metadata: Mapping[str, object],
    failure_directory: str | Path | None = None,
) -> Q1ExperimentResult:
    """Evaluate all cases, save replay fixtures, and retain every disagreement."""

    if not callable(checker):
        raise TypeError("checker must be callable")
    solver_names = tuple(required_solvers)
    if (
        not solver_names
        or not all(isinstance(name, str) and name for name in solver_names)
        or len(set(solver_names)) != len(solver_names)
    ):
        raise ValueError("required_solvers must contain unique non-empty names")
    case_items = tuple(cases)
    if not case_items or not all(isinstance(case, Q1Case) for case in case_items):
        raise ValueError("cases must contain at least one Q1Case")
    if len({case.case_id for case in case_items}) != len(case_items):
        raise ValueError("case IDs must be unique")
    failure_path = None if failure_directory is None else Path(failure_directory)
    if failure_path is not None:
        failure_path.mkdir(parents=True, exist_ok=True)

    records: list[Q1CaseRecord] = []
    for case in case_items:
        instance = case.instance
        grammar_hash = _grammar_sha256(instance.grammar)
        sizes = _case_sizes(instance)
        try:
            report = checker(instance)
            _validate_case_report(instance, report, required_solvers=solver_names)
        except Exception as error:
            fixture_file: str | None = None
            failure_file: str | None = None
            if failure_path is not None:
                fixture_name = f"{case.case_id}.json"
                failure_name = f"{case.case_id}.failure.json"
                instance.write_json(failure_path / fixture_name)
                (failure_path / failure_name).write_text(
                    json.dumps(
                        {
                            "schema_version": Q1_ARTIFACT_SCHEMA_VERSION,
                            "case_id": case.case_id,
                            "family": case.family.value,
                            "seed": instance.seed,
                            "error_type": type(error).__name__,
                            "message": str(error),
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
            records.append(
                Q1CaseRecord(
                    case_id=case.case_id,
                    family=case.family,
                    seed=instance.seed,
                    agreement=False,
                    status="error",
                    objective_value=None,
                    solver_statuses={},
                    property_checks={},
                    timings_seconds={},
                    sizes=sizes,
                    grammar_sha256=grammar_hash,
                    support_sha256=instance.support.fingerprint,
                    support_specification=instance.support.exactness_scope.to_dict(),
                    fixture_file=fixture_file,
                    failure_file=failure_file,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            )
            continue
        records.append(
            Q1CaseRecord(
                case_id=case.case_id,
                family=case.family,
                seed=instance.seed,
                agreement=True,
                status=report.status.value,
                objective_value=report.objective_value,
                solver_statuses=report.solver_statuses,
                property_checks=report.property_checks,
                timings_seconds=report.timings_seconds,
                sizes={
                    **sizes,
                    "enumerated_token_paths": report.enumerated_token_paths,
                    "grammar_valid_paths": report.grammar_valid_paths,
                },
                grammar_sha256=grammar_hash,
                support_sha256=instance.support.fingerprint,
                support_specification=instance.support.exactness_scope.to_dict(),
            )
        )
    return Q1ExperimentResult(records=tuple(records), run_metadata=run_metadata)


def write_q1_artifacts(
    result: Q1ExperimentResult,
    raw_directory: str | Path,
    processed_directory: str | Path,
) -> tuple[Path, Path]:
    """Write immutable raw JSONL separately from its computed summary."""

    if not isinstance(result, Q1ExperimentResult):
        raise TypeError("result must be a Q1ExperimentResult")
    raw_output, processed_output = prepare_artifact_directories(
        raw_directory,
        processed_directory,
    )
    raw_path = raw_output / Q1_RAW_FILENAME
    summary_path = processed_output / Q1_SUMMARY_FILENAME
    if raw_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite Q1 raw or processed artifacts")
    with raw_path.open("x", encoding="utf-8") as output:
        for record in result.records:
            output.write(
                json.dumps(
                    record.to_dict(run_metadata=result.run_metadata),
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    with summary_path.open("x", encoding="utf-8") as output:
        json.dump(result.summary_dict(), output, allow_nan=False, indent=2, sort_keys=True)
        output.write("\n")
    return raw_path, summary_path


def _alternating_two_byte_grammar() -> CnfGrammar:
    """Language ``{ab, ba}`` used by canonical and exhaustive cases."""

    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(
            BinaryProduction(2, 0, 1, 2),
            BinaryProduction(3, 0, 2, 1),
        ),
    )


def _literal_ab_grammar() -> CnfGrammar:
    """Language containing only the two-byte terminal sequence ``ab``."""

    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(BinaryProduction(2, 0, 1, 2),),
    )


def _grammar_sha256(grammar: CnfGrammar) -> str:
    payload = json.dumps(grammar.to_dict(), separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _case_sizes(instance: RandomFiniteLatticeInstance) -> dict[str, int]:
    grammar = instance.grammar
    return {
        "slot_count": len(instance.canvas),
        "vocabulary_size": len(instance.emissions),
        "represented_token_choices": sum(len(row) for row in instance.support_rows),
        "proposal_count": len(instance.proposals),
        "grammar_nonterminal_count": len(grammar.nonterminals),
        "grammar_terminal_count": len(grammar.terminals),
        "grammar_production_count": (
            len(grammar.terminal_productions) + len(grammar.binary_productions)
        ),
    }


def _validate_case_report(
    instance: RandomFiniteLatticeInstance,
    report: FiniteLatticeCaseReport,
    *,
    required_solvers: tuple[str, ...],
) -> None:
    if not isinstance(report, FiniteLatticeCaseReport):
        raise TypeError("Q1 checker must return a FiniteLatticeCaseReport")
    if report.seed != instance.seed:
        raise ValueError("Q1 checker report seed does not match the instance")
    if set(report.solver_statuses) != set(required_solvers):
        raise ValueError("Q1 checker did not report exactly the configured solvers")
    if set(report.timings_seconds) < set(required_solvers):
        raise ValueError("Q1 checker omitted a configured solver timing")
    if set(report.solver_statuses.values()) != {report.status.value}:
        raise AssertionError("Q1 checker reported a solver disagreement")
    if report.status is SolveStatus.OPTIMAL:
        expected_backend_certificates = len(required_solvers) - 1
        if report.property_checks.get("certificate_validation") != expected_backend_certificates:
            raise AssertionError(
                "Q1 checker did not independently validate every backend certificate"
            )


__all__ = [
    "Q1_ARTIFACT_SCHEMA_VERSION",
    "Q1_RAW_ARTIFACT_KIND",
    "Q1_RAW_FILENAME",
    "Q1_SUMMARY_ARTIFACT_KIND",
    "Q1_SUMMARY_FILENAME",
    "Q1Case",
    "Q1CaseFamily",
    "Q1CaseRecord",
    "Q1ExperimentResult",
    "canonical_q1_cases",
    "configured_q1_cases",
    "exhaustive_q1_cases",
    "randomized_q1_cases",
    "run_q1_correctness_cases",
    "write_q1_artifacts",
]
