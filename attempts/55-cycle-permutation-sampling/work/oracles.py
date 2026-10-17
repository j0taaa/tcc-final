"""Independent finite law/cost oracles; no neural weights, timing or MC claim."""

from __future__ import annotations

import itertools as it
import math
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F

if __package__:
    from .cycle_sampler import ewens_links, from_auxiliary_size, prepare, sample
else:
    from cycle_sampler import ewens_links, from_auxiliary_size, prepare, sample


def sign(permutation):
    return (-1) ** sum(a > b for i, a in enumerate(permutation) for b in permutation[i + 1 :])


def permanent(matrix):
    return sum(
        math.prod(matrix[i][p[i]] for i in range(len(matrix)))
        for p in it.permutations(range(len(matrix)))
    )


def determinant(matrix):
    return sum(
        sign(p) * math.prod(matrix[i][p[i]] for i in range(len(matrix)))
        for p in it.permutations(range(len(matrix)))
    )


def det_polynomial(ratios):
    """Leibniz expansion of det(I-zR), independent of sampling construction."""
    n = len(ratios)
    coefficients = [F(0)] * (n + 1)
    for p in it.permutations(range(n)):
        degree = sum(i != p[i] for i in range(n))
        weight = math.prod(-ratios[i][p[i]] for i in range(n) if i != p[i])
        coefficients[degree] += sign(p) * weight
    return coefficients


def cycles(permutation):
    unseen = set(range(len(permutation)))
    result = []
    while unseen:
        root = min(unseen)
        cycle = []
        node = root
        while node in unseen:
            unseen.remove(node)
            cycle.append(node)
            node = permutation[node]
        result.append(tuple(cycle))
    return result


class NeedChoice(Exception):
    def __init__(self, bound):
        self.bound = bound


def execution_law(function):
    """Explore ALL adaptive uniform-integer tapes, with exact branch weights."""
    stack = [((), F(1))]
    outcomes = defaultdict(F)
    leaves = 0
    while stack:
        tape, weight = stack.pop()
        cursor = 0

        def choice(bound, tape=tape):
            nonlocal cursor
            if cursor == len(tape):
                raise NeedChoice(bound)
            value = tape[cursor]
            cursor += 1
            assert 0 <= value < bound
            return value

        try:
            output = function(choice)
        except NeedChoice as request:
            stack.extend(((*tape, v), weight / request.bound) for v in range(request.bound))
        else:
            outcomes[output] += weight
            leaves += 1
    assert sum(outcomes.values()) == 1
    return dict(outcomes), leaves


def inverse(matrix):
    n = len(matrix)
    augmented = [list(row) + [F(i == j) for j in range(n)] for i, row in enumerate(matrix)]
    for i in range(n):
        pivot = next(j for j in range(i, n) if augmented[j][i])
        augmented[i], augmented[pivot] = augmented[pivot], augmented[i]
        scale = augmented[i][i]
        augmented[i] = [x / scale for x in augmented[i]]
        for j in range(n):
            if i != j:
                scale = augmented[j][i]
                augmented[j] = [
                    x - scale * y for x, y in zip(augmented[j], augmented[i], strict=True)
                ]
    return [row[n:] for row in augmented]


