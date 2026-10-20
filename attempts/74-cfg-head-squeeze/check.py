"""A74 finite exact-law oracle and minimal count-DP sampler; no timings/GPU."""

from __future__ import annotations

import hashlib
import json
import math
import random
from decimal import Decimal, localcontext
from fractions import Fraction as F
from functools import lru_cache
from itertools import product


def mass(word, rows):
    return math.prod(rows[i][v] for i, v in enumerate(word))


def valid(word, m):
    modes = {v // (2 * m) for v in word}
    return len(modes) == 1 and sum((v // m) % 2 == 0 for v in word) * 2 == len(word)


def table(rows, m):
    """Competent O(n² + nV) suffix-count control, preserving original IDs."""
    n = len(rows)
    charts = []
    for c in range(2):
        dp = [[0] * (n + 1) for _ in range(n + 1)]
        dp[n][0] = 1
        for i in range(n - 1, -1, -1):
            a = sum(rows[i][c * 2 * m : c * 2 * m + m])
            b = sum(rows[i][c * 2 * m + m : (c + 1) * 2 * m])
            for k in range(n - i + 1):
                dp[i][k] = b * dp[i + 1][k] + (a * dp[i + 1][k - 1] if k else 0)
        charts.append(dp)
    return charts, sum(dp[0][n // 2] for dp in charts) if n % 2 == 0 else 0


class Bits:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.bits = 0

    def below(self, bound):
        if bound <= 0:
            raise ValueError("zero mass")
        k = (bound - 1).bit_length()
        while True:
            self.bits += k
            value = self.rng.getrandbits(k)
            if value < bound:
                return value

    def choose(self, weights):
        den = math.lcm(*(F(w).denominator for w in weights))
        integers = [int(w * den) for w in weights]
        u = self.below(sum(integers))
        for i, w in enumerate(integers):
            if u < w:
                return i
            u -= w
        raise AssertionError("unreachable CDF")


def draw(rows, m, charts, rng):
    n = len(rows)
    c = rng.choose([dp[0][n // 2] for dp in charts])
    dp, left, word = charts[c], n // 2, []
    for i in range(n):
        ids = list(range(c * 2 * m, (c + 1) * 2 * m))
        weights = []
        for v in ids:
            next_left = left - int((v // m) % 2 == 0)
            weights.append(rows[i][v] * dp[i + 1][next_left] if next_left >= 0 else 0)
        v = ids[rng.choose(weights)]
        word.append(v)
        left -= int((v // m) % 2 == 0)
    assert left == 0
    return tuple(word)


def squeeze(lower, target, upper, m, rng, cap=4):
    charts, z = table(upper, m)
    if not z:
        raise ValueError("INFEASIBLE_ON_SUPPORT")
    queries = 0
    for j in range(cap):
        word = draw(upper, m, charts, rng)
        u = rng.below(mass(word, upper))
        if u < mass(word, lower):
            return word, queries, j + 1, False
        queries += len(word)
        if u < mass(word, target):
            return word, queries, j + 1, False
    dense, _ = table(target, m)
    return draw(target, m, dense, rng), queries, cap, True


def derivations(word, c):
    """Independent span parser of the written S/T/U grammar, counting trees."""

    @lru_cache(None)
    def parse(symbol, lo, hi):
        if lo == hi:
            return 1
        result = 0
        for first in (0, 1) if symbol == "S" else ((0,) if symbol == "T" else (1,)):
            if word[lo] != 2 * c + first:
                continue
            middle = "T" if first == 0 else "U"
            tail = symbol if symbol != "S" else "S"
            for split in range(lo + 1, hi):
                if word[split] == 2 * c + 1 - first:
                    result += parse(middle, lo + 1, split) * parse(tail, split + 1, hi)
        return result

    return parse("S", 0, len(word))


def finite_laws():
    laws = 0
    maximum_r = F(0)
    for cells in product(tuple(product((0, 1), (1, 2, 3))), repeat=4):
        lower = [[cells[2 * i + v][0] for v in range(2)] for i in range(2)]
        target = [[cells[2 * i + v][1] for v in range(2)] for i in range(2)]
        upper = [[3, 3], [3, 3]]
        words = ((0, 1), (1, 0))
        zw = sum(mass(x, target) for x in words)
        zl = sum(mass(x, lower) for x in words)
        zu = sum(mass(x, upper) for x in words)
        hits = {x: 0 for x in words}
        queries = 0
        for x in words:
            for u in range(9):
                if u < mass(x, lower):
                    hits[x] += 1
                else:
                    queries += 1
                    if u < mass(x, target):
                        hits[x] += 1
        p, q = F(sum(hits.values()), zu), F(queries, zu)
        assert p == F(zw, zu) and q == 1 - F(zl, zu)
        for x in words:
            accepted = F(hits[x], zu)
            assert accepted / p == F(mass(x, target), zw)
            for cap in (0, 1, 2, 4):
                output = sum((1 - p) ** j * accepted for j in range(cap))
                output += (1 - p) ** cap * F(mass(x, target), zw)
                assert output == F(mass(x, target), zw)
        assert q / p == F(zu - zl, zw)
        if zl:
            r = F(zu, zl)
            maximum_r = max(maximum_r, r)
            assert 1 / p <= r and q / p <= r - 1
        laws += 1
    # Explicit censorship counterexample from proof.md.
    assert (F(1, 2), F(1, 2)) != (F(1, 3), F(2, 3))
    return {"complete_laws": laws, "largest_finite_R": str(maximum_r)}


def grammar_and_dp():
    strings = 0
    for n in (2, 4, 6):
        accepted = 0
        for word in product(range(4), repeat=n):
            count = sum(derivations(word, c) for c in range(2))
            assert count == int(valid(word, 1))
            accepted += count
            strings += 1
        assert accepted == 2 * math.comb(n, n // 2)
    alias_words = [x for x in product(range(8), repeat=4) if valid(x, 2)]
    assert len(alias_words) == 2 * math.comb(4, 2) * 2**4
    source, rng = random.Random(740201), Bits(740202)
    cases, draws, fallback, queries, peak_bits = 0, [], 0, 0, 0
    for n, m in product((2, 4, 6), (1, 2)):
        words = [x for x in product(range(4 * m), repeat=n) if valid(x, m)]
        for _ in range(8):
            w = [[source.randrange(1, 10) for _ in range(4 * m)] for _ in range(n)]
            lower = [[v // 2 for v in row] for row in w]
            upper = [[v + 1 for v in row] for row in w]
            for rows in (lower, w, upper):
                charts, z = table(rows, m)
                assert z == sum(mass(x, rows) for x in words)
                peak_bits = max(
                    peak_bits, *(int(v).bit_length() for d in charts for r in d for v in r)
                )
            for _ in range(16):
                x, q, _, f = squeeze(lower, w, upper, m, rng)
                assert valid(x, m)
                draws.append(x)
                queries += q
                fallback += f
            cases += 1
    # Fixed positions restrict rows, retaining the original IDs.
    rows = [[1] * 8 for _ in range(4)]
    rows[0] = [0, 1, 0, 0, 0, 0, 0, 0]
    _, z = table(rows, 2)
    assert z == sum(mass(x, rows) for x in alias_words)
    empty = [[1, 0, 0, 0], [1, 0, 0, 0]]
    assert table(empty, 1)[1] == 0
    try:
        squeeze(empty, empty, empty, 1, rng)
    except ValueError as exc:
        assert str(exc) == "INFEASIBLE_ON_SUPPORT"
    else:
        raise AssertionError("zero mass accepted")
    return {
        "grammar_strings": strings,
        "alias_strings": 8**4,
        "alias_valid": len(alias_words),
        "weighted_cases": cases,
        "valid_samples": len(draws),
        "fallback_samples": fallback,
        "reference_rows": queries,
        "rng_bits": rng.bits,
        "peak_chart_integer_bits": peak_bits,
        "samples_sha256": hashlib.sha256(json.dumps(draws).encode()).hexdigest(),
    }


def polynomial(t, k):
    out = F(1, math.factorial(k))
    for j in range(k - 1, -1, -1):
        out = out * t + F(1, math.factorial(j))
    return out


def kernel(t, b):
    value = polynomial(t, b + 4) * 2**b
    return F(value.numerator // value.denominator, 2**b)


def analytic_examples():
    kernel_points = 0
    with localcontext() as context:
        context.prec = 90
        for b in (8, 12, 16):
            previous = F(0)
            for k in range(-64, 65):
                t = F(k, 64)
                value = kernel(t, b)
                assert value >= previous and value > 0
                ideal = (Decimal(t.numerator) / Decimal(t.denominator)).exp()
                relative = abs(Decimal(value.numerator) / Decimal(value.denominator) / ideal - 1)
                assert relative < Decimal(4) / Decimal(2**b)
                previous = value
                kernel_points += 1
    for n, delta in product((2, 4, 8), (F(1, 8), F(1, 4))):
        b = (int(40 * n / delta) - 1).bit_length()
        for j in range(-8, 9):
            q, eps = F(j, 16 * n), delta / n
            for residual in (-eps, F(0), eps):
                assert kernel(q - eps, b) <= kernel(q + residual, b) <= kernel(q + eps, b)
    examples = []
    for n, r in product((2, 4, 8), (1, 2, 3)):
        ratio = F(r) ** (2 * n)
        tv = (ratio - 1) / (ratio + 1)
        query = 1 - 1 / ratio
        assert tv <= query <= 2 * tv
        examples.append({"n": n, "r": r, "R": str(ratio), "TV": str(tv), "query": str(query)})
    for n in (2, 4, 8):
        r = F(2, 1 + F(1, 2) ** n)
        assert r < 2 and r < 2**n
    lo, up = [[1, 2], [3, 1]], [[2, 3], [5, 4]]
    words = ((0, 1), (1, 0))
    ratio = F(sum(mass(x, up) for x in words), sum(mass(x, lo) for x in words))
    gauge = (F(2, 3), F(7, 4))
    gauged = [[[v * gauge[i] for v in row] for i, row in enumerate(rows)] for rows in (lo, up)]
    assert ratio == sum(mass(x, gauged[1]) for x in words) / sum(mass(x, gauged[0]) for x in words)
    return {"kernel_grid_points_decimal_crosscheck": kernel_points, "oracle_lower_bound": examples}


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "status": "PASS",
                "scope": "finite_oracle_not_neural_measurement",
                **finite_laws(),
                **grammar_and_dp(),
                **analytic_examples(),
            },
            indent=2,
        )
    )
