"""Strict original-token input serialization for portable certificates."""

from __future__ import annotations

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.evaluation._serde import (
    _exact_fields,
    _float,
    _integer,
    _mapping,
    _sequence,
    _string,
    _validate_sha256,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import PerPositionSupport, SupportInputSource
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactnessScope, Proposal


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
        "top_k_token_ids_by_position": [list(row) for row in support.top_k_token_ids_by_position],
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
            None if token_id is None else _integer(token_id, f"canvas token at position {position}")
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
