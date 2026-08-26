"""Strict immutable configuration contract shared by all experiment drivers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import cast

EXPERIMENT_CONFIG_SCHEMA_VERSION = 1
RESOLVED_CONFIG_ARTIFACT_KIND = "mwpc_resolved_experiment_config"
RESOLVED_CONFIG_FILENAME = "resolved-config.json"

_EXPERIMENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_GRAMMAR_HASH_POLICIES = frozenset(
    {
        "sha256_canonical_grammar",
        "sha256_per_instance",
    }
)


class ExperimentKind(StrEnum):
    """The five research-question experiment families."""

    CORRECTNESS = "correctness"
    HEURISTIC_GAP = "heuristic_gap"
    FINITE_SLOTS = "finite_slots"
    SCALING = "scaling"
    END_TO_END = "end_to_end"


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} keys must be strings")
    return cast(Mapping[str, object], value)


def _exact_fields(
    data: Mapping[str, object],
    *,
    required: Collection[str],
    field_name: str,
) -> None:
    required_fields = set(required)
    missing = required_fields - set(data)
    if missing:
        raise ValueError(f"missing {field_name} fields: {', '.join(sorted(missing))}")
    unknown = set(data) - required_fields
    if unknown:
        raise ValueError(f"unknown {field_name} fields: {', '.join(sorted(unknown))}")


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _positive_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{field_name} must be finite and positive")
    return result


def _seeds(value: object) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("seeds must be a finite sequence")
    result = tuple(_integer(seed, "seeds[]") for seed in value)
    if not result:
        raise ValueError("seeds must be non-empty")
    if len(set(result)) != len(result):
        raise ValueError("seeds must not contain duplicates")
    return result


def _freeze_json(value: object, field_name: str) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{field_name} must not contain NaN or infinity")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{field_name} keys must be strings")
            frozen[key] = _freeze_json(item, f"{field_name}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, field_name) for item in value)
    raise TypeError(f"{field_name} must contain only JSON-compatible values")


def _freeze_json_mapping(value: object, field_name: str) -> Mapping[str, object]:
    frozen = _freeze_json(_mapping(value, field_name), field_name)
    if not isinstance(frozen, Mapping):
        raise AssertionError("mapping freeze returned a non-mapping")
    return cast(Mapping[str, object], frozen)


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _thaw_json(value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """Fully resolved, immutable configuration for one experiment family."""

    schema_version: int
    experiment_id: str
    question: ExperimentKind
    description: str
    publication_mode: bool
    seeds: tuple[int, ...]
    repetitions: int
    exactness_scope: str
    exactness_guarantee: str
    require_independent_certificate: bool
    support_policy: str
    support_top_k: int
    support_k_max: int
    finite_slots: bool
    model_id: str
    model_revision: str
    tokenizer_id: str
    tokenizer_revision: str
    local_files_only: bool
    grammar_id: str
    grammar_source: str
    grammar_revision: str
    grammar_hash_policy: str
    solver_timeout_seconds: float
    run_timeout_seconds: float
    device: str
    dtype: str
    cpu_threads: int
    cuda_device: int | None
    synchronize_cuda: bool
    parameters: Mapping[str, object]

    def __post_init__(self) -> None:
        schema_version = _integer(self.schema_version, "schema_version", minimum=1)
        if schema_version != EXPERIMENT_CONFIG_SCHEMA_VERSION:
            raise ValueError(
                "unsupported experiment config schema_version: "
                f"{self.schema_version}; expected {EXPERIMENT_CONFIG_SCHEMA_VERSION}"
            )
        experiment_id = _string(self.experiment_id, "experiment_id")
        if _EXPERIMENT_ID_PATTERN.fullmatch(experiment_id) is None:
            raise ValueError(
                "experiment_id must contain only lowercase letters, digits, '.', '_', or '-'"
            )
        if not isinstance(self.question, ExperimentKind):
            raise TypeError("question must be an ExperimentKind")
        _string(self.description, "description")
        _boolean(self.publication_mode, "publication_mode")
        normalized_seeds = _seeds(self.seeds)
        object.__setattr__(self, "seeds", normalized_seeds)
        _integer(self.repetitions, "repetitions", minimum=1)

        if self.exactness_scope != "exact_on_support":
            raise ValueError("exactness.scope must be exact_on_support")
        if self.exactness_guarantee != "per_step":
            raise ValueError("exactness.guarantee must be per_step")
        if self.require_independent_certificate is not True:
            raise ValueError("exact experiments must require independent certificate validation")

        _string(self.support_policy, "support.policy")
        _integer(self.support_top_k, "support.top_k", minimum=1)
        _integer(self.support_k_max, "support.k_max", minimum=1)
        if self.support_k_max < self.support_top_k:
            raise ValueError("support.k_max must be at least support.top_k")
        if self.finite_slots is not True:
            raise ValueError("experiment support must use finite token slots")

        for field_name, value in (
            ("model.model_id", self.model_id),
            ("model.model_revision", self.model_revision),
            ("model.tokenizer_id", self.tokenizer_id),
            ("model.tokenizer_revision", self.tokenizer_revision),
            ("grammar.grammar_id", self.grammar_id),
            ("grammar.source", self.grammar_source),
            ("grammar.revision", self.grammar_revision),
        ):
            _string(value, field_name)
        _boolean(self.local_files_only, "model.local_files_only")
        if self.grammar_hash_policy not in _GRAMMAR_HASH_POLICIES:
            allowed = ", ".join(sorted(_GRAMMAR_HASH_POLICIES))
            raise ValueError(f"grammar.hash_policy must be one of: {allowed}")

        solver_timeout = _positive_float(
            self.solver_timeout_seconds, "timeouts.solver_seconds"
        )
        run_timeout = _positive_float(self.run_timeout_seconds, "timeouts.run_seconds")
        object.__setattr__(self, "solver_timeout_seconds", solver_timeout)
        object.__setattr__(self, "run_timeout_seconds", run_timeout)
        if run_timeout < solver_timeout:
            raise ValueError("timeouts.run_seconds must be at least timeouts.solver_seconds")

        device = _string(self.device, "hardware.device")
        _string(self.dtype, "hardware.dtype")
        _integer(self.cpu_threads, "hardware.cpu_threads", minimum=1)
        if self.cuda_device is not None:
            _integer(self.cuda_device, "hardware.cuda_device")
        _boolean(self.synchronize_cuda, "hardware.synchronize_cuda")
        if device.startswith("cuda"):
            if self.cuda_device is None:
                raise ValueError("CUDA experiments require hardware.cuda_device")
        elif self.cuda_device is not None or self.synchronize_cuda:
            raise ValueError(
                "non-CUDA experiments cannot set a CUDA device or request CUDA synchronization"
            )

        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters, "parameters"),
        )

    @classmethod
    def from_dict(cls, value: object) -> ExperimentConfig:
        """Validate a parsed TOML mapping without applying implicit defaults."""

        data = _mapping(value, "experiment config")
        _exact_fields(
            data,
            required={
                "schema_version",
                "experiment_id",
                "question",
                "description",
                "publication_mode",
                "seeds",
                "repetitions",
                "exactness",
                "support",
                "model",
                "grammar",
                "timeouts",
                "hardware",
                "parameters",
            },
            field_name="experiment config",
        )
        exactness = _mapping(data["exactness"], "exactness")
        support = _mapping(data["support"], "support")
        model = _mapping(data["model"], "model")
        grammar = _mapping(data["grammar"], "grammar")
        timeouts = _mapping(data["timeouts"], "timeouts")
        hardware = _mapping(data["hardware"], "hardware")
        _exact_fields(
            exactness,
            required={"scope", "guarantee", "require_independent_certificate"},
            field_name="exactness",
        )
        _exact_fields(
            support,
            required={"policy", "top_k", "k_max", "finite_slots"},
            field_name="support",
        )
        _exact_fields(
            model,
            required={
                "model_id",
                "model_revision",
                "tokenizer_id",
                "tokenizer_revision",
                "local_files_only",
            },
            field_name="model",
        )
        _exact_fields(
            grammar,
            required={"grammar_id", "source", "revision", "hash_policy"},
            field_name="grammar",
        )
        _exact_fields(
            timeouts,
            required={"solver_seconds", "run_seconds"},
            field_name="timeouts",
        )
        _exact_fields(
            hardware,
            required={"device", "dtype", "cpu_threads", "cuda_device", "synchronize_cuda"},
            field_name="hardware",
        )

        raw_cuda_device = hardware["cuda_device"]
        if raw_cuda_device is None or raw_cuda_device == "none":
            cuda_device = None
        else:
            cuda_device = _integer(raw_cuda_device, "hardware.cuda_device")

        try:
            question = ExperimentKind(_string(data["question"], "question"))
        except ValueError as error:
            allowed = ", ".join(kind.value for kind in ExperimentKind)
            raise ValueError(f"question must be one of: {allowed}") from error

        return cls(
            schema_version=_integer(data["schema_version"], "schema_version", minimum=1),
            experiment_id=_string(data["experiment_id"], "experiment_id"),
            question=question,
            description=_string(data["description"], "description"),
            publication_mode=_boolean(data["publication_mode"], "publication_mode"),
            seeds=_seeds(data["seeds"]),
            repetitions=_integer(data["repetitions"], "repetitions", minimum=1),
            exactness_scope=_string(exactness["scope"], "exactness.scope"),
            exactness_guarantee=_string(exactness["guarantee"], "exactness.guarantee"),
            require_independent_certificate=_boolean(
                exactness["require_independent_certificate"],
                "exactness.require_independent_certificate",
            ),
            support_policy=_string(support["policy"], "support.policy"),
            support_top_k=_integer(support["top_k"], "support.top_k", minimum=1),
            support_k_max=_integer(support["k_max"], "support.k_max", minimum=1),
            finite_slots=_boolean(support["finite_slots"], "support.finite_slots"),
            model_id=_string(model["model_id"], "model.model_id"),
            model_revision=_string(model["model_revision"], "model.model_revision"),
            tokenizer_id=_string(model["tokenizer_id"], "model.tokenizer_id"),
            tokenizer_revision=_string(
                model["tokenizer_revision"], "model.tokenizer_revision"
            ),
            local_files_only=_boolean(model["local_files_only"], "model.local_files_only"),
            grammar_id=_string(grammar["grammar_id"], "grammar.grammar_id"),
            grammar_source=_string(grammar["source"], "grammar.source"),
            grammar_revision=_string(grammar["revision"], "grammar.revision"),
            grammar_hash_policy=_string(grammar["hash_policy"], "grammar.hash_policy"),
            solver_timeout_seconds=_positive_float(
                timeouts["solver_seconds"], "timeouts.solver_seconds"
            ),
            run_timeout_seconds=_positive_float(
                timeouts["run_seconds"], "timeouts.run_seconds"
            ),
            device=_string(hardware["device"], "hardware.device"),
            dtype=_string(hardware["dtype"], "hardware.dtype"),
            cpu_threads=_integer(
                hardware["cpu_threads"], "hardware.cpu_threads", minimum=1
            ),
            cuda_device=cuda_device,
            synchronize_cuda=_boolean(
                hardware["synchronize_cuda"], "hardware.synchronize_cuda"
            ),
            parameters=_freeze_json_mapping(data["parameters"], "parameters"),
        )

    def to_dict(self) -> dict[str, object]:
        """Return the complete normalized JSON-compatible configuration."""

        return {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "question": self.question.value,
            "description": self.description,
            "publication_mode": self.publication_mode,
            "seeds": list(self.seeds),
            "repetitions": self.repetitions,
            "exactness": {
                "scope": self.exactness_scope,
                "guarantee": self.exactness_guarantee,
                "require_independent_certificate": self.require_independent_certificate,
            },
            "support": {
                "policy": self.support_policy,
                "top_k": self.support_top_k,
                "k_max": self.support_k_max,
                "finite_slots": self.finite_slots,
            },
            "model": {
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                "tokenizer_id": self.tokenizer_id,
                "tokenizer_revision": self.tokenizer_revision,
                "local_files_only": self.local_files_only,
            },
            "grammar": {
                "grammar_id": self.grammar_id,
                "source": self.grammar_source,
                "revision": self.grammar_revision,
                "hash_policy": self.grammar_hash_policy,
            },
            "timeouts": {
                "solver_seconds": self.solver_timeout_seconds,
                "run_seconds": self.run_timeout_seconds,
            },
            "hardware": {
                "device": self.device,
                "dtype": self.dtype,
                "cpu_threads": self.cpu_threads,
                "cuda_device": self.cuda_device,
                "synchronize_cuda": self.synchronize_cuda,
            },
            "parameters": _thaw_json(self.parameters),
        }

    @property
    def config_sha256(self) -> str:
        """Hash the normalized resolved values, independent of TOML formatting."""

        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load and strictly resolve one UTF-8 TOML experiment configuration."""

    config_path = Path(path)
    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return ExperimentConfig.from_dict(parsed)


