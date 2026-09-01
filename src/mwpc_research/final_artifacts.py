"""Deterministic T1203 tables and figures derived from pinned experiment rows."""

from __future__ import annotations

import hashlib
import html
import json
import re
import tomllib
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path
from typing import cast

from mwpc_exact.experiments.metadata import canonical_json_sha256
from mwpc_research.statistical_summaries import (
    summarize_gaps,
    summarize_numeric_distribution,
    summarize_proportion,
    summarize_runtime_comparison,
)

FINAL_ARTIFACT_SCHEMA_VERSION = 1
FINAL_RESULTS_KIND = "mwpc_final_results"
FINAL_MANIFEST_KIND = "mwpc_final_artifact_manifest"
FINAL_RESULTS_FILENAME = "final-results.json"
FINAL_MANIFEST_FILENAME = "artifact-manifest.json"
CORRECTNESS_TABLE_FILENAME = "correctness-oracle-table.tex"
HEURISTIC_GAP_TABLE_FILENAME = "heuristic-gap-table.tex"
HEURISTIC_GAP_FIGURE_FILENAME = "heuristic-gap-distribution.svg"
FINITE_SLOT_TABLE_FILENAME = "finite-slot-counterexample-table.tex"
RUNTIME_TABLE_FILENAME = "runtime-breakdown-table.tex"
SCALING_FIGURE_FILENAME = "runtime-scaling.svg"
END_TO_END_TABLE_FILENAME = "end-to-end-comparison-table.tex"

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_KINDS = {
    "q1_correctness": "mwpc_q1_correctness_case",
    "q2_heuristic_gap": "mwpc_q2_heuristic_gap_row",
    "q3_finite_slots": "mwpc_q3_finite_slot_row",
    "q4_scaling": "mwpc_q4_scaling_row",
    "q5_end_to_end": "mwpc_q5_end_to_end_row",
}
_INPUT_ROLES = frozenset(_EXPECTED_KINDS)
_SOURCE_INTERPRETATIONS = {
    "q1_correctness": "finite_support_correctness_campaign_not_runtime_benchmark",
    "q2_heuristic_gap": "configured_synthetic_gap_diagnostic_not_model_benchmark",
    "q3_finite_slots": "curated_finite_slot_counterexample_evidence",
    "q4_scaling": "component_profiled_cpu_smoke_not_publication_benchmark",
    "q5_end_to_end": "fixed_task_live_model_diagnostic_not_publication_benchmark",
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return cast(Mapping[str, object], value)


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence")
    return cast(Sequence[object], value)


def _required(value: Mapping[str, object], field_name: str, *fields: str) -> None:
    missing = set(fields) - set(value)
    if missing:
        raise ValueError(f"missing {field_name} fields: {', '.join(sorted(missing))}")


def _exact_fields(value: Mapping[str, object], required: set[str], field_name: str) -> None:
    _required(value, field_name, *required)
    unknown = set(value) - required
    if unknown:
        raise ValueError(f"unknown {field_name} fields: {', '.join(sorted(unknown))}")


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _safe_id(value: object, field_name: str) -> str:
    result = _string(value, field_name)
    if _SAFE_ID.fullmatch(result) is None:
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    return result


def _relative_path(value: object, field_name: str) -> Path:
    path = Path(_string(value, field_name))
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{field_name} must stay inside the repository")
    return path


def _digest(value: object, field_name: str) -> str:
    result = _string(value, field_name)
    if _SHA256.fullmatch(result) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return result


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _number(value: object, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    result = float(value)
    if not isfinite(result) or result < minimum:
        raise ValueError(f"{field_name} must be finite and at least {minimum}")
    return result


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _optional_number(value: object, field_name: str) -> float | None:
    return None if value is None else _number(value, field_name)


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"raw JSONL contains non-finite constant: {value}")


@dataclass(frozen=True, slots=True)
class FinalArtifactInput:
    """One pinned experiment-row input and its semantic role."""

    role: str
    raw_jsonl: Path
    expected_sha256: str

    def __post_init__(self) -> None:
        if self.role not in _INPUT_ROLES:
            raise ValueError(f"unsupported final-artifact input role: {self.role}")
        _relative_path(self.raw_jsonl.as_posix(), "inputs[].raw_jsonl")
        _digest(self.expected_sha256, "inputs[].expected_sha256")


@dataclass(frozen=True, slots=True)
class FinalArtifactConfig:
    """Strict configuration for one raw-to-final-artifact build."""

    schema_version: int
    artifact_id: str
    processed_directory: Path
    paper_directory: Path
    confidence_level: float
    inputs: tuple[FinalArtifactInput, ...]
    normalized_sha256: str
    file_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != FINAL_ARTIFACT_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {FINAL_ARTIFACT_SCHEMA_VERSION}")
        _safe_id(self.artifact_id, "artifact_id")
        _relative_path(self.processed_directory.as_posix(), "processed_directory")
        _relative_path(self.paper_directory.as_posix(), "paper_directory")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be strictly between zero and one")
        roles = {item.role for item in self.inputs}
        if roles != _INPUT_ROLES or len(self.inputs) != len(_INPUT_ROLES):
            raise ValueError("inputs must contain each Q1--Q5 role exactly once")
        if len({item.raw_jsonl for item in self.inputs}) != len(self.inputs):
            raise ValueError("raw_jsonl paths must be unique")
        _digest(self.normalized_sha256, "normalized_sha256")
        _digest(self.file_sha256, "file_sha256")


def load_final_artifact_config(path: str | Path) -> FinalArtifactConfig:
    """Load a versioned T1203 build configuration with exact fields."""

    config_path = Path(path)
    payload = config_path.read_bytes()
    try:
        raw = tomllib.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"invalid final-artifact TOML: {config_path}") from error
    root = _mapping(raw, "final-artifact config")
    _exact_fields(
        root,
        {
            "schema_version",
            "artifact_id",
            "processed_directory",
            "paper_directory",
            "confidence_level",
            "inputs",
        },
        "final-artifact config",
    )
    raw_inputs = _sequence(root["inputs"], "inputs")
    inputs: list[FinalArtifactInput] = []
    for index, raw_input in enumerate(raw_inputs):
        item = _mapping(raw_input, f"inputs[{index}]")
        _exact_fields(
            item,
            {"role", "raw_jsonl", "expected_sha256"},
            f"inputs[{index}]",
        )
        inputs.append(
            FinalArtifactInput(
                role=_string(item["role"], f"inputs[{index}].role"),
                raw_jsonl=_relative_path(item["raw_jsonl"], f"inputs[{index}].raw_jsonl"),
                expected_sha256=_digest(
                    item["expected_sha256"],
                    f"inputs[{index}].expected_sha256",
                ),
            )
        )
    return FinalArtifactConfig(
        schema_version=_integer(root["schema_version"], "schema_version", minimum=1),
        artifact_id=_safe_id(root["artifact_id"], "artifact_id"),
        processed_directory=_relative_path(root["processed_directory"], "processed_directory"),
        paper_directory=_relative_path(root["paper_directory"], "paper_directory"),
        confidence_level=_number(root["confidence_level"], "confidence_level", minimum=0.0),
        inputs=tuple(inputs),
        normalized_sha256=canonical_json_sha256(raw),
        file_sha256=_sha256_bytes(payload),
    )


@dataclass(frozen=True, slots=True)
class _LoadedInput:
    declaration: FinalArtifactInput
    rows: tuple[Mapping[str, object], ...]
    run_metadata: Mapping[str, object]
    observed_sha256: str


