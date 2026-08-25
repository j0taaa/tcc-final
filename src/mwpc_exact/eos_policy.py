"""Explicit EOS/PAD policy contracts independent of lattice construction."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


def _non_negative_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _id_tuple(value: object, field_name: str, *, unique: bool) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of integer IDs")
    result = tuple(_non_negative_id(item, f"{field_name} item") for item in value)
    if unique and len(set(result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


class EOSMode(StrEnum):
    """Configured acceptance behavior at the final physical boundary."""

    ABSENT = "absent"
    REQUIRED = "required"
    OPTIONAL = "optional"


class EOSState(StrEnum):
    """State of the finite-slot termination automaton."""

    BEFORE_EOS = "before_eos"
    AFTER_EOS = "after_eos"


class TokenRole(StrEnum):
    """Grammar-visible role assigned to one represented token choice."""

    ORDINARY = "ordinary"
    EOS = "eos"
    PAD = "pad"


class EOSPolicyViolation(ValueError):
    """A represented full-slot token path is illegal under the EOS policy."""


@dataclass(frozen=True, slots=True)
class EOSPolicy:
    """Explicit EOS profile; no tokenizer- or model-specific default is inferred."""

    mode: EOSMode
    termination_token_ids: tuple[int, ...] = ()
    pad_token_id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, EOSMode):
            raise TypeError("mode must be an EOSMode")
        if not isinstance(self.termination_token_ids, tuple):
            raise TypeError("termination_token_ids must be a tuple")
        termination_ids = _id_tuple(
            self.termination_token_ids,
            "termination_token_ids",
            unique=True,
        )
        pad_token_id = self.pad_token_id
        if pad_token_id is not None:
            pad_token_id = _non_negative_id(pad_token_id, "pad_token_id")

        if self.mode is EOSMode.ABSENT:
            if termination_ids or pad_token_id is not None:
                raise ValueError("ABSENT mode cannot configure termination or PAD token IDs")
        elif not termination_ids or pad_token_id is None:
            raise ValueError("REQUIRED and OPTIONAL modes require termination and PAD token IDs")

        object.__setattr__(self, "termination_token_ids", termination_ids)
        object.__setattr__(self, "pad_token_id", pad_token_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "termination_token_ids": list(self.termination_token_ids),
            "pad_token_id": self.pad_token_id,
        }




__all__ = [
    "EOSMode",
    "EOSPolicy",
    "EOSPolicyViolation",
    "EOSState",
    "TokenRole",
]
