"""Independent original-word/finite-ticket oracles for the consumer refinement."""

import hashlib
import itertools
import json
import signal
import tempfile
import time
import unittest
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from random import Random
from unittest.mock import patch

import numpy as np

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..table import LexerTable
from .block_stats import Partition
from .compact import CompactOutside, evaluate_compact, load, sample_compact
from .query import (
    BoundaryWeights,
    ConfidenceCursor,
    FullSparseOutside,
    confidence,
    evaluate,
    sample,
)


def fixture(words, head, canvas=None, block=3):
    adapter = CompositionalByteLevelAdapter(tuple(words))
    table = LexerTable(adapter)
    canvas = tuple(canvas) if canvas is not None else (None,) * len(head)
    partition = Partition(tuple(table.class_of), len(table.classes), block)
    weights = BoundaryWeights(table, np.asarray(head, dtype=np.float64), canvas, partition)
    return table, weights, partition


def enumerate_words(table, weights, depth=None):
    """Recognize actual bytes with Python JSON, never the lexer/stack under test."""
    domains = [(t,) if t is not None else range(weights.vocabulary_size) for t in weights.canvas]
    accepted = {}
    for tokens in itertools.product(*domains):
        try:
            text = table.adapter.detokenize_bytes(tokens).decode("utf8")
            obj = json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeDecodeError):
            continue
        if depth is not None:
            # Independent character scanner: nesting INSIDE a string is not depth.
            height, peak, quoted, escaped = 0, 0, False, False
            for char in text:
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        quoted = False
                elif char == '"':
                    quoted = True
                elif char in "[{":
                    height += 1
                    peak = max(peak, height)
                elif char in "]}":
                    height -= 1
            if peak > depth:
                continue
        del obj
        value = F(1)
        for p, t in enumerate(tokens):
            value *= F(weights.at(p, t), weights.denominators[p])
        if value:
            accepted[tokens] = value
    return accepted


class Branch(Exception):
    def __init__(self, size):
        self.size = size


class Tickets:
    def __init__(self, tickets):
        self.tickets, self.position = tickets, 0

    def randrange(self, size):
        if self.position == len(self.tickets):
            raise Branch(size)
        result = self.tickets[self.position]
        self.position += 1
        if not 0 <= result < size:
            raise AssertionError("ticket outside integer branch")
        return result


