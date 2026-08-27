"""Q4 scaling measurements for the Python and Rust exact-commit backends.

Every repetition runs in a fresh process.  The parent enforces a wall-clock
deadline for both backends, while the Rust parser also receives its native
deadline.  Consequently a censored Python reference run cannot continue in
the background or be mistaken for infeasibility.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from math import isfinite
from pathlib import Path
from time import monotonic, perf_counter
from types import MappingProxyType
from typing import cast

from mwpc_exact.backend import ExactBackend
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.solver import solve_exact_commit
from mwpc_exact.support import PerPositionSupport, SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import Proposal, SolveStatus, SupportKind

Q4_ARTIFACT_SCHEMA_VERSION = 1
Q4_RAW_ARTIFACT_KIND = "mwpc_q4_scaling_row"
Q4_PLOT_ARTIFACT_KIND = "mwpc_q4_scaling_plot_row"
Q4_SUMMARY_ARTIFACT_KIND = "mwpc_q4_scaling_summary"
Q4_RAW_FILENAME = "q4-scaling-rows.jsonl"
Q4_PLOT_FILENAME = "q4-scaling-plot-rows.jsonl"
Q4_SUMMARY_FILENAME = "q4-scaling-summary.json"

Q4_AXES = (
    "slot_count",
    "top_k",
    "graph_size_scale",
    "grammar_production_count",
    "token_byte_length",
    "proposal_count",
)

_CONCLUSIVE_STATUSES = frozenset(
    {SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE_ON_SUPPORT}
)


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number or None")
    normalized = float(value)
    if not isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


def _json_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return cast("Mapping[str, object]", value)


def _optional_integer(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _positive_integer(value, field_name)


def _optional_integer_tuple(value: object, field_name: str) -> tuple[int, ...] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence or None")
    result = tuple(_non_negative_integer(item, field_name) for item in value)
    return result


@dataclass(frozen=True, slots=True)
class ScalingPoint:
    """One controlled, one-axis-at-a-time generated scaling instance."""

    case_id: str
    axis: str
    axis_value: int
    slot_count: int
    support_kind: SupportKind
    support_width: int
    top_k: int | None
    grammar_production_count: int
    token_byte_length: int
    proposal_count: int
    vocabulary_size: int
    seed: int

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id must be non-empty")
        if self.axis not in Q4_AXES:
            raise ValueError(f"unknown Q4 scaling axis: {self.axis!r}")
        for field_name in (
            "axis_value",
            "slot_count",
            "support_width",
            "grammar_production_count",
            "token_byte_length",
            "proposal_count",
            "vocabulary_size",
        ):
            _positive_integer(getattr(self, field_name), field_name)
        if not isinstance(self.support_kind, SupportKind):
            raise TypeError("support_kind must be a SupportKind")
        if self.support_width >= self.vocabulary_size:
            raise ValueError("support_width must omit at least one vocabulary token")
        if self.support_kind is SupportKind.TOP_K:
            if self.top_k != self.support_width:
                raise ValueError("TOP_K points require top_k equal to support_width")
        elif self.support_kind is SupportKind.EXPLICIT:
            if self.top_k is not None:
                raise ValueError("explicit graph-size points cannot define top_k")
        else:
            raise ValueError("Q4 generated points support only TOP_K or EXPLICIT support")
        if self.grammar_production_count < 4 or self.grammar_production_count % 2:
            raise ValueError("grammar_production_count must be even and at least four")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")

    @property
    def instance_fingerprint(self) -> str:
        payload = json.dumps(
            self.to_dict(), allow_nan=False, separators=(",", ":"), sort_keys=True
        ).encode()
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "axis": self.axis,
            "axis_value": self.axis_value,
            "slot_count": self.slot_count,
            "support_kind": self.support_kind.value,
            "support_width": self.support_width,
            "top_k": self.top_k,
            "grammar_production_count": self.grammar_production_count,
            "token_byte_length": self.token_byte_length,
            "proposal_count": self.proposal_count,
            "vocabulary_size": self.vocabulary_size,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ScalingPoint:
        return cls(
            case_id=str(data["case_id"]),
            axis=str(data["axis"]),
            axis_value=_positive_integer(data["axis_value"], "axis_value"),
            slot_count=_positive_integer(data["slot_count"], "slot_count"),
            support_kind=SupportKind(str(data["support_kind"])),
            support_width=_positive_integer(data["support_width"], "support_width"),
            top_k=_optional_integer(data["top_k"], "top_k"),
            grammar_production_count=_positive_integer(
                data["grammar_production_count"], "grammar_production_count"
            ),
            token_byte_length=_positive_integer(
                data["token_byte_length"], "token_byte_length"
            ),
            proposal_count=_positive_integer(data["proposal_count"], "proposal_count"),
            vocabulary_size=_positive_integer(data["vocabulary_size"], "vocabulary_size"),
            seed=_non_negative_integer(data["seed"], "seed"),
        )


def make_scaling_points(
    *,
    seed: int,
    vocabulary_size: int,
    baseline_slot_count: int,
    baseline_top_k: int,
    baseline_grammar_production_count: int,
    baseline_token_byte_length: int,
    baseline_proposal_count: int,
    slot_counts: Sequence[int],
    top_k_values: Sequence[int],
    graph_size_scales: Sequence[int],
    grammar_production_counts: Sequence[int],
    token_byte_lengths: Sequence[int],
    proposal_counts: Sequence[int],
) -> tuple[ScalingPoint, ...]:
    """Expand one-axis-at-a-time Q4 settings into deterministic instances."""

    baseline = {
        "slot_count": _positive_integer(baseline_slot_count, "baseline_slot_count"),
        "support_width": _positive_integer(baseline_top_k, "baseline_top_k"),
        "grammar_production_count": _positive_integer(
            baseline_grammar_production_count,
            "baseline_grammar_production_count",
        ),
        "token_byte_length": _positive_integer(
            baseline_token_byte_length, "baseline_token_byte_length"
        ),
        "proposal_count": _positive_integer(
            baseline_proposal_count, "baseline_proposal_count"
        ),
    }
    vocabulary = _positive_integer(vocabulary_size, "vocabulary_size")
    if baseline["support_width"] >= vocabulary:
        raise ValueError("baseline_top_k must be smaller than vocabulary_size")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    axes = (
        ("slot_count", slot_counts),
        ("top_k", top_k_values),
        ("graph_size_scale", graph_size_scales),
        ("grammar_production_count", grammar_production_counts),
        ("token_byte_length", token_byte_lengths),
        ("proposal_count", proposal_counts),
    )
    points: list[ScalingPoint] = []
    for axis, raw_values in axes:
        if isinstance(raw_values, (str, bytes)) or not isinstance(raw_values, Sequence):
            raise TypeError(f"{axis} values must be a finite sequence")
        values = tuple(_positive_integer(value, f"{axis} value") for value in raw_values)
        if not values or len(set(values)) != len(values):
            raise ValueError(f"{axis} values must be non-empty and unique")
        for value in values:
            settings = dict(baseline)
            support_kind = SupportKind.TOP_K
            top_k: int | None = baseline["support_width"]
            if axis == "graph_size_scale":
                # Graph size is a derived quantity.  This controlled compound
                # sweep grows both explicit alternatives and private byte paths;
                # the realized node/edge counts are recorded, never inferred.
                support_kind = SupportKind.EXPLICIT
                settings["support_width"] = value
                settings["token_byte_length"] = value
                top_k = None
            elif axis == "top_k":
                settings["support_width"] = value
                top_k = value
            else:
                settings[axis] = value
            if settings["support_width"] >= vocabulary:
                raise ValueError(f"{axis} value requires support_width < vocabulary_size")
            points.append(
                ScalingPoint(
                    case_id=f"{axis}-{value:04d}",
                    axis=axis,
                    axis_value=value,
                    slot_count=settings["slot_count"],
                    support_kind=support_kind,
                    support_width=settings["support_width"],
                    top_k=top_k,
                    grammar_production_count=settings["grammar_production_count"],
                    token_byte_length=settings["token_byte_length"],
                    proposal_count=settings["proposal_count"],
                    vocabulary_size=vocabulary,
                    seed=seed,
                )
            )
    return tuple(points)


def _scaling_grammar(production_count: int) -> CnfGrammar:
    """Build a reachable ambiguous CNF for ``a+`` with an exact size."""

    production_count = _positive_integer(production_count, "production_count")
    if production_count < 4 or production_count % 2:
        raise ValueError("production_count must be even and at least four")
    alias_count = (production_count - 2) // 2
    nonterminals = (
        Nonterminal(0, "S"),
        *(Nonterminal(alias + 1, f"A{alias + 1}") for alias in range(alias_count)),
    )
    terminal_productions = (
        TerminalProduction(0, 0, 0),
        *(TerminalProduction(alias + 1, alias + 1, 0) for alias in range(alias_count)),
    )
    binary_start = len(terminal_productions)
    binary_productions = (
        BinaryProduction(binary_start, 0, 0, 0),
        *(
            BinaryProduction(binary_start + alias + 1, 0, alias + 1, alias + 1)
            for alias in range(alias_count)
        ),
    )
    grammar = CnfGrammar(
        nonterminals=nonterminals,
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=terminal_productions,
        binary_productions=binary_productions,
    )
    actual_count = len(grammar.terminal_productions) + len(grammar.binary_productions)
    if actual_count != production_count:
        raise AssertionError("generated grammar size differs from its scaling specification")
    return grammar


def _grammar_sha256(grammar: CnfGrammar) -> str:
    payload = json.dumps(grammar.to_dict(), separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def scaling_point_grammar_sha256(point: ScalingPoint) -> str:
    """Return the canonical generated grammar hash for one scaling point."""

    if not isinstance(point, ScalingPoint):
        raise TypeError("point must be a ScalingPoint")
    return _grammar_sha256(_scaling_grammar(point.grammar_production_count))


def _build_instance(
    point: ScalingPoint,
    profiler: ComponentProfiler,
) -> tuple[
    CnfGrammar,
    tuple[int | None, ...],
    PerPositionSupport,
    tuple[Proposal, ...],
    CompositionalByteLevelAdapter,
]:
    grammar = _scaling_grammar(point.grammar_production_count)
    canvas: tuple[int | None, ...] = (None,) * point.slot_count
    adapter = CompositionalByteLevelAdapter(
        (b"a" * point.token_byte_length,) * point.vocabulary_size
    )
    proposals = tuple(
        Proposal(
            proposal_id=proposal_id,
            position=proposal_id % point.slot_count,
            token_id=(proposal_id // point.slot_count) % point.support_width,
            weight=1.0 + (proposal_id % 7) / 10.0,
        )
        for proposal_id in range(point.proposal_count)
    )
    if point.support_kind is SupportKind.TOP_K:
        policy = SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=point.vocabulary_size,
            top_k=point.top_k,
        )
        logits = tuple(
            tuple(
                float(point.vocabulary_size - token_id)
                for token_id in range(point.vocabulary_size)
            )
            for _ in canvas
        )
        support = build_per_position_support(
            canvas=canvas,
            policy=policy,
            logits=logits,
            proposals=proposals,
            profiler=profiler,
        )
    else:
        policy = SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=point.vocabulary_size,
        )
        support = build_per_position_support(
            canvas=canvas,
            policy=policy,
            explicit_support={
                position: tuple(range(point.support_width))
                for position in range(point.slot_count)
            },
            proposals=proposals,
            profiler=profiler,
        )
    return grammar, canvas, support, proposals, adapter


@dataclass(frozen=True, slots=True)
class Q4Measurement:
    """One backend repetition with explicit censoring and full certificates."""

    point: ScalingPoint
    backend: ExactBackend
    repetition: int
    status: SolveStatus
    censored: bool
    censor_reason: str | None
    successful_runtime_seconds: float | None
    observed_profile: Mapping[str, object] | None
    worker_wall_seconds: float
    peak_rss_bytes: int | None
    address_space_limit_bytes: int
    grammar_sha256: str
    represented_support_sha256: str | None
    exactness_scope: Mapping[str, object] | None
    objective_value: float | None
    selected_proposal_ids: tuple[int, ...] | None
    witness_token_ids: tuple[int, ...] | None
    witness_terminal_labels: tuple[int | str, ...] | None
    witness_graph_edge_ids: tuple[int, ...] | None
    certificate_valid: bool | None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.backend, ExactBackend):
            raise TypeError("backend must be an ExactBackend")
        if isinstance(self.repetition, bool) or not isinstance(self.repetition, int):
            raise TypeError("repetition must be an integer")
        if self.repetition < 0:
            raise ValueError("repetition must be non-negative")
        if not isinstance(self.status, SolveStatus):
            raise TypeError("status must be a SolveStatus")
        if not isinstance(self.censored, bool):
            raise TypeError("censored must be a boolean")
        runtime = _optional_float(
            self.successful_runtime_seconds, "successful_runtime_seconds"
        )
        _optional_float(self.worker_wall_seconds, "worker_wall_seconds")
        if self.peak_rss_bytes is not None:
            _positive_integer(self.peak_rss_bytes, "peak_rss_bytes")
        _positive_integer(self.address_space_limit_bytes, "address_space_limit_bytes")
        if self.status in _CONCLUSIVE_STATUSES:
            if self.censored or runtime is None or self.censor_reason is not None:
                raise ValueError("conclusive rows require one uncensored successful runtime")
        elif not self.censored or runtime is not None or not self.censor_reason:
            raise ValueError("non-conclusive rows must be censored without a plot runtime")
        if self.status is SolveStatus.OPTIMAL:
            if (
                self.objective_value is None
                or self.selected_proposal_ids is None
                or self.witness_token_ids is None
                or self.witness_terminal_labels is None
                or self.witness_graph_edge_ids is None
                or self.certificate_valid is not True
            ):
                raise ValueError("OPTIMAL scaling rows require a validated complete witness")
        elif any(
            value is not None
            for value in (
                self.objective_value,
                self.selected_proposal_ids,
                self.witness_token_ids,
                self.witness_terminal_labels,
                self.witness_graph_edge_ids,
            )
        ):
            raise ValueError("non-OPTIMAL rows cannot expose partial certificates")
        if self.observed_profile is not None:
            object.__setattr__(
                self, "observed_profile", MappingProxyType(dict(self.observed_profile))
            )
        if self.exactness_scope is not None:
            object.__setattr__(
                self, "exactness_scope", MappingProxyType(dict(self.exactness_scope))
            )

    @property
    def seed(self) -> int:
        return self.point.seed + self.repetition

    def to_dict(self, *, run_metadata: Mapping[str, object]) -> dict[str, object]:
        return {
            "artifact_kind": Q4_RAW_ARTIFACT_KIND,
            "schema_version": Q4_ARTIFACT_SCHEMA_VERSION,
            "case_id": self.point.case_id,
            "instance_fingerprint": self.point.instance_fingerprint,
            "axis": self.point.axis,
            "axis_value": self.point.axis_value,
            "instance": self.point.to_dict(),
            "backend": self.backend.value,
            "repetition": self.repetition,
            "seed": self.seed,
            "status": self.status.value,
            "censored": self.censored,
            "censor_reason": self.censor_reason,
            "successful_runtime_seconds": self.successful_runtime_seconds,
            "observed_profile": (
                None if self.observed_profile is None else dict(self.observed_profile)
            ),
            "worker_wall_seconds": self.worker_wall_seconds,
            "memory": {
                "peak_worker_rss_bytes": self.peak_rss_bytes,
                "address_space_limit_bytes": self.address_space_limit_bytes,
                "rss_metric": "ru_maxrss_isolated_worker_high_water_mark",
            },
            "sizes": self._sizes(),
            "grammar_sha256": self.grammar_sha256,
            "represented_support_sha256": self.represented_support_sha256,
            "exactness_scope": (
                None if self.exactness_scope is None else dict(self.exactness_scope)
            ),
            "objective_value": self.objective_value,
            "selected_proposal_ids": (
                None
                if self.selected_proposal_ids is None
                else list(self.selected_proposal_ids)
            ),
            "witness_token_ids": (
                None if self.witness_token_ids is None else list(self.witness_token_ids)
            ),
            "witness_terminal_labels": (
                None
                if self.witness_terminal_labels is None
                else list(self.witness_terminal_labels)
            ),
            "witness_graph_edge_ids": (
                None
                if self.witness_graph_edge_ids is None
                else list(self.witness_graph_edge_ids)
            ),
            "certificate_valid": self.certificate_valid,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "run_metadata": dict(run_metadata),
        }

    def _sizes(self) -> dict[str, object] | None:
        if self.observed_profile is None:
            return None
        sizes = self.observed_profile.get("sizes")
        return dict(sizes) if isinstance(sizes, Mapping) else None

    def plot_dict(self) -> dict[str, object]:
        if self.censored or self.successful_runtime_seconds is None:
            raise ValueError("censored measurements cannot become plot rows")
        return {
            "artifact_kind": Q4_PLOT_ARTIFACT_KIND,
            "schema_version": Q4_ARTIFACT_SCHEMA_VERSION,
            "case_id": self.point.case_id,
            "instance_fingerprint": self.point.instance_fingerprint,
            "axis": self.point.axis,
            "axis_value": self.point.axis_value,
            "backend": self.backend.value,
            "repetition": self.repetition,
            "seed": self.seed,
            "status": self.status.value,
            "runtime_seconds": self.successful_runtime_seconds,
            "peak_worker_rss_bytes": self.peak_rss_bytes,
            "sizes": self._sizes(),
        }

    def to_worker_dict(self) -> dict[str, object]:
        return self.to_dict(run_metadata={})

    @classmethod
    def from_worker_dict(cls, data: Mapping[str, object]) -> Q4Measurement:
        instance = ScalingPoint.from_dict(_json_mapping(data["instance"], "instance"))
        raw_profile = data["observed_profile"]
        raw_scope = data["exactness_scope"]
        memory = _json_mapping(data["memory"], "memory")
        return cls(
            point=instance,
            backend=ExactBackend(str(data["backend"])),
            repetition=_non_negative_integer(data["repetition"], "repetition"),
            status=SolveStatus(str(data["status"])),
            censored=bool(data["censored"]),
            censor_reason=(
                None if data["censor_reason"] is None else str(data["censor_reason"])
            ),
            successful_runtime_seconds=_optional_float(
                data["successful_runtime_seconds"], "successful_runtime_seconds"
            ),
            observed_profile=(
                None
                if raw_profile is None
                else _json_mapping(raw_profile, "observed_profile")
            ),
            worker_wall_seconds=_optional_float(
                data["worker_wall_seconds"], "worker_wall_seconds"
            )
            or 0.0,
            peak_rss_bytes=_optional_integer(memory["peak_worker_rss_bytes"], "peak_rss"),
            address_space_limit_bytes=_positive_integer(
                memory["address_space_limit_bytes"], "address_space_limit_bytes"
            ),
            grammar_sha256=str(data["grammar_sha256"]),
            represented_support_sha256=(
                None
                if data["represented_support_sha256"] is None
                else str(data["represented_support_sha256"])
            ),
            exactness_scope=(
                None if raw_scope is None else _json_mapping(raw_scope, "exactness_scope")
            ),
            objective_value=_optional_float(data["objective_value"], "objective_value"),
            selected_proposal_ids=_optional_integer_tuple(
                data["selected_proposal_ids"], "selected_proposal_ids"
            ),
            witness_token_ids=_optional_integer_tuple(
                data["witness_token_ids"], "witness_token_ids"
            ),
            witness_terminal_labels=(
                None
                if data["witness_terminal_labels"] is None
                else tuple(cast("Sequence[int | str]", data["witness_terminal_labels"]))
            ),
            witness_graph_edge_ids=_optional_integer_tuple(
                data["witness_graph_edge_ids"], "witness_graph_edge_ids"
            ),
            certificate_valid=(
                None if data["certificate_valid"] is None else bool(data["certificate_valid"])
            ),
            error_type=None if data["error_type"] is None else str(data["error_type"]),
            error_message=(
                None if data["error_message"] is None else str(data["error_message"])
            ),
        )


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if platform.system() == "Darwin" else value * 1024)


def _failure_measurement(
    *,
    point: ScalingPoint,
    backend: ExactBackend,
    repetition: int,
    status: SolveStatus,
    reason: str,
    worker_wall_seconds: float,
    address_space_limit_bytes: int,
    error_type: str | None = None,
    error_message: str | None = None,
) -> Q4Measurement:
    return Q4Measurement(
        point=point,
        backend=backend,
        repetition=repetition,
        status=status,
        censored=True,
        censor_reason=reason,
        successful_runtime_seconds=None,
        observed_profile=None,
        worker_wall_seconds=worker_wall_seconds,
        peak_rss_bytes=None,
        address_space_limit_bytes=address_space_limit_bytes,
        grammar_sha256=_grammar_sha256(_scaling_grammar(point.grammar_production_count)),
        represented_support_sha256=None,
        exactness_scope=None,
        objective_value=None,
        selected_proposal_ids=None,
        witness_token_ids=None,
        witness_terminal_labels=None,
        witness_graph_edge_ids=None,
        certificate_valid=None,
        error_type=error_type,
        error_message=error_message,
    )


def measure_scaling_point(
    point: ScalingPoint,
    backend: ExactBackend,
    repetition: int,
    *,
    solver_timeout_seconds: float,
    address_space_limit_bytes: int,
) -> Q4Measurement:
    """Measure one point in the current process (the driver uses a child)."""

    profiler = ComponentProfiler(enabled=True)
    grammar, canvas, support, proposals, adapter = _build_instance(point, profiler)
    result = solve_exact_commit(
        grammar,
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=backend,
        timeout_seconds=(solver_timeout_seconds if backend is ExactBackend.RUST else None),
        profiler=profiler,
    )
    event = profiler.snapshot()
    if event is None:
        raise AssertionError("enabled Q4 profiler did not emit an event")
    profile = event.to_dict()
    validation = result.diagnostics.get("certificate_validation")
    certificate_valid = (
        bool(validation.get("is_valid")) if isinstance(validation, Mapping) else None
    )
    conclusive = result.status in _CONCLUSIVE_STATUSES
    diagnostics_scope = result.exactness_scope.to_dict()
    support_hash = result.diagnostics.get("represented_support_sha256")
    return Q4Measurement(
        point=point,
        backend=backend,
        repetition=repetition,
        status=result.status,
        censored=not conclusive,
        censor_reason=(None if conclusive else f"solver_status_{result.status.value}"),
        successful_runtime_seconds=(event.wall_span_seconds if conclusive else None),
        observed_profile=profile,
        worker_wall_seconds=0.0,
        peak_rss_bytes=_peak_rss_bytes(),
        address_space_limit_bytes=address_space_limit_bytes,
        grammar_sha256=_grammar_sha256(grammar),
        represented_support_sha256=(
            support_hash if isinstance(support_hash, str) else support.fingerprint
        ),
        exactness_scope=diagnostics_scope,
        objective_value=result.objective_value,
        selected_proposal_ids=(
            result.selected_proposal_ids if result.status is SolveStatus.OPTIMAL else None
        ),
        witness_token_ids=(
            result.witness_token_ids if result.status is SolveStatus.OPTIMAL else None
        ),
        witness_terminal_labels=(
            result.witness_terminal_labels if result.status is SolveStatus.OPTIMAL else None
        ),
        witness_graph_edge_ids=(
            result.witness_graph_edge_ids if result.status is SolveStatus.OPTIMAL else None
        ),
        certificate_valid=certificate_valid,
        error_type=(
            str(result.diagnostics.get("error_type"))
            if result.status is SolveStatus.ERROR
            else None
        ),
        error_message=(
            str(result.diagnostics.get("error_message"))
            if result.status is SolveStatus.ERROR
            else None
        ),
    )


def _apply_address_space_limit(limit_bytes: int) -> int:
    requested = _positive_integer(limit_bytes, "address_space_limit_bytes")
    _soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    actual = requested if hard == resource.RLIM_INFINITY else min(requested, hard)
    resource.setrlimit(resource.RLIMIT_AS, (actual, hard))
    return int(actual)


def _worker(payload: Mapping[str, object]) -> Q4Measurement:
    point = ScalingPoint.from_dict(_json_mapping(payload["point"], "point"))
    backend = ExactBackend(str(payload["backend"]))
    repetition = _non_negative_integer(payload["repetition"], "repetition")
    timeout = _optional_float(payload["solver_timeout_seconds"], "solver_timeout_seconds")
    if timeout is None or timeout <= 0.0:
        raise ValueError("solver_timeout_seconds must be positive")
    limit = _positive_integer(payload["address_space_limit_bytes"], "address_space_limit_bytes")
    actual_limit = _apply_address_space_limit(limit)
    try:
        return measure_scaling_point(
            point,
            backend,
            repetition,
            solver_timeout_seconds=timeout,
            address_space_limit_bytes=actual_limit,
        )
    except MemoryError as error:
        return _failure_measurement(
            point=point,
            backend=backend,
            repetition=repetition,
            status=SolveStatus.ERROR,
            reason="address_space_limit",
            worker_wall_seconds=0.0,
            address_space_limit_bytes=actual_limit,
            error_type=type(error).__name__,
            error_message=str(error),
        )


def _worker_entry(payload_json: str) -> int:
    try:
        payload = _json_mapping(json.loads(payload_json), "worker payload")
        measurement = _worker(payload)
    except Exception as error:
        print(
            json.dumps(
                {
                    "worker_error_type": type(error).__name__,
                    "worker_error_message": str(error),
                },
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            measurement.to_worker_dict(),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


def run_bounded_measurement(
    point: ScalingPoint,
    backend: ExactBackend,
    repetition: int,
    timeout_seconds: float,
    address_space_limit_bytes: int,
) -> Q4Measurement:
    """Run one isolated worker and preempt it at the configured deadline."""

    payload = {
        "point": point.to_dict(),
        "backend": backend.value,
        "repetition": repetition,
        "solver_timeout_seconds": timeout_seconds,
        "address_space_limit_bytes": address_space_limit_bytes,
    }
    environment = dict(os.environ)
    environment.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "RAYON_NUM_THREADS": "1",
            "PYTHONHASHSEED": str(point.seed + repetition),
        }
    )
    started = perf_counter()
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "mwpc_research.q4_scaling",
                "--worker-payload",
                json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return _failure_measurement(
            point=point,
            backend=backend,
            repetition=repetition,
            status=SolveStatus.TIMEOUT,
            reason="worker_wall_timeout",
            worker_wall_seconds=perf_counter() - started,
            address_space_limit_bytes=address_space_limit_bytes,
            error_type="TimeoutExpired",
            error_message="isolated worker exceeded its configured wall-clock deadline",
        )
    elapsed = perf_counter() - started
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        return _failure_measurement(
            point=point,
            backend=backend,
            repetition=repetition,
            status=SolveStatus.ERROR,
            reason="worker_error",
            worker_wall_seconds=elapsed,
            address_space_limit_bytes=address_space_limit_bytes,
            error_type="WorkerProcessError",
            error_message=message[-2000:],
        )
    try:
        raw = _json_mapping(json.loads(completed.stdout), "worker output")
        measurement = Q4Measurement.from_worker_dict(raw)
    except Exception as error:
        return _failure_measurement(
            point=point,
            backend=backend,
            repetition=repetition,
            status=SolveStatus.ERROR,
            reason="invalid_worker_output",
            worker_wall_seconds=elapsed,
            address_space_limit_bytes=address_space_limit_bytes,
            error_type=type(error).__name__,
            error_message=str(error),
        )
    if (
        measurement.point != point
        or measurement.backend is not backend
        or measurement.repetition != repetition
    ):
        return _failure_measurement(
            point=point,
            backend=backend,
            repetition=repetition,
            status=SolveStatus.ERROR,
            reason="worker_identity_mismatch",
            worker_wall_seconds=elapsed,
            address_space_limit_bytes=address_space_limit_bytes,
            error_type="WorkerIdentityError",
            error_message="worker result did not match its requested point/backend/repetition",
        )
    return replace(measurement, worker_wall_seconds=elapsed)


BoundedRunner = Callable[[ScalingPoint, ExactBackend, int, float, int], Q4Measurement]


@dataclass(frozen=True, slots=True)
class Q4ExperimentResult:
    measurements: tuple[Q4Measurement, ...]
    run_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        measurements = tuple(self.measurements)
        if not measurements:
            raise ValueError("Q4 experiment requires at least one measurement")
        identities = tuple(
            (row.point.case_id, row.backend, row.repetition) for row in measurements
        )
        if len(set(identities)) != len(identities):
            raise ValueError("Q4 measurement identities must be unique")
        object.__setattr__(self, "measurements", measurements)
        object.__setattr__(self, "run_metadata", MappingProxyType(dict(self.run_metadata)))

    @property
    def failed_rows(self) -> int:
        return sum(
            row.status in {SolveStatus.ERROR, SolveStatus.UNSUPPORTED}
            for row in self.measurements
        )

    def _backend_mismatches(self) -> list[dict[str, object]]:
        groups: dict[tuple[str, int], dict[ExactBackend, Q4Measurement]] = defaultdict(dict)
        for row in self.measurements:
            groups[(row.point.case_id, row.repetition)][row.backend] = row
        mismatches: list[dict[str, object]] = []
        for (case_id, repetition), rows in sorted(groups.items()):
            python = rows.get(ExactBackend.PYTHON)
            rust = rows.get(ExactBackend.RUST)
            if python is None or rust is None:
                continue
            if python.status not in _CONCLUSIVE_STATUSES or rust.status not in _CONCLUSIVE_STATUSES:
                continue
            same_objective = python.objective_value == rust.objective_value
            same_instance = (
                python.point.instance_fingerprint == rust.point.instance_fingerprint
                and python.grammar_sha256 == rust.grammar_sha256
                and python.represented_support_sha256 == rust.represented_support_sha256
            )
            if python.status is not rust.status or not same_objective or not same_instance:
                mismatches.append(
                    {
                        "case_id": case_id,
                        "repetition": repetition,
                        "python_status": python.status.value,
                        "rust_status": rust.status.value,
                        "python_objective": python.objective_value,
                        "rust_objective": rust.objective_value,
                        "same_instance": same_instance,
                    }
                )
        return mismatches

    def summary_dict(self) -> dict[str, object]:
        status_counts = Counter(row.status.value for row in self.measurements)
        backend_statuses: dict[str, Counter[str]] = defaultdict(Counter)
        axis_counts = Counter(row.point.axis for row in self.measurements)
        for row in self.measurements:
            backend_statuses[row.backend.value][row.status.value] += 1
        plot_rows = tuple(row for row in self.measurements if not row.censored)
        timeouts = tuple(row for row in self.measurements if row.status is SolveStatus.TIMEOUT)
        mismatch_rows = self._backend_mismatches()
        return {
            "artifact_kind": Q4_SUMMARY_ARTIFACT_KIND,
            "schema_version": Q4_ARTIFACT_SCHEMA_VERSION,
            "measurement_count": len(self.measurements),
            "axis_counts": dict(sorted(axis_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "backend_status_counts": {
                backend: dict(sorted(counts.items()))
                for backend, counts in sorted(backend_statuses.items())
            },
            "censored_count": sum(row.censored for row in self.measurements),
            "timeout_count": len(timeouts),
            "failed_row_count": self.failed_rows,
            "plot_ready_runtime_count": len(plot_rows),
            "timeout_plot_runtime_count": sum(
                row.successful_runtime_seconds is not None for row in timeouts
            ),
            "censoring_integrity": all(
                (row.status in _CONCLUSIVE_STATUSES)
                == (not row.censored and row.successful_runtime_seconds is not None)
                for row in self.measurements
            ),
            "backend_comparison_count": sum(
                1
                for point in {row.point.case_id for row in self.measurements}
                for repetition in {
                    row.repetition
                    for row in self.measurements
                    if row.point.case_id == point
                }
                if all(
                    any(
                        row.point.case_id == point
                        and row.repetition == repetition
                        and row.backend is backend
                        and row.status in _CONCLUSIVE_STATUSES
                        for row in self.measurements
                    )
                    for backend in ExactBackend
                )
            ),
            "backend_mismatch_count": len(mismatch_rows),
            "backend_mismatches": mismatch_rows,
            "run_metadata": dict(self.run_metadata),
        }


def run_q4_scaling(
    points: Sequence[ScalingPoint],
    *,
    backends: Sequence[ExactBackend],
    repetitions: int,
    solver_timeout_seconds: float,
    run_timeout_seconds: float,
    address_space_limit_bytes: int,
    run_metadata: Mapping[str, object],
    bounded_runner: BoundedRunner = run_bounded_measurement,
) -> Q4ExperimentResult:
    """Execute all measurements without reclassifying censored outcomes."""

    point_items = tuple(points)
    backend_items = tuple(backends)
    if not point_items or not backend_items:
        raise ValueError("Q4 points and backends must not be empty")
    if len(set(backend_items)) != len(backend_items):
        raise ValueError("Q4 backends must be unique")
    repetitions = _positive_integer(repetitions, "repetitions")
    solver_timeout = _optional_float(solver_timeout_seconds, "solver_timeout_seconds")
    run_timeout = _optional_float(run_timeout_seconds, "run_timeout_seconds")
    if solver_timeout is None or solver_timeout <= 0.0:
        raise ValueError("solver_timeout_seconds must be positive")
    if run_timeout is None or run_timeout <= 0.0:
        raise ValueError("run_timeout_seconds must be positive")
    limit = _positive_integer(address_space_limit_bytes, "address_space_limit_bytes")
    deadline = monotonic() + run_timeout
    measurements: list[Q4Measurement] = []
    for point in point_items:
        for repetition in range(repetitions):
            for backend in backend_items:
                remaining = deadline - monotonic()
                if remaining <= 0.0:
                    measurements.append(
                        _failure_measurement(
                            point=point,
                            backend=backend,
                            repetition=repetition,
                            status=SolveStatus.TIMEOUT,
                            reason="run_deadline_before_worker",
                            worker_wall_seconds=0.0,
                            address_space_limit_bytes=limit,
                            error_type="RunTimeout",
                            error_message="Q4 run deadline expired before this worker started",
                        )
                    )
                    continue
                measurements.append(
                    bounded_runner(
                        point,
                        backend,
                        repetition,
                        min(solver_timeout, remaining),
                        limit,
                    )
                )
    return Q4ExperimentResult(tuple(measurements), run_metadata)


def write_q4_artifacts(
    result: Q4ExperimentResult,
    run_directory: str | Path,
) -> tuple[Path, Path, Path]:
    """Write immutable raw, uncensored plot-input, and summary artifacts."""

    if not isinstance(result, Q4ExperimentResult):
        raise TypeError("result must be a Q4ExperimentResult")
    directory = Path(run_directory)
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / Q4_RAW_FILENAME
    plot_path = directory / Q4_PLOT_FILENAME
    summary_path = directory / Q4_SUMMARY_FILENAME
    with raw_path.open("x", encoding="utf-8") as output:
        for row in result.measurements:
            output.write(
                json.dumps(
                    row.to_dict(run_metadata=result.run_metadata),
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    with plot_path.open("x", encoding="utf-8") as output:
        for row in result.measurements:
            if not row.censored:
                output.write(
                    json.dumps(
                        row.plot_dict(),
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    + "\n"
                )
    with summary_path.open("x", encoding="utf-8") as output:
        json.dump(result.summary_dict(), output, allow_nan=False, indent=2, sort_keys=True)
        output.write("\n")
    return raw_path, plot_path, summary_path


def _main(argv: Sequence[str]) -> int:
    if len(argv) == 2 and argv[0] == "--worker-payload":
        return _worker_entry(argv[1])
    raise SystemExit("q4_scaling is an internal worker module; use run_q4_scaling.py")


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


__all__ = [
    "Q4_AXES",
    "Q4_PLOT_FILENAME",
    "Q4_RAW_FILENAME",
    "Q4_SUMMARY_FILENAME",
    "Q4ExperimentResult",
    "Q4Measurement",
    "ScalingPoint",
    "make_scaling_points",
    "measure_scaling_point",
    "run_bounded_measurement",
    "run_q4_scaling",
    "scaling_point_grammar_sha256",
    "write_q4_artifacts",
]
