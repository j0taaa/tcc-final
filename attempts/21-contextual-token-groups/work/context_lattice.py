"""Context-dependent overlapping token groups; original choices never conflated."""

from collections import defaultdict
from dataclasses import replace
from math import fsum, ldexp

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind, TerminalEdge, WeightedTerminalDAG

from .lexer import END, MARK, OUT, finish, scan


class Transitions:
    def __init__(self, adapter):
        self.adapter, self.values = adapter, {}

    def get(self, token, q):
        key = (token, q)
        if key not in self.values:
            word = self.adapter.emissions[token]
            self.values[key] = None if word is None else scan(word, q)
        return self.values[key]


class ContextLattice:
    lexical = True

    def __init__(self, state, cache=None):
        self.state, self.cache = state, cache or Transitions(state.tokenizer_adapter)
        self.edges, self.closes, self.groups, self.paths = [], {}, [], []
        self.by_key, self.by_token, self.states, self.position_groups = {}, [], [], []
        self.active_rows = tuple(frozenset(row) for row in state.support.rows)
        layer, vertices = {OUT: 0}, 1
        for p, row in enumerate(state.support.rows):
            self.states.append(tuple(layer))
            memberships, grouped = defaultdict(set), {}
            for q in sorted(layer):
                for token in row:
                    effect = self.cache.get(token, q)
                    if effect is not None:
                        grouped.setdefault((q, *effect), set()).add(token)
            pending, gids = [], []
            for (q, target, output), members in sorted(grouped.items()):
                gid = len(self.groups)
                self.by_key[p, q, target, output] = gid
                self.groups.append(dict(p=p, q=q, target=target, output=output, members=members))
                gids.append(gid)
                for token in members:
                    memberships[token].add(gid)
                node, path = layer[q], []
                for label in output:
                    eid = len(self.edges)
                    self.edges.append(TerminalEdge(eid, node, vertices, label))
                    path.append(eid)
                    node = vertices
                    vertices += 1
                pending.append((node, gid, target, path))
            targets = sorted({target for _, _, target, _ in pending})
            new_layer = {q: vertices + i for i, q in enumerate(targets)}
            vertices += len(targets)
            for node, gid, target, path in pending:
                eid = len(self.edges)
                self.edges.append(TerminalEdge(eid, node, new_layer[target], MARK))
                self.closes[eid] = (p, gid)
                self.paths.append(tuple((*path, eid)))
            self.position_groups.append(tuple(gids))
            self.by_token.append({t: set(memberships.get(t, ())) for t in row})
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
        self.final = vertices
        for node in endings:
            eid = len(self.edges)
            self.edges.append(TerminalEdge(eid, node, self.final, END))
        self.tail = tuple(range(tail_start, len(self.edges)))

    def update(self, state):
        if any(
            fixed is None and not old.issubset(row)
            for fixed, old, row in zip(
                state.canvas, self.active_rows, state.support.rows, strict=True
            )
        ):
            raise ValueError("context reuse requires monotonic free support")
        additions = []
        for p, row in enumerate(state.support.rows):
            for token in row:
                if token in self.by_token[p]:
                    continue
                gids = set()
                for q in self.states[p]:
                    effect = self.cache.get(token, q)
                    if effect is not None:
                        gid = self.by_key.get((p, q, *effect))
                        if gid is None:
                            return False
                        gids.add(gid)
                additions.append((p, token, gids))
        for p, token, gids in additions:
            self.by_token[p][token] = gids
            for gid in gids:
                self.groups[gid]["members"].add(token)
        self.state = state
        self.active_rows = tuple(frozenset(row) for row in state.support.rows)
        return True

    def graph(self, ids, changes):
        edges = tuple(changes.get(eid, self.edges[eid]) for eid in sorted(ids))
        nodes = tuple(
            sorted(
                {0, self.final, *(e.source_state for e in edges), *(e.target_state for e in edges)}
            )
        )
        return WeightedTerminalDAG(nodes, 0, (self.final,), edges)

    def virtual(self, grammar):
        if any(not row for row in self.position_groups):
            raise ValueError("infeasible_on_support")
        canvas = (None,) * len(self.position_groups)
        emissions = tuple(
            self.state.tokenizer_adapter.emissions[min(g["members"])] for g in self.groups
        )
        support = build_per_position_support(
            canvas=canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=len(self.groups),
                pruning_description=(
                    "internal context-specific groups; not independent original probabilities"
                ),
            ),
            explicit_support=dict(enumerate(self.position_groups)),
        )
        state = SelectionInput(
            grammar,
            canvas,
            (),
            support,
            CompositionalByteLevelAdapter(emissions),
            EOSPolicy(EOSMode.ABSENT),
        )
        return state, self.graph(range(len(self.edges)), {}), self.closes

    def query(self, canvas, proposals, objective="lex"):
        first = next((p for p, t in enumerate(canvas) if t is None), None)
        row = () if first is None else tuple(sorted(self.active_rows[first]))
        bits = (len(row) - 1).bit_length() if row else 0
        if len(proposals) + bits > 1075:
            raise NotImplementedError("contextual priorities exceed1075 bits")
        rewards, scores = defaultdict(list), defaultdict(int)
        for j, (p, t, _) in enumerate(proposals):
            exponent = len(proposals) - j - 1 if objective == "lex" else 0
            units = 1 << (bits + exponent)
            scores[p, t] += units
            rewards[p, t].append((j, ldexp(1.0, bits + exponent - 1074)))
        for i, t in enumerate(row):
            rank = len(row) - 1 - i
            if rank:
                scores[first, t] += rank
                rewards[first, t].append((None, ldexp(float(rank), -1074)))
        ids, changes, closes = set(self.tail), {}, {}
        for gid, g in enumerate(self.groups):
            p = g["p"]
            members = (
                g["members"].intersection(self.active_rows[p])
                if canvas[p] is None
                else ({canvas[p]} if canvas[p] in g["members"] else set())
            )
            if not members:
                continue
            token = min(members, key=lambda t: (-scores[p, t], t))
            path = self.paths[gid]
            ids.update(path)
            eid = path[-1]
            closes[eid] = (p, token)
            parts = rewards[p, token]
            if parts:
                changes[eid] = replace(
                    self.edges[eid],
                    weight=fsum(w for _, w in parts),
                    matched_proposal_ids=tuple(j for j, _ in parts if j is not None),
                    weight_terms=tuple(w for _, w in parts),
                )
        return self.graph(ids, changes), closes, first
