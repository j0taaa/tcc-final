"""Finite independent rational audits of the written arbitrary-class proof."""

import unittest
from collections import defaultdict
from fractions import Fraction as F
from functools import cache
from itertools import combinations, permutations, product
from math import factorial, prod

if __package__:
    from .couple_six import pair6
else:
    from couple_six import pair6


def elementary(values, order):
    return sum((prod(subset) for subset in combinations(values, order)), F(0))


def compositions(total, length):
    if length == 1:
        yield (total,)
    else:
        for count in range(total + 1):
            for remaining in compositions(total - count, length - 1):
                yield (count, *remaining)


@cache
def profile_joint(counts):
    occupied = [i for i, count in enumerate(counts) if count]
    canonical = tuple(sorted(counts[i] for i in occupied))
    order = sorted(occupied, key=lambda i: counts[i])
    small = canonical_joint(canonical)
    result = [[F(0) for _ in counts] for _ in counts]
    for i, original_i in enumerate(order):
        for j, original_j in enumerate(order):
            result[original_i][original_j] = small[i][j]
    return tuple(tuple(row) for row in result)


@cache
def canonical_joint(counts):
    # Independent original ticket enumeration; no population polynomial.
    b = sum(counts)
    accumulator = [[0 for _ in counts] for _ in counts]
    orders = list(permutations(range(len(counts))))
    for order in orders:
        tickets = [i for i in order for _ in range(2 * counts[i])]
        for offset, i in enumerate(tickets):
            accumulator[i][tickets[(offset + b) % (2 * b)]] += 1
    return tuple(tuple(F(value, 2 * b * len(orders)) for value in row) for row in accumulator)


def family_profile_joint(counts, parameter):
    if sorted(c for c in counts if c) != [1, 1, 2, 2]:
        return profile_joint(counts)
    joint = [[F(0) for _ in counts] for _ in counts]
    for i, count_i in enumerate(counts):
        for j, count_j in enumerate(counts):
            if i == j or not count_i or not count_j:
                continue
            if count_i == count_j == 2:
                joint[i][j] = F(1, 6) + parameter
            elif count_i == count_j == 1:
                joint[i][j] = parameter
            else:
                joint[i][j] = F(1, 12) - parameter / 2
    return joint


def enumerated_joint(p, parameter=F(1, 18)):
    joint = [[F(0) for _ in p] for _ in p]
    for counts in compositions(6, len(p)):
        weight = F(factorial(6), prod(factorial(count) for count in counts))
        weight *= prod(probability**count for probability, count in zip(p, counts, strict=True))
        conditional = family_profile_joint(counts, parameter)
        for i in range(len(p)):
            for j in range(len(p)):
                joint[i][j] += weight * conditional[i][j]
    return joint


def polynomial_joint(p, parameter=F(1, 18)):
    s2, s3, s4 = (sum(x**k for x in p) for k in (2, 3, 4))
    result = [[F(0) for _ in p] for _ in p]
    for i, x in enumerate(p):
        for j, y in enumerate(p):
            if i == j:
                result[i][j] = 5 * x**4 - 6 * x**5 + 2 * x**6
            else:
                base = (
                    1
                    + x
                    + y
                    - s2
                    + 2 * (x**2 + y**2)
                    - s2 * (x + y)
                    - 2 * s3
                    - (x**3 + y**3)
                    - 2 * x * y * (x + y)
                    + s2**2
                    + s2 * x * y
                    + s4
                    + x * y * (x**2 + y**2)
                )
                r1, r2, r3, r4 = (
                    1 - x - y,
                    s2 - x**2 - y**2,
                    s3 - x**3 - y**3,
                    s4 - x**4 - y**4,
                )
                delta = x * y * (r1**2 - r2) + r2**2 - r4 - (x + y) * (r1 * r2 - r3)
                result[i][j] = x * y * (base + (90 * parameter - 3) * delta)
    return result