def _load_input(path: Path, declaration: FinalArtifactInput) -> _LoadedInput:
    observed = _sha256_file(path)
    if observed != declaration.expected_sha256:
        raise ValueError(
            f"raw hash mismatch for {declaration.role}: expected "
            f"{declaration.expected_sha256}, observed {observed}"
        )
    payload = path.read_bytes()
    if not payload or not payload.endswith(b"\n"):
        raise ValueError("raw JSONL must be non-empty and newline-terminated")
    rows: list[Mapping[str, object]] = []
    metadata: Mapping[str, object] | None = None
    metadata_hash: str | None = None
    expected_kind = _EXPECTED_KINDS[declaration.role]
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            raise ValueError(f"raw JSONL line {line_number} is blank")
        try:
            value = json.loads(raw_line, parse_constant=_reject_json_constant)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid raw JSONL line {line_number}") from error
        row = _mapping(value, f"raw JSONL line {line_number}")
        _required(
            row, f"raw JSONL line {line_number}", "artifact_kind", "schema_version", "run_metadata"
        )
        if row["artifact_kind"] != expected_kind:
            raise ValueError(
                f"unexpected artifact_kind for {declaration.role} on line {line_number}"
            )
        if _integer(row["schema_version"], "schema_version", minimum=1) != 1:
            raise ValueError("unsupported raw row schema_version")
        row_metadata = _mapping(row["run_metadata"], "run_metadata")
        current_metadata_hash = canonical_json_sha256(row_metadata)
        if metadata is None:
            metadata = row_metadata
            metadata_hash = current_metadata_hash
        elif current_metadata_hash != metadata_hash:
            raise ValueError(f"run_metadata differs within {declaration.role}")
        rows.append(row)
    assert metadata is not None
    _required(
        metadata,
        "run_metadata",
        "git_commit",
        "git_dirty",
        "config_sha256",
        "run_id",
        "exactness_scope",
        "exactness_guarantee",
    )
    if _boolean(metadata["git_dirty"], "run_metadata.git_dirty"):
        raise ValueError(f"{declaration.role} was produced from a dirty worktree")
    if metadata["exactness_scope"] != "exact_on_support":
        raise ValueError(f"{declaration.role} does not declare exact_on_support")
    if metadata["exactness_guarantee"] != "per_step":
        raise ValueError(f"{declaration.role} does not declare a per-step guarantee")
    if declaration.role == "q5_end_to_end" and metadata.get("benchmark_claim") is not False:
        raise ValueError("Q5 raw rows must explicitly reject a benchmark claim")
    if _sha256_file(path) != observed:
        raise RuntimeError("raw artifact changed while final artifacts were being built")
    return _LoadedInput(declaration, tuple(rows), metadata, observed)


