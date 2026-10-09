"""Prepared proper-prefix DAG with dominated canonical secondary rank."""

from collections import defaultdict
from dataclasses import replace
from math import fsum, ldexp

from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG


class TrieLattice:
    def __init__(self, state):
        self.state = state
        self.edges, self.closes, self.slot_edges, self.paths = [], {}, [], []
        vertices, boundary = 1, 0
        for p, row in enumerate(state.support.rows):
            begin = len(self.edges)
            words = {
                t: state.tokenizer_adapter.emissions[t]
                for t in row
                if state.tokenizer_adapter.emissions[t] is not None
            }
            prefixes = sorted(
                {w[:i] for w in words.values() for i in range(1, len(w))}, key=lambda x: (len(x), x)
            )
            nodes, prefix_edges = {b"": boundary}, {}
            for prefix in prefixes:
                nodes[prefix] = vertices
                vertices += 1
                eid = len(self.edges)
                prefix_edges[prefix] = eid
                self.edges.append(TerminalEdge(eid, nodes[prefix[:-1]], nodes[prefix], prefix[-1]))
            end = vertices
            vertices += 1
            paths = {}
            for token, word in words.items():
                eid = len(self.edges)
                self.edges.append(TerminalEdge(eid, nodes[word[:-1]], end, word[-1]))
                self.closes[eid] = (p, token)
                paths[token] = (*(prefix_edges[word[:i]] for i in range(1, len(word))), eid)
            self.slot_edges.append(tuple(range(begin, len(self.edges))))
            self.paths.append(paths)
            boundary = end
        self.end = boundary
        self.close_id = {choice: eid for eid, choice in self.closes.items()}

    def query(self, canvas, proposals, objective="lex"):
        if objective not in ("lex", "count"):
            raise ValueError("unknown primary objective")
        first = next((p for p, t in enumerate(canvas) if t is None), None)
        row = () if first is None else self.state.support.rows[first]
        bits = (len(row) - 1).bit_length() if row else 0
        if len(proposals) + bits > 1075:
            raise NotImplementedError("native primary+canonical priorities require <=1075 bits")
        rewards = defaultdict(list)
        for j, (p, token, _) in enumerate(proposals):
            exponent = len(proposals) - j - 1 if objective == "lex" else 0
            rewards[p, token].append((j, ldexp(1.0, bits + exponent - 1074)))
        for i, token in enumerate(row):
            rank = len(row) - 1 - i
            if rank:
                rewards[first, token].append((None, ldexp(float(rank), -1074)))
        changes = {}
        for choice, parts in rewards.items():
            eid = self.close_id.get(choice)
            if eid is not None:
                changes[eid] = replace(
                    self.edges[eid],
                    weight=fsum(w for _, w in parts),
                    matched_proposal_ids=tuple(j for j, _ in parts if j is not None),
                    weight_terms=tuple(w for _, w in parts),
                )
        ids = [
            eid
            for p, t in enumerate(canvas)
            for eid in (self.slot_edges[p] if t is None else self.paths[p].get(t, ()))
        ]
        edges = tuple(changes.get(eid, self.edges[eid]) for eid in ids)
        nodes = tuple(
            sorted(
                {0, self.end, *(e.source_state for e in edges), *(e.target_state for e in edges)}
            )
        )
        return WeightedTerminalDAG(nodes, 0, (self.end,), edges), self.closes, first
