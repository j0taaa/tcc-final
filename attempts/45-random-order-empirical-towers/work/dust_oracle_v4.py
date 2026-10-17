"""Exact obstruction audit; constructed mathematics, no model or timing data."""

import json
from collections import Counter
from fractions import Fraction as F
from functools import cache
from itertools import permutations, product
from math import factorial, prod


def moments(p):
    s2, s3, s4 = (sum(x**k for x in p) for k in (2, 3, 4))
    return (1 - s2) / 2, (1 - 3 * s2 + 2 * s3) / 6, (1 - 6 * s2 + 3 * s2**2 + 8 * s3 - 6 * s4) / 24


def completed(p, b, lam):
    z, w, v = moments(p)
    c0 = (6 + 2 * lam) * z**2 - (2 + 4 * lam) * w + 4 * (lam - 1) * v
    rr = 2 * z + 6 * z**2 + 2 * (lam - 1) * w + 4 * (lam - 1) * v
    diagonal = [c0 + (2 * (2 - lam) * z + 6 * lam * w) * x + 2 * (lam - 1) * z * x**2 for x in p]
    ell = [x * (1 - x - z) for x in p]
    return (
        -sum(d * value**2 for d, value in zip(diagonal, b, strict=True))
        + 2 * lam * sum(x * value for x, value in zip(ell, b, strict=True)) ** 2
        + rr * sum(x * value for x, value in zip(p, b, strict=True)) ** 2
    )


def partitions(total, least=1):
    if total == 0:
        yield ()
    for first in range(least, total + 1):
        for rest in partitions(total - first, first):
            yield (first, *rest)


@cache
def occupied_profile_joint(counts, parameter):
    """All occupied labels and all12 tickets, not a population polynomial."""
    assert sum(counts) == 6 and min(counts) > 0
    if sorted(counts) == [1, 1, 2, 2]:
        return tuple(
            tuple(
                F(0)
                if i == j
                else F(1, 6) + parameter
                if x == y == 2
                else parameter
                if x == y == 1
                else F(1, 12) - parameter / 2
                for j, y in enumerate(counts)
            )
            for i, x in enumerate(counts)
        )
    result = [[0 for _ in counts] for _ in counts]
    for order in permutations(range(len(counts))):
        tape = [i for i in order for _ in range(2 * counts[i])]
        for index, i in enumerate(tape):
            result[i][tape[(index + 6) % 12]] += 1
    denominator = 12 * factorial(len(counts))
    return tuple(tuple(F(x, denominator) for x in row) for row in result)


def occupancy_macro_joint(first, second, rare, count, parameter):
    """Exact grouping of every six-draw tape on count+2 ORIGINAL classes."""
    assert first + second + count * rare == 1
    result = [[F(0) for _ in range(3)] for _ in range(3)]
    profiles = 0
    source_mass = F(0)
    for r1 in range(7):
        for r2 in range(7 - r1):
            remaining = 6 - r1 - r2
            for part in partitions(remaining):
                if len(part) > count:
                    continue
                groups = ([0] if r1 else []) + ([1] if r2 else []) + [2] * len(part)
                sizes = ([r1] if r1 else []) + ([r2] if r2 else []) + list(part)
                falling = prod(range(count - len(part) + 1, count + 1))
                labels = F(falling, prod(factorial(x) for x in Counter(part).values()))
                tapes = F(factorial(6), factorial(r1) * factorial(r2))
                tapes /= prod(factorial(x) for x in part)
                mass = labels * tapes * first**r1 * second**r2 * rare**remaining
                source_mass += mass
                law = occupied_profile_joint(tuple(sizes), parameter)
                assert all(sum(row) == F(n, 6) for row, n in zip(law, sizes, strict=True))
                assert all(x >= 0 for row in law for x in row)
                for i, group_i in enumerate(groups):
                    for j, group_j in enumerate(groups):
                        result[group_i][group_j] += mass * law[i][j]
                profiles += 1
    assert source_mass == 1
    assert [sum(row) for row in result] == [first, second, count * rare]
    assert all(result[i][j] == result[j][i] for i, j in product(range(3), repeat=2))
    return result, profiles


