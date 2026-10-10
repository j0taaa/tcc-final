"""Classical lazy weighted epsilon removal, retaining original-choice circuits.

MARK is not a syntax terminal. Canonically attach every epsilon block to the
NEXT real terminal, including explicit END. No nullable CFG boundary moves.
Shared reverse END closures avoid rebuilding the same terminal suffix.
See Mohri2002. This is a reference implementation, not a new removal theorem.
"""

import heapq
from collections import defaultdict
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit, _Term

from .forest import Prepared
from .lexer import END, MARK
from .relevant_forest import relevant_forest
from .rooted_parser import RootParser


class Scanner:
    def __init__(self, prepared, *, max_cells, max_terms, deadline):
        self.max_cells, self.max_terms, self.deadline = max_cells, max_terms, deadline
        self.terms, self.alternatives, self.cache = [], 0, {}
        self.epsilon, self.ordinary = defaultdict(list), defaultdict(list)
        self.one = self.node([_Term()])
        self.final = prepared.graph.final_node_ids[0]
        indices = {(p, c): i for p, row in enumerate(prepared.rows) for i, c in enumerate(row)}
        leaves = {}
        for edge in prepared.graph.edges:
            if edge.edge_id % 256 == 0 and monotonic() >= deadline:
                raise TimeoutError("epsilon scanner preparation deadline")
            if edge.terminal_label == MARK:
                key = prepared.closes[edge.edge_id]
                if key not in leaves:
                    p, _ = key
                    leaves[key] = self.node([_Term(choice=(p, indices[key]))])
                self.epsilon[edge.source_state].append((edge.target_state, leaves[key]))
            else:
                self.ordinary[edge.source_state].append((edge.target_state, edge.terminal_label))
        self.end = {}
        for vertex in reversed(prepared.graph.node_ids):
            terms = [
                _Term(children=(leaf, self.end[target]))
                for target, leaf in self.epsilon[vertex]
                if target in self.end
            ]
            for target, label in self.ordinary[vertex]:
                if label == END:
                    if target != self.final:
                        raise ValueError("END must reach unique final boundary")
                    terms.append(_Term())
            if terms:
                self.end[vertex] = self.node(terms)

    def node(self, terms):
        if monotonic() >= self.deadline:
            raise TimeoutError("epsilon scanner deadline")
        if len(self.terms) >= self.max_cells or self.alternatives + len(terms) > self.max_terms:
            raise CompilationLimit("epsilon circuit budget; feasibility unresolved")
        node = len(self.terms)
        self.terms.append(tuple(terms))
        self.alternatives += len(terms)
        return node

    def scan(self, start, label):
        if label == END:
            return ((self.final, self.end[start]),) if start in self.end else ()
        if start not in self.cache:
            pending, incoming, expressions = [start], {}, {}
            ordinary = defaultdict(list)
            while pending:
                if monotonic() >= self.deadline:
                    raise TimeoutError("epsilon closure deadline")
                vertex = heapq.heappop(pending)
                expression = self.one if vertex == start else self.node(incoming.pop(vertex))
                expressions[vertex] = expression
                for target, emitted in self.ordinary[vertex]:
                    if emitted != END:
                        ordinary[emitted, target].append(expression)
                for target, leaf in self.epsilon[vertex]:
                    if target not in incoming:
                        incoming[target] = []
                        heapq.heappush(pending, target)
                    incoming[target].append(_Term(children=(expression, leaf)))
            by_label = defaultdict(list)
            for (emitted, target), expressions in ordinary.items():
                expression = (
                    expressions[0]
                    if len(expressions) == 1
                    else self.node([_Term(children=(child,)) for child in expressions])
                )
                by_label[emitted].append((target, expression))
            self.cache[start] = dict(by_label)
        return self.cache[start].get(label, ())


class EpsilonPrepared(Prepared):
    def __init__(self, table, canvas, grammar, kind="local", **limits):
        begin = monotonic()
        super().__init__(table, canvas, None, "bidir_" + kind, **limits)
        scanner = Scanner(
            self,
            max_cells=limits.get("max_cells", 1_000_000),
            max_terms=limits.get("max_terms", 5_000_000),
            deadline=begin + limits.get("timeout_seconds", 120),
        )
        self.plan = relevant_forest(
            RootParser(grammar).parse(
                self.graph,
                state=self.state,
                closes=self.closes,
                scanner=scanner,
                max_cells=limits.get("max_cells", 1_000_000),
                max_terms=limits.get("max_terms", 5_000_000),
                timeout_seconds=max(0, scanner.deadline - monotonic()),
            )
        )
        self.scanner_cells = len(scanner.terms)
        self.scanner_alternatives = scanner.alternatives