def _status_counts(values: Sequence[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _configured_set_agreement(event_count: int, observation_count: int) -> dict[str, object]:
    return {
        "analysis_unit": "finite_support_case",
        "event_count": event_count,
        "observation_count": observation_count,
        "rate": event_count / observation_count,
        "uncertainty_method": "not_applicable_complete_configured_set",
    }


def _q1_summary(rows: Sequence[Mapping[str, object]], confidence_level: float) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for index, row in enumerate(rows):
        family = _string(row.get("family"), f"q1[{index}].family")
        agreement = _boolean(row.get("agreement"), f"q1[{index}].agreement")
        if not agreement:
            raise ValueError(f"Q1 correctness disagreement in row {index}")
        grouped[family].append(row)

    family_order = tuple(
        name for name in ("canonical", "exhaustive", "randomized") if name in grouped
    ) + tuple(sorted(set(grouped) - {"canonical", "exhaustive", "randomized"}))
    output_rows: list[dict[str, object]] = []
    for family, family_rows in (
        *((name, grouped[name]) for name in family_order),
        ("overall", list(rows)),
    ):
        statuses: list[str] = []
        for index, row in enumerate(family_rows):
            solvers = _mapping(row.get("solver_statuses"), f"q1.{family}[{index}].solver_statuses")
            _required(
                solvers,
                "q1 solver_statuses",
                "exhaustive_oracle",
                "python_reference",
                "rust_production",
            )
            statuses.append(_string(solvers["exhaustive_oracle"], "exhaustive_oracle status"))
        agreement_summary: dict[str, object]
        if family == "randomized":
            agreement_summary = cast(
                dict[str, object],
                summarize_proportion(
                    len(family_rows),
                    len(family_rows),
                    analysis_unit="finite_support_case",
                    confidence_level=confidence_level,
                ).to_dict(),
            )
            agreement_summary["uncertainty_method"] = "wilson_score_seeded_randomized_family"
        else:
            agreement_summary = _configured_set_agreement(
                len(family_rows),
                len(family_rows),
            )
        output_rows.append(
            {
                "family": family,
                "case_count": len(family_rows),
                "agreement": agreement_summary,
                "oracle_status_counts": _status_counts(statuses),
            }
        )
    randomized_rows = grouped.get("randomized", [])
    randomized_seeds = sorted(
        _integer(row.get("seed"), f"q1.randomized[{index}].seed")
        for index, row in enumerate(randomized_rows)
    )
    randomized_sampling: dict[str, object] | None = None
    if randomized_seeds:
        randomized_sampling = {
            "generator": "mwpc_research.q1_correctness.generate_random_finite_lattice_instance",
            "seed_selection": "consecutive_integer_seeds",
            "seed_count": len(randomized_seeds),
            "unique_seed_count": len(set(randomized_seeds)),
            "minimum_seed": min(randomized_seeds),
            "maximum_seed": max(randomized_seeds),
            "seeds_are_consecutive": randomized_seeds
            == list(range(min(randomized_seeds), max(randomized_seeds) + 1)),
        }
    return {
        "interpretation": _SOURCE_INTERPRETATIONS["q1_correctness"],
        "exactness_scope": "exact_on_support",
        "case_count": len(rows),
        "failed_case_count": 0,
        "families": output_rows,
        "randomized_sampling": randomized_sampling,
    }


def _q2_summary(rows: Sequence[Mapping[str, object]], confidence_level: float) -> dict[str, object]:
    scores: dict[tuple[str, str], tuple[list[float], list[float]]] = {}
    runtime_seconds: dict[str, list[float]] = defaultdict(list)
    for index, row in enumerate(rows):
        if not _boolean(row.get("success"), f"q2[{index}].success"):
            raise ValueError(f"Q2 unsuccessful row {index}")
        weight_mode = _string(row.get("weight_mode"), f"q2[{index}].weight_mode")
        selector_results = _mapping(row.get("selector_results"), f"q2[{index}].selector_results")
        for selector, raw_result in selector_results.items():
            result = _mapping(raw_result, f"q2[{index}].selector_results.{selector}")
            runtime_seconds[selector].append(
                _number(result.get("runtime_seconds"), f"q2[{index}].{selector}.runtime")
            )
        comparisons = _mapping(row.get("comparisons"), f"q2[{index}].comparisons")
        for selector, raw_comparison in comparisons.items():
            comparison = _mapping(raw_comparison, f"q2[{index}].comparisons.{selector}")
            exact_score = _number(
                comparison.get("exact_score"), f"q2[{index}].{selector}.exact_score"
            )
            heuristic_score = _number(
                comparison.get("heuristic_score"),
                f"q2[{index}].{selector}.heuristic_score",
            )
            absolute_gap = _number(
                comparison.get("absolute_gap"),
                f"q2[{index}].{selector}.absolute_gap",
            )
            if not isclose(
                absolute_gap,
                exact_score - heuristic_score,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise ValueError(f"Q2 stored gap mismatch in row {index}")
            exact, heuristic = scores.setdefault((weight_mode, selector), ([], []))
            exact.append(exact_score)
            heuristic.append(heuristic_score)

    gap_rows: list[dict[str, object]] = []
    mode_order = {"unit": 0, "confidence": 1}
    selector_order = {"greedy_exact_feasibility": 0, "epic_regular_cover": 1}
    for (weight_mode, selector), (exact, heuristic) in sorted(
        scores.items(),
        key=lambda item: (
            mode_order.get(item[0][0], 99),
            selector_order.get(item[0][1], 99),
            item[0],
        ),
    ):
        gap_rows.append(
            {
                "weight_mode": weight_mode,
                "selector": selector,
                "statistics": summarize_gaps(
                    exact,
                    heuristic,
                    confidence_level=confidence_level,
                ).to_dict(),
            }
        )
    return {
        "interpretation": _SOURCE_INTERPRETATIONS["q2_heuristic_gap"],
        "exactness_scope": "exact_on_support",
        "case_count": len(rows),
        "gap_rows": gap_rows,
        "selector_runtime_seconds": {
            selector: summarize_numeric_distribution(values).to_dict()
            for selector, values in sorted(runtime_seconds.items())
        },
    }


def _q3_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    output_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        if not _boolean(row.get("success"), f"q3[{index}].success"):
            raise ValueError(f"Q3 unsuccessful row {index}")
        abstract = _mapping(row.get("abstract_decision"), f"q3[{index}].abstract")
        finite = _mapping(row.get("finite_decision"), f"q3[{index}].finite")
        slots = _mapping(row.get("slot_accounting"), f"q3[{index}].slots")
        comparison = _mapping(row.get("comparison"), f"q3[{index}].comparison")
        exactness = _mapping(finite.get("exactness_scope"), f"q3[{index}].exactness")
        if abstract.get("status") != "accepted":
            raise ValueError(f"Q3 abstract baseline did not accept row {index}")
        if comparison.get("abstract_witness_fits_finite_canvas") is not False:
            raise ValueError(f"Q3 abstract witness unexpectedly fits row {index}")
        if comparison.get("claim_supported") is not True:
            raise ValueError(f"Q3 counterexample claim is unsupported in row {index}")
        if exactness.get("claim") != "exact_on_support":
            raise ValueError(f"Q3 finite decision lacks exact_on_support in row {index}")
        output_rows.append(
            {
                "case_id": _string(row.get("case_id"), f"q3[{index}].case_id"),
                "title": _string(row.get("title"), f"q3[{index}].title"),
                "available_physical_slots": _integer(
                    slots.get("available_physical_slots"),
                    f"q3[{index}].available_physical_slots",
                ),
                "minimum_required_physical_tokens": _integer(
                    slots.get("minimum_required_physical_tokens"),
                    f"q3[{index}].minimum_required_physical_tokens",
                ),
                "slot_shortfall": _integer(
                    slots.get("slot_shortfall"), f"q3[{index}].slot_shortfall"
                ),
                "abstract_status": _string(abstract.get("status"), f"q3[{index}].abstract_status"),
                "abstract_objective_value": _number(
                    abstract.get("objective_value"),
                    f"q3[{index}].abstract_objective_value",
                ),
                "finite_status": _string(finite.get("status"), f"q3[{index}].finite_status"),
                "finite_objective_value": _optional_number(
                    finite.get("objective_value"),
                    f"q3[{index}].finite_objective_value",
                ),
                "finite_reason_code": _string(
                    finite.get("reason_code"), f"q3[{index}].finite_reason_code"
                ),
                "exactness_scope": "exact_on_support",
                "claim_supported": True,
            }
        )
    return {
        "interpretation": _SOURCE_INTERPRETATIONS["q3_finite_slots"],
        "case_count": len(output_rows),
        "counterexample_count": len(output_rows),
        "cases": output_rows,
    }


def _q4_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    status_values: list[str] = []
    component_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    backend_runtime: dict[str, list[float]] = defaultdict(list)
    scaling_values: dict[tuple[str, str, float], list[float]] = defaultdict(list)
    censored_count = 0
    for index, row in enumerate(rows):
        backend = _string(row.get("backend"), f"q4[{index}].backend")
        status = _string(row.get("status"), f"q4[{index}].status")
        status_values.append(status)
        censored = _boolean(row.get("censored"), f"q4[{index}].censored")
        censored_count += censored
        if censored or status != "optimal":
            continue
        if row.get("certificate_valid") is not True:
            raise ValueError(f"Q4 OPTIMAL row {index} lacks a valid certificate")
        runtime = _number(row.get("successful_runtime_seconds"), f"q4[{index}].runtime")
        backend_runtime[backend].append(runtime)
        axis = _string(row.get("axis"), f"q4[{index}].axis")
        axis_value = _number(row.get("axis_value"), f"q4[{index}].axis_value")
        scaling_values[(axis, backend, axis_value)].append(runtime)
        profile = _mapping(row.get("observed_profile"), f"q4[{index}].profile")
        timings = _mapping(profile.get("timings_seconds"), f"q4[{index}].timings")
        components = _mapping(timings.get("components"), f"q4[{index}].components")
        for component, value in components.items():
            component_values[(backend, component)].append(
                _number(value, f"q4[{index}].components.{component}")
            )
        for component in ("unattributed_measurement_overhead", "wall_span"):
            component_values[(backend, component)].append(
                _number(timings.get(component), f"q4[{index}].{component}")
            )

    component_order = {
        "proposal_policy": 0,
        "support_construction": 1,
        "token_lattice_construction": 2,
        "byte_lattice_expansion": 3,
        "parser": 4,
        "backtracking": 5,
        "validation": 6,
        "commit_update": 7,
        "unattributed_measurement_overhead": 8,
        "wall_span": 9,
    }
    breakdown = [
        {
            "backend": backend,
            "component": component,
            "runtime_seconds": summarize_numeric_distribution(values).to_dict(),
        }
        for (backend, component), values in sorted(
            component_values.items(),
            key=lambda item: (
                item[0][0],
                component_order.get(item[0][1], 99),
                item[0][1],
            ),
        )
    ]
    axis_order = {
        "slot_count": 0,
        "top_k": 1,
        "graph_size_scale": 2,
        "grammar_production_count": 3,
        "token_byte_length": 4,
        "proposal_count": 5,
    }
    scaling_series: list[dict[str, object]] = []
    series: dict[tuple[str, str], list[tuple[float, list[float]]]] = defaultdict(list)
    for (axis, backend, axis_value), values in scaling_values.items():
        series[(axis, backend)].append((axis_value, values))
    for (axis, backend), points in sorted(
        series.items(),
        key=lambda item: (
            axis_order.get(item[0][0], 99),
            item[0][0],
            item[0][1],
        ),
    ):
        scaling_series.append(
            {
                "axis": axis,
                "backend": backend,
                "points": [
                    {
                        "axis_value": axis_value,
                        "runtime_seconds": summarize_numeric_distribution(values).to_dict(),
                    }
                    for axis_value, values in sorted(points)
                ],
            }
        )
    return {
        "interpretation": _SOURCE_INTERPRETATIONS["q4_scaling"],
        "measurement_count": len(rows),
        "censored_count": censored_count,
        "status_counts": _status_counts(status_values),
        "backend_runtime_seconds": {
            backend: summarize_numeric_distribution(values).to_dict()
            for backend, values in sorted(backend_runtime.items())
        },
        "component_breakdown": breakdown,
        "scaling_series": scaling_series,
    }


def _q5_summary(rows: Sequence[Mapping[str, object]], confidence_level: float) -> dict[str, object]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    fingerprints: set[str] = set()
    for index, row in enumerate(rows):
        strategy = _string(row.get("strategy"), f"q5[{index}].strategy")
        grouped[strategy].append(row)
        fingerprints.add(
            _string(
                row.get("comparison_fingerprint"),
                f"q5[{index}].comparison_fingerprint",
            )
        )
    if len(fingerprints) != 1:
        raise ValueError("Q5 rows do not share one comparison fingerprint")

    strategy_order = ("unconstrained", "serial", "epic", "exact")
    if set(grouped) != set(strategy_order):
        raise ValueError("Q5 rows must contain unconstrained, serial, epic, and exact")
    method_rows: list[dict[str, object]] = []
    runtimes: dict[str, list[float]] = {}
    all_required_methods_passed = True
    for strategy in strategy_order:
        method = grouped[strategy]
        execution_statuses = [
            _string(row.get("execution_status"), f"q5.{strategy}.execution_status")
            for row in method
        ]
        complete = sum(status == "complete" for status in execution_statuses)
        syntactic = sum(
            _boolean(row.get("syntactic_valid"), f"q5.{strategy}.syntactic_valid") for row in method
        )
        functional = sum(
            _boolean(row.get("functional_success"), f"q5.{strategy}.functional_success")
            for row in method
        )
        successful_runtimes = [
            _number(
                _mapping(row.get("resources"), f"q5.{strategy}.resources").get("elapsed_seconds"),
                f"q5.{strategy}.elapsed_seconds",
            )
            for row, status in zip(method, execution_statuses, strict=True)
            if status == "complete"
        ]
        runtimes[strategy] = successful_runtimes
        batch_sizes = [
            _number(
                _mapping(row.get("generation"), f"q5.{strategy}.generation").get(
                    "average_commit_batch_size"
                ),
                f"q5.{strategy}.average_commit_batch_size",
            )
            for row in method
        ]
        fallback_generations = sum(
            _integer(
                _mapping(row.get("generation"), f"q5.{strategy}.generation").get("fallback_count"),
                f"q5.{strategy}.fallback_count",
            )
            > 0
            for row in method
        )
        timeout_generations = sum(status == "timeout" for status in execution_statuses)
        exact_statuses: list[str] = []
        support_expansion_generations: int | None = None
        if strategy == "exact":
            support_expansion_generations = 0
            for row in method:
                exact = _mapping(row.get("exact_solver"), "q5.exact.exact_solver")
                status = _string(exact.get("status"), "q5.exact.status")
                exact_statuses.append(status)
                if status == "optimal" and exact.get("certificate_valid") is not True:
                    raise ValueError("Q5 OPTIMAL row lacks an independently valid certificate")
                generation = _mapping(row.get("generation"), "q5.exact.generation")
                support_expansion_generations += (
                    _integer(
                        generation.get("support_expansion_count"),
                        "q5.exact.support_expansion_count",
                    )
                    > 0
                )
        passed = complete == len(method) and syntactic == len(method) and functional == len(method)
        if strategy == "exact":
            passed = passed and exact_statuses == ["optimal"] * len(method)
        all_required_methods_passed = all_required_methods_passed and passed
        method_rows.append(
            {
                "strategy": strategy,
                "generation_count": len(method),
                "execution_status_counts": _status_counts(execution_statuses),
                "complete": summarize_proportion(
                    complete,
                    len(method),
                    analysis_unit="generation",
                    confidence_level=confidence_level,
                ).to_dict(),
                "syntactic_validity": summarize_proportion(
                    syntactic,
                    len(method),
                    analysis_unit="generation",
                    confidence_level=confidence_level,
                ).to_dict(),
                "functional_success": summarize_proportion(
                    functional,
                    len(method),
                    analysis_unit="generation",
                    confidence_level=confidence_level,
                ).to_dict(),
                "runtime_seconds": summarize_numeric_distribution(successful_runtimes).to_dict(),
                "average_commit_batch_size": summarize_numeric_distribution(batch_sizes).to_dict(),
                "fallback_rate_per_generation": summarize_proportion(
                    fallback_generations,
                    len(method),
                    analysis_unit="generation",
                    confidence_level=confidence_level,
                ).to_dict(),
                "timeout_rate_per_generation": summarize_proportion(
                    timeout_generations,
                    len(method),
                    analysis_unit="generation",
                    confidence_level=confidence_level,
                ).to_dict(),
                "support_expansion_rate_per_generation": (
                    None
                    if support_expansion_generations is None
                    else summarize_proportion(
                        support_expansion_generations,
                        len(method),
                        analysis_unit="generation",
                        confidence_level=confidence_level,
                    ).to_dict()
                ),
                "exact_solver_status_counts": (
                    None if not exact_statuses else _status_counts(exact_statuses)
                ),
            }
        )
    exact_runtimes = runtimes["exact"]
    comparisons = {
        baseline: summarize_runtime_comparison(exact_runtimes, runtimes[baseline]).to_dict()
        for baseline in ("unconstrained", "serial", "epic")
    }
    return {
        "interpretation": _SOURCE_INTERPRETATIONS["q5_end_to_end"],
        "benchmark_claim": False,
        "analysis_unit": "generation",
        "step_level_rates": None,
        "step_level_rate_unavailability_reason": (
            "raw generation rows aggregate optimizer steps and do not retain "
            "one event record per step"
        ),
        "comparison_fingerprint": next(iter(fingerprints)),
        "all_required_methods_passed": all_required_methods_passed,
        "methods": method_rows,
        "exact_runtime_comparisons": comparisons,
    }


def _source_context(item: _LoadedInput) -> dict[str, object]:
    metadata = item.run_metadata
    nested_model = _mapping(metadata.get("model", {}), "run_metadata.model")
    comparison = _mapping(
        metadata.get("comparison_contract", {}),
        "run_metadata.comparison_contract",
    )
    model_id_value = metadata.get("model_id", nested_model.get("model_id"))
    model_revision_value = metadata.get("model_revision", nested_model.get("resolved_revision"))
    model_id = "not_applicable" if model_id_value is None else _string(model_id_value, "model_id")
    model_revision = (
        "not_applicable"
        if model_revision_value is None
        else _string(model_revision_value, "model_revision")
    )
    task_configuration: str
    if isinstance(metadata.get("dataset"), str):
        task_configuration = _string(metadata["dataset"], "dataset")
    elif "task_ids" in comparison:
        task_configuration = ",".join(
            _string(value, "task_id") for value in _sequence(comparison["task_ids"], "task_ids")
        )
    elif isinstance(metadata.get("grammar_id"), str):
        task_configuration = _string(metadata["grammar_id"], "grammar_id")
    else:
        task_configuration = "not_applicable"
    top_k = metadata.get("support_top_k")
    k_max = metadata.get("support_k_max")
    return {
        "run_id": _string(metadata["run_id"], "run_id"),
        "model_id": model_id,
        "model_revision": model_revision,
        "task_configuration": task_configuration,
        "support_top_k": (None if top_k is None else _integer(top_k, "support_top_k")),
        "support_k_max": (None if k_max is None else _integer(k_max, "support_k_max")),
        "exactness_scope": "exact_on_support",
        "exactness_guarantee": "per_step",
    }


def _source_entry(item: _LoadedInput) -> dict[str, object]:
    metadata = item.run_metadata
    return {
        "role": item.declaration.role,
        "path": item.declaration.raw_jsonl.as_posix(),
        "sha256": item.observed_sha256,
        "row_count": len(item.rows),
        "artifact_kind": _EXPECTED_KINDS[item.declaration.role],
        "interpretation": _SOURCE_INTERPRETATIONS[item.declaration.role],
        "producing_git_commit": _string(metadata["git_commit"], "git_commit"),
        "run_id": _string(metadata["run_id"], "run_id"),
        "config_sha256": _digest(metadata["config_sha256"], "config_sha256"),
        "exactness_scope": "exact_on_support",
        "exactness_guarantee": "per_step",
        "timing_scope": metadata.get("timing_scope"),
        "benchmark_claim": metadata.get("benchmark_claim"),
        "analysis_context": _source_context(item),
    }


def _latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def _percentage(value: object) -> str:
    return f"{_number(value, 'rate') * 100.0:.1f}"


def _generated_table(lines: Sequence[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def _caption_context(summary: Mapping[str, object]) -> str:
    context = _mapping(summary["source_context"], "source_context")
    model_id = _string(context["model_id"], "model_id")
    model_revision = _string(context["model_revision"], "model_revision")
    model = _latex_escape(model_id)
    if model_revision != "not_applicable":
        model += "@" + _latex_escape(model_revision[:12])
    support_parts = [r"\texttt{exact\_on\_support}"]
    if context["support_top_k"] is not None:
        support_parts.append(f"top-K={_integer(context['support_top_k'], 'support_top_k')}")
    if context["support_k_max"] is not None:
        support_parts.append(f"Kmax={_integer(context['support_k_max'], 'support_k_max')}")
    return (
        f"run \\texttt{{{_latex_escape(_string(context['run_id'], 'run_id'))}}}; "
        f"{', '.join(support_parts)}; model \\texttt{{{model}}}; task "
        f"\\texttt{{{_latex_escape(_string(context['task_configuration'], 'task'))}}}"
    )


def _plain_context(summary: Mapping[str, object]) -> str:
    context = _mapping(summary["source_context"], "source_context")
    model = _string(context["model_id"], "model_id")
    revision = _string(context["model_revision"], "model_revision")
    if revision != "not_applicable":
        model += "@" + revision[:12]
    support = "exact_on_support"
    if context["support_top_k"] is not None:
        support += f", top-K={_integer(context['support_top_k'], 'support_top_k')}"
    if context["support_k_max"] is not None:
        support += f", Kmax={_integer(context['support_k_max'], 'support_k_max')}"
    return (
        f"run {_string(context['run_id'], 'run_id')}; {support}; model {model}; "
        f"task {_string(context['task_configuration'], 'task')}"
    )


def _correctness_table(summary: Mapping[str, object]) -> bytes:
    context = _caption_context(summary)
    sampling = summary.get("randomized_sampling")
    sampling_note = "No randomized family was configured."
    if sampling is not None:
        randomized_sampling = _mapping(sampling, "q1 randomized_sampling")
        sampling_note = (
            "The Wilson interval applies only to the seeded randomized family "
            f"(consecutive seeds {_integer(randomized_sampling['minimum_seed'], 'minimum_seed')}--"
            f"{_integer(randomized_sampling['maximum_seed'], 'maximum_seed')})."
        )
    lines = [
        "% Generated by scripts/exact_commit/build_final_artifacts.py.",
        "% Every numeric value is derived from pinned Q1 raw rows.",
        r"\begin{table}[t]",
        r"\centering",
        (
            r"\caption{Agreement of the exhaustive oracle, independent Python "
            r"reference, and Rust production solver on finite represented support "
            f"({context}).}}"
        ),
        r"\label{tab:mwpc-correctness-oracle}",
        r"\begin{tabular}{p{4.0cm}rrlr}",
        r"\toprule",
        r"Family & Cases & Agreement & 95\% Wilson CI & Oracle OPT/INF \\",
        r"\midrule",
    ]
    for raw_row in _sequence(summary["families"], "q1 families"):
        row = _mapping(raw_row, "q1 family")
        agreement = _mapping(row["agreement"], "q1 agreement")
        statuses = _mapping(row["oracle_status_counts"], "q1 statuses")
        family = _string(row["family"], "family")
        family_label = {
            "canonical": "Canonical",
            "exhaustive": "Exhaustive configured family",
            "randomized": "Randomized seeds",
            "overall": "Overall configured cases",
        }.get(family, family)
        interval = "--"
        if family == "randomized":
            interval = (
                f"[{_percentage(agreement['confidence_interval_lower'])}, "
                f"{_percentage(agreement['confidence_interval_upper'])}]"
            )
        lines.append(
            f"{_latex_escape(family_label)} & "
            f"{_integer(row['case_count'], 'case_count')} & "
            f"{_integer(agreement['event_count'], 'agreement event_count')}/"
            f"{_integer(agreement['observation_count'], 'agreement observation_count')} & "
            f"{interval} & "
            f"{_integer(statuses.get('optimal', 0), 'optimal_count')}/"
            f"{_integer(statuses.get('infeasible_on_support', 0), 'infeasible_count')} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Canonical and exhaustive families are complete "
                r"configured sets, and the overall row mixes fixed and randomized "
                r"cases; sampling intervals do not apply to those rows. "
                f"{sampling_note} Complete agreement was observed on every configured "
                r"case. Exactness is per optimizer step and only over "
                r"each represented finite support; INF means "
                r"\texttt{INFEASIBLE\_ON\_SUPPORT}, not timeout."
            ),
            r"\end{table}",
        )
    )
    return _generated_table(lines)


def _selector_label(selector: str) -> str:
    return {
        "greedy_exact_feasibility": "Serial greedy",
        "epic_regular_cover": "EPIC regular cover",
    }.get(selector, selector)


def _heuristic_gap_table(summary: Mapping[str, object]) -> bytes:
    context = _caption_context(summary)
    lines = [
        "% Generated by scripts/exact_commit/build_final_artifacts.py.",
        "% Gap values are recomputed from paired exact and heuristic raw scores.",
        r"\begin{table}[t]",
        r"\centering",
        f"\\caption{{Heuristic MWPC gaps on configured synthetic states ({context}).}}",
        r"\label{tab:mwpc-heuristic-gaps}",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Weights & Selector & Pairs & Equal (\%) & Abs. gap median [IQR] & Rel. gap median \\",
        r"\midrule",
    ]
    for raw_row in _sequence(summary["gap_rows"], "gap_rows"):
        row = _mapping(raw_row, "gap row")
        statistics = _mapping(row["statistics"], "gap statistics")
        equality = _mapping(statistics["equality"], "gap equality")
        absolute = _mapping(statistics["absolute_gap"], "absolute gap")
        relative = _mapping(statistics["relative_gap"], "relative gap")
        lines.append(
            f"{_latex_escape(_string(row['weight_mode'], 'weight_mode'))} & "
            f"{_latex_escape(_selector_label(_string(row['selector'], 'selector')))} & "
            f"{_integer(statistics['comparison_count'], 'comparison_count')} & "
            f"{_percentage(equality['rate'])} & "
            f"{_number(absolute['median'], 'absolute median'):.3f} "
            f"[{_number(absolute['iqr'], 'absolute iqr'):.3f}] & "
            f"{_number(relative['median'], 'relative median'):.3f} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Diagnostic synthetic campaign; not a model "
                r"benchmark. Relative gaps are undefined and excluded when the "
                r"exact optimum is zero."
            ),
            r"\end{table}",
        )
    )
    return _generated_table(lines)


def _heuristic_gap_figure(summary: Mapping[str, object]) -> bytes:
    context = html.escape(_plain_context(summary), quote=True)
    rows = [_mapping(value, "gap row") for value in _sequence(summary["gap_rows"], "gap_rows")]
    maxima = [
        _number(
            _mapping(_mapping(row["statistics"], "statistics")["absolute_gap"], "gap")["maximum"],
            "maximum gap",
        )
        for row in rows
    ]
    maximum = max(maxima, default=0.0)
    width = 980
    top = 112
    row_height = 64
    height = top + len(rows) * row_height + 70
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            '<text x="24" y="32" font-family="sans-serif" font-size="21" '
            'font-weight="bold">Synthetic heuristic absolute gaps</text>'
        ),
        (
            f'<text x="24" y="57" font-family="sans-serif" font-size="13" '
            f'fill="#444">{context}</text>'
        ),
        (
            '<rect x="650" y="70" width="18" height="14" fill="#2f6f9f"/>'
            '<text x="675" y="83" font-family="sans-serif" '
            'font-size="13">median</text>'
        ),
        (
            '<rect x="760" y="70" width="18" height="14" fill="#c96f24"/>'
            '<text x="785" y="83" font-family="sans-serif" '
            'font-size="13">maximum</text>'
        ),
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        statistics = _mapping(row["statistics"], "statistics")
        absolute = _mapping(statistics["absolute_gap"], "absolute_gap")
        median = _number(absolute["median"], "median gap")
        row_maximum = _number(absolute["maximum"], "maximum gap")
        scale = 0.0 if maximum == 0.0 else 520.0 / maximum
        median_width = median * scale
        maximum_width = row_maximum * scale
        label = html.escape(
            f"{_string(row['weight_mode'], 'weight_mode')} / "
            f"{_selector_label(_string(row['selector'], 'selector'))}",
            quote=True,
        )
        lines.extend(
            (
                f'<text x="24" y="{y + 23}" font-family="sans-serif" font-size="14">{label}</text>',
                f'<rect x="300" y="{y}" width="{maximum_width:.3f}" height="18" fill="#c96f24"/>',
                (
                    f'<rect x="300" y="{y + 23}" width="{median_width:.3f}" '
                    'height="18" fill="#2f6f9f"/>'
                ),
                (
                    f'<text x="{312 + maximum_width:.3f}" y="{y + 14}" '
                    f'font-family="sans-serif" font-size="12">{row_maximum:.3f}</text>'
                ),
                (
                    f'<text x="{312 + median_width:.3f}" y="{y + 37}" '
                    f'font-family="sans-serif" font-size="12">{median:.3f}</text>'
                ),
            )
        )
    lines.extend(
        (
            (
                f'<text x="24" y="{height - 24}" font-family="sans-serif" '
                'font-size="13" fill="#444">Configured synthetic states; '
                "diagnostic only, not a model benchmark.</text>"
            ),
            "</svg>",
            "",
        )
    )
    return "\n".join(lines).encode("utf-8")


