"""Layered deterministic lexer image, explicit original/class token-close MARK."""

from collections import defaultdict
from dataclasses import replace
from math import fsum, ldexp

from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG

from .lexer import END, MARK, OUT, finish, scan


class LexLattice:
    lexical = True

    def __init__(self, state):
        self.state, self.edges, self.closes = state, [], {}
        self.paths, self.rank_rows = [], state.support.rows
        vertices, layer = 1, {OUT: 0}
        for p, row in enumerate(state.support.rows):
            transitions = []
            # Compute actual reachable lexical states, never use original
            # reference text to assume a lexer state inside a free slot.
            for q, node in sorted(layer.items()):
                for token in row:
                    word = state.tokenizer_adapter.emissions[token]
                    transition = None if word is None else scan(word, q)
                    if transition is not None:
                        transitions.append((node, token, *transition))
            pending, paths = [], defaultdict(list)
            for begin, token, target, output in transitions:
                node = begin
                for label in output:
                    eid = len(self.edges)
                    self.edges.append(TerminalEdge(eid, node, vertices, label))
                    paths[token].append(eid)
                    node = vertices
                    vertices += 1
                pending.append((node, token, target))
            targets = sorted({target for _, _, target in pending})
            new_layer = {q: vertices + i for i, q in enumerate(targets)}
            vertices += len(targets)
            for node, token, target in pending:
                eid = len(self.edges)
                self.edges.append(TerminalEdge(eid, node, new_layer[target], MARK))
                self.closes[eid] = (p, token)
                paths[token].append(eid)
            self.paths.append(dict(paths))
            layer = new_layer
        tail_start = len(self.edges)
        endings = []
        for q, node in sorted(layer.items()):
            ending = finish(q)
            if ending is not None:
                for label in ending:
                    eid = len(self.edges)
                    self.edges.append(TerminalEdge(eid, node, vertices, label))
                    node = vertices
                    vertices += 1
                endings.append(node)
        final = vertices
        for node in endings:
            eid = len(self.edges)
            self.edges.append(TerminalEdge(eid, node, final, END))
        self.finals = (final,)
        self.tail_edges = tuple(range(tail_start, len(self.edges)))
        self.close_ids = defaultdict(list)
        for eid, choice in self.closes.items():
            self.close_ids[choice].append(eid)

    def query(self, canvas, proposals, objective="lex"):
        first = next((p for p, t in enumerate(canvas) if t is None), None)
        row = () if first is None else self.rank_rows[first]
        bits = (len(row) - 1).bit_length() if row else 0
        if len(proposals) + bits > 1075:
            raise NotImplementedError("lexical priorities exceed 1075 bits")
        rewards = defaultdict(list)
        for j, (p, t, _) in enumerate(proposals):
            exponent = len(proposals) - j - 1 if objective == "lex" else 0
            rewards[p, t].append((j, ldexp(1.0, bits + exponent - 1074)))
        for i, t in enumerate(row):
            rank = len(row) - 1 - i
            if rank:
                rewards[first, t].append((None, ldexp(float(rank), -1074)))
        changes = {}
        for choice, parts in rewards.items():
            for eid in self.close_ids.get(choice, ()):
                changes[eid] = replace(
                    self.edges[eid],
                    weight=fsum(w for _, w in parts),
                    matched_proposal_ids=tuple(j for j, _ in parts if j is not None),
                    weight_terms=tuple(w for _, w in parts),
                )
        ids = set(self.tail_edges)
        for p, token in enumerate(canvas):
            for t in self.paths[p] if token is None else (token,):
                ids.update(self.paths[p].get(t, ()))
        # No accepting lexical final: use unreachable synthetic final. Empty
        # finals cannot be encoded by the generic immutable graph type.
        finals = self.finals or (max((e.target_state for e in self.edges), default=0) + 1,)
        edges = tuple(changes.get(eid, self.edges[eid]) for eid in sorted(ids))
        nodes = tuple(
            sorted({0, *finals, *(e.source_state for e in edges), *(e.target_state for e in edges)})
        )
        return WeightedTerminalDAG(nodes, 0, finals, edges), self.closes, first
