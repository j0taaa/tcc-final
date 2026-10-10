"""A26: exact small laws and every verifier, without a favorable benchmark."""

import importlib
import itertools
import json
import unittest
from collections import Counter
from fractions import Fraction as F
from random import Random

from test_cfg_posterior import inputs, oracle

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.reference.json_grammar import json_source_grammar

batch = importlib.import_module("attempts.26-stratified-decoder-batches.work.batch")
ranks = importlib.import_module("attempts.26-stratified-decoder-batches.work.ranks")


class NeedDraw(Exception):
    def __init__(self, stop):
        self.stop = stop


class ExactRandom(Random):
    """Independently enumerate RNG transcripts, including label permutations."""

    def __init__(self, transcript):
        super().__init__(0)
        self.transcript = iter(transcript)

    def randrange(self, stop):
        if stop == 1:
            return 0
        try:
            value = next(self.transcript)
        except StopIteration:
            raise NeedDraw(stop) from None
        if not 0 <= value < stop:
            raise AssertionError("test transcript outside requested range")
        return value

    def shuffle(self, values):
        for j in reversed(range(1, len(values))):
            i = self.randrange(j + 1)
            values[i], values[j] = values[j], values[i]


def enumerate_law(draw):
    pending, law = [((), F(1))], Counter()
    while pending:
        transcript, probability = pending.pop()
        try:
            value = draw(ExactRandom(transcript))
        except NeedDraw as error:
            pending.extend(((*transcript, r), probability / error.stop) for r in range(error.stop))
        else:
            law[value] += probability
    if sum(law.values()) != 1:
        raise AssertionError("enumerated law lost probability")
    return dict(law)


def marginal(law, label):
    result = Counter()
    for outcome, probability in law.items():
        result[outcome[label]] += probability
    return dict(result)


def covariance(law, support):
    size = len(next(iter(law)))
    mean = [F() for _ in support]
    second = [[F() for _ in support] for _ in support]
    for outcome, probability in law.items():
        counts = [F(outcome.count(x), size) for x in support]
        for i, x in enumerate(counts):
            mean[i] += probability * x
            for j, y in enumerate(counts):
                second[i][j] += probability * x * y
    return [[second[i][j] - mean[i] * mean[j] for j in range(len(mean))] for i in range(len(mean))]


def determinant(matrix):
    matrix = [row[:] for row in matrix]
    value = F(1)
    for i in range(len(matrix)):
        pivot = next((j for j in range(i, len(matrix)) if matrix[j][i]), None)
        if pivot is None:
            return F()
        if pivot != i:
            matrix[i], matrix[pivot] = matrix[pivot], matrix[i]
            value = -value
        value *= matrix[i][i]
        for j in range(i + 1, len(matrix)):
            factor = matrix[j][i] / matrix[i][i]
            for k in range(i + 1, len(matrix)):
                matrix[j][k] -= factor * matrix[i][k]
    return value