def _finite_slot_table(summary: Mapping[str, object]) -> bytes:
    context = _caption_context(summary)
    lines = [
        "% Generated by scripts/exact_commit/build_final_artifacts.py.",
        "% Counterexample values come directly from independently validated Q3 rows.",
        r"\begin{table}[t]",
        r"\centering",
        (
            r"\caption{Finite-slot counterexamples to an abstract unbounded-gap "
            f"baseline ({context}).}}"
        ),
        r"\label{tab:mwpc-finite-slot-counterexamples}",
        r"\small",
        r"\begin{tabular}{p{5.0cm}rrlll}",
        r"\toprule",
        r"Case & Slots & Required & Abstract & Finite exact-on-support & Objective \\",
        r"\midrule",
    ]
    for raw_row in _sequence(summary["cases"], "q3 cases"):
        row = _mapping(raw_row, "q3 case")
        objective = row["finite_objective_value"]
        objective_text = "--" if objective is None else f"{_number(objective, 'objective'):.1f}"
        lines.append(
            f"{_latex_escape(_string(row['title'], 'title'))} & "
            f"{_integer(row['available_physical_slots'], 'available slots')} & "
            f"{_integer(row['minimum_required_physical_tokens'], 'required tokens')} & "
            f"{_latex_escape(_string(row['abstract_status'], 'abstract status'))} & "
            f"{_latex_escape(_string(row['finite_status'], 'finite status'))} & "
            f"{objective_text} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Each abstract witness needs more physical tokens "
                r"than the configured canvas permits. "
                r"\texttt{INFEASIBLE\_ON\_SUPPORT} remains distinct from timeout."
            ),
            r"\end{table}",
        )
    )
    return _generated_table(lines)


