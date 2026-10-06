"""Portable conflict certificates; verification imports no optimization engine."""

from __future__ import annotations

from mwpc_exact.budget_proof import (
    _fraction,
    _ints,
    budget_proof_data,
    fraction_data,
    read_budget_proof,
)
from mwpc_exact.conflict_certificate import (
    CertifiedConflict,
    ConflictCommitCertificate,
    ConflictCommitResult,
    MasterNode,
    check_conflict_commit,
    restrict_choices,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.serde import _integer, _mapping, _sequence, _string
from mwpc_exact.serialization import _selection_input_from_dict, _selection_input_to_dict
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import SolveStatus


def state_data(state: SelectionInput) -> dict[str, object]:
    return {"grammar": state.grammar.to_dict(), "selection": _selection_input_to_dict(state)}


def read_state(value: object) -> SelectionInput:
    data = _mapping(value, "input")
    return _selection_input_from_dict(
        data["selection"], CnfGrammar.from_dict(_mapping(data["grammar"], "grammar"))
    )


def conflict_proof_data(state: SelectionInput, result: ConflictCommitResult) -> dict[str, object]:
    check_conflict_commit(state, result)
    certificate = result.certificate
    assert certificate is not None
    return {
        "schema_version": 1,
        "kind": "original_input_conflict_commitment_proof",
        "input": state_data(state),
        "input_fingerprint": certificate.input_fingerprint,
        "conflicts": [
            {
                "source": state_data(c.source),
                "choices": c.choices,
                "proof": budget_proof_data(
                    restrict_choices(c.source, c.choices), (c.infeasibility,)
                ),
            }
            for c in certificate.conflicts
        ],
        "master": {
            "root": certificate.root,
            "nodes": [
                {
                    "excluded": n.excluded,
                    "upper_bound": fraction_data(n.upper_bound),
                    "conflict_index": n.conflict_index,
                    "children": n.children,
                }
                for n in certificate.master_nodes
            ],
        },
        "result": {
            "status": result.status.value,
            "budget": result.budget,
            "objective_value": fraction_data(result.objective_value),
            "committed_positions": result.committed_positions,
            "committed_proposal_ids": result.committed_proposal_ids,
            "matched_proposal_ids": result.matched_proposal_ids,
            "witness_token_ids": result.witness_token_ids,
            "witness_graph_edge_ids": result.witness_graph_edge_ids,
            "oracle_calls": result.oracle_calls,
            "learned_conflicts": result.learned_conflicts,
            "reused_conflicts": result.reused_conflicts,
        },
    }


def read_conflict_proof(value: object) -> tuple[SelectionInput, ConflictCommitResult]:
    data = _mapping(value, "conflict proof")
    if (
        _integer(data["schema_version"], "version") != 1
        or data["kind"] != "original_input_conflict_commitment_proof"
    ):
        raise ValueError("unsupported conflict proof")
    state = read_state(data["input"])
    conflicts = []
    for raw in _sequence(data["conflicts"], "conflicts"):
        item = _mapping(raw, "conflict")
        choices = []
        for raw_choice in _sequence(item["choices"], "choices"):
            pair = _ints(raw_choice, "choice")
            if len(pair) != 2:
                raise ValueError("choice must contain a position and token ID")
            choices.append((pair[0], pair[1]))
        source = read_state(item["source"])
        encoded_state, proofs = read_budget_proof(item["proof"])
        if encoded_state != restrict_choices(source, tuple(choices)) or len(proofs) != 1:
            raise ValueError("conflict proof does not describe its restricted source")
        conflicts.append(CertifiedConflict(source, tuple(choices), proofs[0]))
    master = _mapping(data["master"], "master")
    nodes = []
    for raw in _sequence(master["nodes"], "nodes"):
        item = _mapping(raw, "master node")
        nodes.append(
            MasterNode(
                _ints(item["excluded"], "excluded"),
                None if item["upper_bound"] is None else _fraction(item["upper_bound"]),
                None
                if item["conflict_index"] is None
                else _integer(item["conflict_index"], "core"),
                _ints(item["children"], "children"),
            )
        )
    certificate = ConflictCommitCertificate(
        _string(data["input_fingerprint"], "input fingerprint"),
        tuple(conflicts),
        tuple(nodes),
        _integer(master["root"], "root"),
    )
    raw = _mapping(data["result"], "result")
    result = ConflictCommitResult(
        SolveStatus(_string(raw["status"], "status")),
        _integer(raw["budget"], "budget"),
        None if raw["objective_value"] is None else _fraction(raw["objective_value"]),
        _ints(raw["committed_positions"], "positions"),
        _ints(raw["committed_proposal_ids"], "committed IDs"),
        _ints(raw["matched_proposal_ids"], "matched IDs"),
        None if raw["witness_token_ids"] is None else _ints(raw["witness_token_ids"], "tokens"),
        state.support.exactness_scope,
        certificate,
        _integer(raw["oracle_calls"], "calls"),
        _integer(raw["learned_conflicts"], "learned"),
        _integer(raw["reused_conflicts"], "reused"),
        None
        if raw["witness_graph_edge_ids"] is None
        else _ints(raw["witness_graph_edge_ids"], "token graph edges"),
    )
    return state, result


def verify_conflict_proof(
    value: object, *, expected_input: SelectionInput | None = None
) -> ConflictCommitResult:
    state, result = read_conflict_proof(value)
    if expected_input is not None and expected_input != state:
        raise ValueError("proof belongs to a different expected input")
    check_conflict_commit(state, result)
    return result