def _resolved_config_bytes(config: ExperimentConfig) -> bytes:
    if not isinstance(config, ExperimentConfig):
        raise TypeError("config must be an ExperimentConfig")
    artifact = {
        "artifact_kind": RESOLVED_CONFIG_ARTIFACT_KIND,
        "schema_version": 1,
        "config_sha256": config.config_sha256,
        "resolved_config": config.to_dict(),
    }
    rendered = json.dumps(
        artifact,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return f"{rendered}\n".encode()


def save_resolved_config(config: ExperimentConfig, run_directory: str | Path) -> Path:
    """Persist the resolved config once, accepting only byte-identical reruns."""

    content = _resolved_config_bytes(config)
    destination_directory = Path(run_directory)
    destination_directory.mkdir(parents=True, exist_ok=True)
    destination = destination_directory / RESOLVED_CONFIG_FILENAME
    try:
        with destination.open("xb") as output:
            output.write(content)
    except FileExistsError:
        if destination.read_bytes() != content:
            raise FileExistsError(
                f"refusing to overwrite a different resolved config at {destination}"
            ) from None
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    """Validate and materialize one resolved configuration for a run directory."""

    parser = argparse.ArgumentParser(
        prog="mwpc-resolve-experiment-config",
        description="Validate, hash, and save an immutable MWPC experiment configuration.",
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-directory", required=True, type=Path)
    arguments = parser.parse_args(argv)
    config = load_experiment_config(arguments.config)
    destination = save_resolved_config(config, arguments.run_directory)
    print(
        json.dumps(
            {
                "config_sha256": config.config_sha256,
                "resolved_config_path": str(destination),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