def square_certificate(p, scores):
    mean = sum(x * value for x, value in zip(p, scores, strict=True))
    f = [value - mean for value in scores]
    if len(p) == 1:
        return F(0), [F(0)]
    z, w, v = (elementary(p, order) for order in (2, 3, 4))
    a = [x * value for x, value in zip(p, f, strict=True)]
    h = sum(x * value for x, value in zip(p, a, strict=True))
    b = [value + h * x / (2 * z) for x, value in zip(p, a, strict=True)]
    weights = [x * (1 - x - z) for x in p]
    total_r = 2 * z + 6 * z**2 + 2 * w + 4 * v
    slack = []
    for i, x in enumerate(p):
        other = [value for j, value in enumerate(p) if j != i]
        u = sum(other)
        zi, wi, vi = (elementary(other, order) for order in (2, 3, 4))
        assert zi**2 - u * wi >= 0
        slack.append(
            2 * (1 + u) * x**2 * u**2
            + 4 * x * u**2 * zi
            + 2 * x * zi**2
            + (6 + 4 * u) * (zi**2 - u * wi)
            + 4 * u * vi
        )
    assert all(weight >= 0 for weight in weights)
    assert all(value > 0 for value in slack)
    assert sum(weights) == z
    result = -sum(s * value**2 for s, value in zip(slack, b, strict=True))
    result -= sum(
        (4 * weights[i] * weights[j] + total_r * p[i] * p[j]) * (b[i] - b[j]) ** 2
        for i, j in combinations(range(len(p)), 2)
    )
    return result, slack


def endpoint_certificate(p, scores, parameter):
    mean = sum(x * value for x, value in zip(p, scores, strict=True))
    if len(p) == 1:
        return F(0)
    z, w, v = (elementary(p, order) for order in (2, 3, 4))
    a = [x * (value - mean) for x, value in zip(p, scores, strict=True)]
    h = sum(x * value for x, value in zip(p, a, strict=True))
    b = [value + h * x / (2 * z) for x, value in zip(p, a, strict=True)]
    ell = [x * (1 - x - z) for x in p]
    lam = 90 * parameter - 3
    rr = 2 * z + 6 * z**2 + 2 * (lam - 1) * w + 4 * (lam - 1) * v
    assert rr > 0
    slack = []
    for i, x in enumerate(p):
        u = 1 - x
        if lam == -3:
            assert 10 * w - 16 * v >= 0 and z <= u
            slack.append(u * (10 * w - 16 * v) + 2 * z * x * (4 * u - 3 * z))
        else:
            assert lam == 3
            other = [value for j, value in enumerate(p) if j != i]
            zi, wi, vi = (elementary(other, order) for order in (2, 3, 4))
            assert zi**2 - F(3, 2) * u * wi >= 0
            slack.append(
                2 * x**2 * u**2
                + (4 + F(16, 3) * u) * (zi**2 - F(3, 2) * u * wi)
                + (8 - F(16, 3) * u) * zi**2
                + 8 * u * vi
            )
    assert all(value > 0 for value in slack)
    result = -sum(s * value**2 for s, value in zip(slack, b, strict=True))
    if lam == -3:
        result -= 6 * sum(weight * value for weight, value in zip(ell, b, strict=True)) ** 2
    else:
        result -= 6 * sum(
            ell[i] * ell[j] * (b[i] - b[j]) ** 2 for i, j in combinations(range(len(p)), 2)
        )
    result -= rr * sum(p[i] * p[j] * (b[i] - b[j]) ** 2 for i, j in combinations(range(len(p)), 2))
    return result


class Choice(Exception):
    def __init__(self, bound):
        self.bound = bound


def execution_law(function):
    pending = [((), F(1))]
    result = defaultdict(F)
    leaves = 0
    while pending:
        tape, probability = pending.pop()
        index = 0

        def randbelow(bound, tape=tape):
            nonlocal index
            if index == len(tape):
                raise Choice(bound)
            value = tape[index]
            index += 1
            assert 0 <= value < bound
            return value

        try:
            output = function(randbelow)
        except Choice as branch:
            pending.extend(
                ((*tape, value), probability / branch.bound) for value in range(branch.bound)
            )
        else:
            result[output] += probability
            leaves += 1
    assert sum(result.values()) == 1
    return result, leaves


