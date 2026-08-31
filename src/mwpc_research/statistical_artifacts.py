"""Strict raw-row loader and deterministic statistical-summary artifact builder."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from mwpc_exact.experiments.metadata import canonical_json_sha256
from mwpc_research.statistical_summaries import (
    DEFAULT_CONFIDENCE_LEVEL,
    OperationalEvent,
    summarize_gaps,
    summarize_operational_rates,
    summarize_proportion,
    summarize_runtime_comparison,
)

STATISTICAL_ARTIFACT_SCHEMA_VERSION = 1
STATISTICAL_OBSERVATION_KIND = "mwpc_statistical_observation"
STATISTICAL_SUMMARY_KIND = "mwpc_statistical_summary"
STATISTICAL_INTERPRETATION = "synthetic_formula_regression_fixture_not_experimental_result"

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact_fields(
    value: Mapping[str, object],
    required: set[str],
    field_name: str,
) -> None:
    missing = required - set(value)
    if missing:
        raise ValueError(f"missing {field_name} fields: {', '.join(sorted(missing))}")
    unknown = set(value) - required
    if unknown:
        raise ValueError(f"unknown {field_name} fields: {', '.join(sorted(unknown))}")


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return cast(Mapping[str, object], value)


def _safe_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    return value


def _relative_path(value: object, field_name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{field_name} must stay inside the repository")
    return path


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _finite_non_negative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    result = float(value)
    if not 0.0 <= result < float("inf"):
        raise ValueError(f"{field_name} must be finite and non-negative")
    return result


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _schema_version(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value != STATISTICAL_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(f"unsupported {field_name}")
    return value


def _event(value: object, field_name: str) -> OperationalEvent:
    raw = _mapping(value, field_name)
    _exact_fields(
        raw,
        {"fallback_used", "timed_out", "support_expanded"},
        field_name,
    )
    return OperationalEvent(
        fallback_used=_boolean(raw["fallback_used"], f"{field_name}.fallback_used"),
        timed_out=_boolean(raw["timed_out"], f"{field_name}.timed_out"),
        support_expanded=_boolean(
            raw["support_expanded"],
            f"{field_name}.support_expanded",
        ),
    )


@dataclass(frozen=True, slots=True)
class StatisticalObservation:
    """One explicit optimizer-step observation and its generation-level flags."""

    observation_id: str
    generation_id: str
    agreement: bool
    exact_score: float
    comparator_score: float
    baseline_runtime_seconds: float
    candidate_runtime_seconds: float
    step_events: OperationalEvent
    generation_events: OperationalEvent

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> StatisticalObservation:
        _exact_fields(
            value,
            {
                "artifact_kind",
                "schema_version",
                "observation_id",
                "generation_id",
                "agreement",
                "exact_score",
                "comparator_score",
                "baseline_runtime_seconds",
                "candidate_runtime_seconds",
                "step_events",
                "generation_events",
            },
            "statistical observation",
        )
        if value["artifact_kind"] != STATISTICAL_OBSERVATION_KIND:
            raise ValueError("unexpected statistical observation artifact_kind")
        _schema_version(value["schema_version"], "statistical observation schema_version")
        return cls(
            observation_id=_safe_id(value["observation_id"], "observation_id"),
            generation_id=_safe_id(value["generation_id"], "generation_id"),
            agreement=_boolean(value["agreement"], "agreement"),
            exact_score=_finite_non_negative(value["exact_score"], "exact_score"),
            comparator_score=_finite_non_negative(
                value["comparator_score"],
                "comparator_score",
            ),
            baseline_runtime_seconds=_finite_non_negative(
                value["baseline_runtime_seconds"],
                "baseline_runtime_seconds",
            ),
            candidate_runtime_seconds=_finite_non_negative(
                value["candidate_runtime_seconds"],
                "candidate_runtime_seconds",
            ),
            step_events=_event(value["step_events"], "step_events"),
            generation_events=_event(value["generation_events"], "generation_events"),
        )


@dataclass(frozen=True, slots=True)
class StatisticalArtifactConfig:
    """Pinned source and destination for a statistical summary artifact."""

    artifact_id: str
    input_jsonl: Path
    expected_sha256: str
    output_json: Path
    confidence_level: float
    normalized_sha256: str
    file_sha256: str


def load_statistical_artifact_config(path: str | Path) -> StatisticalArtifactConfig:
    """Load one strict versioned TOML configuration."""

    config_path = Path(path)
    payload = config_path.read_bytes()
    try:
        value = tomllib.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"invalid statistical artifact TOML: {config_path}") from error
    raw = _mapping(value, "statistical artifact config")
    _exact_fields(
        raw,
        {
            "schema_version",
            "artifact_id",
            "input_jsonl",
            "expected_sha256",
            "output_json",
            "confidence_level",
        },
        "statistical artifact config",
    )
    _schema_version(raw["schema_version"], "statistical artifact config schema_version")
    confidence = _finite_non_negative(raw["confidence_level"], "confidence_level")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence_level must be strictly between zero and one")
    input_path = _relative_path(raw["input_jsonl"], "input_jsonl")
    output_path = _relative_path(raw["output_json"], "output_json")
    if input_path == output_path:
        raise ValueError("input_jsonl and output_json must be distinct")
    return StatisticalArtifactConfig(
        artifact_id=_safe_id(raw["artifact_id"], "artifact_id"),
        input_jsonl=input_path,
        expected_sha256=_digest(raw["expected_sha256"], "expected_sha256"),
        output_json=output_path,
        confidence_level=confidence,
        normalized_sha256=canonical_json_sha256(raw),
        file_sha256=_sha256_bytes(payload),
    )


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"raw JSONL contains non-finite constant: {value}")


def load_statistical_observations(path: str | Path) -> tuple[StatisticalObservation, ...]:
    """Load strict newline-terminated JSONL observations."""

    input_path = Path(path)
    payload = input_path.read_bytes()
    if not payload or not payload.endswith(b"\n"):
        raise ValueError("statistical JSONL must be non-empty and newline-terminated")
    observations: list[StatisticalObservation] = []
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            raise ValueError(f"statistical JSONL line {line_number} is blank")
        try:
            value = json.loads(raw_line, parse_constant=_reject_json_constant)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid statistical JSONL line {line_number}") from error
        observations.append(
            StatisticalObservation.from_dict(
                _mapping(value, f"statistical JSONL line {line_number}")
            )
        )
    if len({item.observation_id for item in observations}) != len(observations):
        raise ValueError("statistical observation IDs must be unique")
    generation_events: dict[str, OperationalEvent] = {}
    for observation in observations:
        previous = generation_events.setdefault(
            observation.generation_id,
            observation.generation_events,
        )
        if previous != observation.generation_events:
            raise ValueError("generation event flags must agree within each generation")
    return tuple(observations)


def summarize_statistical_observations(
    observations: Sequence[StatisticalObservation],
    *,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> dict[str, object]:
    """Compute every T1202 statistic from explicit raw observations."""

    rows = tuple(observations)
    if not rows:
        raise ValueError("statistical summary requires at least one observation")
    if not all(isinstance(row, StatisticalObservation) for row in rows):
        raise TypeError("observations must contain StatisticalObservation values")
    if len({row.observation_id for row in rows}) != len(rows):
        raise ValueError("statistical observation IDs must be unique")
    generation_events: dict[str, OperationalEvent] = {}
    for row in rows:
        previous = generation_events.setdefault(row.generation_id, row.generation_events)
        if previous != row.generation_events:
            raise ValueError("generation event flags must agree within each generation")
    return {
        "benchmark_claim": False,
        "interpretation": STATISTICAL_INTERPRETATION,
        "observation_count": len(rows),
        "generation_count": len(generation_events),
        "analysis_units": {
            "agreement": "optimizer_step",
            "gap": "paired_optimizer_step_score",
            "runtime": "optimizer_step",
            "operational_rates": ["optimizer_step", "generation"],
        },
        "agreement": summarize_proportion(
            sum(row.agreement for row in rows),
            len(rows),
            analysis_unit="optimizer_step",
            confidence_level=confidence_level,
        ).to_dict(),
        "gap": summarize_gaps(
            tuple(row.exact_score for row in rows),
            tuple(row.comparator_score for row in rows),
            confidence_level=confidence_level,
        ).to_dict(),
        "runtime": summarize_runtime_comparison(
            tuple(row.candidate_runtime_seconds for row in rows),
            tuple(row.baseline_runtime_seconds for row in rows),
        ).to_dict(),
        "operational_rates": {
            "per_step": summarize_operational_rates(
                tuple(row.step_events for row in rows),
                analysis_unit="optimizer_step",
                confidence_level=confidence_level,
            ).to_dict(),
            "per_generation": summarize_operational_rates(
                tuple(generation_events.values()),
                analysis_unit="generation",
                confidence_level=confidence_level,
            ).to_dict(),
        },
    }


@dataclass(frozen=True, slots=True)
class StatisticalArtifactBuildResult:
    """Created or verified statistical artifact identity."""

    output_path: Path
    output_sha256: str
    source_sha256: str
    verified_existing: bool


def _resolved_within(repository_root: Path, relative: Path, field_name: str) -> Path:
    root = repository_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field_name} resolves outside the repository")
    return resolved


def build_statistical_artifact(
    config_path: str | Path,
    *,
    repository_root: str | Path,
    verify_existing: bool = False,
) -> StatisticalArtifactBuildResult:
    """Build or byte-verify a statistical JSON artifact from pinned raw JSONL."""

    if not isinstance(verify_existing, bool):
        raise TypeError("verify_existing must be a boolean")
    root = Path(repository_root).resolve()
    config_file = Path(config_path).resolve()
    if not config_file.is_relative_to(root):
        raise ValueError("statistical artifact config must be inside the repository")
    config = load_statistical_artifact_config(config_file)
    input_path = _resolved_within(root, config.input_jsonl, "input_jsonl")
    output_path = _resolved_within(root, config.output_json, "output_json")
    raw_directory = input_path.parent
    processed_directory = output_path.parent
    if (
        raw_directory == processed_directory
        or raw_directory.is_relative_to(processed_directory)
        or processed_directory.is_relative_to(raw_directory)
    ):
        raise ValueError("raw and processed statistical directories must be non-nested")
    source_sha256 = _sha256_file(input_path)
    if source_sha256 != config.expected_sha256:
        raise ValueError(
            "statistical raw artifact hash mismatch: "
            f"expected {config.expected_sha256}, observed {source_sha256}"
        )
    observations = load_statistical_observations(input_path)
    summary = {
        "artifact_kind": STATISTICAL_SUMMARY_KIND,
        "schema_version": STATISTICAL_ARTIFACT_SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "configuration": {
            "path": config_file.relative_to(root).as_posix(),
            "normalized_sha256": config.normalized_sha256,
            "file_sha256": config.file_sha256,
        },
        "source": {
            "path": config.input_jsonl.as_posix(),
            "sha256": source_sha256,
            "row_count": len(observations),
        },
        **summarize_statistical_observations(
            observations,
            confidence_level=config.confidence_level,
        ),
    }
    payload = (json.dumps(summary, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    if _sha256_file(input_path) != source_sha256:
        raise RuntimeError("statistical raw artifact changed while summary was being built")
    if verify_existing:
        if not output_path.is_file():
            raise FileNotFoundError(f"statistical artifact is missing: {output_path}")
        if output_path.read_bytes() != payload:
            raise ValueError(f"statistical artifact differs from raw input: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("xb") as output:
            output.write(payload)
    return StatisticalArtifactBuildResult(
        output_path=output_path,
        output_sha256=_sha256_bytes(payload),
        source_sha256=source_sha256,
        verified_existing=verify_existing,
    )


__all__ = [
    "STATISTICAL_ARTIFACT_SCHEMA_VERSION",
    "STATISTICAL_INTERPRETATION",
    "STATISTICAL_OBSERVATION_KIND",
    "STATISTICAL_SUMMARY_KIND",
    "StatisticalArtifactBuildResult",
    "StatisticalArtifactConfig",
    "StatisticalObservation",
    "build_statistical_artifact",
    "load_statistical_artifact_config",
    "load_statistical_observations",
    "summarize_statistical_observations",
]
