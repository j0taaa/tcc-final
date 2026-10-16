"""Classical EOT/PAD language adapter with an exact integer posterior.

The separate termination proof precedes this code. Whitespace-surrogate
probability is used ONLY for an upper tail; never for the shallow valid mass.
"""

from array import array
from time import monotonic
from types import SimpleNamespace

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..stack_control import StackPosterior, StackPrepared
from ..table import LexerTable
from .mosaic_control import sparse_graph


def surrogate_table(emissions, eot, pad):
    ids = {eot, pad}
    if any(type(t) is not int or not 0 <= t < len(emissions) for t in ids):
        raise ValueError("EOT/PAD must be original vocabulary IDs")
    words = tuple(b" " if t in ids else word for t, word in enumerate(emissions))
    table = LexerTable(CompositionalByteLevelAdapter(words))
    # Refine, never merge probabilities or original identities. EOT/PAD must
    # not share an automaton alphabet symbol with ordinary whitespace.
    classes = [tuple(t for t in members if t not in ids) for members in table.classes]
    table.classes = tuple(c for c in classes if c) + tuple((t,) for t in sorted(ids))
    table.class_of = array("i", [-1]) * len(emissions)
    for cid, members in enumerate(table.classes):
        for token in members:
            table.class_of[token] = cid
    table.class_to_local = {
        q: tuple(table.by_token[q][members[0]] for members in table.classes) for q in table.by_state
    }
    table.local_to_class = [[] for _ in table.groups]
    for q in table.by_state:
        for cid, gid in enumerate(table.class_to_local[q]):
            if gid >= 0:
                table.local_to_class[gid].append(cid)
    return table


def terminated_graph(table, canvas, depth, eot, pad, *, symbolic=False, **limits):
    if table.adapter.emissions[eot] != b" " or table.adapter.emissions[pad] != b" ":
        raise ValueError("termination compilation needs its declared surrogate table")
    prepared = StackPrepared(table, canvas, max_depth=depth, **limits)
    raw = sparse_graph(prepared, symbolic=symbolic)
    eot_label = table.class_of[eot] if symbolic else eot
    pad_label = table.class_of[pad] if symbolic else pad
    edges = []
    for u, v, ids in raw["edges"]:
        kept = tuple(t for t in ids if t not in (eot_label, pad_label))
        if kept:
            edges.append((u, v, kept))
    done = raw["num_nodes"]
    edges.extend((u, done, (eot_label,)) for u in raw["accept_states"])
    edges.append((done, done, (pad_label,)))
    outgoing = {u for u, _, _ in edges}
    edges.extend((u, u, ()) for u in range(done) if u not in outgoing)
    return dict(
        raw,
        edges=edges,
        num_nodes=done + 1,
        accept_states=[done],
        eot_id=eot,
        pad_id=pad,
        termination="JSON EOT PAD*; first EOT ends content",
    )


class ClassLookup:
    """Original token -> outgoing edge, without an N by V Python table."""

    def __init__(self, class_of, edge_of):
        self.class_of, self.edge_of = class_of, edge_of

    def __getitem__(self, token):
        return self.edge_of[self.class_of[token]]


def posterior(
    graph,
    table,
    weights,
    *,
    timeout_seconds=120,
    max_cells=10_000_000,
    max_edges=10_000_000,
    max_terms=50_000_000,
):
    """Expose a finite graph as the existing exact StackPosterior DAG interface.

    Compiled graph can be reused for further fixed positions, with unchanged
    original rows/IDs. A released or changed initial fixed ID is rejected.
    """
    if len(weights.canvas) != len(graph["canvas"]) or any(
        t is not None and weights.canvas[p] != t for p, t in enumerate(graph["canvas"])
    ):
        raise ValueError("graph reuse changed the initial fixed original canvas")
    end = monotonic() + timeout_seconds
    n = graph["num_nodes"]
    by_state, members, local_to_class = {u: [] for u in range(n)}, [], []
    class_to_local = {u: [-1] * len(table.classes) for u in range(n)}
    targets = []
    for u, v, ids in graph["edges"]:
        if not ids:
            continue
        cids = tuple(sorted({table.class_of[t] for t in ids}))
        if sum(len(table.classes[c]) for c in cids) != len(ids):
            raise ValueError("finite graph edge splits an original class")
        gid = len(members)
        for cid in cids:
            if class_to_local[u][cid] >= 0:
                raise ValueError("finite graph has multiple paths for an original token")
            class_to_local[u][cid] = gid
        by_state[u].append(gid)
        members.append(ids)
        local_to_class.append(cids)
        targets.append(v)
    finite_table = SimpleNamespace(
        adapter=table.adapter,
        classes=table.classes,
        class_of=table.class_of,
        by_state=by_state,
        local_to_class=local_to_class,
        class_to_local=class_to_local,
        by_token={u: ClassLookup(table.class_of, row) for u, row in class_to_local.items()},
    )
    layers, arcs, used = [((graph["initial_state"], ()),)], [], {}
    cell_count, edge_count = 1, 0
    for p, fixed in enumerate(weights.canvas):
        following, layer_arcs = {}, []
        for u, _ in layers[-1]:
            choices = by_state[u] if fixed is None else (finite_table.by_token[u][fixed],)
            outgoing = []
            for gid in choices:
                if gid < 0:
                    continue
                v = targets[gid]
                b = following.setdefault(v, len(following))
                outgoing.append((b, (gid,)))
                used[p, gid] = members[gid] if fixed is None else (fixed,)
            layer_arcs.append(outgoing)
            edge_count += len(outgoing)
        layers.append(tuple((u, ()) for u in following))
        arcs.append(layer_arcs)
        cell_count += len(following)
        if cell_count > max_cells or edge_count > min(max_edges, max_terms):
            raise CompilationLimit("finite original-token DAG allocation guard")
        if monotonic() >= end:
            raise CompilationLimit("finite original-token DAG deadline")
    accepting = tuple(u in graph["accept_states"] for u, _ in layers[-1])
    live = [set() for _ in layers]
    live[-1] = {u for u, accepted in enumerate(accepting) if accepted}
    for p in reversed(range(len(arcs))):
        live[p] = {
            a for a, outgoing in enumerate(arcs[p]) if any(b in live[p + 1] for b, _ in outgoing)
        }
    live[0].add(0)
    mapping = [{old: new for new, old in enumerate(sorted(layer))} for layer in live]
    trimmed = [
        [
            [(mapping[p + 1][b], gids) for b, gids in arcs[p][a] if b in live[p + 1]]
            for a in sorted(live[p])
        ]
        for p in range(len(arcs))
    ]
    kept = {
        (p, gid)
        for p, layer in enumerate(trimmed)
        for out in layer
        for _, gids in out
        for gid in gids
    }
    prepared = SimpleNamespace(
        table=finite_table,
        canvas=weights.canvas,
        kind="local",
        max_depth=graph["depth"],
        layers=[tuple(layer[a] for a in sorted(live[p])) for p, layer in enumerate(layers)],
        arcs=trimmed,
        accepting=tuple(accepting[a] for a in sorted(live[-1])),
        members={key: ids for key, ids in used.items() if key in kept},
        graph_nodes=cell_count,
        graph_edges=edge_count,
    )
    if monotonic() >= end:
        raise CompilationLimit("finite original-token DAG trim deadline")
    result = StackPosterior(prepared, weights, sums=weights.sums)
    if monotonic() >= end:
        raise CompilationLimit("finite original-token inside deadline")
    return result