def _component_label(component: str) -> str:
    return {
        "proposal_policy": "Proposal policy",
        "support_construction": "Support construction",
        "token_lattice_construction": "Token lattice",
        "byte_lattice_expansion": "Byte expansion",
        "parser": "Parser",
        "backtracking": "Backtracking",
        "validation": "Validation",
        "commit_update": "Commit update",
        "unattributed_measurement_overhead": "Unattributed overhead",
        "wall_span": "Measured wall span",
    }.get(component, component)


def _runtime_table(summary: Mapping[str, object]) -> bytes:
    context = _caption_context(summary)
    lines = [
        "% Generated by scripts/exact_commit/build_final_artifacts.py.",
        "% Component medians and IQRs are computed from uncensored OPTIMAL Q4 rows.",
        r"\begin{table}[t]",
        r"\centering",
        f"\\caption{{Exact-commit CPU component timing breakdown ({context}).}}",
        r"\label{tab:mwpc-runtime-breakdown}",
        r"\small",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"Backend & Component & Samples & Median (ms) & IQR (ms) \\",
        r"\midrule",
    ]
    previous_backend: str | None = None
    for raw_row in _sequence(summary["component_breakdown"], "component_breakdown"):
        row = _mapping(raw_row, "component row")
        backend = _string(row["backend"], "backend")
        runtime = _mapping(row["runtime_seconds"], "runtime")
        if previous_backend is not None and backend != previous_backend:
            lines.append(r"\addlinespace")
        previous_backend = backend
        lines.append(
            f"{_latex_escape(backend)} & "
            f"{_latex_escape(_component_label(_string(row['component'], 'component')))} & "
            f"{_integer(runtime['count'], 'runtime count')} & "
            f"{_number(runtime['median'], 'runtime median') * 1000.0:.4f} & "
            f"{_number(runtime['iqr'], 'runtime iqr') * 1000.0:.4f} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Component-profiled CPU scaling smoke; not a "
                r"publication benchmark. TIMEOUT and censored rows, if present, are "
                r"counted separately and excluded from timing distributions."
            ),
            r"\end{table}",
        )
    )
    return _generated_table(lines)


