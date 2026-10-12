"""Direct integer product recurrence for the written deterministic TV bound."""

from fractions import Fraction
from math import lcm, prod

from . import optimal_planar_fast


def certificate(first, second, epsilon=Fraction(1, 10), max_rows=1_000_000, compressor=None):
    engine = optimal_planar_fast if compressor is None else compressor
    if len(first) != len(second):
        raise ValueError("heads must share all original position domains")
    grid = engine.grid_for(epsilon, max(1, len(first)))
    paired, normalizers = [], [1, 1]
    for p, q in zip(first, second, strict=True):
        if not p or len(p) != len(q):
            raise ValueError("nonempty identical original domains required")
        integers = []
        for row in [p, q]:
            if any(not isinstance(x, (int, Fraction)) or x < 0 for x in row):
                raise ValueError("nonnegative exact rational probabilities required")
            if sum(row) > 1:
                raise ValueError("declared row mass must be at most1")
            row = [Fraction(x) for x in row]
            scale = lcm(*(x.denominator for x in row))
            integers.append([x.numerator * (scale // x.denominator) for x in row])
        for j in [0, 1]:
            normalizers[j] *= sum(integers[j])
        paired.append(list(zip(*integers, strict=True)))
    if 0 in normalizers:
        return dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    core, peak, bits = [(1, 1)], 1, 1
    for row in paired:
        if len(row) * len(core) > max_rows:
            raise RuntimeError("research core budget: no certificate issued")
        images = getattr(engine, "compress_images", None)
        if images is not None:
            peak = max(peak, len(row) * len(core))
            bits = max(
                bits,
                max(
                    (
                        (
                            max((abs(a[j]) for a in row), default=0)
                            * max((abs(a[j]) for a in core), default=0)
                        ).bit_length()
                        for j in [0, 1]
                    ),
                    default=0,
                ),
            )
            core = images(core, row, grid)
        else:
            candidates = [(a * x, b * y) for a, b in row for x, y in core]
            peak = max(peak, len(candidates))
            bits = max(bits, max((abs(x).bit_length() for a in candidates for x in a), default=0))
            core = engine.compress(candidates, grid)
    a, b = normalizers
    lower = Fraction(sum(abs(b * x - a * y) for x, y in core), 2 * prod(normalizers))
    return dict(
        status="CERTIFIED_PRODUCT",
        lower=lower,
        upper=min(Fraction(1), (1 + epsilon) * lower),
        grid=grid,
        root_rows=len(core),
        peak_candidate_rows=peak,
        peak_integer_bits=bits,
    )
