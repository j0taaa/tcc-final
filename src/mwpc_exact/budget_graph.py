"""Direct finite-slot resource graphs with optional exact token-prefix sharing.

Rewards and physical budget are attached to token CLOSURES, never a shared
prefix. No token is pruned and no ordinary MWPC epsilon normalization is run.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from mwpc_exact.budget_bounds import proposal_rewards
from mwpc_exact.eos_policy import EOSMode, TokenRole
from mwpc_exact.reference.budget_types import ResourceArc, ResourceDAG, nonnegative_integer
from mwpc_exact.state import SelectionInput


class BudgetGraphLayout(StrEnum):
    PRIVATE = "private"
    COMPACT = "compact"


@dataclass(frozen=True)
class BudgetGraphNode:
    node_id: int
    position: int
    after_eos: bool
    prefix: bytes = b""
    private_token_id: int | None = None

    def __post_init__(self) -> None:
        nonnegative_integer(self.node_id, "node_id")
        nonnegative_integer(self.position, "position")
        if not isinstance(self.after_eos, bool) or not isinstance(self.prefix, bytes):
            raise ValueError("node EOS state must be Boolean and its prefix must be bytes")
        if self.private_token_id is not None:
            nonnegative_integer(self.private_token_id, "private_token_id")


@dataclass(frozen=True)
class TokenClosing:
    arc_id: int
    position: int
    token_id: int
    role: TokenRole

    def __post_init__(self) -> None:
        for name in ("arc_id", "position", "token_id"):
            nonnegative_integer(getattr(self, name), name)
        if not isinstance(self.role, TokenRole):
            raise ValueError("closing role must be a TokenRole")


@dataclass(frozen=True)
class CompiledBudgetGraph:
    graph: ResourceDAG
    layout: BudgetGraphLayout
    nodes: tuple[BudgetGraphNode, ...]
    closings: tuple[TokenClosing, ...]
    private_node_count: int

    @property
    def node_savings(self) -> int:
        return self.private_node_count - len(self.graph.nodes)


def compile_budget_graph(
    state: SelectionInput, *, layout: BudgetGraphLayout = BudgetGraphLayout.COMPACT
) -> CompiledBudgetGraph:
    """Compile precisely the represented tokens with the configured EOS/PAD policy.

    Proper prefixes are shared only inside one physical slot. Leaf tokens close
    on their last byte; a token that prefixes another closes by epsilon. Aliases
    with identical bytes still have separate identifiable closing arcs.
    """
    if not isinstance(layout, BudgetGraphLayout):
        raise ValueError("layout must be a BudgetGraphLayout")
    count = len(state.canvas)
    nodes = [
        BudgetGraphNode(2 * i + int(after), i, after)
        for i in range(count + 1)
        for after in (False, True)
    ]
    prefix_nodes: dict[tuple[int, int | None, bytes], int] = {}
    ordinary: dict[int, tuple[int, ...]] = {}
    private_count = len(nodes)
    special_mode = state.eos_policy.mode is not EOSMode.ABSENT
    special_ids = set(state.eos_policy.termination_token_ids)
    if special_mode and state.eos_policy.pad_token_id is not None:
        special_ids.add(state.eos_policy.pad_token_id)
    for position, row in enumerate(state.support.rows):
        tokens = tuple(
            t
            for t in row
            if t not in special_ids and state.tokenizer_adapter.emissions[t] is not None
        )
        ordinary[position] = tokens
        keys: set[tuple[int | None, bytes]] = set()
        for token in tokens:
            word = state.tokenizer_adapter.token_bytes(token)
            private_count += len(word) - 1
            owner = token if layout is BudgetGraphLayout.PRIVATE else None
            keys.update((owner, word[:offset]) for offset in range(1, len(word)))
        for owner, prefix in sorted(
            keys, key=lambda x: (len(x[1]), x[1], -1 if x[0] is None else x[0])
        ):
            node_id = len(nodes)
            nodes.append(BudgetGraphNode(node_id, position, False, prefix, owner))
            prefix_nodes[position, owner, prefix] = node_id

    arcs: list[ResourceArc] = []
    closings: list[TokenClosing] = []
    rewards = proposal_rewards(state)

    def add_arc(
        source: int, target: int, label: int | None, reward: Fraction = Fraction(), cost: int = 0
    ) -> int:
        arc_id = len(arcs)
        arcs.append(ResourceArc(arc_id, source, target, label, reward, cost))
        return arc_id

    def close(
        position: int, token: int, role: TokenRole, source: int, target: int, label: int | None
    ) -> None:
        arc_id = add_arc(source, target, label)
        closings.append(TokenClosing(arc_id, position, token, role))
        reward = rewards.get((position, token), Fraction())
        if state.canvas[position] is None and reward > 0:
            arc_id = add_arc(source, target, label, reward, 1)
            closings.append(TokenClosing(arc_id, position, token, role))

    for node in nodes[2 * (count + 1) :]:
        prefix = node.prefix
        parent = (
            2 * node.position
            if len(prefix) == 1
            else prefix_nodes[node.position, node.private_token_id, prefix[:-1]]
        )
        add_arc(parent, node.node_id, prefix[-1])
    for position, row in enumerate(state.support.rows):
        for token in ordinary[position]:
            word = state.tokenizer_adapter.token_bytes(token)
            owner = token if layout is BudgetGraphLayout.PRIVATE else None
            end_prefix = prefix_nodes.get((position, owner, word))
            if end_prefix is not None:
                close(position, token, TokenRole.ORDINARY, end_prefix, 2 * (position + 1), None)
            else:
                source = (
                    2 * position if len(word) == 1 else prefix_nodes[position, owner, word[:-1]]
                )
                close(position, token, TokenRole.ORDINARY, source, 2 * (position + 1), word[-1])
        if special_mode:
            for token in row:
                if token in state.eos_policy.termination_token_ids:
                    close(
                        position, token, TokenRole.EOS, 2 * position, 2 * (position + 1) + 1, None
                    )
                if token == state.eos_policy.pad_token_id:
                    close(
                        position,
                        token,
                        TokenRole.PAD,
                        2 * position + 1,
                        2 * (position + 1) + 1,
                        None,
                    )
    finals: tuple[int, ...] = (2 * count,)
    if state.eos_policy.mode is EOSMode.REQUIRED:
        finals = (2 * count + 1,)
    elif state.eos_policy.mode is EOSMode.OPTIONAL:
        finals = (2 * count, 2 * count + 1)
    graph = ResourceDAG(
        tuple(
            n.node_id for n in sorted(nodes, key=lambda n: (n.position, len(n.prefix), n.node_id))
        ),
        0,
        finals,
        tuple(arcs),
        f"exact_on_support: {state.support.fingerprint}; EOS={state.eos_policy.to_dict()}",
    )
    return CompiledBudgetGraph(graph, layout, tuple(nodes), tuple(closings), private_count)


def reconstruct_budget_tokens(
    compiled: CompiledBudgetGraph, arc_ids: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Read token identity only at closing arcs on a validated original path."""
    by_id = {arc.arc_id: arc for arc in compiled.graph.arcs}
    closing = {end.arc_id: end for end in compiled.closings}
    tokens: list[int] = []
    commits: list[int] = []
    current = compiled.graph.start
    for arc_id in arc_ids:
        arc = by_id.get(arc_id)
        if arc is None or arc.source != current:
            raise ValueError("resource witness is not a connected original path")
        current = arc.target
        end = closing.get(arc_id)
        if end is not None:
            if end.position != len(tokens):
                raise ValueError("token closing does not consume the next physical slot")
            tokens.append(end.token_id)
            if arc.cost:
                commits.append(end.position)
    if current not in compiled.graph.finals:
        raise ValueError("resource witness does not end at an accepting boundary")
    return tuple(tokens), tuple(commits)
