"""Independent Decimal/dual/absolute-distance and CDF-integral oracles."""

import itertools
import json
import math
import unittest
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

from .reference import meaning, score


class Dual:
    def __init__(self, value, derivative):
        self.value, self.derivative = Fraction(value), tuple(derivative)

    def lift(self, other):
        return (
            other if isinstance(other, Dual) else Dual(other, [Fraction(0)] * len(self.derivative))
        )

    def __add__(self, other):
        other = self.lift(other)
        return Dual(
            self.value + other.value,
            [a + b for a, b in zip(self.derivative, other.derivative, strict=True)],
        )

    __radd__ = __add__

    def __neg__(self):
        return Dual(-self.value, [-x for x in self.derivative])

    def __sub__(self, other):
        return self + (-self.lift(other))

    def __mul__(self, other):
        other = self.lift(other)
        return Dual(
            self.value * other.value,
            [
                a * other.value + self.value * b
                for a, b in zip(self.derivative, other.derivative, strict=True)
            ],
        )

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.lift(other)
        return Dual(
            self.value / other.value,
            [
                (a * other.value - self.value * b) / other.value**2
                for a, b in zip(self.derivative, other.derivative, strict=True)
            ],
        )


def independent_meaning(data):
    try:
        value = json.loads(data.decode("ascii"), parse_int=Decimal, parse_float=Decimal)
        if not isinstance(value, Decimal):
            return None
        value = Fraction(value)
    except (UnicodeError, ValueError):
        return None
    if not value:
        return (0, 0), Fraction(0)
    sign, mantissa, order = (1 if value > 0 else -1), abs(value), 0
    while mantissa < 1:
        mantissa *= 10
        order -= 1
    while mantissa >= 10:
        mantissa /= 10
        order += 1
    return (sign, order), mantissa


def dual_oracle(rows, byte_of, label):
    coordinates = [(i, t) for i, row in enumerate(rows) for t in row]
    variables = {
        coordinate: Dual(
            rows[coordinate[0]][coordinate[1]],
            [
                rows[coordinate[0]][coordinate[1]] if c == coordinate else Fraction(0)
                for c in coordinates
            ],
        )
        for coordinate in coordinates
    }
    zero = Dual(0, [Fraction(0)] * len(coordinates))
    category, target = independent_meaning(label)
    pool = []
    for tape in itertools.product(*rows):
        semantic = independent_meaning(b"".join(byte_of[t] for t in tape))
        if semantic is not None:
            weight = zero.lift(1)
            for i, token in enumerate(tape):
                weight *= variables[i, token]
            pool.append((weight, *semantic))
    total = sum((w for w, _, _ in pool), zero)
    selected = [(w, m) for w, c, m in pool if c == category]
    mass = sum((w for w, _ in selected), zero)
    absolute = sum((w * abs(m - target) for w, m in selected), zero) / mass
    paired = sum((w * v * abs(m - n) for w, m in selected for v, n in selected), zero)
    crps = absolute - paired / (mass * mass * 2) if category != (0, 0) else zero
    gradient = {
        c: total.derivative[i] / total.value
        - mass.derivative[i] / mass.value
        + crps.derivative[i] / 9
        for i, c in enumerate(coordinates)
    }
    return total.value / mass.value, crps.value / 9, gradient


def law(row, byte_of):
    result = defaultdict(Fraction)
    total = sum(row.values(), Fraction(0))
    for token, weight in row.items():
        result[independent_meaning(byte_of[token])] += weight / total
    return dict(result)


def category_masses(distribution):
    result = defaultdict(Fraction)
    for (category, _), weight in distribution.items():
        result[category] += weight
    return result


def cdf_divergence(p, q, category):
    pc, qc = category_masses(p)[category], category_masses(q)[category]
    atoms = {Fraction(1), Fraction(10)} | {m for c, m in p | q if c == category}
    result = Fraction(0)
    for left, right in itertools.pairwise(sorted(atoms)):
        fp = sum((w for (c, m), w in p.items() if c == category and m <= left), Fraction(0)) / pc
        fq = sum((w for (c, m), w in q.items() if c == category and m <= left), Fraction(0)) / qc
        result += (right - left) * (fp - fq) ** 2
    return result