def _axis_label(axis: str) -> str:
    return {
        "slot_count": "Physical slots",
        "top_k": "Top-K",
        "graph_size_scale": "Graph-size scale",
        "grammar_production_count": "Grammar productions",
        "token_byte_length": "Token byte length",
        "proposal_count": "Proposal count",
    }.get(axis, axis)


def _scale_x(value: float, minimum: float, maximum: float, left: float, right: float) -> float:
    if minimum == maximum:
        return (left + right) / 2.0
    return left + (value - minimum) * (right - left) / (maximum - minimum)


def _scale_y(value: float, limit: float, top: float, bottom: float) -> float:
    return bottom - value * (bottom - top) / limit


def _scaling_figure(summary: Mapping[str, object]) -> bytes:
    grouped: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(dict)
    for raw_series in _sequence(summary["scaling_series"], "scaling_series"):
        series = _mapping(raw_series, "scaling series")
        axis = _string(series["axis"], "axis")
        backend = _string(series["backend"], "backend")
        points: list[tuple[float, float]] = []
        for raw_point in _sequence(series["points"], "scaling points"):
            point = _mapping(raw_point, "scaling point")
            runtime = _mapping(point["runtime_seconds"], "scaling runtime")
            points.append(
                (
                    _number(point["axis_value"], "axis_value"),
                    _number(runtime["median"], "runtime median") * 1000.0,
                )
            )
        grouped[axis][backend] = sorted(points)
    axis_order = (
        "slot_count",
        "top_k",
        "graph_size_scale",
        "grammar_production_count",
        "token_byte_length",
        "proposal_count",
    )
    axes = tuple(axis for axis in axis_order if axis in grouped)
    if not axes:
        raise ValueError("scaling figure requires at least one axis")

    width = 1040
    panel_width = 500
    panel_height = 205
    top = 105
    rows = (len(axes) + 1) // 2
    height = top + rows * panel_height + 45
    context = html.escape(_plain_context(summary), quote=True)
    colors = {"python": "#2f6f9f", "rust": "#c96f24"}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            '<text x="24" y="31" font-family="sans-serif" font-size="21" '
            'font-weight="bold">CPU exact-on-support scaling diagnostic</text>'
        ),
        (
            f'<text x="24" y="55" font-family="sans-serif" font-size="12" '
            f'fill="#444">{context}</text>'
        ),
        (
            '<text x="24" y="76" font-family="sans-serif" font-size="12" '
            'fill="#444">Median measured wall span; generated instances; '
            "not a publication benchmark.</text>"
        ),
        '<line x1="770" y1="28" x2="798" y2="28" stroke="#2f6f9f" stroke-width="3"/>',
        '<text x="806" y="32" font-family="sans-serif" font-size="13">python</text>',
        '<line x1="890" y1="28" x2="918" y2="28" stroke="#c96f24" stroke-width="3"/>',
        '<text x="926" y="32" font-family="sans-serif" font-size="13">rust</text>',
    ]
    for index, axis in enumerate(axes):
        column = index % 2
        row_index = index // 2
        panel_x = 20 + column * panel_width
        panel_y = top + row_index * panel_height
        plot_left = panel_x + 70
        plot_right = panel_x + 465
        plot_top = panel_y + 38
        plot_bottom = panel_y + 165
        backend_points = grouped[axis]
        all_points = [point for points in backend_points.values() for point in points]
        x_min = min(value for value, _ in all_points)
        x_max = max(value for value, _ in all_points)
        y_max = max(runtime for _, runtime in all_points)
        y_limit = 1.0 if y_max == 0.0 else y_max * 1.1

        lines.extend(
            (
                f'<text x="{panel_x + 10}" y="{panel_y + 20}" '
                f'font-family="sans-serif" font-size="15" font-weight="bold">'
                f"{html.escape(_axis_label(axis), quote=True)}</text>",
                f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" '
                f'y2="{plot_bottom}" stroke="#555"/>',
                f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" '
                f'y2="{plot_bottom}" stroke="#555"/>',
                f'<text x="{panel_x + 7}" y="{plot_top + 5}" '
                f'font-family="sans-serif" font-size="11">{y_limit:.2f} ms</text>',
                f'<text x="{plot_left - 4}" y="{plot_bottom + 18}" '
                f'font-family="sans-serif" font-size="11">{x_min:g}</text>',
                f'<text x="{plot_right - 18}" y="{plot_bottom + 18}" '
                f'font-family="sans-serif" font-size="11">{x_max:g}</text>',
            )
        )
        for backend in ("python", "rust"):
            points = backend_points.get(backend, [])
            if not points:
                continue
            coordinates = [
                (
                    _scale_x(value, x_min, x_max, plot_left, plot_right),
                    _scale_y(runtime, y_limit, plot_top, plot_bottom),
                )
                for value, runtime in points
            ]
            color = colors[backend]
            path = " ".join(
                f"{'M' if point_index == 0 else 'L'} {x:.3f} {y:.3f}"
                for point_index, (x, y) in enumerate(coordinates)
            )
            lines.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"/>')
            lines.extend(
                f'<circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="{color}"/>' for x, y in coordinates
            )
    lines.extend(
        (
            f'<text x="24" y="{height - 18}" font-family="sans-serif" '
            'font-size="12" fill="#444">Each point is recomputed from uncensored '
            "OPTIMAL rows; other statuses remain separately counted.</text>",
            "</svg>",
            "",
        )
    )
    return "\n".join(lines).encode("utf-8")


