"""Artifact contracts for the paired Q5 live-model experiment.

The live CUDA driver is intentionally separate from this model-free module so
that artifact validation and summary formulas remain covered by the ordinary
CPU test suite.  Solver status and generation execution status are separate:
in particular, a timeout is never serialized as represented-support
infeasibility.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import fsum, isfinite
from pathlib import Path
from types import MappingProxyType

from mwpc_exact.types import SolveStatus

Q5_ARTIFACT_SCHEMA_VERSION = 1
Q5_RAW_ARTIFACT_KIND = "mwpc_q5_end_to_end_row"
Q5_SUMMARY_ARTIFACT_KIND = "mwpc_q5_end_to_end_summary"
Q5_RAW_FILENAME = "q5-end-to-end-rows.jsonl"
Q5_SUMMARY_FILENAME = "q5-end-to-end-summary.json"
Q5_STRATEGIES = ("unconstrained", "serial", "epic", "exact")


class Q5ExecutionStatus(StrEnum):
    """Outcome of the generation call, distinct from exact-solver status."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    TIMEOUT = "timeout"
    ERROR = "error"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_non_negative_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number or None")
    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return result


def _integer_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be a finite integer sequence")
    items: tuple[object, ...] = tuple(value)
    return tuple(_non_negative_integer(item, f"{field_name} item") for item in items)


