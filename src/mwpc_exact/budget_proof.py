"""Portable original-input proofs, readable without importing the optimizer."""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

from mwpc_exact.budget_bounds import budget_input_fingerprint, certify_budget_batch
from mwpc_exact.budget_certificate import check_budget_commit_certificate
from mwpc_exact.budget_graph import (
    BudgetGraphLayout,
    BudgetGraphNode,
    CompiledBudgetGraph,
    TokenClosing,
)
from mwpc_exact.budget_result import BudgetedCommitResult
from mwpc_exact.eos_policy import TokenRole
from mwpc_exact.reference.budget_types import (
    BudgetCertificate,
    BudgetPathResult,
    ResourceArc,
    ResourceDAG,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.serde import _integer, _mapping, _sequence, _string, _text
from mwpc_exact.serialization import _selection_input_from_dict, _selection_input_to_dict
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import SolveStatus, TerminalLabel


def fraction_data(value: Fraction | None) -> list[int] | None:
    return None if value is None else [value.numerator, value.denominator]


def _ints(value: object, name: str) -> tuple[int, ...]:
    return tuple(_integer(x, name) for x in _sequence(value, name))


def _optional_int(value: object, name: str) -> int | None:
    return None if value is None else _integer(value, name)


def _row(value: object, width: int, name: str) -> Sequence[object]:
    row = _sequence(value, name)
    if len(row) != width:
        raise ValueError(f"{name} must contain exactly {width} fields")
    return row


def _fraction(value: object) -> Fraction:
    pair = _row(value, 2, "rational")
    return Fraction(_integer(pair[0], "numerator"), _integer(pair[1], "denominator", minimum=1))


def _label(value: object) -> TerminalLabel:
    if isinstance(value, str):
        return _string(value, "label")
    byte = _integer(value, "label")
    if byte > 255:
        raise ValueError("integer label must be a byte")
    return byte


def budget_proof_data(
    state: SelectionInput, frontier: Sequence[BudgetedCommitResult]
) -> dict[str, object]:
    """Write one common graph/potential table plus every budget's witness.

    Reuse the established strict saved-state codec rather than inventing a
    second tokenizer/support/proposal format. There is no model dependency.
    """
    if not frontier or [r.budget for r in frontier] != list(range(len(frontier))):
        raise ValueError("proof requires a complete budget frontier starting at zero")
    first = frontier[0]
    proof = first.path_result.certificate
    if proof.max_budget != len(frontier) - 1:
        raise ValueError("frontier does not match proof budget range")
    for result in frontier:
        report = check_budget_commit_certificate(state, result)
        if (
            not report.accepted
            or result.compiled_graph != first.compiled_graph
            or result.path_result.certificate != proof
        ):
            raise ValueError(f"invalid or inconsistent original-input proof: {report.errors}")
    graph, compiled = first.proof_graph, first.compiled_graph
    return {
        "schema_version": 2,
        "kind": "original_input_budget_optimality_proof",
        "input": {"grammar": state.grammar.to_dict(), "selection": _selection_input_to_dict(state)},
        "input_fingerprint": budget_input_fingerprint(state),
        "graph": {
            "nodes": list(graph.nodes),
            "start": graph.start,
            "finals": list(graph.finals),
            "support_description": graph.support_description,
            "arcs": [
                [a.arc_id, a.source, a.target, a.label, fraction_data(a.reward), a.cost]
                for a in graph.arcs
            ],
        },
        "compilation": {
            "layout": compiled.layout.value,
            "private_node_count": compiled.private_node_count,
            "nodes": [
                [n.node_id, n.position, n.after_eos, n.prefix.hex(), n.private_token_id]
                for n in compiled.nodes
            ],
            "closings": [
                [c.arc_id, c.position, c.token_id, c.role.value] for c in compiled.closings
            ],
        },
        "certificate": {
            "max_budget": proof.max_budget,
            "epsilon_bounds": [[*r[:-1], fraction_data(r[-1])] for r in proof.epsilon_bounds],
            "grammar_bounds": [[*r[:-1], fraction_data(r[-1])] for r in proof.grammar_bounds],
        },
        "frontier": [
            {
                "budget": r.budget,
                "status": r.status.value,
                "objective_value": fraction_data(r.objective_value),
                "witness_arc_ids": r.path_result.witness_arc_ids,
                "witness_terminal_labels": r.witness_terminal_labels,
                "consumed_budget": r.path_result.consumed_budget,
                "committed_positions": r.committed_positions,
                "committed_proposal_ids": r.committed_proposal_ids,
                "matched_proposal_ids": r.matched_proposal_ids,
                "witness_token_ids": r.witness_token_ids,
            }
            for r in frontier
        ],
    }


def read_budget_proof(value: object) -> tuple[SelectionInput, tuple[BudgetedCommitResult, ...]]:
    """Strict typed decoding; verification is a separate, mandatory operation."""
    data = _mapping(value, "proof")
    if _integer(data["schema_version"], "schema_version") != 2:
        raise ValueError("unsupported original-input proof schema")
    original = _mapping(data["input"], "original input")
    state = _selection_input_from_dict(
        original["selection"], CnfGrammar.from_dict(_mapping(original["grammar"], "grammar"))
    )
    raw = _mapping(data["graph"], "graph")
    arcs = []
    for value in _sequence(raw["arcs"], "arcs"):
        row = _row(value, 6, "resource arc")
        arcs.append(
            ResourceArc(
                _integer(row[0], "arc id"),
                _integer(row[1], "source"),
                _integer(row[2], "target"),
                None if row[3] is None else _label(row[3]),
                _fraction(row[4]),
                _integer(row[5], "cost"),
            )
        )
    graph = ResourceDAG(
        _ints(raw["nodes"], "nodes"),
        _integer(raw["start"], "start"),
        _ints(raw["finals"], "finals"),
        tuple(arcs),
        _string(raw["support_description"], "scope"),
    )
    raw_compile = _mapping(data["compilation"], "compilation")
    nodes = []
    for value in _sequence(raw_compile["nodes"], "node meanings"):
        row = _row(value, 5, "node meaning")
        after = row[2]
        if not isinstance(after, bool):
            raise ValueError("after_eos must be Boolean")
        nodes.append(
            BudgetGraphNode(
                _integer(row[0], "node"),
                _integer(row[1], "position"),
                after,
                bytes.fromhex(_text(row[3], "prefix")),
                _optional_int(row[4], "private token"),
            )
        )
    closings = []
    for value in _sequence(raw_compile["closings"], "closings"):
        row = _row(value, 4, "token closing")
        closings.append(
            TokenClosing(
                _integer(row[0], "closing arc"),
                _integer(row[1], "position"),
                _integer(row[2], "token"),
                TokenRole(_string(row[3], "role")),
            )
        )
    compiled = CompiledBudgetGraph(
        graph,
        BudgetGraphLayout(_string(raw_compile["layout"], "layout")),
        tuple(nodes),
        tuple(closings),
        _integer(raw_compile["private_node_count"], "private count"),
    )
    raw_proof = _mapping(data["certificate"], "potentials")
    epsilon = []
    grammar = []
    for value in _sequence(raw_proof["epsilon_bounds"], "epsilon bounds"):
        row = _row(value, 4, "epsilon bound")
        epsilon.append(
            (
                _integer(row[0], "source"),
                _integer(row[1], "target"),
                _integer(row[2], "cost"),
                _fraction(row[3]),
            )
        )
    for value in _sequence(raw_proof["grammar_bounds"], "grammar bounds"):
        row = _row(value, 5, "grammar bound")
        grammar.append(
            (
                _integer(row[0], "nonterminal"),
                _integer(row[1], "source"),
                _integer(row[2], "target"),
                _integer(row[3], "cost"),
                _fraction(row[4]),
            )
        )
    proof = BudgetCertificate(
        _integer(raw_proof["max_budget"], "max budget"), tuple(epsilon), tuple(grammar)
    )
    results = []
    for value in _sequence(data["frontier"], "frontier"):
        result_data = _mapping(value, "budget result")
        tokens = (
            None
            if result_data["witness_token_ids"] is None
            else _ints(result_data["witness_token_ids"], "witness tokens")
        )
        ids = (
            None
            if result_data["witness_arc_ids"] is None
            else _ints(result_data["witness_arc_ids"], "witness arcs")
        )
        objective = (
            None
            if result_data["objective_value"] is None
            else _fraction(result_data["objective_value"])
        )
        labels = (
            None
            if result_data["witness_terminal_labels"] is None
            else tuple(
                _label(x) for x in _sequence(result_data["witness_terminal_labels"], "labels")
            )
        )
        path = BudgetPathResult(
            SolveStatus(_string(result_data["status"], "status")),
            _integer(result_data["budget"], "budget"),
            objective,
            ids,
            labels,
            _optional_int(result_data["consumed_budget"], "consumed budget"),
            proof,
            graph.support_description,
        )
        results.append(
            BudgetedCommitResult(
                path.status,
                path.budget,
                objective,
                _ints(result_data["committed_positions"], "commitments"),
                _ints(result_data["committed_proposal_ids"], "committed IDs"),
                _ints(result_data["matched_proposal_ids"], "matched IDs"),
                tokens,
                labels,
                state.support.exactness_scope,
                path,
                graph,
                _string(data["input_fingerprint"], "input fingerprint"),
                compiled,
            )
        )
    if [r.budget for r in results] != list(range(proof.max_budget + 1)):
        raise ValueError("proof must contain the complete budget frontier")
    return state, tuple(results)


def verify_budget_proof(
    value: object,
    *,
    expected_input: SelectionInput | None = None,
    expected_input_fingerprint: str | None = None,
) -> dict[str, object]:
    """Verify a portable proof, optionally bound to an externally supplied input."""
    state, results = read_budget_proof(value)
    actual_fingerprint = budget_input_fingerprint(state)
    if expected_input is not None and actual_fingerprint != budget_input_fingerprint(
        expected_input
    ):
        raise ValueError("portable proof does not match the expected external input")
    if expected_input_fingerprint is not None and actual_fingerprint != expected_input_fingerprint:
        raise ValueError("portable proof does not match the expected input fingerprint")
    checked = []
    for result in results:
        report = check_budget_commit_certificate(state, result)
        if not report.accepted:
            raise ValueError(f"Budget {result.budget}: {report.errors}")
        row: dict[str, object] = {"budget": result.budget, "objective": str(result.objective_value)}
        if result.witness_token_ids is not None:
            quality = certify_budget_batch(
                state,
                budget=result.budget,
                witness_token_ids=result.witness_token_ids,
                committed_positions=result.committed_positions,
            )
            row.update(
                upper_bound=str(quality.upper_bound),
                gap_bound=str(quality.additive_gap_bound),
                optimal_under_support_expansion=quality.optimal_under_support_expansion,
            )
        checked.append(row)
    return {
        "verification": "PASS",
        "verification_scope": "original_input_and_resource_optimality",
        "input_fingerprint": actual_fingerprint,
        "scope": results[0].proof_graph.support_description,
        "frontier": checked,
    }