def _end_to_end_table(summary: Mapping[str, object]) -> bytes:
    comparisons = _mapping(summary["exact_runtime_comparisons"], "runtime comparisons")
    context = _caption_context(summary)
    lines = [
        "% Generated by scripts/exact_commit/build_final_artifacts.py.",
        "% Q5 rows explicitly carry benchmark_claim=false.",
        r"\begin{table}[t]",
        r"\centering",
        f"\\caption{{Pinned LLaDA fixed-task end-to-end diagnostic ({context}).}}",
        r"\label{tab:mwpc-end-to-end}",
        r"\scriptsize",
        r"\begin{tabular}{lrrrrrrrrl}",
        r"\toprule",
        (
            r"Strategy & Runs & Complete & Syntax & Functional & F/T/E gen. & "
            r"Batch & Runtime ms [IQR] & Exact/method & Exact status \\"
        ),
        r"\midrule",
    ]
    for raw_row in _sequence(summary["methods"], "q5 methods"):
        row = _mapping(raw_row, "q5 method")
        strategy = _string(row["strategy"], "strategy")
        runtime = _mapping(row["runtime_seconds"], "runtime")
        batch = _mapping(row["average_commit_batch_size"], "batch")
        complete = _mapping(row["complete"], "complete")
        syntactic = _mapping(row["syntactic_validity"], "syntactic")
        functional = _mapping(row["functional_success"], "functional")
        fallback = _mapping(row["fallback_rate_per_generation"], "fallback")
        timeout = _mapping(row["timeout_rate_per_generation"], "timeout")
        expansion_value = row["support_expansion_rate_per_generation"]
        expansion_text = "--"
        if expansion_value is not None:
            expansion = _mapping(expansion_value, "support expansion")
            expansion_text = str(_integer(expansion["event_count"], "support expansion count"))
        exact_statuses = row["exact_solver_status_counts"]
        exact_status_text = "--"
        if exact_statuses is not None:
            statuses = _mapping(exact_statuses, "exact statuses")
            exact_status_text = f"OPTIMAL ({_integer(statuses.get('optimal', 0), 'optimal')})"
        ratio = 1.0
        if strategy != "exact":
            comparison = _mapping(comparisons[strategy], f"comparison.{strategy}")
            ratio = _number(comparison["median_runtime_ratio"], "runtime ratio")
        strategy_label = "EPIC-enabled (serial fallback)" if strategy == "epic" else strategy
        lines.append(
            f"{_latex_escape(strategy_label)} & "
            f"{_integer(row['generation_count'], 'generation_count')} & "
            f"{_integer(complete['event_count'], 'complete_count')} & "
            f"{_integer(syntactic['event_count'], 'syntactic_count')} & "
            f"{_integer(functional['event_count'], 'functional_count')} & "
            f"{_integer(fallback['event_count'], 'fallback_count')}/"
            f"{_integer(timeout['event_count'], 'timeout_count')}/{expansion_text} & "
            f"{_number(batch['mean'], 'batch mean'):.2f} & "
            f"{_number(runtime['median'], 'runtime median') * 1000.0:.2f} "
            f"[{_number(runtime['iqr'], 'runtime iqr') * 1000.0:.2f}] & "
            f"{ratio:.2f}$\\times$ & {_latex_escape(exact_status_text)} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Eight warm, balanced-cyclic repetitions of one "
                r"literal-output task. This validates live integration and timing "
                r"instrumentation only (\texttt{benchmark\_claim=false}); it is not "
                r"a publication benchmark. F/T/E denotes generations with fallback, "
                r"timeout, or support expansion; -- is not applicable. Rates are per "
                r"generation; step-level rates are unavailable from these aggregated "
                r"rows. The EPIC row is an EPIC-enabled decoder with serial fallback "
                r"on the configured single-token task."
            ),
            r"\end{table}",
        )
    )
    return _generated_table(lines)