def main():
    binary_checks = 0
    for x, lam, b in product(
        (F(1, 100), F(1, 5), F(1, 2), F(4, 5), F(99, 100)),
        (F(-3), F(2), F(3), F(9, 2), F(5), F(12)),
        ((F(1), F(0)), (F(1), F(1)), (F(7, 16), F(9, 16))),
    ):
        y = 1 - x
        s, d, m, z = b[0] + b[1], b[0] - b[1], x - y, x * y
        direct = z**2 * (
            (lam - 5) * s**2 / 2 + (3 - lam) * m * s * d + ((lam + 3) * m**2 / 2 - 6) * d**2
        )
        assert completed((x, y), b, lam) == direct
        aa, cc, off = (lam - 5) / 2, (lam + 3) * m**2 / 2 - 6, (3 - lam) * m / 2
        assert aa * cc - off**2 == (lam - 6) * m**2 + 15 - 3 * lam
        binary_checks += 1
    assert completed((F(4, 5), F(1, 5)), (F(7, 16), F(9, 16)), F(5)) == F(63, 31250)

    # Deterministic mathematical fixture, selected before its first computation.
    # This is a finite obstruction, not a favorable application benchmark.
    epsilon, count = F(1, 4096), 1024
    p = [(1 - epsilon) * F(4, 5), (1 - epsilon) * F(1, 5)] + [epsilon / count] * count
    b = [F(7, 16), F(9, 16)]
    residual = sum((1 - x) * value for x, value in zip(p[:2], b, strict=True))
    b += [-residual / (count * (1 - epsilon / count))] * count
    assert sum((1 - x) * value for x, value in zip(p, b, strict=True)) == 0
    qq = sum(x * value for x, value in zip(p, b, strict=True))
    f = [value / x - qq for x, value in zip(p, b, strict=True)]
    assert sum(x * value for x, value in zip(p, f, strict=True)) == 0
    assert len(set(f)) == 3
    z, _, _ = moments(p)
    h = sum(x**2 * value for x, value in zip(p, f, strict=True))
    assert [x * value + h * x / (2 * z) for x, value in zip(p, f, strict=True)] == b
    joint, profiles = occupancy_macro_joint(p[0], p[1], p[2], count, F(4, 45))
    score = f[:3]
    covariance = sum(joint[i][j] * score[i] * score[j] for i, j in product(range(3), repeat=2))
    assert covariance == completed(p, b, F(5))
    assert covariance > 0
    # Literal Boolean verifier on extra source payload bits; class-only
    # selection preserves independent residuals, as already checked in V3.
    lower, width = min(score), max(score) - min(score)
    success = [(value - lower) / width for value in score]
    macro_p = (p[0], p[1], epsilon)
    mean = sum(x * value for x, value in zip(macro_p, success, strict=True))
    hit_both = sum(joint[i][j] * success[i] * success[j] for i, j in product(range(3), repeat=2))
    verifier_cov = hit_both - mean**2
    assert verifier_cov == covariance / width**2 > 0
    print(
        json.dumps(
            {
                "status": "PASS_EXACT_FINITE_OBSTRUCTION",
                "binary_identities": binary_checks,
                "original_classes": len(p),
                "epsilon": str(epsilon),
                "rare_classes": count,
                "parameter": "4/45",
                "lambda": "5",
                "source_occupancy_profiles": profiles,
                "macro_joint": [[str(x) for x in row] for row in joint],
                "centered_score": list(map(str, score)),
                "covariance": str(covariance),
                "verifier_success_probabilities": list(map(str, success)),
                "verifier_covariance": str(verifier_cov),
                "pass2_candidate": str(2 * mean - hit_both),
                "pass2_iid": str(2 * mean - mean**2),
                "scope": "mathematical family obstruction, not A45 tower/model/latency failure",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
