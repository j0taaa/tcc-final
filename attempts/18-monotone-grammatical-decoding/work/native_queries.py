"""Best-derivation lex/greedy queries on identical maintained parser kernels.

Research contract: JSON, finite original-token slots, ABSENT EOS. Lossless
dyadic transport uses the existing Fraction/BigUint comparison throughout.
All native controls have the same independent linear JSON/path validation.
No change to the maintained public MWPC objective or certificate API.
"""

import json
from collections import Counter
from dataclasses import replace
from math import ldexp
from types import SimpleNamespace

from grammar_selectors import CachedPrefix, Recompute
from monotone import validate_order
from trie_lattice import TrieLattice

from mwpc_exact.backend import ExactBackend
from mwpc_exact.eos_lattice import build_eos_lattice
from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.reference.dag_parser import _reconstruct_dag_path, run_dag_cky
from mwpc_exact.rust_solver import solve_rust_dag
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.types import Proposal, SolveStatus


class NativeQuery:
    def initialize(self, state, backend, compressed, grammar):
        if state.eos_policy.mode is not EOSMode.ABSENT:
            raise NotImplementedError("native research decoder requires ABSENT EOS")
        self.backend = backend
        self.compressed = compressed
        self.query_grammar = state.grammar if grammar is None else grammar
        self.geometry = TrieLattice(state) if compressed else None
        self.minimum_position = None
        self.plan = SimpleNamespace(state=state)
        self.base = replace(
            state.support,
            permitted_token_ids=tuple(sorted({t for row in state.support.rows for t in row})),
        )

    def solve(self, canvas, proposals=(), objective="lex"):
        self.calls += 1
        if len(proposals) > 1075:
            raise NotImplementedError("native dyadic priorities support at most 1075 proposals")
        state = self.plan.state
        if self.compressed:
            graph, closes, first = self.geometry.query(canvas, proposals, objective)
            lattice = None
        else:
            if objective != "lex":
                raise NotImplementedError("count warm start requires prepared trie")
            support = replace(
                self.base,
                canvas=tuple(canvas),
                rows=tuple(
                    (t,) if t is not None else row
                    for t, row in zip(canvas, self.base.rows, strict=True)
                ),
            )
            priorities = tuple(
                Proposal(j, p, token, ldexp(1.0, -j)) for j, (p, token, _) in enumerate(proposals)
            )
            lattice = build_eos_lattice(
                token_lattice=build_token_lattice(support=support, proposals=priorities),
                adapter=state.tokenizer_adapter,
                policy=state.eos_policy,
            )
            graph = lattice.normalized_graph
        if hasattr(self, "root_parser"):
            result, certificate = self.root_parser.parse(graph)
        elif self.backend is ExactBackend.RUST:
            result = solve_rust_dag(self.query_grammar, graph, timeout_seconds=30)
            certificate = result.certificate
        else:
            result = run_dag_cky(self.query_grammar, graph)
            certificate = (
                _reconstruct_dag_path(result) if result.status is SolveStatus.OPTIMAL else None
            )
        if result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
            return None
        if result.status is SolveStatus.TIMEOUT:
            raise TimeoutError("native_parser_deadline")
        if result.status is SolveStatus.UNSUPPORTED:
            raise NotImplementedError("native_parser_unavailable")
        if result.status is not SolveStatus.OPTIMAL or certificate is None:
            raise RuntimeError(f"native_parser_status_{result.status}")
        if self.compressed:
            node, choices, labels = graph.start_node_id, [], []
            edge_by_id = {e.edge_id: e for e in graph.edges}
            for edge_id in certificate.witness_graph_edge_ids:
                edge = edge_by_id[edge_id]
                if edge.source_state != node:
                    raise RuntimeError("non-contiguous native trie path")
                node = edge.target_state
                labels.append(edge.terminal_label)
                if edge_id in closes:
                    choices.append(closes[edge_id])
            if node not in graph.final_node_ids or [p for p, _ in choices] != list(
                range(len(canvas))
            ):
                raise RuntimeError("native trie path did not consume every original slot")
            tokens = tuple(token for _, token in choices)
            if bytes(labels) != state.tokenizer_adapter.detokenize_bytes(tokens):
                raise RuntimeError("native trie bytes differ from original tokens")
            matched_ids = certificate.selected_proposal_ids
        else:
            path = lattice.reconstruct_normalized_path(certificate.witness_graph_edge_ids)
            lattice.validate_path(path)
            tokens = path.token_path.token_ids
            matched_ids = path.matched_proposal_ids
        if len(tokens) != len(canvas) or any(
            token not in row or (fixed is not None and fixed != token)
            for token, row, fixed in zip(tokens, self.base.rows, canvas, strict=True)
        ):
            raise RuntimeError("native witness violated original slots/support/canvas")
        expected = [j for j, (p, token, _) in enumerate(proposals) if tokens[p] == token]
        if Counter(matched_ids) != Counter(expected):
            raise RuntimeError("native witness violated exact priority provenance")
        text = state.tokenizer_adapter.detokenize_bytes(tokens).decode()
        json.loads(text, parse_constant=self.reject_constant)
        if self.compressed:
            self.minimum_position = first if not proposals else None
        return tokens

    @staticmethod
    def reject_constant(value):
        raise ValueError(f"non-JSON constant {value}")