class ScientificScoreTests(unittest.TestCase):
    def test_exact_original_logit_derivatives_and_bounds(self):
        byte_of = {
            1: b"1",
            2: b"10",
            3: b"e0",
            4: b"e-1",
            5: b"",
            6: b"0",
            7: b"-1",
            8: b"2",
            9: b".5",
            10: b".0",
            11: b"invalid",
            12: b"1",
            13: b" ",
            14: b"-0",
        }
        cases = []
        for p, q in itertools.product(
            (Fraction(1, 10), Fraction(1, 3), Fraction(2, 3), Fraction(9, 10)),
            (Fraction(1, 10), Fraction(1, 3), Fraction(2, 3), Fraction(9, 10), Fraction(1, 10**30)),
        ):
            rows = [{1: p, 8: 1 - p}, {3: q, 4: 1 - q}]
            cases.extend((rows, label) for label in (b"1.5", b"0.15"))
        cases.extend(
            [
                (
                    [
                        {1: Fraction(1, 5), 8: Fraction(3, 10), 7: Fraction(1, 2)},
                        {5: Fraction(3, 10), 9: Fraction(7, 10)},
                    ],
                    b"-1.2",
                ),
                (
                    [
                        {13: Fraction(1, 2), 5: Fraction(1, 2)},
                        {1: Fraction(3, 10), 12: Fraction(1, 5), 8: Fraction(1, 2)},
                        {10: Fraction(1, 2), 5: Fraction(3, 10), 11: Fraction(1, 5)},
                    ],
                    b"1.1",
                ),
                (
                    [
                        {14: Fraction(1, 4), 6: Fraction(1, 4), 1: Fraction(1, 2)},
                        {5: Fraction(1, 2), 3: Fraction(1, 2)},
                    ],
                    b"0",
                ),
                ([{1: Fraction(7)}, {5: Fraction(1, 3), 9: Fraction(2, 3)}], b"1.2"),
            ]
        )
        components = traces = 0
        for rows, label in cases:
            actual = score(rows, byte_of, label)
            ratio, offset, gradient = dual_oracle(rows, byte_of, label)
            self.assertEqual((actual["log_ratio"], actual["offset"]), (ratio, offset))
            self.assertEqual(actual["gradient"], gradient)
            for i, row in enumerate(rows):
                values = [gradient[i, token] for token in row]
                self.assertEqual(sum(values), 0)
                self.assertLessEqual(sum(map(abs, values)), 4)
                self.assertTrue(all(abs(v) <= 2 for v in values))
            components += len(gradient)
            traces += actual["valid_traces"]
        print(
            json.dumps(
                {
                    "source_label_cases": len(cases),
                    "exact_logit_components": components,
                    "valid_trace_occurrences": traces,
                    "tiny_category_mass": "1e-30",
                }
            )
        )

    def test_population_identity_and_semantic_strictness(self):
        byte_of = {0: b"0", 1: b"1", 2: b"1.5", 3: b"2", 4: b"-10", 5: b"-15", 6: b"1.0"}
        truth = {
            0: Fraction(1, 6),
            1: Fraction(1, 12),
            2: Fraction(1, 6),
            3: Fraction(1, 6),
            4: Fraction(1, 6),
            5: Fraction(1, 6),
            6: Fraction(1, 12),
        }
        alias = dict(truth, **{})
        alias[1], alias[6] = Fraction(1, 24), Fraction(1, 8)
        predictions = [
            truth,
            alias,
            {i: Fraction(1, 7) for i in byte_of},
            {i: Fraction(i + 1, 28) for i in byte_of},
            {
                0: Fraction(1, 6),
                1: Fraction(1, 8),
                6: Fraction(1, 8),
                2: Fraction(1, 8),
                3: Fraction(1, 8),
                4: Fraction(1, 4),
                5: Fraction(1, 12),
            },
        ]
        q = law(truth, byte_of)
        qc = category_masses(q)
        denominator = math.lcm(*(w.denominator for w in truth.values()))
        for row in predictions:
            p = law(row, byte_of)
            pc = category_masses(p)
            log_product, residual = Fraction(1), Fraction(0)
            for token, weight in truth.items():
                predicted = score([row], byte_of, byte_of[token])
                correct = score([truth], byte_of, byte_of[token])
                log_product *= (predicted["log_ratio"] / correct["log_ratio"]) ** int(
                    weight * denominator
                )
                residual += weight * (predicted["offset"] - correct["offset"])
            kl_product = math.prod((qc[c] / pc[c]) ** int(qc[c] * denominator) for c in qc)
            integral = sum(
                (w * cdf_divergence(p, q, c) / 9 for c, w in qc.items() if c != (0, 0)), Fraction(0)
            )
            self.assertEqual(log_product, kl_product)
            self.assertEqual(residual, integral)
            self.assertGreaterEqual(log_product, 1)
            self.assertGreaterEqual(residual, 0)
            self.assertEqual(log_product == 1 and residual == 0, p == q)
        print(
            json.dumps(
                {
                    "population_laws": len(predictions),
                    "truth_original_ids": len(truth),
                    "exact_log_product_and_cdf_identities": len(predictions),
                }
            )
        )

    def test_decimal_rescaling_and_huge_signed_categories(self):
        original = {0: b"1", 1: b"1.5", 2: b"10", 3: b"0", 4: b"-2"}
        rows = [{i: Fraction(1, 5) for i in original}]
        baseline = score(rows, original, b"1.2")
        for shift in (-(10**20), -2, 0, 3, 10**20):
            suffix = b"e" + str(shift).encode()
            transformed = {i: data + suffix for i, data in original.items()}
            observed = score(rows, transformed, b"1.2" + suffix)
            for key in ("log_ratio", "offset", "gradient"):
                self.assertEqual(observed[key], baseline[key])
        huge = 10**20
        self.assertEqual(meaning(b"0.0001e" + str(huge + 4).encode()), ((1, huge), Fraction(1)))
        self.assertEqual(meaning(b"-1e-" + str(huge).encode()), ((-1, -huge), Fraction(1)))
        self.assertEqual(meaning(b"-0e" + str(huge).encode()), ((0, 0), Fraction(0)))

    def test_alias_example_strong_controls_and_refusals(self):
        byte_of = {0: b"1", 1: b"10", 2: b"e0", 3: b"e-1"}
        rows = [{0: Fraction(1, 2), 1: Fraction(1, 2)}, {2: Fraction(1, 2), 3: Fraction(1, 2)}]
        raw = score(rows, byte_of, b"1")
        self.assertEqual((raw["log_ratio"], raw["offset"]), (2, 0))
        values = (
            (Fraction(1, 10), Fraction(1, 4)),
            (Fraction(1), Fraction(1, 2)),
            (Fraction(10), Fraction(1, 4)),
        )
        ordinary = sum(p * abs(x - 1) for x, p in values) - sum(
            p * q * abs(x - y) / 2 for x, p in values for y, q in values
        )
        self.assertEqual(ordinary, Fraction(99, 160))
        canonical = score([{0: Fraction(1)}, {2: Fraction(1)}], byte_of, b"1")
        self.assertEqual((canonical["log_ratio"], canonical["offset"]), (1, 0))
        # Complete semantic NLL ALREADY gives this example's same log-ratio.
        self.assertEqual(raw["log_ratio"], 1 / sum(p for x, p in values if x == 1))
        aliases = {0: b"1", 1: b"1.0", 2: b"2"}
        a = score([{0: Fraction(1, 5), 1: Fraction(3, 10), 2: Fraction(1, 2)}], aliases, b"1.5")
        b = score([{0: Fraction(1, 10), 1: Fraction(2, 5), 2: Fraction(1, 2)}], aliases, b"1.5")
        self.assertEqual((a["log_ratio"], a["offset"]), (b["log_ratio"], b["offset"]))
        self.assertEqual(
            a["gradient"][0, 0] / Fraction(1, 5), a["gradient"][0, 1] / Fraction(3, 10)
        )
        with self.assertRaisesRegex(ValueError, "EMPTY"):
            score([{}], {}, b"1")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED"):
            score([{0: Fraction(1)}], aliases, b"10")
        with self.assertRaisesRegex(ValueError, "label"):
            score([{0: Fraction(1)}], aliases, b"true")
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            score([{0: Fraction(-1)}], aliases, b"1")


if __name__ == "__main__":
    unittest.main()