class QueryConsumerTests(unittest.TestCase):
    def test_neural_service_real_cpu_clock_and_same_word_refinement(self):
        from .neural import Service

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vocabulary = root / "vocabulary.json"
            vocabulary.write_text(json.dumps(["[]", "{}", "[[]]"]))
            head = root / "case.npy"
            np.save(head, np.array([[0.79995, 0.19995, 0.0001]], dtype=np.float64))
            case = head.with_suffix(".json")
            case.write_text(
                json.dumps(
                    dict(
                        canvas=[None],
                        positions=[0],
                        mask_count=1,
                        probabilities_sha256=hashlib.sha256(head.read_bytes()).hexdigest(),
                        forward_and_softmax=dict(wall=0.0, cpu=0.0),
                    )
                )
            )
            signatures = []
            for method in ("handoff_numpy", "handoff_full_sparse"):
                service = Service(method, vocabulary, root / (method + ".stderr"))
                try:
                    before = time.clock_gettime(service.child_clock)
                    result = service.query(dict(case_path=str(case), seed=42))
                    self.assertGreater(time.clock_gettime(service.child_clock), before)
                    self.assertEqual(result["status"], "complete")
                    self.assertEqual(len(result["refinements"]), 1)
                    self.assertFalse(result["decisions"]["0"]["accepted"])
                    signatures.append((result["sample"], result["committed"], result["decisions"]))
                finally:
                    service.close()
            self.assertEqual(signatures[0], signatures[1])

    def test_new_service_cancellation_race_does_not_return_commits(self):
        from . import service

        actual, arrived = signal.setitimer, []

        def late_cancellation(which, seconds):
            value = actual(which, seconds)
            if seconds == 0 and not arrived:
                arrived.append(True)
                raise TimeoutError("late alarm in cancellation")
            return value

        with patch.object(service.signal, "setitimer", late_cancellation):
            result = service.run_timed(lambda: dict(status="complete", committed=[0]), 120)
        self.assertEqual(result["status"], "resource_refusal")
        self.assertNotIn("committed", result)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))

    def test_three_immutable_compact_controls_match_original_word_queries(self):
        table, weights, _ = fixture(
            [b"0", b"0", b" ", b"[", b"]", b"[]"],
            [[1, 2, 1, 1, 1, 1], [2, 1, 1, 1, 1, 1]],
            block=2,
        )
        expected = enumerate_words(table, weights)
        mass = sum(expected.values(), F())
        modules, origin = load()
        self.assertTrue(origin["source_archive_sha256"])
        for method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
            with self.subTest(method=method):
                post, _ = evaluate_compact(table, weights, method, modules=modules)
                self.assertEqual(post.mass, mass)
                query = CompactOutside(post)
                for p in range(len(weights.canvas)):
                    for t in range(weights.vocabulary_size):
                        value = sum((v for w, v in expected.items() if w[p] == t), F()) / mass
                        self.assertEqual(F(query.at(p, t), post.total), value)
                for seed in range(8):
                    weights.consumed = False
                    self.assertIn(sample_compact(post, weights, Random(seed)), expected)

    def test_epsilon_compact_entire_sample_law_after_summary_adaptation(self):
        table, weights, _ = fixture(
            [b"0", b"0", b" ", b"[", b"]", b"[]"],
            [[1, 2, 1, 1, 1, 1], [2, 1, 1, 1, 1, 1]],
            block=2,
        )
        post, _ = evaluate_compact(table, weights, "exact_eps_local")
        expected = enumerate_words(table, weights)
        total = sum(expected.values(), F())
        law, pending = defaultdict(F), [((), F(1))]
        while pending:
            tickets, probability = pending.pop()
            weights.consumed = False
            try:
                word = sample_compact(post, weights, Tickets(tickets))
            except Branch as branch:
                self.assertLessEqual(branch.size, 128)
                pending.extend(
                    ((*tickets, i), probability / branch.size) for i in range(branch.size)
                )
            else:
                law[word] += probability
        self.assertEqual(dict(law), {w: v / total for w, v in expected.items()})

    def test_all_original_marginals_across_aliases_lexical_states_and_depths(self):
        cases = [
            (
                [b"[", b"]", b"0", b"0", b"[]", b"{}", b" ", b"[[]]"],
                [[1, 3, 2, 4, 1, 2, 1, 1], [2, 1, 4, 2, 2, 1, 3, 1]],
                None,
            ),
            (
                [b'"', b"a", "é".encode(), b'\\"', b"[", b" ", b"a"],
                [[1, 2, 3, 1, 1, 2, 4]],
                (0, None, 0),
            ),
            ([b"0", b"1", b"0", b"[]", b"[[]]"], [[1, 2, 3, 1, 1]], None),
        ]
        checks = 0
        for words, head, canvas in cases:
            table, weights, _ = fixture(words, head, canvas)
            for depth in (0, 1, None):
                method = "exact_stack" if depth is None else "closed"
                post, cert = evaluate(
                    table,
                    weights,
                    "999/1000",
                    method=method,
                    depths=(depth,) if depth is not None else (1,),
                )
                # The adaptive operation may increase from a zero-mass depth.
                expected = enumerate_words(table, weights, cert["depth"])
                mass = sum(expected.values(), F())
                self.assertEqual(post.mass, mass)
                if not mass:
                    continue
                sparse = FullSparseOutside(post)
                cursor = ConfidenceCursor(post)
                for p in range(len(weights.canvas)):
                    for t in range(weights.vocabulary_size):
                        value = sum((v for w, v in expected.items() if w[p] == t), F()) / mass
                        self.assertEqual(F(cursor.at(p, t), post.total), value)
                        self.assertEqual(F(sparse.at(p, t), post.total), value)
                        checks += 1
        self.assertGreater(checks, 100)

    def test_entire_joint_sample_law_by_exhaustive_integer_tickets(self):
        table, weights, partition = fixture(
            [b"[", b"]", b"0", b"0", b"[]", b"{}", b" "],
            [[1, 2, 1, 2, 1, 1, 1], [2, 1, 2, 1, 1, 1, 1]],
            block=2,
        )
        post, _ = evaluate(table, weights, "1/1000", method="exact_stack")
        expected = enumerate_words(table, weights)
        total = sum(expected.values(), F())
        law, pending = defaultdict(F), [((), F(1))]
        branches = 0
        while pending:
            tickets, probability = pending.pop()
            weights.consumed = False  # Independent rerun of the complete finite RNG tree.
            try:
                tokens = sample(post, weights, Tickets(tickets))
            except Branch as branch:
                self.assertLessEqual(branch.size, 32)
                pending.extend(
                    ((*tickets, i), probability / branch.size) for i in range(branch.size)
                )
                branches += 1
            else:
                law[tokens] += probability
        self.assertGreater(branches, 5)
        self.assertEqual(dict(law), {w: v / total for w, v in expected.items()})
        self.assertEqual(partition.block_size, 2)

    def test_full_binary64_summary_including_subnormals_and_extremes(self):
        head = [[np.nextafter(0.0, 1.0), 1.0, np.finfo(np.float64).max, 0.0]]
        table, weights, _ = fixture([b"0", b"0", b"1", b"[]"], head, block=2)
        row = list(map(lambda x: F(float(x)), head[0]))
        denominator = sum(row, F())
        for t, value in enumerate(row):
            self.assertEqual(F(weights.at(0, t), weights.denominators[0]), value / denominator)
        for cid, members in enumerate(table.classes):
            self.assertEqual(
                F(weights.sums[0][cid], weights.denominators[0]),
                sum((row[t] for t in members), F()) / denominator,
            )
        for bad in (float("nan"), float("inf"), -1.0):
            with self.assertRaises(ValueError):
                fixture([b"0"], [[bad]])

    def test_commit_early_stop_matches_full_policy_and_preserves_fixed_ids(self):
        table, weights, _ = fixture([b" ", b"0"], [[1, 0]] * 8, (None,) * 8 + (1,))
        post, cert = evaluate(table, weights, "1/1000")
        word = sample(post, weights, Random(19))
        direct = confidence(post, cert, word, outside="cursor")
        sparse = confidence(post, cert, word, outside="full_sparse")
        self.assertEqual(direct, sparse)
        self.assertEqual(direct["committed"], [0, 1, 2, 3])
        self.assertEqual(direct["queries"], 4)
        self.assertEqual(word[-1], 1)
        with self.assertRaises(ValueError):
            sample(post, weights, Random(19))

    def test_threshold_equality_and_refinement_keep_same_sample(self):
        table, weights, _ = fixture([b"[]", b"{}", b"[[]]"], [[0.79995, 0.19995, 0.0001]])
        post, cert = evaluate(table, weights, "1/1000")
        word = (0,)
        before = confidence(post, cert, word)
        self.assertEqual(before["ambiguous"], [0])
        exact, exact_cert = evaluate(table, weights, "1/1000", method="exact_stack")
        after = confidence(exact, exact_cert, word)
        self.assertFalse(after["decisions"][0]["accepted"])
        self.assertEqual(after["committed"], [0])
        table, weights, _ = fixture([b"[]", b"{}"], [[4.0, 1.0]])
        post, cert = evaluate(table, weights, "1/1000", method="exact_stack")
        self.assertTrue(confidence(post, cert, (0,))["decisions"][0]["accepted"])

    def test_cursor_refuses_backward_and_invalid_original_queries(self):
        table, weights, _ = fixture([b" ", b"0"], [[1, 0]], (None, 1))
        post, _ = evaluate(table, weights, "1/1000", method="exact_stack")
        cursor = ConfidenceCursor(post)
        self.assertEqual(cursor.at(1, 1), post.total)
        with self.assertRaises(ValueError):
            cursor.at(0, 0)
        with self.assertRaises(ValueError):
            cursor.at(2, 0)
        with self.assertRaises(ValueError):
            cursor.at(1, 2)


if __name__ == "__main__":
    unittest.main()