class NativeLex(NativeQuery, Recompute):
    def __init__(self, state, *, backend=ExactBackend.RUST, compressed=False, grammar=None):
        self.initialize(state, backend, compressed, grammar)
        Recompute.__init__(self, self.plan, lex=True)

    def transition(self, proposals, *, threshold=0.8, cap=None):
        if not self.compressed:
            return super().transition(proposals, threshold=threshold, cap=cap)
        validate_order(proposals)
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        current = self.solve(self.canvas, proposals)
        if current is None:
            raise ValueError("infeasible_on_support")
        accepted = [(p, t, w) for p, t, w in proposals if current[p] == t]
        updates = {}
        for p, t, w in accepted:
            if w >= threshold and self.canvas[p] is None and len(updates) < cap:
                updates.setdefault(p, t)
        if not updates:
            free = [(p, t) for p, t, _ in accepted if self.canvas[p] is None]
            if free:
                updates = dict(free[:1])
            else:
                p = self.canvas.index(None)
                updates[p] = current[p]
        for p, t in updates.items():
            self.canvas[p] = t
        return tuple(updates.items())


class NativeSpeculative(NativeLex):
    """Verify an observable priority prefix jointly, else use full exact lex."""

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        free = [(p, t, w) for p, t, w in proposals if self.canvas[p] is None]
        selected = {}
        for p, t, w in free:
            if w < threshold or len(selected) == cap:
                break
            if p in selected and selected[p] != t:
                return super().transition(proposals, threshold=threshold, cap=cap)
            selected[p] = t
        if not selected and free:
            selected = {free[0][0]: free[0][1]}
        if selected:
            trial = list(self.canvas)
            for p, t in selected.items():
                trial[p] = t
            if self.solve(trial) is not None:
                for p, t in selected.items():
                    self.canvas[p] = t
                self.speculative_successes = getattr(self, "speculative_successes", 0) + 1
                return tuple(selected.items())
        return super().transition(proposals, threshold=threshold, cap=cap)


class NativePrefix(NativeQuery, CachedPrefix):
    def __init__(
        self, state, *, lazy=False, backend=ExactBackend.RUST, compressed=False, grammar=None
    ):
        self.initialize(state, backend, compressed, grammar)
        Recompute.__init__(self, self.plan)
        self.current = None if lazy else self.solve(self.canvas)
        if not lazy and self.current is None:
            raise ValueError("infeasible_on_support")

    def try_token(self, position, token):
        if self.current is not None and self.current[position] == token:
            return True
        trial = list(self.canvas)
        trial[position] = token
        candidate = self.solve(trial)
        if candidate is None:
            return False
        self.current = candidate
        return True

    def canonical(self):
        if not self.compressed:
            return super().canonical()
        p = self.canvas.index(None)
        if self.minimum_position != p:
            self.current = self.solve(self.canvas)
        if self.current is None:
            raise ValueError("infeasible_on_support")
        return p, self.current[p]

    def transition(self, proposals, *, threshold=0.8, cap=None):
        try:
            return super().transition(proposals, threshold=threshold, cap=cap)
        except RuntimeError as error:
            if self.current is None and str(error) == "no progress despite feasible forest":
                raise ValueError("infeasible_on_support") from None
            raise


class NativeCountWarm(NativePrefix):
    """Strong greedy control: maximize proposal matches to warm its witness.

    This objective does NOT choose commitments. It only supplies a compatible
    witness to the unchanged observable-prefix greedy policy.
    """

    def __init__(self, state, **kwargs):
        if not kwargs.get("compressed"):
            raise NotImplementedError("count warm start requires prepared trie")
        super().__init__(state, lazy=True, **kwargs)

    def transition(self, proposals, *, threshold=0.8, cap=None):
        validate_order(proposals)
        cap = len(self.canvas) if cap is None else cap
        if type(cap) is not int or cap < 1:
            raise ValueError("cap must be positive")
        self.current = self.solve(self.canvas, proposals, objective="count")
        if self.current is None:
            raise ValueError("infeasible_on_support")
        free = [(p, t) for p, t, _ in proposals if self.canvas[p] is None]
        if not any(self.current[p] == t for p, t in free):
            # Maximal count zero on free slots implies no free proposal is
            # individually feasible; fixed-slot contributions are constant.
            p = self.canvas.index(None)
            self.minimum_position = p
            self.fix(p, self.current[p])
            return ((p, self.current[p]),)
        return super().transition(proposals, threshold=threshold, cap=cap)
