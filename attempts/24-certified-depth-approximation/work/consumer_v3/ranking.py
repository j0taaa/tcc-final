"""Certify the common full-posterior top-k commit map (classical intervals)."""

from fractions import Fraction
from math import prod

from ..consumer_v2.query import ConfidenceCursor


def ranked_commits(posterior, word, upper_mass, count):
    weights = posterior.weights
    if len(word) != len(weights.canvas) or any(
        t is not None and word[p] != t for p, t in enumerate(weights.canvas)
    ):
        raise ValueError("ranking word changed original fixed canvas")
    if type(count) is not int or not 1 <= count <= len(weights.free):
        raise ValueError("commit count outside currently free slots")
    upper = Fraction(upper_mass) * prod(weights.denominators)
    if upper < 0 or upper.denominator != 1:
        raise ValueError("tail bound must have the original exact row units")
    cursor = ConfidenceCursor(posterior)
    values = {p: cursor.at(p, word[p]) for p in weights.free}
    selected = tuple(sorted(sorted(values, key=lambda p: (-values[p], p))[:count]))
    unselected = set(values) - set(selected)
    comparisons = [
        (p, q)
        for p in selected
        for q in unselected
        if values[p] < values[q] + upper or (values[p] == values[q] + upper and p > q)
    ]
    return dict(
        selected=None if comparisons else selected,
        proposed=selected,
        ambiguous_comparisons=comparisons,
        numerators=values,
        denominator=posterior.total + upper.numerator,
        upper_units=upper.numerator,
        queries=cursor.queries,
        tie_rule="larger exact confidence, then smaller physical index",
    )
