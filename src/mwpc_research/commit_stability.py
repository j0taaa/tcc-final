"""Exhaustive research reference for commitment stability, not a production decoder.

The optimizer's complete selected set is retained. A separate gate commits only
matches shared by every completion within ``tolerance`` of the current optimum.
This is score stability on an explicit path catalog, not semantic confidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import fsum, isfinite

from mwpc_research.tool_screen import CatalogSelection, select_catalog


@dataclass(frozen=True)
class PositionStability:
    position: int
    alternative_objective: float | None
    margin: float | None
    forced_on_support: bool


@dataclass(frozen=True)
class StableCatalogCommit:
    optimizer: CatalogSelection
    stability: tuple[PositionStability, ...]
    certified_positions: tuple[int, ...]
    committed_positions: tuple[int, ...]
    progress_fallback: bool
    exactness_scope: str = "exact_on_support: supplied finite token paths"


def stable_catalog_commit(
    paths: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    proposals: Sequence[tuple[int, int, float]],
    *,
    tolerance: float,
) -> StableCatalogCommit:
    """Gate an exact optimum by counterfactual score loss.

    ``margin > tolerance`` is strict: alternatives at the boundary belong to the
    near-optimal set. No alternative means structurally forced, represented by
    an explicit flag rather than a non-finite JSON number. A progress fallback
    is returned separately and has no stability guarantee. Enumeration is only
    a small-instance oracle; its timing cannot stand for CFG parser timing.
    """
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")
    optimum = select_catalog(paths, canvas, proposals, method="exact")
    if not isfinite(optimum.objective):
        raise ValueError("objective overflow")
    feasible = [
        path
        for path in paths
        if all(fixed is None or fixed == path[p] for p, fixed in enumerate(canvas))
    ]
    scores = [fsum(w for p, token, w in proposals if path[p] == token) for path in feasible]
    stability = []
    certified = []
    for position in optimum.selected_positions:
        alternatives = [
            score
            for path, score in zip(feasible, scores, strict=True)
            if path[position] != optimum.witness_token_ids[position]
        ]
        alternative = max(alternatives) if alternatives else None
        margin = None if alternative is None else optimum.objective - alternative
        stability.append(PositionStability(position, alternative, margin, alternative is None))
        if alternative is None or (margin is not None and margin > tolerance):
            certified.append(position)
    commits = tuple(certified)
    fallback = False
    if not commits and any(token is None for token in canvas):
        fallback = True
        # Prefer a matched proposal by original weight, then stable position.
        matched = set(optimum.selected_positions)
        available = [(w, -p, p) for p, _, w in proposals if p in matched]
        position = (
            max(available)[2]
            if available
            else next(p for p, token in enumerate(canvas) if token is None)
        )
        commits = (position,)
    return StableCatalogCommit(optimum, tuple(stability), tuple(certified), commits, fallback)
