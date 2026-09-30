"""Joint selection under a physical-position budget, separate from ordinary MWPC.

This is an exact-rational research API, not a claim of fast production inference.
It accepts the same model-independent frozen state as the existing selectors.
Full witness matches and actual budgeted commitments are distinct fields.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction

from mwpc_exact.eos_lattice import build_eos_lattice
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budget_types import BudgetPathResult, ResourceArc, ResourceDAG
from mwpc_exact.reference.budgeted_parser import budgeted_frontier
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.types import ExactnessScope, SolveStatus, TerminalEdge


@dataclass(frozen=True)
class BudgetedCommitResult:
    status: SolveStatus
    budget: int
    objective_value: Fraction | None
    committed_positions: tuple[int, ...]
    committed_proposal_ids: tuple[int, ...]
    matched_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...] | None
    witness_terminal_labels: tuple[int | str, ...] | None
    exactness_scope: ExactnessScope
    path_result: BudgetPathResult
    proof_graph: ResourceDAG
    input_fingerprint: str


def _input_fingerprint(state: SelectionInput) -> str:
    used = sorted({t for row in state.support.rows for t in row})
    emissions: dict[int, str | None] = {}
    for token in used:
        emission = state.tokenizer_adapter.emissions[token]
        emissions[token] = None if emission is None else emission.hex()
    data = {
        "grammar": state.grammar.to_dict(),
        "canvas": state.canvas,
        "rows": state.support.rows,
        "scope": state.support.exactness_scope.to_dict(),
        "proposals": [(p.proposal_id, p.position, p.token_id, p.weight) for p in state.proposals],
        "eos": state.eos_policy.to_dict(),
        "emissions": emissions,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def budgeted_commit_frontier(
    state: SelectionInput, max_budget: int
) -> tuple[BudgetedCommitResult, ...]:
    """Maximize committed proposal reward jointly over all free slots and tokens."""
    fingerprint = _input_fingerprint(state)
    lattice = build_eos_lattice(
        token_lattice=build_token_lattice(support=state.support, proposals=state.proposals),
        adapter=state.tokenizer_adapter,
        policy=state.eos_policy,
    )
    first = {arc.graph_edge_ids[0]: arc for arc in lattice.arcs}
    resource_arcs: list[ResourceArc] = []
    origins: dict[int, int] = {}
    charged_positions: dict[int, int] = {}
    for edge in lattice.graph.edges:
        label = edge.terminal_label if isinstance(edge, TerminalEdge) else None
        arc_id = len(resource_arcs)
        resource_arcs.append(
            ResourceArc(arc_id, edge.source_state, edge.target_state, label, Fraction(), 0)
        )
        origins[arc_id] = edge.edge_id
        token_arc = first.get(edge.edge_id)
        if token_arc is None or state.canvas[token_arc.position] is not None:
            continue
        reward = sum(
            (
                Fraction(p.weight)
                for p in state.proposals
                if p.position == token_arc.position
                and p.token_id == token_arc.token_id
                and p.weight > 0
            ),
            Fraction(),
        )
        if reward:
            arc_id = len(resource_arcs)
            resource_arcs.append(
                ResourceArc(arc_id, edge.source_state, edge.target_state, label, reward, 1)
            )
            origins[arc_id] = edge.edge_id
            charged_positions[arc_id] = token_arc.position
    graph = ResourceDAG(
        index_terminal_dag(lattice.graph).topological_order,
        lattice.graph.start_node_id,
        lattice.graph.final_node_ids,
        tuple(resource_arcs),
        f"exact_on_support: {state.support.fingerprint}; EOS={state.eos_policy.to_dict()}",
    )
    results: list[BudgetedCommitResult] = []
    for path in budgeted_frontier(state.grammar, graph, max_budget):
        report = check_budget_certificate(state.grammar, graph, path)
        if not report.accepted:
            raise RuntimeError(f"Independent budget optimality proof rejected: {report.errors}")
        tokens = None
        commits: tuple[int, ...] = ()
        matched: tuple[int, ...] = ()
        committed_ids: tuple[int, ...] = ()
        if path.witness_arc_ids is not None:
            original = tuple(origins[i] for i in path.witness_arc_ids)
            token_path = lattice.reconstruct_original_path(original)
            lattice.validate_path(token_path)
            tokens = token_path.token_path.token_ids
            commits = tuple(
                sorted(charged_positions[i] for i in path.witness_arc_ids if i in charged_positions)
            )
            if len(set(commits)) != len(commits) or len(commits) != path.consumed_budget:
                raise RuntimeError("Resource path double charges a physical slot")
            matched = tuple(
                p.proposal_id
                for p in state.proposals
                if p.weight > 0 and tokens[p.position] == p.token_id
            )
            committed_ids = tuple(
                p.proposal_id
                for p in state.proposals
                if p.proposal_id in matched and p.position in commits
            )
            recomputed = sum(
                (Fraction(p.weight) for p in state.proposals if p.proposal_id in committed_ids),
                Fraction(),
            )
            if recomputed != path.objective_value:
                raise RuntimeError("Budgeted objective does not equal original committed weights")
        results.append(
            BudgetedCommitResult(
                path.status,
                path.budget,
                path.objective_value,
                commits,
                committed_ids,
                matched,
                tokens,
                path.witness_terminal_labels,
                state.support.exactness_scope,
                path,
                graph,
                fingerprint,
            )
        )
    return tuple(results)


def solve_budgeted_commit(state: SelectionInput, budget: int) -> BudgetedCommitResult:
    """One-cap convenience API; existing serial/EPIC/exact strategies are unchanged."""
    return budgeted_commit_frontier(state, budget)[budget]


def budgeted_progress_update(
    state: SelectionInput, result: BudgetedCommitResult
) -> tuple[tuple[int | None, ...], tuple[int, ...]]:
    """Fill up to B free slots from the certified witness; fallback has no reward."""
    if result.status is not SolveStatus.OPTIMAL or result.witness_token_ids is None:
        raise ValueError("progress requires an OPTIMAL witness")
    if result.budget == 0 and any(t is None for t in state.canvas):
        raise ValueError("a zero budget cannot guarantee progress")
    # Check state compatibility rather than silently accepting another state's witness.
    if result.input_fingerprint != _input_fingerprint(state):
        raise ValueError("result belongs to a different frozen input")
    if len(result.witness_token_ids) != len(state.canvas) or any(
        token is not None and token != result.witness_token_ids[i]
        for i, token in enumerate(state.canvas)
    ):
        raise ValueError("witness does not preserve this canvas")
    chosen = list(result.committed_positions)
    fallback: list[int] = []
    for i, token in enumerate(state.canvas):
        if len(chosen) == result.budget:
            break
        if token is None and i not in chosen:
            chosen.append(i)
            fallback.append(i)
    updated = list(state.canvas)
    for i in chosen:
        updated[i] = result.witness_token_ids[i]
    if any(
        p.weight > 0
        and p.position in fallback
        and result.witness_token_ids[p.position] == p.token_id
        for p in state.proposals
    ):
        raise RuntimeError("unscored fallback contradicts budget optimality")
    return tuple(updated), tuple(fallback)
