"""Versioned immutable inputs for fair offline selector comparisons.

The schema freezes the common :class:`~mwpc_exact.selection.SelectionInput`
rather than rebuilding proposals or represented support during replay.  Saved
logits are optional provenance data and never substitute for serialized rows.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from math import isfinite, isnan
from pathlib import Path
from types import MappingProxyType
from typing import cast

from mwpc_exact.backend import ExactBackend
from mwpc_exact.brute_force_selection import select_brute_force
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.epic_selection import EpicSelectionContext, select_epic
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    select_exact,
    select_serial,
)
from mwpc_exact.support import PerPositionSupport, SupportInputSource
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactnessScope, Proposal

BENCHMARK_INSTANCE_ARTIFACT_KIND = "mwpc_benchmark_instance"
BENCHMARK_INSTANCE_SCHEMA_VERSION = 1


class UnsupportedBenchmarkSchemaVersion(ValueError):
    """Raised when no explicit migration exists for an instance version."""


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


@dataclass(frozen=True, slots=True)
class BenchmarkGrammar:
    """Both grammar representations needed by exact and EPIC replay."""

    grammar_id: str
    cnf: CnfGrammar
    epic_cfg_text: str | None = None
    epic_start_symbol: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "grammar_id", _string(self.grammar_id, "grammar_id"))
        if not isinstance(self.cnf, CnfGrammar):
            raise TypeError("cnf must be a CnfGrammar")
        text = _optional_string(self.epic_cfg_text, "epic_cfg_text")
        start = _optional_string(self.epic_start_symbol, "epic_start_symbol")
        if (text is None) != (start is None):
            raise ValueError("EPIC CFG text and start symbol must be provided together")
        object.__setattr__(self, "epic_cfg_text", text)
        object.__setattr__(self, "epic_start_symbol", start)

    @property
    def fingerprint(self) -> str:
        """Hash every serialized grammar representation, excluding its display ID."""

        return _sha256(self._content_dict())

    def _content_dict(self) -> dict[str, object]:
        return {
            "cnf": self.cnf.to_dict(),
            "epic_cfg": (
                None
                if self.epic_cfg_text is None
                else {
                    "text": self.epic_cfg_text,
                    "start_symbol": self.epic_start_symbol,
                }
            ),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "grammar_id": self.grammar_id,
            "grammar_sha256": self.fingerprint,
            **self._content_dict(),
        }

    @classmethod
    def from_dict(cls, value: object) -> BenchmarkGrammar:
        data = _mapping(value, "grammar")
        _exact_fields(
            data,
            required={"grammar_id", "grammar_sha256", "cnf", "epic_cfg"},
            field_name="grammar",
        )
        epic_value = data["epic_cfg"]
        epic_text: str | None = None
        epic_start: str | None = None
        if epic_value is not None:
            epic = _mapping(epic_value, "grammar.epic_cfg")
            _exact_fields(
                epic,
                required={"text", "start_symbol"},
                field_name="grammar.epic_cfg",
            )
            epic_text = _string(epic["text"], "grammar.epic_cfg.text")
            epic_start = _string(epic["start_symbol"], "grammar.epic_cfg.start_symbol")
        grammar = cls(
            grammar_id=_string(data["grammar_id"], "grammar.grammar_id"),
            cnf=CnfGrammar.from_dict(_mapping(data["cnf"], "grammar.cnf")),
            epic_cfg_text=epic_text,
            epic_start_symbol=epic_start,
        )
        recorded = _validate_sha256(data["grammar_sha256"], "grammar.grammar_sha256")
        if recorded != grammar.fingerprint:
            raise ValueError("grammar_sha256 does not match the serialized grammar")
        return grammar


@dataclass(frozen=True, slots=True)
class SavedLogits:
    """Portable saved model output; model parameters are deliberately absent."""

    values: tuple[tuple[float, ...], ...]
    dtype: str
    source: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        rows = tuple(tuple(row) for row in self.values)
        if not rows or not rows[0]:
            raise ValueError("saved logits must contain at least one row and one token")
        width = len(rows[0])
        normalized: list[tuple[float, ...]] = []
        for position, row in enumerate(rows):
            if len(row) != width:
                raise ValueError("saved logit rows must have equal vocabulary width")
            normalized.append(
                tuple(
                    _float(score, f"saved logit at ({position}, {token_id})", allow_infinity=True)
                    for token_id, score in enumerate(row)
                )
            )
        object.__setattr__(self, "values", tuple(normalized))
        object.__setattr__(self, "dtype", _string(self.dtype, "saved logits dtype"))
        object.__setattr__(self, "source", _string(self.source, "saved logits source"))
        object.__setattr__(
            self,
            "metadata",
            _freeze_json_mapping(self.metadata, "saved logits metadata"),
        )

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.values), len(self.values[0])

    def _content_dict(self) -> dict[str, object]:
        return {
            "dtype": self.dtype,
            "source": self.source,
            "shape": list(self.shape),
            "values": [[_encode_logit(score) for score in row] for row in self.values],
            "metadata": _thaw_json(self.metadata),
        }

    @property
    def fingerprint(self) -> str:
        return _sha256(self._content_dict())

    def to_dict(self) -> dict[str, object]:
        return {**self._content_dict(), "logits_sha256": self.fingerprint}

    @classmethod
    def from_dict(cls, value: object) -> SavedLogits:
        data = _mapping(value, "saved_logits")
        _exact_fields(
            data,
            required={"dtype", "source", "shape", "values", "metadata", "logits_sha256"},
            field_name="saved_logits",
        )
        raw_rows = _sequence(data["values"], "saved_logits.values")
        rows = tuple(
            tuple(
                _decode_logit(score, f"saved_logits.values[{position}][{token_id}]")
                for token_id, score in enumerate(
                    _sequence(raw_row, f"saved_logits.values[{position}]")
                )
            )
            for position, raw_row in enumerate(raw_rows)
        )
        logits = cls(
            values=rows,
            dtype=_string(data["dtype"], "saved_logits.dtype"),
            source=_string(data["source"], "saved_logits.source"),
            metadata=_mapping(data["metadata"], "saved_logits.metadata"),
        )
        shape = _sequence(data["shape"], "saved_logits.shape")
        if len(shape) != 2 or tuple(
            _integer(item, "saved_logits.shape item", minimum=1) for item in shape
        ) != logits.shape:
            raise ValueError("saved_logits.shape does not match the values matrix")
        recorded = _validate_sha256(data["logits_sha256"], "saved_logits.logits_sha256")
        if recorded != logits.fingerprint:
            raise ValueError("logits_sha256 does not match the saved logits")
        return logits


@dataclass(frozen=True, slots=True)
class EpicReplaySpec:
    """JSON-compatible EPIC lexical state and token decoding table."""

    words_full: tuple[object, ...]
    prompt_length: int
    decoded_tokens: tuple[tuple[int, object], ...]
    lex_map: object = None
    terminals: tuple[str, ...] = ()
    prelex: str | None = None
    single_token_lexing: object = None
    inject_gap_size: int = 0
    max_total_injections: int = 0
    subtokens: object = None
    supertokens: object = None
    strip_chars: str | None = None
    trace: bool = False

    def __post_init__(self) -> None:
        words = tuple(
            _freeze_json(word, f"epic words_full[{index}]")
            for index, word in enumerate(self.words_full)
        )
        decoded: list[tuple[int, object]] = []
        seen: set[int] = set()
        for token_id, word in self.decoded_tokens:
            normalized_id = _integer(token_id, "decoded token ID")
            if normalized_id in seen:
                raise ValueError("decoded_tokens must not repeat token IDs")
            frozen_word = _freeze_json(word, f"decoded token {normalized_id}")
            if frozen_word is None:
                raise ValueError("decoded token words must not be None")
            decoded.append((normalized_id, frozen_word))
            seen.add(normalized_id)
        terminals = tuple(self.terminals)
        if not all(isinstance(terminal, str) for terminal in terminals):
            raise TypeError("EPIC terminals must contain only strings")
        if not isinstance(self.trace, bool):
            raise TypeError("EPIC trace must be a boolean")
        object.__setattr__(self, "words_full", words)
        object.__setattr__(self, "prompt_length", _integer(self.prompt_length, "prompt_length"))
        object.__setattr__(self, "decoded_tokens", tuple(decoded))
        object.__setattr__(self, "terminals", terminals)
        object.__setattr__(self, "prelex", _optional_text(self.prelex, "prelex"))
        object.__setattr__(
            self, "strip_chars", _optional_text(self.strip_chars, "strip_chars")
        )
        object.__setattr__(
            self,
            "inject_gap_size",
            _integer(self.inject_gap_size, "inject_gap_size"),
        )
        object.__setattr__(
            self,
            "max_total_injections",
            _integer(self.max_total_injections, "max_total_injections"),
        )
        for name in ("lex_map", "single_token_lexing", "subtokens", "supertokens"):
            object.__setattr__(self, name, _freeze_json(getattr(self, name), f"EPIC {name}"))

    def to_context(self, cfg: object) -> EpicSelectionContext:
        decoded = dict(self.decoded_tokens)

        def decode_token(token_id: int) -> object:
            try:
                return _thaw_json(decoded[token_id])
            except KeyError as error:
                raise ValueError(f"no saved EPIC decoding for token ID {token_id}") from error

        return EpicSelectionContext(
            words_full=tuple(_thaw_json(word) for word in self.words_full),
            prompt_length=self.prompt_length,
            cfg=cfg,
            decode_token=decode_token,
            lex_map=_thaw_json(self.lex_map),
            terminals=self.terminals,
            prelex=self.prelex,
            single_token_lexing=_thaw_json(self.single_token_lexing),
            inject_gap_size=self.inject_gap_size,
            max_total_injections=self.max_total_injections,
            subtokens=_thaw_json(self.subtokens),
            supertokens=_thaw_json(self.supertokens),
            strip_chars=self.strip_chars,
            trace=self.trace,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "words_full": [_thaw_json(word) for word in self.words_full],
            "prompt_length": self.prompt_length,
            "decoded_tokens": [
                {"token_id": token_id, "word": _thaw_json(word)}
                for token_id, word in self.decoded_tokens
            ],
            "lex_map": _thaw_json(self.lex_map),
            "terminals": list(self.terminals),
            "prelex": self.prelex,
            "single_token_lexing": _thaw_json(self.single_token_lexing),
            "inject_gap_size": self.inject_gap_size,
            "max_total_injections": self.max_total_injections,
            "subtokens": _thaw_json(self.subtokens),
            "supertokens": _thaw_json(self.supertokens),
            "strip_chars": self.strip_chars,
            "trace": self.trace,
        }

    @classmethod
    def from_dict(cls, value: object) -> EpicReplaySpec:
        data = _mapping(value, "epic_replay")
        fields = {
            "words_full",
            "prompt_length",
            "decoded_tokens",
            "lex_map",
            "terminals",
            "prelex",
            "single_token_lexing",
            "inject_gap_size",
            "max_total_injections",
            "subtokens",
            "supertokens",
            "strip_chars",
            "trace",
        }
        _exact_fields(data, required=fields, field_name="epic_replay")
        decoded: list[tuple[int, object]] = []
        for index, raw_entry in enumerate(
            _sequence(data["decoded_tokens"], "epic_replay.decoded_tokens")
        ):
            entry = _mapping(raw_entry, f"epic_replay.decoded_tokens[{index}]")
            _exact_fields(
                entry,
                required={"token_id", "word"},
                field_name=f"epic_replay.decoded_tokens[{index}]",
            )
            decoded.append(
                (
                    _integer(entry["token_id"], "decoded token ID"),
                    entry["word"],
                )
            )
        raw_terminals = _sequence(data["terminals"], "epic_replay.terminals")
        terminals = tuple(_text(item, "EPIC terminal") for item in raw_terminals)
        trace = data["trace"]
        if not isinstance(trace, bool):
            raise TypeError("epic_replay.trace must be a boolean")
        return cls(
            words_full=tuple(_sequence(data["words_full"], "epic_replay.words_full")),
            prompt_length=_integer(data["prompt_length"], "epic_replay.prompt_length"),
            decoded_tokens=tuple(decoded),
            lex_map=data["lex_map"],
            terminals=terminals,
            prelex=_optional_text(data["prelex"], "epic_replay.prelex"),
            single_token_lexing=data["single_token_lexing"],
            inject_gap_size=_integer(data["inject_gap_size"], "epic_replay.inject_gap_size"),
            max_total_injections=_integer(
                data["max_total_injections"], "epic_replay.max_total_injections"
            ),
            subtokens=data["subtokens"],
            supertokens=data["supertokens"],
            strip_chars=_optional_text(data["strip_chars"], "epic_replay.strip_chars"),
            trace=trace,
        )


def _proposal_to_dict(proposal: Proposal) -> dict[str, object]:
    return {
        "proposal_id": proposal.proposal_id,
        "position": proposal.position,
        "token_id": proposal.token_id,
        "weight": proposal.weight,
        "model_confidence": proposal.model_confidence,
    }


def _proposal_from_dict(value: object, index: int) -> Proposal:
    data = _mapping(value, f"proposal {index}")
    _exact_fields(
        data,
        required={"proposal_id", "position", "token_id", "weight", "model_confidence"},
        field_name=f"proposal {index}",
    )
    confidence_value = data["model_confidence"]
    confidence = (
        None
        if confidence_value is None
        else _float(confidence_value, f"proposal {index} model_confidence")
    )
    return Proposal(
        proposal_id=_integer(data["proposal_id"], f"proposal {index} proposal_id"),
        position=_integer(data["position"], f"proposal {index} position"),
        token_id=_integer(data["token_id"], f"proposal {index} token_id"),
        weight=_float(data["weight"], f"proposal {index} weight"),
        model_confidence=confidence,
    )


def _support_to_dict(support: PerPositionSupport) -> dict[str, object]:
    return {
        "rows": [list(row) for row in support.rows],
        "permitted_token_ids": list(support.permitted_token_ids),
        "exactness_scope": support.exactness_scope.to_dict(),
        "input_source": support.input_source.value,
        "top_k_token_ids_by_position": [
            list(row) for row in support.top_k_token_ids_by_position
        ],
        "proposal_token_ids_by_position": [
            list(row) for row in support.proposal_token_ids_by_position
        ],
        "proposal_token_inclusion_enabled": support.proposal_token_inclusion_enabled,
        "represented_support_sha256": support.fingerprint,
    }


def _integer_tuple(value: object, field_name: str) -> tuple[int, ...]:
    return tuple(_integer(item, f"{field_name} item") for item in _sequence(value, field_name))


def _indexed_integer_rows(value: object, field_name: str) -> tuple[tuple[int, ...], ...]:
    return tuple(
        _integer_tuple(row, f"{field_name}[{position}]")
        for position, row in enumerate(_sequence(value, field_name))
    )


def _support_from_dict(value: object, canvas: tuple[int | None, ...]) -> PerPositionSupport:
    data = _mapping(value, "support")
    fields = {
        "rows",
        "permitted_token_ids",
        "exactness_scope",
        "input_source",
        "top_k_token_ids_by_position",
        "proposal_token_ids_by_position",
        "proposal_token_inclusion_enabled",
        "represented_support_sha256",
    }
    _exact_fields(data, required=fields, field_name="support")
    source_value = _string(data["input_source"], "support.input_source")
    try:
        source = SupportInputSource(source_value)
    except ValueError as error:
        raise ValueError(f"unknown support input_source: {source_value!r}") from error
    inclusion = data["proposal_token_inclusion_enabled"]
    if not isinstance(inclusion, bool):
        raise TypeError("support.proposal_token_inclusion_enabled must be a boolean")
    support = PerPositionSupport(
        canvas=canvas,
        rows=_indexed_integer_rows(data["rows"], "support.rows"),
        permitted_token_ids=_integer_tuple(
            data["permitted_token_ids"], "support.permitted_token_ids"
        ),
        exactness_scope=ExactnessScope.from_dict(
            _mapping(data["exactness_scope"], "support.exactness_scope")
        ),
        input_source=source,
        top_k_token_ids_by_position=_indexed_integer_rows(
            data["top_k_token_ids_by_position"], "support.top_k_token_ids_by_position"
        ),
        proposal_token_ids_by_position=_indexed_integer_rows(
            data["proposal_token_ids_by_position"],
            "support.proposal_token_ids_by_position",
        ),
        proposal_token_inclusion_enabled=inclusion,
    )
    recorded = _validate_sha256(
        data["represented_support_sha256"], "support.represented_support_sha256"
    )
    if recorded != support.fingerprint:
        raise ValueError("represented_support_sha256 does not match the support rows")
    return support


def _canvas_from_json(value: object) -> tuple[int | None, ...]:
    canvas: list[int | None] = []
    for position, token_id in enumerate(_sequence(value, "selection_input.canvas")):
        canvas.append(
            None
            if token_id is None
            else _integer(token_id, f"canvas token at position {position}")
        )
    return tuple(canvas)


def _adapter_to_dict(adapter: CompositionalByteLevelAdapter) -> dict[str, object]:
    return {
        "kind": "compositional_byte_level",
        "emissions_hex": [
            None if emission is None else emission.hex() for emission in adapter.emissions
        ],
    }


def _adapter_from_dict(value: object) -> CompositionalByteLevelAdapter:
    data = _mapping(value, "tokenizer_adapter")
    _exact_fields(
        data,
        required={"kind", "emissions_hex"},
        field_name="tokenizer_adapter",
    )
    if data["kind"] != "compositional_byte_level":
        raise ValueError("unsupported tokenizer adapter kind")
    emissions: list[bytes | None] = []
    for token_id, encoded in enumerate(
        _sequence(data["emissions_hex"], "tokenizer_adapter.emissions_hex")
    ):
        if encoded is None:
            emissions.append(None)
            continue
        if not isinstance(encoded, str):
            raise TypeError(f"tokenizer emission {token_id} must be hex text or None")
        try:
            emissions.append(bytes.fromhex(encoded))
        except ValueError as error:
            raise ValueError(f"tokenizer emission {token_id} is not valid hex") from error
    return CompositionalByteLevelAdapter(tuple(emissions))


def _eos_policy_from_dict(value: object) -> EOSPolicy:
    data = _mapping(value, "eos_policy")
    _exact_fields(
        data,
        required={"mode", "termination_token_ids", "pad_token_id"},
        field_name="eos_policy",
    )
    mode_value = _string(data["mode"], "eos_policy.mode")
    try:
        mode = EOSMode(mode_value)
    except ValueError as error:
        raise ValueError(f"unknown EOS mode: {mode_value!r}") from error
    raw_pad = data["pad_token_id"]
    return EOSPolicy(
        mode=mode,
        termination_token_ids=_integer_tuple(
            data["termination_token_ids"], "eos_policy.termination_token_ids"
        ),
        pad_token_id=None if raw_pad is None else _integer(raw_pad, "eos_policy.pad_token_id"),
    )


def _selection_input_to_dict(selection_input: SelectionInput) -> dict[str, object]:
    return {
        "canvas": list(selection_input.canvas),
        "proposals": [_proposal_to_dict(proposal) for proposal in selection_input.proposals],
        "support": _support_to_dict(selection_input.support),
        "tokenizer_adapter": _adapter_to_dict(selection_input.tokenizer_adapter),
        "eos_policy": selection_input.eos_policy.to_dict(),
    }


def _selection_input_from_dict(
    value: object,
    grammar: CnfGrammar,
) -> SelectionInput:
    data = _mapping(value, "selection_input")
    _exact_fields(
        data,
        required={"canvas", "proposals", "support", "tokenizer_adapter", "eos_policy"},
        field_name="selection_input",
    )
    canvas = _canvas_from_json(data["canvas"])
    proposals = tuple(
        _proposal_from_dict(proposal, index)
        for index, proposal in enumerate(_sequence(data["proposals"], "proposals"))
    )
    return SelectionInput(
        grammar=grammar,
        canvas=canvas,
        proposals=proposals,
        support=_support_from_dict(data["support"], canvas),
        tokenizer_adapter=_adapter_from_dict(data["tokenizer_adapter"]),
        eos_policy=_eos_policy_from_dict(data["eos_policy"]),
    )


@dataclass(frozen=True, slots=True)
class BenchmarkInstance:
    """One validated immutable selector input and its replay provenance."""

    instance_id: str
    grammar: BenchmarkGrammar
    selection_input: SelectionInput
    metadata: Mapping[str, object]
    expected_metadata: Mapping[str, object] = field(default_factory=dict)
    saved_logits: SavedLogits | None = None
    epic_replay: EpicReplaySpec | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instance_id", _string(self.instance_id, "instance_id"))
        if not isinstance(self.grammar, BenchmarkGrammar):
            raise TypeError("grammar must be a BenchmarkGrammar")
        if not isinstance(self.selection_input, SelectionInput):
            raise TypeError("selection_input must be a SelectionInput")
        if self.selection_input.grammar != self.grammar.cnf:
            raise ValueError("selection_input grammar must equal the serialized benchmark CNF")
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata, "metadata"))
        object.__setattr__(
            self,
            "expected_metadata",
            _freeze_json_mapping(self.expected_metadata, "expected_metadata"),
        )
        if self.saved_logits is not None:
            saved_logits = self.saved_logits
            if not isinstance(saved_logits, SavedLogits):
                raise TypeError("saved_logits must be SavedLogits or None")
            expected_shape = (
                len(self.selection_input.canvas),
                self.selection_input.support.exactness_scope.vocabulary_size,
            )
            if saved_logits.shape != expected_shape:
                raise ValueError(
                    "saved logits shape must equal canvas length by tokenizer vocabulary size"
                )
            support = self.selection_input.support
            if support.input_source is SupportInputSource.LOGITS:
                effective_top_k = support.effective_top_k
                if effective_top_k is not None:
                    for position, fixed_token in enumerate(self.selection_input.canvas):
                        expected_ranked: tuple[int, ...] = ()
                        if fixed_token is None:
                            expected_ranked = tuple(
                                sorted(
                                    support.permitted_token_ids,
                                    key=lambda token_id: (
                                        -saved_logits.values[position][token_id],
                                        token_id,
                                    ),
                                )[:effective_top_k]
                            )
                        if support.top_k_token_ids_by_position[position] != expected_ranked:
                            raise ValueError(
                                "saved logits do not reproduce ranked top-K diagnostics "
                                f"at position {position}"
                            )
        if self.epic_replay is not None:
            if not isinstance(self.epic_replay, EpicReplaySpec):
                raise TypeError("epic_replay must be EpicReplaySpec or None")
            if self.grammar.epic_cfg_text is None:
                raise ValueError("EPIC replay requires serialized EPIC CFG text")
            expected_words = self.epic_replay.prompt_length + len(self.selection_input.canvas)
            if len(self.epic_replay.words_full) != expected_words:
                raise ValueError("EPIC words_full must contain prompt plus complete canvas")
            for position, token_id in enumerate(self.selection_input.canvas):
                word = self.epic_replay.words_full[self.epic_replay.prompt_length + position]
                if (token_id is None) != (word is None):
                    raise ValueError(
                        "EPIC words_full and canvas disagree at generated position "
                        f"{position}"
                    )
            decoded_ids = {token_id for token_id, _ in self.epic_replay.decoded_tokens}
            special_ids = set(self.selection_input.eos_policy.termination_token_ids)
            if self.selection_input.eos_policy.pad_token_id is not None:
                special_ids.add(self.selection_input.eos_policy.pad_token_id)
            required_decodings = {
                proposal.token_id
                for proposal in self.selection_input.proposals
                if proposal.token_id not in special_ids
                and proposal.token_id
                in self.selection_input.support.rows[proposal.position]
            }
            missing = sorted(required_decodings - decoded_ids)
            if missing:
                raise ValueError(f"EPIC replay omits proposal token decodings: {missing}")

    def _payload_dict(self) -> dict[str, object]:
        return {
            "artifact_kind": BENCHMARK_INSTANCE_ARTIFACT_KIND,
            "schema_version": BENCHMARK_INSTANCE_SCHEMA_VERSION,
            "instance_id": self.instance_id,
            "grammar": self.grammar.to_dict(),
            "selection_input": _selection_input_to_dict(self.selection_input),
            "saved_logits": None if self.saved_logits is None else self.saved_logits.to_dict(),
            "epic_replay": None if self.epic_replay is None else self.epic_replay.to_dict(),
            "metadata": _thaw_json(self.metadata),
            "expected_metadata": _thaw_json(self.expected_metadata),
        }

    @property
    def fingerprint(self) -> str:
        """Hash the normalized schema payload, including frozen logits and metadata."""

        return _sha256(self._payload_dict())

    def to_dict(self) -> dict[str, object]:
        return {**self._payload_dict(), "instance_sha256": self.fingerprint}

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return standards-compliant JSON with deterministic key ordering."""

        return json.dumps(
            self.to_dict(),
            allow_nan=False,
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    def write_json(self, path: str | Path, *, overwrite: bool = False) -> None:
        """Write one instance, refusing accidental replacement by default."""

        destination = Path(path)
        if destination.exists() and not overwrite:
            raise FileExistsError(f"benchmark instance already exists: {destination}")
        destination.write_text(f"{self.to_json()}\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, value: object) -> BenchmarkInstance:
        data = migrate_benchmark_instance_data(value)
        fields = {
            "artifact_kind",
            "schema_version",
            "instance_id",
            "grammar",
            "selection_input",
            "saved_logits",
            "epic_replay",
            "metadata",
            "expected_metadata",
            "instance_sha256",
        }
        _exact_fields(data, required=fields, field_name="benchmark instance")
        if data["artifact_kind"] != BENCHMARK_INSTANCE_ARTIFACT_KIND:
            raise ValueError("unknown benchmark artifact_kind")
        grammar = BenchmarkGrammar.from_dict(data["grammar"])
        instance = cls(
            instance_id=_string(data["instance_id"], "instance_id"),
            grammar=grammar,
            selection_input=_selection_input_from_dict(data["selection_input"], grammar.cnf),
            saved_logits=(
                None
                if data["saved_logits"] is None
                else SavedLogits.from_dict(data["saved_logits"])
            ),
            epic_replay=(
                None
                if data["epic_replay"] is None
                else EpicReplaySpec.from_dict(data["epic_replay"])
            ),
            metadata=_mapping(data["metadata"], "metadata"),
            expected_metadata=_mapping(data["expected_metadata"], "expected_metadata"),
        )
        recorded = _validate_sha256(data["instance_sha256"], "instance_sha256")
        if recorded != instance.fingerprint:
            raise ValueError("instance_sha256 does not match the normalized instance payload")
        return instance

    @classmethod
    def read_json(cls, path: str | Path) -> BenchmarkInstance:
        """Load strict JSON; non-standard NaN/Infinity constants are rejected."""

        def reject_constant(value: str) -> object:
            raise ValueError(f"non-standard JSON numeric constant is forbidden: {value}")

        parsed = json.loads(
            Path(path).read_text(encoding="utf-8"),
            parse_constant=reject_constant,
        )
        return cls.from_dict(parsed)


def migrate_benchmark_instance_data(value: object) -> Mapping[str, object]:
    """Apply explicit sequential migrations to the current schema.

    Version 1 is the first public schema, so there are intentionally no legacy
    migrations yet.  Unknown older and newer versions fail closed; future
    versions must add a deterministic ``N -> N + 1`` transform and regression
    fixture before being accepted here.
    """

    data = _mapping(value, "benchmark instance")
    artifact_kind = data.get("artifact_kind")
    if artifact_kind != BENCHMARK_INSTANCE_ARTIFACT_KIND:
        raise ValueError("unknown benchmark artifact_kind")
    version = _integer(data.get("schema_version"), "schema_version")
    if version != BENCHMARK_INSTANCE_SCHEMA_VERSION:
        raise UnsupportedBenchmarkSchemaVersion(
            "unsupported benchmark instance schema_version: "
            f"{version}; no deterministic migration to "
            f"{BENCHMARK_INSTANCE_SCHEMA_VERSION} is registered"
        )
    return data


EpicCfgFactory = Callable[[str, str], object]


def _default_epic_cfg_factory(text: str, start_symbol: str) -> object:
    cfg_module = import_module("rustformlang.cfg")
    cfg_type = cfg_module.CFG
    return cast(object, cfg_type.from_text(text, start_symbol))


def _unsupported_epic_result(
    selection_input: SelectionInput,
    error: Exception,
) -> SelectionResult:
    return SelectionResult(
        selector=SelectorKind.EPIC,
        status=SelectionStatus.UNSUPPORTED,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=0.0,
        diagnostics={
            "error_stage": "benchmark_epic_cfg_reconstruction",
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def replay_benchmark_instance(
    instance: BenchmarkInstance,
    *,
    backend: ExactBackend = ExactBackend.PYTHON,
    timeout_seconds: float | None = None,
    brute_force_max_completions: int = 100_000,
    epic_cfg_factory: EpicCfgFactory | None = None,
) -> Mapping[SelectorKind, SelectionResult]:
    """Replay every applicable selector against the same frozen input object."""

    if not isinstance(instance, BenchmarkInstance):
        raise TypeError("instance must be a BenchmarkInstance")
    selection_input = instance.selection_input
    results: dict[SelectorKind, SelectionResult] = {}
    results[SelectorKind.SERIAL] = select_serial(
        selection_input,
        backend=backend,
        timeout_seconds=timeout_seconds,
    )
    if instance.epic_replay is not None:
        text = instance.grammar.epic_cfg_text
        start_symbol = instance.grammar.epic_start_symbol
        if text is None or start_symbol is None:
            raise AssertionError("validated EPIC replay lost its grammar representation")
        factory = epic_cfg_factory or _default_epic_cfg_factory
        try:
            cfg = factory(text, start_symbol)
            context = instance.epic_replay.to_context(cfg)
        except (ImportError, ModuleNotFoundError, AttributeError, TypeError, ValueError) as error:
            results[SelectorKind.EPIC] = _unsupported_epic_result(selection_input, error)
        else:
            results[SelectorKind.EPIC] = select_epic(selection_input, context)
    results[SelectorKind.EXACT] = select_exact(
        selection_input,
        backend=backend,
        timeout_seconds=timeout_seconds,
    )
    results[SelectorKind.BRUTE_FORCE] = select_brute_force(
        selection_input,
        max_completions=brute_force_max_completions,
    )
    return MappingProxyType(results)


__all__ = [
    "BENCHMARK_INSTANCE_ARTIFACT_KIND",
    "BENCHMARK_INSTANCE_SCHEMA_VERSION",
    "BenchmarkGrammar",
    "BenchmarkInstance",
    "EpicCfgFactory",
    "EpicReplaySpec",
    "SavedLogits",
    "UnsupportedBenchmarkSchemaVersion",
    "migrate_benchmark_instance_data",
    "replay_benchmark_instance",
]
