"""Equal rooted CFG kernel for raw, global-class and contextual vocabularies."""

from types import SimpleNamespace

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG

from .lexer import END, MARK, OUT, finish
from .relevant_forest import relevant_forest
from .rooted_parser import RootParser


def coaccessible_layers(table, canvas):
    """Classical lexical forward/backward trimming, without weights or grammar."""
    layers = [{OUT}]

    def choices(q, fixed):
        if fixed is None:
            return table.by_state[q]
        gid = table.by_token[q][fixed]
        return () if gid < 0 else (gid,)

    for fixed in canvas:
        layers.append({table.groups[g][1] for q in layers[-1] for g in choices(q, fixed)})
    layers[-1] = {q for q in layers[-1] if finish(q) is not None}
    for p in reversed(range(len(canvas))):
        layers[p] = {
            q
            for q in layers[p]
            if any(table.groups[g][1] in layers[p + 1] for g in choices(q, canvas[p]))
        }
    return layers


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
        trimmed = kind.startswith("bidir_")
        if trimmed:
            kind = kind.removeprefix("bidir_")
        if kind not in ("raw", "global", "position", "local"):
            raise ValueError("unknown representation")
        self.table, self.canvas, self.kind = table, tuple(canvas), kind
        self.members, self.source_state = {}, {}
        self.position_groups, self.position_of = {}, {}
        self.rows = []
        edges, closes = [], {}
        allowed = coaccessible_layers(table, canvas) if trimmed else None
        layer, vertices = ({OUT: 0} if allowed is None or OUT in allowed[0] else {}), 1

        def edge(a, b, label):
            if len(edges) >= max_edges:
                raise CompilationLimit("DAG edge budget; feasibility unresolved")
            eid = len(edges)
            edges.append(TerminalEdge(eid, a, b, label))
            return eid

        for p, fixed in enumerate(canvas):
            pending, codes = [], set()
            if kind == "position" and fixed is not None:
                self.position_groups[p] = ((table.class_of[fixed],),)
                self.position_of[p] = (0,) * len(table.classes)
                position_members = ((fixed,),)
            elif kind == "position":
                # Competent per-variable quotient: ignore unreachable incoming
                # states, but retain ALL reachable states, not a witness/gold state.
                signatures, groups, mapping = {}, [], []
                for cid in range(len(table.classes)):
                    signature = tuple(
                        gid
                        if (gid := table.class_to_local[q][cid]) >= 0
                        and (allowed is None or table.groups[gid][1] in allowed[p + 1])
                        else -1
                        for q in sorted(layer)
                    )
                    code = signatures.get(signature)
                    if code is None:
                        code = len(groups)
                        signatures[signature] = code
                        groups.append([])
                    groups[code].append(cid)
                    mapping.append(code)
                self.position_groups[p] = tuple(map(tuple, groups))
                self.position_of[p] = tuple(mapping)
                position_members = tuple(
                    tuple(t for cid in group for t in table.classes[cid]) for group in groups
                )
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
                elif kind == "position":
                    candidates = (
                        (code, gid, position_members[code])
                        for code, group in enumerate(self.position_groups[p])
                        if (gid := table.class_to_local[q][group[0]]) >= 0
                    )
                else:
                    candidates = ((gid, gid, table.groups[gid][3]) for gid in table.by_state[q])
                for code, gid, members in candidates:
                    _, target, output, _ = table.groups[gid]
                    if allowed is not None and target not in allowed[p + 1]:
                        continue
                    if fixed is not None:
                        code = (
                            fixed
                            if kind == "raw"
                            else table.class_of[fixed]
                            if kind == "global"
                            else self.position_of[p][table.class_of[fixed]]
                            if kind == "position"
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
