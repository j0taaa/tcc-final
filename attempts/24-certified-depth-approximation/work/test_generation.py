"""Independent JSON and threshold checks across actual CPU-service boundaries."""

import hashlib
import json
import signal
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import generation_service
from .generation import Service
from .generation_service import classify, timed_query


class CertifiedGeneration(unittest.TestCase):
    def test_deadline_during_cancellation_cannot_commit_progress(self):
        actual_timer, arrived = signal.setitimer, []

        def cancellation_race(which, seconds):
            previous = actual_timer(which, seconds)
            if seconds == 0 and not arrived:
                arrived.append(True)
                raise TimeoutError("alarm arrived while cancelling")
            return previous

        with (
            patch.object(generation_service.signal, "setitimer", cancellation_race),
            patch.object(
                generation_service,
                "query",
                return_value=dict(status="complete", sample=[0], committed=[0]),
            ),
        ):
            result = timed_query({}, {}, None, None)
        self.assertEqual(result["status"], "resource_refusal")
        self.assertNotIn("committed", result)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))

    def test_threshold_equality_refinement_and_both_real_services(self):
        decisions, ambiguous = classify((0,), (None,), ((4, 1),), 5, 0, Fraction(4, 5))
        self.assertTrue(decisions[0]["accepted"])
        self.assertEqual(ambiguous, [])
        decisions, ambiguous = classify((0,), (None,), ((4, 1),), 5, 1, Fraction(4, 5))
        self.assertIsNone(decisions[0]["accepted"])
        self.assertEqual(ambiguous, [0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vocabulary = root / "vocabulary.json"
            vocabulary.write_text(json.dumps(["[]", "{}", "[[]]"]))
            probabilities = root / "head.npy"
            np.save(probabilities, np.array([[0.79995, 0.19995, 0.0001]]))
            for method in ("handoff", "exact_stack"):
                with self.subTest(method=method):
                    service = Service(method, vocabulary, root / (method + ".stderr"))
                    refined = False
                    try:
                        for seed in range(4):
                            response = service.query(
                                dict(
                                    probabilities=str(probabilities),
                                    positions=[0],
                                    canvas=[None],
                                    probabilities_sha256=hashlib.sha256(
                                        probabilities.read_bytes()
                                    ).hexdigest(),
                                    initial_masks=1,
                                    seed=seed,
                                )
                            )
                            self.assertEqual(response["status"], "complete")
                            token = response["sample"][0]
                            # All three tokens are valid; FULL conditional=the
                            # normalized model row. Every value is below4/5.
                            self.assertIsInstance(
                                json.loads(["[]", "{}", "[[]]"][token]), (list, dict)
                            )
                            self.assertFalse(response["decisions"]["0"]["accepted"])
                            self.assertEqual(response["committed"], [0])
                            self.assertLessEqual(
                                Fraction(response["sample_certificate"]["delta"]), Fraction(1, 1000)
                            )
                            refined |= bool(response["refinements"])
                    finally:
                        service.close()
                    self.assertEqual(refined, method == "handoff")