class SixSafetyTests(unittest.TestCase):
    def test_proven_family_endpoints_and_preserved_unsafe_control(self):
        checked = 0
        for p in (
            (F(1),),
            (F(1, 5), F(4, 5)),
            (F(1, 10), F(1, 5), F(7, 10)),
            tuple(F(i, 10) for i in range(1, 5)),
            (F(49, 100), F(49, 100), F(1, 150), F(1, 150), F(1, 150)),
            tuple(F(i, 21) for i in range(1, 7)),
            tuple(F(i, 28) for i in range(1, 8)),
        ):
            for parameter in (F(0), F(1, 15)):
                joint = enumerated_joint(p, parameter)
                self.assertEqual(joint, polynomial_joint(p, parameter))
                self.assertEqual([sum(row) for row in joint], list(p))
                for f in product((0, 1), repeat=len(p)):
                    mean = sum(x * value for x, value in zip(p, f, strict=True))
                    direct = (
                        sum(joint[i][j] * f[i] * f[j] for i in range(len(p)) for j in range(len(p)))
                        - mean**2
                    )
                    self.assertEqual(direct, endpoint_certificate(p, f, parameter))
                    self.assertLessEqual(direct, 0)
                    checked += 1
        p = (F(49, 100), F(49, 100), F(1, 150), F(1, 150), F(1, 150))
        unsafe = enumerated_joint(p, F(1, 6))
        covariance = sum(unsafe[i][j] for i in range(2, 5) for j in range(2, 5)) - F(1, 50) ** 2
        self.assertEqual(covariance, F(111816971, 1687500000000))
        self.assertGreater(covariance, 0)
        print(
            "proved-family endpoint exact verifier/square checks:",
            checked,
            "unsafe control retained",
        )

    def test_all_profiles_production_original_index_law(self):
        partitions = [
            r
            for length in range(1, 7)
            for r in compositions(6, length)
            if min(r) > 0 and tuple(sorted(r, reverse=True)) == r
        ]
        self.assertEqual(len(partitions), 11)
        leaves = cases = 0
        for counts in partitions:
            conditional = profile_joint(counts)
            original = [
                (index, label)
                for label, count in enumerate(counts)
                for index in range(sum(counts[:label]), sum(counts[: label + 1]))
            ]
            for first_label in range(len(counts)):
                first = next(item for item in original if item[1] == first_label)
                pool = [first, *(item for item in original if item != first)]

                def execute(rng, pool=pool):
                    source = iter(pool)
                    x, y = pair6(lambda: next(source), lambda value: value[1], rng)
                    self.assertIs(x, pool[0])
                    self.assertIsNot(x, y)
                    self.assertIsNone(next(source, None))
                    return y[0]

                law, count = execution_law(execute)
                leaves += count
                for item in pool[1:]:
                    partner_label = item[1]
                    expected = conditional[first_label][partner_label] / F(counts[first_label], 6)
                    expected /= counts[partner_label] - (first_label == partner_label)
                    self.assertEqual(law[item[0]], expected)
                self.assertEqual(law.get(first[0], 0), 0)
                cases += 1
        print("six-pool production conditional rows:", cases, "integer-tape leaves:", leaves)

    def test_population_joint_and_full_square_certificate(self):
        populations = (
            (F(1),),
            (F(1, 5), F(4, 5)),
            (F(1, 10), F(1, 5), F(7, 10)),
            (F(1, 4),) * 4,
            tuple(F(i, 10) for i in range(1, 5)),
            (F(49, 100), F(49, 100), F(1, 150), F(1, 150), F(1, 150)),
            (F(1, 6),) * 6,
            tuple(F(i, 21) for i in range(1, 7)),
            tuple(F(i, 28) for i in range(1, 8)),
        )
        entries = directions = verifiers = 0
        for p in populations:
            self.assertEqual(sum(p), 1)
            joint = enumerated_joint(p)
            self.assertEqual(joint, polynomial_joint(p))
            self.assertEqual([sum(row) for row in joint], list(p))
            entries += len(p) ** 2
            basis = [tuple(F(i == j) for i in range(len(p))) for j in range(len(p))]
            vectors = [
                *basis,
                *(
                    tuple(x + y for x, y in zip(a, b, strict=True))
                    for a, b in combinations(basis, 2)
                ),
            ]
            for f in vectors:
                mean = sum(x * value for x, value in zip(p, f, strict=True))
                direct = (
                    sum(joint[i][j] * f[i] * f[j] for i in range(len(p)) for j in range(len(p)))
                    - mean**2
                )
                certificate, _ = square_certificate(p, f)
                self.assertEqual(direct, certificate)
                self.assertLessEqual(direct, 0)
                directions += 1
            for event in product((0, 1), repeat=len(p)):
                mass = sum(x * bit for x, bit in zip(p, event, strict=True))
                both = sum(
                    joint[i][j] * event[i] * event[j] for i in range(len(p)) for j in range(len(p))
                )
                self.assertLessEqual(both, mass**2)
                verifiers += 1
        print(
            "six-pool exact population entries:",
            entries,
            "square directions:",
            directions,
            "Boolean verifiers:",
            verifiers,
        )

    def test_elementary_positive_remainder_counting_identity(self):
        checked = 0
        for length in range(1, 9):
            y = tuple(F(i, length + 2) for i in range(1, length + 1))
            u, zi, wi = sum(y), elementary(y, 2), elementary(y, 3)
            expansion = sum(a * a * b * b for a, b in combinations(y, 2))
            expansion += sum(a * b * c * (a + b + c) for a, b, c in combinations(y, 3))
            expansion += 2 * sum(prod(group) for group in combinations(y, 4))
            self.assertEqual(zi**2 - u * wi, expansion)
            self.assertGreaterEqual(expansion, 0)
            checked += 1
        print("positive remainder independent expansions:", checked)

    def test_raw_alias_and_failure_lift_by_all_original_payload_tapes(self):
        probabilities = (F(1, 8), F(3, 8), F(1, 8), F(3, 8))
        labels = (0, 0, 1, 2)  # Two raw aliases and an original failure payload.
        scores = (F(7), F(-2), F(4), F(0))
        raw_joint = [[F(0) for _ in probabilities] for _ in probabilities]
        for tape in product(range(4), repeat=6):
            probability = prod(probabilities[index] for index in tape)
            classes = [labels[index] for index in tape]
            counts = tuple(classes.count(label) for label in range(3))
            first = classes[0]
            row = profile_joint(counts)[first]
            for index in range(1, 6):
                other = classes[index]
                chance = row[other] / F(counts[first], 6)
                chance /= counts[other] - (other == first)
                raw_joint[tape[0]][tape[index]] += probability * chance
        self.assertEqual([sum(row) for row in raw_joint], list(probabilities))
        self.assertEqual([sum(row[j] for row in raw_joint) for j in range(4)], list(probabilities))
        class_p = tuple(
            sum(p for p, c in zip(probabilities, labels, strict=True) if c == label)
            for label in range(3)
        )
        class_f = tuple(
            sum(p * f for p, c, f in zip(probabilities, labels, scores, strict=True) if c == label)
            / class_p[label]
            for label in range(3)
        )
        mean = sum(p * f for p, f in zip(probabilities, scores, strict=True))
        raw_cov = (
            sum(raw_joint[i][j] * scores[i] * scores[j] for i in range(4) for j in range(4))
            - mean**2
        )
        certificate, _ = square_certificate(class_p, class_f)
        self.assertEqual(raw_cov, certificate)
        self.assertLess(raw_cov, 0)
        print("original raw-alias/failure source tapes:", 4**6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
