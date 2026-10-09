"""Equal rooted CFG kernel for raw, global-class and contextual vocabularies."""

from types import SimpleNamespace

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG

from .lexer import END, MARK, OUT, finish
from .relevant_forest import relevant_forest
from .rooted_parser import RootParser


class Prepared:
    def __init__(
        self,
        table,
        canvas,
        grammar,
        kind,
        *,
        max_edges=2_000_000,
        max_cells=1_000_000,
        max_terms=5_000_000,
        timeout_seconds=120,
    ):
        if kind not in ("raw", "global", "local"):
            raise ValueError("unknown representation")
        self.table, self.canvas, self.kind = table, tuple(canvas), kind
        self.members, self.source_state = {}, {}
        self.rows = []
        edges, closes = [], {}
        layer, vertices = {OUT: 0}, 1

        def edge(a, b, label):
            if len(edges) >= max_edges:
                raise CompilationLimit("DAG edge budget; feasibility unresolved")
            eid = len(edges)
            edges.append(TerminalEdge(eid, a, b, label))
            return eid

        for p, fixed in enumerate(canvas):
            pending, codes = [], set()
            for q, node in sorted(layer.items()):
                if fixed is not None:
                    gid = table.by_token[q][fixed]
                    candidates = () if gid < 0 else ((fixed, gid, (fixed,)),)
                elif kind == "raw":
                    candidates = (
                        (token, gid, (token,))
                        for gid in table.by_state[q]
                        for token in table.groups[gid][3]
                    )
                elif kind == "global":
                    candidates = (
                        (cid, gid, table.classes[cid])
                        for cid, gid in enumerate(table.class_to_local[q])
                        if gid >= 0
                    )
                else:
                    candidates = ((gid, gid, table.groups[gid][3]) for gid in table.by_state[q])
                for code, gid, members in candidates:
                    _, target, output, _ = table.groups[gid]
                    if fixed is not None:
                        code = (
                            fixed
                            if kind == "raw"
                            else table.class_of[fixed]
                            if kind == "global"
                            else gid
                        )
                    self.members[p, code] = members
                    if kind == "local":
                        self.source_state[code] = q
                    codes.add(code)
                    current = node
                    for label in output:
                        edge(current, vertices, label)
                        current = vertices
                        vertices += 1
                    pending.append((current, code, target))
            targets = sorted({q for _, _, q in pending})
            new_layer = {q: vertices + i for i, q in enumerate(targets)}
            vertices += len(targets)
            for node, code, target in pending:
                eid = edge(node, new_layer[target], MARK)
                closes[eid] = (p, code)
            self.rows.append(tuple(sorted(codes)))
            layer = new_layer
        ends = []
        for q, node in sorted(layer.items()):
            ending = finish(q)
            if ending is not None:
                for label in ending:
                    edge(node, vertices, label)
                    node = vertices
                    vertices += 1
                ends.append(node)
        final = vertices
        for node in ends:
            edge(node, final, END)
        nodes = tuple(
            sorted({0, final, *(e.source_state for e in edges), *(e.target_state for e in edges)})
        )
        graph = WeightedTerminalDAG(nodes, 0, (final,), tuple(edges))
        # Private structural forest interface. Original input/frame/table are
        # validated separately; do not relax maintained SelectionInput checks.
        state = SimpleNamespace(
            canvas=(None,) * len(canvas), support=SimpleNamespace(rows=tuple(self.rows))
        )
        self.plan = relevant_forest(
            RootParser(grammar).parse(
                graph,
                state=state,
                closes=closes,
                max_cells=max_cells,
                max_terms=max_terms,
                timeout_seconds=timeout_seconds,
            )
        )
        self.graph_nodes, self.graph_edges = len(nodes), len(edges)
