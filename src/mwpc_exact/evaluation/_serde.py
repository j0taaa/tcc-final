"""Private strict JSON and numeric helpers for benchmark artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection, Mapping, Sequence
from math import isfinite, isnan
from types import MappingProxyType
from typing import cast


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} keys must be strings")
    return cast(Mapping[str, object], value)


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    return cast(Sequence[object], value)


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return value


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _string(value, field_name)


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _exact_fields(
    data: Mapping[str, object],
    *,
    required: set[str],
    optional: Collection[str] = (),
    field_name: str,
) -> None:
    missing = required - set(data)
    if missing:
        raise ValueError(f"missing {field_name} fields: {', '.join(sorted(missing))}")
    unknown = set(data) - required - set(optional)
    if unknown:
        raise ValueError(f"unknown {field_name} fields: {', '.join(sorted(unknown))}")


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


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _validate_sha256(value: object, field_name: str) -> str:
    digest = _string(value, field_name)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return digest


def _float(value: object, field_name: str, *, allow_infinity: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{field_name} is outside the supported float range") from error
    if isnan(result) or (not allow_infinity and not isfinite(result)):
        raise ValueError(f"{field_name} must be finite")
    return result


def _encode_logit(value: float) -> float | str:
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    return value


def _decode_logit(value: object, field_name: str) -> float:
    if value == "Infinity":
        return float("inf")
    if value == "-Infinity":
        return float("-inf")
    if isinstance(value, str):
        raise ValueError(f"{field_name} has an unknown encoded logit value")
    return _float(value, field_name, allow_infinity=True)
