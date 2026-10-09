"""Classical grouped Earley deduction on an acyclic byte DAG, epsilon-free CNF.

Predictions are reachability side conditions, not multiplied contexts. Each
constituent ends after its start. At an end vertex, finalize descending starts:
right-child completions only create constituents with strictly earlier starts.
Return max-plus best derivations or ALL alternatives for incremental controls.
See Opedal et al., ACL2023 sections5/6 and notes7/10; no new parsing theorem.
"""

import heapq
from collections import defaultdict
from time import monotonic
from types import SimpleNamespace

from mwpc_exact.cfg_posterior import CfgSampler, CompilationLimit, _Term
from mwpc_exact.types import SolveStatus


class RootParser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.binary, self.terminal = defaultdict(list), defaultdict(list)
        labels = {t.symbol_id: t.label for t in grammar.terminals}
        for r in grammar.binary_productions:
            self.binary[r.head_id].append((r.left_id, r.right_id, r.production_id))
        for r in grammar.terminal_productions:
            self.terminal[r.head_id].append((labels[r.terminal_id], r.production_id))

    def parse(self, graph, *, state=None, closes=None, max_cells=200_000, max_terms=1_000_000):
        forest = state is not None
        if any(e.source_state >= e.target_state for e in graph.edges):
            raise NotImplementedError("rooted parser requires forward byte arcs")
        if graph.start_node_id in graph.final_node_ids:
            raise NotImplementedError("rooted reference requires nonempty token slots")
        deadline = monotonic() + 30
        outgoing = defaultdict(list)
        for e in graph.edges:
            # Transport floats are exact dyadics; never use their rounded sum.
            score = 0
            for w in e.weight_terms or ((e.weight,) if e.weight else ()):
                a, b = w.as_integer_ratio()
                score += a << (1074 - (b.bit_length() - 1))
            outgoing[e.source_state, e.terminal_label].append((e, score))
        keys, ids, scores, backs, terms, heaps = [], {}, [], [], [], defaultdict(list)
        predicted, left_wait, right_wait = set(), defaultdict(list), defaultdict(dict)
        order, finalized, alternatives = [], set(), 0
        indices = (
            {(p, t): i for p, row in enumerate(state.support.rows) for i, t in enumerate(row)}
            if forest
            else None
        )

        def add(head, start, end, score, back, rule_id):
            nonlocal alternatives
            key = (head, start, end)
            node = ids.get(key)
            if node is None:
                if len(keys) >= max_cells:
                    raise CompilationLimit("rooted chart budget; feasibility unresolved")
                node = ids[key] = len(keys)
                keys.append(key)
                scores.append(score)
                backs.append(back)
                terms.append([])
                heapq.heappush(heaps[end], (-start, node))
            elif score > scores[node]:
                if node in finalized:
                    raise RuntimeError("rooted score changed after finalization")
                scores[node], backs[node] = score, back
            if forest:
                if alternatives >= max_terms:
                    raise CompilationLimit("rooted alternative budget; feasibility unresolved")
                if back[0] == "edge":
                    choice = closes.get(back[1])
                    if choice is not None:
                        p, t = choice
                        choice = (p, indices[p, t])
                    term = _Term(choice=choice, production_id=rule_id)
                else:
                    term = _Term(children=back[1:], production_id=rule_id)
                terms[node].append(term)
                alternatives += 1

        def predict(head, vertex):
            pending = [head]
            while pending:
                a = pending.pop()
                if (a, vertex) in predicted:
                    continue
                predicted.add((a, vertex))
                for label, rule in self.terminal[a]:
                    for e, score in outgoing[vertex, label]:
                        add(a, vertex, e.target_state, score, ("edge", e.edge_id), rule)
                for b, c, rule in self.binary[a]:
                    left_wait[b, vertex].append((a, c, rule))
                    pending.append(b)

        predict(self.grammar.start_nonterminal_id, graph.start_node_id)
        for vertex in sorted(graph.node_ids):
            agenda = heaps[vertex]
            while agenda:
                if monotonic() >= deadline:
                    raise TimeoutError("rooted_parser_deadline")
                _, node = heapq.heappop(agenda)
                if node in finalized:
                    raise RuntimeError("rooted constituent finalized twice")
                finalized.add(node)
                order.append(node)
                head, start, _ = keys[node]
                for a, c, rule in left_wait[head, start]:
                    prefixes = right_wait[c, vertex]
                    k = (a, start)
                    if forest:
                        prefixes.setdefault(k, []).append((node, rule))
                    else:
                        old = prefixes.get(k)
                        if old is None or scores[node] > scores[old[0]]:
                            prefixes[k] = (node, rule)
                    predict(c, vertex)
                for (a, origin), prefixes in right_wait[head, start].items():
                    for child, rule in prefixes if forest else (prefixes,):
                        add(
                            a,
                            origin,
                            vertex,
                            scores[child] + scores[node],
                            ("children", child, node),
                            rule,
                        )
        roots = [
            ids[self.grammar.start_nonterminal_id, graph.start_node_id, end]
            for end in graph.final_node_ids
            if (self.grammar.start_nonterminal_id, graph.start_node_id, end) in ids
        ]
        root = max(roots, key=lambda n: scores[n]) if roots else None
        if forest:
            if len(graph.final_node_ids) != 1:
                raise NotImplementedError("forest reference requires unique terminal boundary")
            return CfgSampler(
                state,
                self.grammar,
                tuple(map(tuple, terms)),
                tuple(order),
                root,
                len(graph.node_ids),
                len(graph.edges),
                tuple(k[0] for k in keys),
            )
        if root is None:
            return SimpleNamespace(status=SolveStatus.INFEASIBLE_ON_SUPPORT), None
        path, pending = [], [root]
        while pending:
            back = backs[pending.pop()]
            if back[0] == "edge":
                path.append(back[1])
            else:
                pending.extend(reversed(back[1:]))
        by_id = {e.edge_id: e for e in graph.edges}
        proposals = tuple(j for eid in path for j in by_id[eid].matched_proposal_ids)
        certificate = SimpleNamespace(
            witness_graph_edge_ids=tuple(path), selected_proposal_ids=proposals
        )
        return SimpleNamespace(status=SolveStatus.OPTIMAL), certificate