@dataclass(frozen=True, slots=True)
class FinalArtifactBuildResult:
    """Paths and hashes for one created or verified T1203 artifact bundle."""

    artifact_id: str
    source_sha256: Mapping[str, str]
    output_sha256: Mapping[str, str]
    verified_existing: bool


def _resolved_within(repository_root: Path, relative: Path, field_name: str) -> Path:
    root = repository_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field_name} resolves outside the repository")
    return resolved


def build_final_artifacts(
    config_path: str | Path,
    *,
    repository_root: str | Path,
    verify_existing: bool = False,
) -> FinalArtifactBuildResult:
    """Create or byte-verify final tables and figures from five pinned raw inputs."""

    if not isinstance(verify_existing, bool):
        raise TypeError("verify_existing must be a boolean")
    root = Path(repository_root).resolve()
    config_file = Path(config_path).resolve()
    if not config_file.is_relative_to(root):
        raise ValueError("final-artifact config must be inside the repository")
    config = load_final_artifact_config(config_file)
    processed = _resolved_within(root, config.processed_directory, "processed_directory")
    paper = _resolved_within(root, config.paper_directory, "paper_directory")
    if processed == paper or processed.is_relative_to(paper) or paper.is_relative_to(processed):
        raise ValueError("processed and paper directories must be distinct and non-nested")

    loaded: dict[str, _LoadedInput] = {}
    for declaration in config.inputs:
        raw_path = _resolved_within(root, declaration.raw_jsonl, "raw_jsonl")
        if raw_path.is_relative_to(processed) or raw_path.is_relative_to(paper):
            raise ValueError("raw artifacts cannot live inside derived output directories")
        loaded[declaration.role] = _load_input(raw_path, declaration)

    correctness = _q1_summary(loaded["q1_correctness"].rows, config.confidence_level)
    heuristic_gap = _q2_summary(loaded["q2_heuristic_gap"].rows, config.confidence_level)
    finite_slots = _q3_summary(loaded["q3_finite_slots"].rows)
    runtime_breakdown = _q4_summary(loaded["q4_scaling"].rows)
    end_to_end = _q5_summary(loaded["q5_end_to_end"].rows, config.confidence_level)
    for role, summary in (
        ("q1_correctness", correctness),
        ("q2_heuristic_gap", heuristic_gap),
        ("q3_finite_slots", finite_slots),
        ("q4_scaling", runtime_breakdown),
        ("q5_end_to_end", end_to_end),
    ):
        summary["source_context"] = _source_context(loaded[role])

    results: dict[str, object] = {
        "artifact_kind": FINAL_RESULTS_KIND,
        "schema_version": FINAL_ARTIFACT_SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "configuration": {
            "path": config_file.relative_to(root).as_posix(),
            "normalized_sha256": config.normalized_sha256,
            "file_sha256": config.file_sha256,
            "confidence_level": config.confidence_level,
        },
        "sources": [
            _source_entry(loaded[role])
            for role in (
                "q1_correctness",
                "q2_heuristic_gap",
                "q3_finite_slots",
                "q4_scaling",
                "q5_end_to_end",
            )
        ],
        "correctness": correctness,
        "heuristic_gap": heuristic_gap,
        "finite_slots": finite_slots,
        "runtime_breakdown": runtime_breakdown,
        "end_to_end": end_to_end,
    }
    results_payload = (
        json.dumps(results, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    rendered: dict[Path, bytes] = {
        processed / FINAL_RESULTS_FILENAME: results_payload,
        paper / CORRECTNESS_TABLE_FILENAME: _correctness_table(
            _mapping(results["correctness"], "correctness")
        ),
        paper / HEURISTIC_GAP_TABLE_FILENAME: _heuristic_gap_table(
            _mapping(results["heuristic_gap"], "heuristic_gap")
        ),
        paper / HEURISTIC_GAP_FIGURE_FILENAME: _heuristic_gap_figure(
            _mapping(results["heuristic_gap"], "heuristic_gap")
        ),
        paper / FINITE_SLOT_TABLE_FILENAME: _finite_slot_table(
            _mapping(results["finite_slots"], "finite_slots")
        ),
        paper / RUNTIME_TABLE_FILENAME: _runtime_table(
            _mapping(results["runtime_breakdown"], "runtime_breakdown")
        ),
        paper / SCALING_FIGURE_FILENAME: _scaling_figure(
            _mapping(results["runtime_breakdown"], "runtime_breakdown")
        ),
        paper / END_TO_END_TABLE_FILENAME: _end_to_end_table(
            _mapping(results["end_to_end"], "end_to_end")
        ),
    }
    generated_entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_bytes(payload),
        }
        for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix())
    ]
    manifest = {
        "artifact_kind": FINAL_MANIFEST_KIND,
        "schema_version": FINAL_ARTIFACT_SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "configuration": results["configuration"],
        "sources": results["sources"],
        "generated_artifacts": generated_entries,
    }
    rendered[processed / FINAL_MANIFEST_FILENAME] = (
        json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    for item in loaded.values():
        raw_path = _resolved_within(root, item.declaration.raw_jsonl, "raw_jsonl")
        if _sha256_file(raw_path) != item.observed_sha256:
            raise RuntimeError("raw artifact changed while final artifacts were rendered")
    if verify_existing:
        for path, expected in rendered.items():
            if not path.is_file():
                raise FileNotFoundError(f"generated artifact is missing: {path}")
            if path.read_bytes() != expected:
                raise ValueError(f"generated artifact differs from raw inputs: {path}")
    else:
        existing = [path for path in rendered if path.exists()]
        if existing:
            raise FileExistsError(
                "refusing to overwrite derived artifacts: "
                + ", ".join(path.as_posix() for path in sorted(existing))
            )
        processed.mkdir(parents=True, exist_ok=True)
        paper.mkdir(parents=True, exist_ok=True)
        for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix()):
            with path.open("xb") as output:
                output.write(payload)

    return FinalArtifactBuildResult(
        artifact_id=config.artifact_id,
        source_sha256={
            item.declaration.raw_jsonl.as_posix(): item.observed_sha256 for item in loaded.values()
        },
        output_sha256={
            path.relative_to(root).as_posix(): _sha256_bytes(payload)
            for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix())
        },
        verified_existing=verify_existing,
    )


__all__ = [
    "CORRECTNESS_TABLE_FILENAME",
    "END_TO_END_TABLE_FILENAME",
    "FINAL_ARTIFACT_SCHEMA_VERSION",
    "FINAL_MANIFEST_FILENAME",
    "FINAL_MANIFEST_KIND",
    "FINAL_RESULTS_FILENAME",
    "FINAL_RESULTS_KIND",
    "FINITE_SLOT_TABLE_FILENAME",
    "HEURISTIC_GAP_FIGURE_FILENAME",
    "HEURISTIC_GAP_TABLE_FILENAME",
    "RUNTIME_TABLE_FILENAME",
    "SCALING_FIGURE_FILENAME",
    "FinalArtifactBuildResult",
    "FinalArtifactConfig",
    "FinalArtifactInput",
    "build_final_artifacts",
    "load_final_artifact_config",
]