def _frozen_json_mapping(value: Mapping[str, object], field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    copied = dict(value)
    try:
        json.dumps(copied, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must contain finite JSON values") from error
    return MappingProxyType(copied)


def upstream_selection_batch_size(
    physical_update_count: int,
    regular_cover_selected_count: int,
) -> int:
    """Separate an upstream selector batch from EOS suffix side effects.

    The unmodified serial path selects exactly one token per decision, but an
    accepted EOS physically fills the remaining suffix in the same event.  A
    non-empty regular-cover result instead reports its exact selected batch
    and deliberately excludes EOS.
    """

    physical = _non_negative_integer(physical_update_count, "physical_update_count")
    regular = _non_negative_integer(
        regular_cover_selected_count,
        "regular_cover_selected_count",
    )
    if physical == 0:
        raise ValueError("an upstream selection event must physically update a slot")
    if regular > physical:
        raise ValueError("a regular-cover selection cannot exceed physical updates")
    return regular if regular else 1


@dataclass(frozen=True, slots=True)
class Q5MethodRecord:
    """One method applied to the same frozen prompt/model/schedule identity."""

    strategy: str
    execution_status: Q5ExecutionStatus
    comparison_fingerprint: str
    seed: int
    repetition: int
    generated_token_ids: tuple[int, ...]
    decoded_with_specials: str
    syntactic_valid: bool | None
    functional_success: bool | None
    checker: Mapping[str, object]
    configured_diffusion_steps: int
    model_forward_count: int
    commit_batch_sizes: tuple[int, ...]
    physical_update_batch_sizes: tuple[int, ...]
    fallback_count: int
    support_expansion_count: int | None
    empty_optimal_batch_count: int | None
    solver_backend: str | None
    solver_status: SolveStatus | None
    exactness_scope: Mapping[str, object] | None
    objective_value: float | None
    certificate_valid: bool | None
    certificate: Mapping[str, object] | None
    elapsed_seconds: float
    process_rss_before_bytes: int
    process_rss_after_bytes: int
    process_high_water_rss_bytes: int
    cuda_peak_allocated_bytes: int
    cuda_peak_reserved_bytes: int
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.strategy not in Q5_STRATEGIES:
            raise ValueError(f"unknown Q5 strategy: {self.strategy!r}")
        if not isinstance(self.execution_status, Q5ExecutionStatus):
            raise TypeError("execution_status must be a Q5ExecutionStatus")
        if not self.comparison_fingerprint:
            raise ValueError("comparison_fingerprint must be non-empty")
        _non_negative_integer(self.seed, "seed")
        _non_negative_integer(self.repetition, "repetition")
        object.__setattr__(
            self,
            "generated_token_ids",
            _integer_tuple(self.generated_token_ids, "generated_token_ids"),
        )
        if not isinstance(self.decoded_with_specials, str):
            raise TypeError("decoded_with_specials must be a string")
        for field_name in ("syntactic_valid", "functional_success"):
            if (value := getattr(self, field_name)) is not None and not isinstance(value, bool):
                raise TypeError(f"{field_name} must be a boolean or None")
        object.__setattr__(self, "checker", _frozen_json_mapping(self.checker, "checker"))
        for field_name in (
            "configured_diffusion_steps",
            "model_forward_count",
            "fallback_count",
            "process_rss_before_bytes",
            "process_rss_after_bytes",
            "process_high_water_rss_bytes",
            "cuda_peak_allocated_bytes",
            "cuda_peak_reserved_bytes",
        ):
            _non_negative_integer(getattr(self, field_name), field_name)
        if self.configured_diffusion_steps == 0:
            raise ValueError("configured_diffusion_steps must be positive")
        for field_name in ("commit_batch_sizes", "physical_update_batch_sizes"):
            values = _integer_tuple(getattr(self, field_name), field_name)
            if any(value == 0 for value in values):
                raise ValueError(f"{field_name} cannot contain empty updates")
            object.__setattr__(self, field_name, values)
        for field_name in ("support_expansion_count", "empty_optimal_batch_count"):
            value = getattr(self, field_name)
            if value is not None:
                _non_negative_integer(value, field_name)
        elapsed = _optional_non_negative_float(self.elapsed_seconds, "elapsed_seconds")
        assert elapsed is not None
        object.__setattr__(self, "elapsed_seconds", elapsed)
        objective = _optional_non_negative_float(self.objective_value, "objective_value")
        object.__setattr__(self, "objective_value", objective)

        is_exact = self.strategy == "exact"
        if is_exact:
            if self.solver_backend not in {"python", "rust"}:
                raise ValueError("exact rows require a recorded Python or Rust backend")
            if not isinstance(self.solver_status, SolveStatus):
                raise TypeError("exact rows require an explicit solver_status")
            if (
                self.execution_status is Q5ExecutionStatus.COMPLETE
                and (
                    self.support_expansion_count is None
                    or self.empty_optimal_batch_count is None
                )
            ):
                raise ValueError("exact rows require support-expansion and empty-batch counts")
            if self.solver_status is SolveStatus.OPTIMAL:
                if self.certificate_valid is not True or self.certificate is None:
                    raise ValueError("OPTIMAL Q5 rows require a validated certificate")
                required = {
                    "witness_token_ids",
                    "witness_terminal_labels",
                    "witness_graph_edge_ids",
                    "selected_proposal_ids",
                    "objective_value",
                }
                if not required <= set(self.certificate):
                    raise ValueError("OPTIMAL Q5 certificate is not reconstructible")
                if self.exactness_scope is None or self.objective_value is None:
                    raise ValueError("OPTIMAL Q5 rows require scope and objective")
        elif any(
            value is not None
            for value in (
                self.solver_backend,
                self.solver_status,
                self.exactness_scope,
                self.objective_value,
                self.certificate_valid,
                self.certificate,
                self.support_expansion_count,
                self.empty_optimal_batch_count,
            )
        ):
            raise ValueError("baseline rows must not masquerade as exact-solver results")

        if self.execution_status is Q5ExecutionStatus.COMPLETE:
            if not self.generated_token_ids:
                raise ValueError("complete Q5 rows require generated tokens")
            if self.syntactic_valid is None or self.functional_success is None:
                raise ValueError("complete Q5 rows require checker decisions")
            if self.model_forward_count == 0:
                raise ValueError("complete Q5 rows require an observed model forward")
            if sum(self.physical_update_batch_sizes) != len(self.generated_token_ids):
                raise ValueError("complete Q5 rows must account for every physical output slot")
        if self.fallback_count > sum(self.commit_batch_sizes):
            raise ValueError("fallback_count cannot exceed selected updates")
        if self.process_high_water_rss_bytes < max(
            self.process_rss_before_bytes,
            self.process_rss_after_bytes,
        ):
            raise ValueError("process high-water RSS cannot be below an RSS snapshot")
        if self.cuda_peak_reserved_bytes < self.cuda_peak_allocated_bytes:
            raise ValueError("CUDA peak reserved bytes cannot be below allocated bytes")
        object.__setattr__(
            self,
            "exactness_scope",
            (
                None
                if self.exactness_scope is None
                else _frozen_json_mapping(self.exactness_scope, "exactness_scope")
            ),
        )
        object.__setattr__(
            self,
            "certificate",
            (
                None
                if self.certificate is None
                else _frozen_json_mapping(self.certificate, "certificate")
            ),
        )
        object.__setattr__(
            self,
            "diagnostics",
            _frozen_json_mapping(self.diagnostics, "diagnostics"),
        )

    @property
    def average_commit_batch_size(self) -> float | None:
        if not self.commit_batch_sizes:
            return None
        return fsum(self.commit_batch_sizes) / len(self.commit_batch_sizes)

    def to_dict(self, *, run_metadata: Mapping[str, object]) -> dict[str, object]:
        return {
            "artifact_kind": Q5_RAW_ARTIFACT_KIND,
            "schema_version": Q5_ARTIFACT_SCHEMA_VERSION,
            "run_metadata": dict(run_metadata),
            "strategy": self.strategy,
            "execution_status": self.execution_status.value,
            "comparison_fingerprint": self.comparison_fingerprint,
            "seed": self.seed,
            "repetition": self.repetition,
            "generated_output": {
                "token_ids": list(self.generated_token_ids),
                "decoded_with_specials": self.decoded_with_specials,
            },
            "checker": dict(self.checker),
            "syntactic_valid": self.syntactic_valid,
            "functional_success": self.functional_success,
            "generation": {
                "configured_diffusion_steps": self.configured_diffusion_steps,
                "model_forward_count": self.model_forward_count,
                "commit_batch_sizes": list(self.commit_batch_sizes),
                "physical_update_batch_sizes": list(self.physical_update_batch_sizes),
                "average_commit_batch_size": self.average_commit_batch_size,
                "fallback_count": self.fallback_count,
                "support_expansion_count": self.support_expansion_count,
                "empty_optimal_batch_count": self.empty_optimal_batch_count,
            },
            "exact_solver": {
                "backend": self.solver_backend,
                "status": None if self.solver_status is None else self.solver_status.value,
                "exactness_scope": (
                    None if self.exactness_scope is None else dict(self.exactness_scope)
                ),
                "objective_value": self.objective_value,
                "certificate_valid": self.certificate_valid,
                "certificate": None if self.certificate is None else dict(self.certificate),
            },
            "resources": {
                "elapsed_seconds": self.elapsed_seconds,
                "process_rss_before_bytes": self.process_rss_before_bytes,
                "process_rss_after_bytes": self.process_rss_after_bytes,
                "process_high_water_rss_bytes": self.process_high_water_rss_bytes,
                "cuda_peak_allocated_bytes": self.cuda_peak_allocated_bytes,
                "cuda_peak_reserved_bytes": self.cuda_peak_reserved_bytes,
            },
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True, slots=True)
class Q5ExperimentResult:
    """Four paired method records and a summary derived only from those rows."""

    records: tuple[Q5MethodRecord, ...]
    run_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        records = tuple(self.records)
        if tuple(record.strategy for record in records) != Q5_STRATEGIES:
            raise ValueError(f"Q5 records must use the configured order {Q5_STRATEGIES!r}")
        if len({record.comparison_fingerprint for record in records}) != 1:
            raise ValueError("Q5 methods did not use one frozen comparison input")
        if len({(record.seed, record.repetition) for record in records}) != 1:
            raise ValueError("Q5 methods did not use one seed/repetition pair")
        object.__setattr__(self, "records", records)
        object.__setattr__(
            self,
            "run_metadata",
            _frozen_json_mapping(self.run_metadata, "run_metadata"),
        )

    @property
    def failed_record_count(self) -> int:
        return sum(
            record.execution_status is not Q5ExecutionStatus.COMPLETE
            for record in self.records
        )

    @property
    def required_contract_failure_count(self) -> int:
        failures = 0
        for record in self.records:
            if record.strategy == "unconstrained":
                continue
            valid = (
                record.execution_status is Q5ExecutionStatus.COMPLETE
                and record.syntactic_valid is True
                and record.functional_success is True
            )
            if record.strategy == "exact":
                valid = (
                    valid
                    and record.solver_status is SolveStatus.OPTIMAL
                    and record.certificate_valid is True
                )
            failures += not valid
        return failures

    def summary_dict(self) -> dict[str, object]:
        by_strategy = {record.strategy: record for record in self.records}
        exact = by_strategy["exact"]
        overhead: dict[str, float | None] = {}
        for strategy in Q5_STRATEGIES[:-1]:
            baseline_seconds = by_strategy[strategy].elapsed_seconds
            overhead[strategy] = (
                None if baseline_seconds == 0.0 else exact.elapsed_seconds / baseline_seconds
            )
        execution_statuses = Counter(record.execution_status.value for record in self.records)
        solver_statuses = Counter(
            record.solver_status.value
            for record in self.records
            if record.solver_status is not None
        )
        return {
            "artifact_kind": Q5_SUMMARY_ARTIFACT_KIND,
            "schema_version": Q5_ARTIFACT_SCHEMA_VERSION,
            "benchmark_claim": False,
            "measurement_count": len(self.records),
            "strategies": list(Q5_STRATEGIES),
            "paired_input_verified": True,
            "comparison_fingerprint": self.records[0].comparison_fingerprint,
            "execution_status_counts": dict(sorted(execution_statuses.items())),
            "exact_solver_status_counts": dict(sorted(solver_statuses.items())),
            "failed_record_count": self.failed_record_count,
            "required_contract_failure_count": self.required_contract_failure_count,
            "all_required_methods_passed": self.required_contract_failure_count == 0,
            "syntactic_valid_count": sum(record.syntactic_valid is True for record in self.records),
            "functional_success_count": sum(
                record.functional_success is True for record in self.records
            ),
            "fallback_count": sum(record.fallback_count for record in self.records),
            "support_expansion_count": exact.support_expansion_count,
            "empty_optimal_batch_count": exact.empty_optimal_batch_count,
            "diagnostic_exact_runtime_ratio": overhead,
            "timing_interpretation": (
                "single ordered smoke; ratios are diagnostic and not a publication benchmark"
            ),
            "methods": {
                record.strategy: {
                    "execution_status": record.execution_status.value,
                    "solver_status": (
                        None if record.solver_status is None else record.solver_status.value
                    ),
                    "syntactic_valid": record.syntactic_valid,
                    "functional_success": record.functional_success,
                    "configured_diffusion_steps": record.configured_diffusion_steps,
                    "model_forward_count": record.model_forward_count,
                    "commit_batch_sizes": list(record.commit_batch_sizes),
                    "average_commit_batch_size": record.average_commit_batch_size,
                    "fallback_count": record.fallback_count,
                    "support_expansion_count": record.support_expansion_count,
                    "empty_optimal_batch_count": record.empty_optimal_batch_count,
                    "elapsed_seconds": record.elapsed_seconds,
                    "process_high_water_rss_bytes": record.process_high_water_rss_bytes,
                    "cuda_peak_allocated_bytes": record.cuda_peak_allocated_bytes,
                    "cuda_peak_reserved_bytes": record.cuda_peak_reserved_bytes,
                }
                for record in self.records
            },
            "run_metadata": dict(self.run_metadata),
        }


def write_q5_artifacts(
    result: Q5ExperimentResult,
    run_directory: str | Path,
) -> tuple[Path, Path]:
    """Write immutable raw generated/checker rows and their computed summary."""

    if not isinstance(result, Q5ExperimentResult):
        raise TypeError("result must be a Q5ExperimentResult")
    directory = Path(run_directory)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / Q5_RAW_FILENAME
    summary_path = directory / Q5_SUMMARY_FILENAME
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


__all__ = [
    "Q5_ARTIFACT_SCHEMA_VERSION",
    "Q5_RAW_FILENAME",
    "Q5_STRATEGIES",
    "Q5_SUMMARY_FILENAME",
    "Q5ExecutionStatus",
    "Q5ExperimentResult",
    "Q5MethodRecord",
    "upstream_selection_batch_size",
    "write_q5_artifacts",
]
