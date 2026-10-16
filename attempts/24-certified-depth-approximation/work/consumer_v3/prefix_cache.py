"""Classical compatible-canvas reweighting of the original A24 prefix bound.

The historical OverflowFrontier contract is unchanged. This adapter explicitly
provides the new singleton canvas and retains the initial language supersets,
as justified BEFORE implementation in consumer-v4-cache-proof.md.
"""

from types import SimpleNamespace

from ..handoff import OverflowFrontier
from ..stack_control import StackPrepared
from .mosaic_control import sparse_graph
from .termination import terminate_graph


class PrefixCache:
    def __init__(self, table, canvas, depth, **limits):
        self.table, self.canvas = table, tuple(canvas)
        self.class_of = tuple(table.class_of)
        self.prepared = StackPrepared(table, canvas, max_depth=depth, track_overflow=True, **limits)

    def terminated_graph(self, eot, pad):
        raw = sparse_graph(self.prepared, symbolic=True)
        return terminate_graph(raw, self.table, eot, pad)

    def frontier(self, weights, **limits):
        if weights.stats.partition.class_of != self.class_of:
            raise ValueError("prefix cache changed original class partition")
        if len(weights.canvas) != len(self.canvas) or any(
            t is not None and weights.canvas[p] != t for p, t in enumerate(self.canvas)
        ):
            raise ValueError("prefix cache changed the initial fixed original canvas")
        # These immutable arrays still describe initial language-only supersets.
        # Only the declared numeric singleton canvas differs for this query.
        state = dict(vars(self.prepared))
        state["canvas"] = weights.canvas
        return OverflowFrontier(SimpleNamespace(**state), weights, sums=weights.sums, **limits)