class CycleOracles(unittest.TestCase):
    def test_classical_ordered_loop_control_has_same_full_accepted_law(self):
        # Enumerate every compatible ordered growing-loop tuple. Their prefix
        # masses integrate ALL unbounded discarded tails via independently
        # solved Green matrices; they are not capped walk probabilities.
        checked = 0
        for n in range(1, 6):
            ratios = [
                [F(0) if i == j else F(1 + (i + 2 * j) % 3, 7 * n) for j in range(n)]
                for i in range(n)
            ]
            factors = []
            for v in range(n):
                remaining = range(v, n)
                green = inverse([[F(i == j) - ratios[i][j] for j in remaining] for i in remaining])
                factors.append(1 / green[0][0])
            minus = [[F(i == j) - ratios[i][j] for j in range(n)] for i in range(n)]
            plus = [[F(i == j) + ratios[i][j] for j in range(n)] for i in range(n)]
            self.assertEqual(math.prod(factors), determinant(minus))
            law = defaultdict(F)

            def visit(
                v, occupied, assignment, weight, n=n, law=law, factors=factors, ratios=ratios
            ):
                if v == n:
                    law[tuple(assignment)] += weight
                    return
                # An occupied FUTURE vertex still contributes its empty-prefix
                # normalizer. Skipping it would yield the wrong distribution.
                visit(v + 1, occupied, assignment, weight * factors[v])
                if v in occupied:
                    return
                available = [j for j in range(v + 1, n) if j not in occupied]
                for count in range(1, len(available) + 1):
                    for tail in it.permutations(available, count):
                        cycle = (v, *tail)
                        next_assignment = assignment.copy()
                        cycle_weight = F(1)
                        for i, j in zip(cycle, (*tail, v), strict=True):
                            next_assignment[i] = j
                            cycle_weight *= ratios[i][j]
                        visit(
                            v + 1,
                            occupied.union(cycle),
                            next_assignment,
                            weight * factors[v] * cycle_weight,
                        )

            visit(0, set(), list(range(n)), F(1))
            for permutation in it.permutations(range(n)):
                expected = determinant(minus) * math.prod(plus[i][permutation[i]] for i in range(n))
                self.assertEqual(law[permutation], expected)
                checked += 1
            self.assertEqual(sum(law.values()), determinant(minus) * permanent(plus))
        print("classical ordered-loop accepted assignment masses:", checked)

    def test_classical_accepted_cycle_law(self):
        # Explicit compatible SIMPLE-cycle sets, not permutation enumeration.
        checked = 0
        for n in range(1, 6):
            ratios = [
                [F(0) if i == j else F(1 + (i + j) % 2, 4 * n) for j in range(n)] for i in range(n)
            ]
            elementary = []
            for k in range(2, n + 1):
                for subset in it.combinations(range(n), k):
                    for tail in it.permutations(subset[1:]):
                        cycle = (subset[0], *tail)
                        weight = math.prod(
                            ratios[i][j] for i, j in zip(cycle, cycle[1:] + cycle[:1], strict=True)
                        )
                        elementary.append((cycle, weight))
            result = defaultdict(F)

            def extend(start, used, permutation, weight, result=result, elementary=elementary):
                result[tuple(permutation)] += weight
                for index in range(start, len(elementary)):
                    cycle, value = elementary[index]
                    if used.isdisjoint(cycle):
                        following = permutation.copy()
                        for i, j in zip(cycle, cycle[1:] + cycle[:1], strict=True):
                            following[i] = j
                        extend(index + 1, used.union(cycle), following, weight * value)

            extend(0, set(), list(range(n)), F(1))
            matrix = [[F(i == j) + ratios[i][j] for j in range(n)] for i in range(n)]
            normalizer = permanent(matrix)
            det = determinant([[F(i == j) - ratios[i][j] for j in range(n)] for i in range(n)])
            self.assertEqual(sum(result.values()), normalizer)
            for permutation in it.permutations(range(n)):
                expected = math.prod(matrix[i][permutation[i]] for i in range(n))
                self.assertEqual(result[permutation], expected)
                checked += 1
            self.assertGreater(det * normalizer, 0)
            self.assertLessEqual(det * normalizer, 1)
        print("cycle-set/permutation exact assignments:", checked)

    def test_ewens_full_adaptive_integer_law(self):
        leaves = 0
        for n in (1, 2, 3):
            for m in range(5):
                law, count = execution_law(lambda rng, n=n, m=m: tuple(ewens_links(n, m, rng)))
                leaves += count
                denominator = math.prod(range(n, n + m))
                for permutation in it.permutations(range(m)):
                    self.assertEqual(
                        law[permutation], F(n ** len(cycles(permutation)), denominator)
                    )
        print("Ewens integer-tape leaves:", leaves)

    def test_marked_soup_joint_coefficients(self):
        # An independent determinant generating function checks every accepted
        # output of the ACTUAL bounded-M implementation, including unused walks.
        cases = (
            [[1, F(1, 3)], [F(1, 3), 1]],
            [[1, F(1, 4)], [F(1, 8), 1]],
            [[1, F(1, 6), F(1, 6)], [F(1, 6), 1, F(1, 6)], [F(1, 6), F(1, 6), 1]],
        )
        leaves = 0
        checked = 0
        for matrix in cases:
            prepared = prepare(matrix)
            n, r = prepared.n, prepared.r
            dpoly = det_polynomial(prepared.ratios)
            for m in range(4):
                law, count = execution_law(
                    lambda rng, p=prepared, m=m: from_auxiliary_size(p, m, rng)
                )
                leaves += count
                nb_weight = F(math.comb(n + m - 1, m)) * r**m
                expected_total = F(0)
                for permutation in it.permutations(range(n)):
                    degree = sum(i != permutation[i] for i in range(n))
                    weight = math.prod(
                        prepared.ratios[i][permutation[i]] for i in range(n) if i != permutation[i]
                    )
                    coefficient = (
                        sum(
                            dpoly[j]
                            * math.comb(n + m - degree - j - 1, m - degree - j)
                            * r ** (m - degree - j)
                            for j in range(min(n, m - degree) + 1)
                        )
                        if degree <= m
                        else F(0)
                    )
                    expected = weight * coefficient / nb_weight
                    self.assertEqual(law.get(permutation, 0), expected)
                    expected_total += expected
                    checked += 1
                self.assertEqual(law.get(None, 0), 1 - expected_total)
        print("marked-soup finite integer tapes:", leaves, "output coefficients:", checked)

    def test_geometric_mixture_cycle_coefficients(self):
        # Ewens/negative-binomial factorization, ALL partitions through size8.
        checked = 0
        for n, r in ((1, F(1, 3)), (3, F(2, 5)), (5, F(3, 4))):
            for m in range(9):
                for counts in it.product(*(range(m // k + 1) for k in range(1, m + 1))):
                    if sum(k * c for k, c in enumerate(counts, 1)) != m:
                        continue
                    denominator = math.prod(
                        k**c * math.factorial(c) for k, c in enumerate(counts, 1)
                    )
                    ewens = F(
                        math.factorial(m) * n ** sum(counts),
                        math.prod(range(n, n + m)) * denominator,
                    )
                    nb = F(math.comb(n + m - 1, m)) * (1 - r) ** n * r**m
                    poisson = (1 - r) ** n * math.prod(
                        (n * r**k / k) ** c / math.factorial(c) for k, c in enumerate(counts, 1)
                    )
                    self.assertEqual(nb * ewens, poisson)
                    checked += 1
        print("NB/Ewens cycle-count coefficients:", checked)

    def test_return_occupation_certificate(self):
        checked = 0
        for n in range(2, 6):
            for denominator in (2, 3, 5):
                ratios = [
                    [
                        F(0) if i == j else F(1 + ((2 * i + j) % 3), denominator * 4 * n)
                        for j in range(n)
                    ]
                    for i in range(n)
                ]
                minus = [[F(i == j) - ratios[i][j] for j in range(n)] for i in range(n)]
                plus = [[F(i == j) + ratios[i][j] for j in range(n)] for i in range(n)]
                green = inverse(minus)
                acceptance = determinant(minus) * permanent(plus)
                bound = sum((1 - 1 / green[i][i]) ** 2 for i in range(n))
                prepared = prepare(plus)
                self.assertGreaterEqual(acceptance, 1 - bound)
                self.assertLessEqual(bound, prepared.cheap_failure_bound())
                # Independent one-site determinant-ratio pgf coefficients.
                for i in range(n):
                    other = [[minus[j][k] for k in range(n) if k != i] for j in range(n) if j != i]
                    hit = 1 - determinant(minus) / determinant(other)
                    self.assertEqual(hit, 1 - 1 / green[i][i])
                    checked += 1
        print("exact return/minor/certificate checks:", checked)

    def test_input_and_identifier_invariance(self):
        matrix = [[F(1, 5), 2, F(1, 9)], [3, F(1, 7), F(1, 8)], [F(1, 6), F(1, 7), 4]]
        prepared = prepare(matrix)
        self.assertEqual(prepared.base, (1, 0, 2))
        norm = permanent(matrix)
        for permutation in it.permutations(range(3)):
            original = tuple(prepared.base[j] for j in permutation)
            weight = math.prod(
                (F(i == permutation[i]) + prepared.ratios[i][permutation[i]]) for i in range(3)
            )
            normalized = weight / permanent(
                [[F(i == j) + prepared.ratios[i][j] for j in range(3)] for i in range(3)]
            )
            self.assertEqual(normalized, math.prod(matrix[i][original[i]] for i in range(3)) / norm)
        rng = random.Random(55001)
        for _ in range(32):
            self.assertEqual(set(sample(prepared, rng.randrange)), set(range(3)))
        self.assertEqual(
            sample(prepare([[1, 0], [0, 1]]), lambda _: self.fail("identity must not draw")), (0, 1)
        )
        for invalid in ([], [[0]], [[1, 1], [1, 1]], [[1, 2], [1, 2]], [[1, -1], [0, 1]]):
            with self.assertRaises(ValueError):
                prepare(invalid)

    def test_unfavorable_local_cycles_and_cap_bias(self):
        r = F(1, 2)
        for pairs in range(1, 4):
            n = 2 * pairs
            ratios = [
                [r if i // 2 == j // 2 and i != j else F(0) for j in range(n)] for i in range(n)
            ]
            minus = [[F(i == j) - ratios[i][j] for j in range(n)] for i in range(n)]
            plus = [[F(i == j) + ratios[i][j] for j in range(n)] for i in range(n)]
            self.assertEqual(determinant(minus) * permanent(plus), (1 - r**4) ** pairs)
        # Conditioning a cap M=0 or1 keeps ONLY the identity, whereas the
        # unlimited 2x2 target has strictly positive swap mass r²/(1+r²).
        prepared = prepare([[1, r], [r, 1]])
        for m in (0, 1):
            law, _ = execution_law(lambda rng, m=m: from_auxiliary_size(prepared, m, rng))
            self.assertEqual(law, {(0, 1): F(1)})
        self.assertEqual(r**2 / (1 + r**2), F(1, 5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