class StratifiedBatchTests(unittest.TestCase):
    def assert_dominance(self, stratified, iid):
        size = len(next(iter(iid)))
        support = sorted({x for outcome in iid for x in outcome})
        for label in range(size):
            self.assertEqual(marginal(stratified, label), marginal(iid, label))
        # Every binary verifier, including empty/universal/disconnected sets.
        for bits in itertools.product((False, True), repeat=len(support)):
            accepted = {x for x, bit in zip(support, bits, strict=True) if bit}

            def hit(law, accepted=accepted):
                return sum(p for output, p in law.items() if any(x in accepted for x in output))

            self.assertGreaterEqual(hit(stratified), hit(iid))
        # PSD covariance difference proves the small-case variance inequality
        # for ALL real scores, not just sampled or handpicked score vectors.
        left, right = covariance(iid, support), covariance(stratified, support)
        difference = [
            [a - b for a, b in zip(x, y, strict=True)] for x, y in zip(left, right, strict=True)
        ]
        for n in range(1, len(support) + 1):
            for subset in itertools.combinations(range(len(support)), n):
                self.assertGreaterEqual(
                    determinant([[difference[i][j] for j in subset] for i in subset]), 0
                )

    def test_all_small_ticket_maps_and_nondivisible_masses(self):
        for total in range(1, 5):
            for size in range(1, 4):
                # All surjective/non-surjective two-output deterministic maps.
                for mapping in itertools.product(range(2), repeat=total):
                    kernel = batch.Kernel(total, mapping.__getitem__)
                    left = enumerate_law(
                        lambda rng, kernel=kernel, size=size: batch.draw_batch(kernel, size, rng)
                    )
                    right = enumerate_law(
                        lambda rng, kernel=kernel, size=size: batch.draw_batch(
                            kernel, size, rng, stratified=False
                        )
                    )
                    self.assert_dominance(left, right)

    def test_arbitrary_future_kernels_and_every_terminal_verifier(self):
        roots = ((0,), (0, 1), (0, 0, 1), (0, 1, 1))
        futures = ((0, 1), (0, 0, 1), (0, 1, 1))

        def stop(h):
            return len(h) == 2

        for root, first, second in itertools.product(roots, futures, futures):

            def prepare(history, root=root, first=first, second=second):
                values = root if not history else (first if history[0] == 0 else second)
                return batch.Kernel(len(values), values.__getitem__)

            left = enumerate_law(lambda rng: batch.decode_batch(prepare, stop, 2, 2, rng)[0])
            right = enumerate_law(
                lambda rng: batch.decode_batch(prepare, stop, 2, 2, rng, stratified=False)[0]
            )
            self.assert_dominance(left, right)

    def test_cfg_unranking_against_independent_json_and_original_ids(self):
        emissions = (b"[", b"0", b"1", b",", b"]", b"0", b" ", b"[]", b"[0]", b"[0")
        cases = (
            (((0,), (1, 2, 5), (3,), (1, 2), (4,)), (0, None, 3, None, 4)),
            (((7, 8, 9), (4, 6)), (None, None)),
            (((0,), (0, 1, 2), (1, 4), (4,)), (0, None, None, 4)),
        )

        def valid(word):
            try:
                json.loads(word.decode("utf8"))
                return True
            except (ValueError, UnicodeError):
                return False

        source = json_source_grammar()
        for rows, canvas in cases:
            probabilities = tuple(
                tuple(F(j + 1, sum(range(1, len(row) + 1))) for j in range(len(row)))
                for row in rows
            )
            data = inputs(source, emissions, rows, probabilities, canvas)
            expected_mass, _, law = oracle(data, valid)
            posterior = compile_cfg_sampler(source, data.state).evaluate(data)
            self.assertEqual(posterior.valid_mass, expected_mass)
            adapter = ranks.CfgRanks(posterior)
            counts = Counter(adapter.unrank(i) for i in range(adapter.total))
            self.assertEqual({x: F(n, adapter.total) for x, n in counts.items()}, law)
            words = tuple(adapter.unrank(i) for i in range(adapter.total))
            for p, row in enumerate(data.state.support.rows):
                for token in row:
                    expected = [0]
                    for word in words:
                        expected.append(expected[-1] + (word[p] == token))
                    self.assertEqual(
                        adapter.evidence_prefix({p: {token}}, range(adapter.total + 1)),
                        tuple(expected),
                    )
            for word in counts:
                expected = [0]
                for candidate in words:
                    expected.append(expected[-1] + (candidate == word))
                constraints = {p: {t} for p, t in enumerate(word)}
                self.assertEqual(
                    adapter.evidence_prefix(constraints, range(adapter.total + 1)), tuple(expected)
                )
            # Check actual integer calls of batch sampling, not only a formula.
            if adapter.total <= 30:
                left = enumerate_law(
                    lambda rng, adapter=adapter: batch.draw_batch(adapter.kernel, 2, rng)
                )
                right = enumerate_law(
                    lambda rng, adapter=adapter: batch.draw_batch(
                        adapter.kernel, 2, rng, stratified=False
                    )
                )
                self.assert_dominance(left, right)
            for invalid in (-1, adapter.total, 1.0, True):
                with self.assertRaises(ValueError):
                    adapter.unrank(invalid)

    def test_strict_gain_and_negative_controls(self):
        kernel = batch.Kernel(2, lambda x: x)
        left = enumerate_law(lambda rng: batch.draw_batch(kernel, 2, rng))
        right = enumerate_law(lambda rng: batch.draw_batch(kernel, 2, rng, stratified=False))
        self.assertEqual(sum(p for out, p in left.items() if 1 in out), 1)
        self.assertEqual(sum(p for out, p in right.items() if 1 in out), F(3, 4))
        # Systematic arithmetic phase and per-coordinate coupling can BOTH
        # worsen an arbitrary verifier. They are not our admissible algorithm.
        systematic = [((phase, (phase + 2) % 4), F(1, 4)) for phase in range(4)]
        self.assertEqual(sum(p for out, p in systematic if any(x in (0, 2) for x in out)), F(1, 2))
        self.assertLess(F(1, 2), F(3, 4))
        parity_batches = (((0, 0), (1, 1)), ((0, 1), (1, 0)))
        self.assertEqual(
            sum(F(1, 2) for out in parity_batches if any(x == y for x, y in out)), F(1, 2)
        )

    def test_boundaries_and_no_history_merging(self):
        calls = []

        def prepare(history):
            calls.append(history)
            return batch.Kernel(
                2 if not history else 1, (lambda x: x) if not history else (lambda _: 9)
            )

        histories, complete = batch.decode_batch(prepare, lambda h: len(h) == 3, 2, 3, Random(1))
        self.assertTrue(all(complete))
        self.assertNotEqual(histories[0][0], histories[1][0])
        self.assertEqual(set(calls), {(), (0,), (1,), (0, 9), (1, 9)})
        truncated, flags = batch.decode_batch(prepare, lambda h: len(h) == 3, 2, 0, Random(1))
        self.assertEqual(truncated, ((), ()))
        self.assertEqual(flags, (False, False))
        for total in (0, -1, 1.0, True):
            with self.assertRaises(ValueError):
                batch.draw_batch(batch.Kernel(total, lambda x: x), 2, Random(1))
        with self.assertRaises(ValueError):
            batch.draw_batch(batch.Kernel(1, lambda x: x), 0, Random(1))
        with self.assertRaises(TypeError):
            batch.draw_batch(batch.Kernel(1, lambda x: x), 1, None)
