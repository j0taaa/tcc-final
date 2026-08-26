"""Recorded semantic alignment between exact and EPIC benchmark representations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from mwpc_exact.reference.recognizer import recognizes_cnf

if TYPE_CHECKING:
    from mwpc_exact.evaluation.instance import BenchmarkInstance


class EpicGrammar(Protocol):
    def accepts(self, word: list[str], /) -> bool: ...


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class AlignmentCase:
    token_ids: tuple[int, ...]
    expected_accepts: bool

    def __post_init__(self) -> None:
        if isinstance(self.token_ids, (str, bytes)) or not isinstance(self.token_ids, Sequence):
            raise TypeError("alignment token_ids must be a finite sequence")
        token_ids = tuple(
            _integer(token_id, f"alignment token at {position}")
            for position, token_id in enumerate(self.token_ids)
        )
        if not isinstance(self.expected_accepts, bool):
            raise TypeError("expected_accepts must be a boolean")
        object.__setattr__(self, "token_ids", token_ids)

    def to_dict(self) -> dict[str, object]:
        return {"token_ids": list(self.token_ids), "expected_accepts": self.expected_accepts}


@dataclass(frozen=True, slots=True)
class SemanticAlignmentEvidence:
    source_grammar_id: str
    exact_compiler_version: str
    epic_compiler_version: str
    method: str
    cases: tuple[AlignmentCase, ...]

    def __post_init__(self) -> None:
        for name in (
            "source_grammar_id",
            "exact_compiler_version",
            "epic_compiler_version",
            "method",
        ):
            object.__setattr__(self, name, _string(getattr(self, name), name))
        cases = tuple(self.cases)
        if not cases or not all(isinstance(case, AlignmentCase) for case in cases):
            raise ValueError("semantic alignment requires at least one AlignmentCase")
        if len({case.token_ids for case in cases}) != len(cases):
            raise ValueError("semantic alignment cases must not repeat token sequences")
        if not any(case.expected_accepts for case in cases):
            raise ValueError("semantic alignment evidence must include an accepted case")
        if not any(not case.expected_accepts for case in cases):
            raise ValueError("semantic alignment evidence must include a rejected case")
        object.__setattr__(self, "cases", cases)

    def _payload(self) -> dict[str, object]:
        return {
            "source_grammar_id": self.source_grammar_id,
            "exact_compiler_version": self.exact_compiler_version,
            "epic_compiler_version": self.epic_compiler_version,
            "method": self.method,
            "cases": [case.to_dict() for case in self.cases],
        }

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(self._payload(), separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "alignment_sha256": self.fingerprint}

    @classmethod
    def from_dict(cls, value: object) -> SemanticAlignmentEvidence:
        if not isinstance(value, Mapping):
            raise TypeError("semantic_alignment must be a mapping")
        required = {
            "source_grammar_id",
            "exact_compiler_version",
            "epic_compiler_version",
            "method",
            "cases",
            "alignment_sha256",
        }
        missing = required - set(value)
        unknown = set(value) - required
        if missing or unknown:
            raise ValueError(
                "semantic_alignment fields differ from the version-1 contract "
                f"(missing={sorted(missing)}, unknown={sorted(unknown)})"
            )
        raw_cases = value["cases"]
        if isinstance(raw_cases, (str, bytes)) or not isinstance(raw_cases, Sequence):
            raise TypeError("semantic_alignment.cases must be a finite sequence")
        cases: list[AlignmentCase] = []
        for index, raw_case in enumerate(raw_cases):
            if not isinstance(raw_case, Mapping):
                raise TypeError(f"semantic alignment case {index} must be a mapping")
            if set(raw_case) != {"token_ids", "expected_accepts"}:
                raise ValueError(f"semantic alignment case {index} has unknown fields")
            token_ids = raw_case["token_ids"]
            if isinstance(token_ids, (str, bytes)) or not isinstance(token_ids, Sequence):
                raise TypeError(f"semantic alignment case {index} token_ids must be a sequence")
            cases.append(
                AlignmentCase(
                    token_ids=tuple(cast(Sequence[int], token_ids)),
                    expected_accepts=cast(bool, raw_case["expected_accepts"]),
                )
            )
        evidence = cls(
            source_grammar_id=_string(value["source_grammar_id"], "source_grammar_id"),
            exact_compiler_version=_string(
                value["exact_compiler_version"], "exact_compiler_version"
            ),
            epic_compiler_version=_string(value["epic_compiler_version"], "epic_compiler_version"),
            method=_string(value["method"], "method"),
            cases=tuple(cases),
        )
        recorded = _string(value["alignment_sha256"], "alignment_sha256")
        if recorded != evidence.fingerprint:
            raise ValueError("alignment_sha256 does not match semantic alignment evidence")
        return evidence


def alignment_evidence_from_instance(instance: BenchmarkInstance) -> SemanticAlignmentEvidence:
    raw = instance.expected_metadata.get("semantic_alignment")
    evidence = SemanticAlignmentEvidence.from_dict(raw)
    if evidence.source_grammar_id != instance.grammar.grammar_id:
        raise ValueError("semantic alignment source_grammar_id differs from benchmark grammar_id")
    return evidence


def validate_semantic_alignment(
    instance: BenchmarkInstance,
    epic_cfg: EpicGrammar,
) -> dict[str, object]:
    """Recompute every recorded case through both language representations."""

    evidence = alignment_evidence_from_instance(instance)
    if not hasattr(epic_cfg, "accepts") or not callable(epic_cfg.accepts):
        raise TypeError("EPIC CFG must expose accepts(list[str])")
    if instance.epic_replay is None:
        raise ValueError("semantic alignment requires EPIC replay data")
    decoded = dict(instance.epic_replay.decoded_tokens)
    adapter = instance.selection_input.tokenizer_adapter
    checked: list[dict[str, object]] = []
    for case in evidence.cases:
        labels: list[int] = []
        words: list[str] = []
        for token_id in case.token_ids:
            if token_id >= adapter.vocabulary_size:
                raise ValueError("semantic alignment token is outside the exact vocabulary")
            emission = adapter.emissions[token_id]
            if emission is None:
                raise ValueError("semantic alignment cases must use ordinary byte-emitting tokens")
            labels.extend(emission)
            word = decoded.get(token_id)
            if not isinstance(word, str):
                raise ValueError("semantic alignment token lacks a saved EPIC string decoding")
            words.append(word)
        exact_accepts = recognizes_cnf(instance.grammar.cnf, tuple(labels))
        epic_accepts = bool(epic_cfg.accepts(words))
        if exact_accepts != epic_accepts or exact_accepts != case.expected_accepts:
            raise ValueError(
                "exact and EPIC grammar representations disagree on recorded alignment case "
                f"{case.token_ids}: exact={exact_accepts}, epic={epic_accepts}, "
                f"expected={case.expected_accepts}"
            )
        checked.append(
            {
                "token_ids": list(case.token_ids),
                "accepts": exact_accepts,
            }
        )
    return {
        "method": evidence.method,
        "source_grammar_id": evidence.source_grammar_id,
        "alignment_sha256": evidence.fingerprint,
        "checked_case_count": len(checked),
        "cases": checked,
    }


__all__ = [
    "AlignmentCase",
    "EpicGrammar",
    "SemanticAlignmentEvidence",
    "alignment_evidence_from_instance",
    "validate_semantic_alignment",
]
