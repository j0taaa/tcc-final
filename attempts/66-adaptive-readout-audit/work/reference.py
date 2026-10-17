"""Classical stopped-packet conditioning; a rational audit reference only."""

from fractions import Fraction


def aggregate_auto(values, eligible, cap):
    """Keep the original global stopping rule; return an exact point, no stderr."""
    if not isinstance(cap, int) or cap < 1 or not values or len(values) != len(eligible):
        raise ValueError("Invalid stopped sample")
    expected = cap if eligible[0] else 1
    if len(values) != expected or not values[0]:
        raise ValueError("Packets do not match the original stopping rule")
    width = len(values[0])
    if any(len(row) != width for row in values):
        raise ValueError("Inconsistent probability-vector width")
    selected = [0] if len(values) == 1 else [i for i, high in enumerate(eligible) if high]
    return tuple(
        sum((Fraction(values[i][j]) for i in selected), Fraction()) / len(selected)
        for j in range(width)
    )
