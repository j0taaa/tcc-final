"""Small independent laws through every real worker; do not charge marginals."""

import hashlib
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit

from .analyze import paired
from .measure import WORK, Rejection, worker


class ExactSamplingMeasurement(unittest.TestCase):
    def test_all_thirteen_workers_same_original_mass_and_batch_only_refusal(self):
        protocol = json.loads((WORK / "protocol.json").read_text())
        protocol["batch_size"] = 2
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Independent enumeration: only [] + space (1/4) and [[ ]] (1/8) valid.
            vocabulary = ["[[", "[]", "]]", "]}", "Ġ"]
            np.save(root / "fixture.npy", np.array([[0.5, 0.5, 0, 0, 0], [0, 0, 0.25, 0.25, 0.5]]))
            case = dict(
                case="fixture",
                mask_count=2,
                canvas=[None, None],
                positions=[0, 1],
                probabilities_sha256=hashlib.sha256(
                    (root / "fixture.npy").read_bytes()
                ).hexdigest(),
                forward_and_softmax=dict(wall=0, cpu=0),
            )
            (root / "fixture.json").write_text(json.dumps(case))
            (root / "vocabulary.json").write_text(json.dumps(vocabulary))
            arguments = SimpleNamespace(capture=root, case="fixture", repeat=0)
            for method in protocol["methods"]:
                with self.subTest(method=method):
                    arguments.method = method
                    row = worker(arguments, protocol)
                    self.assertEqual(row["status"], "complete")
                    self.assertEqual(row["first_status"], "complete")
                    self.assertEqual(len(row["samples"]), 2)
                    self.assertTrue(all(tuple(w) in ((0, 2), (1, 4)) for w in row["samples"]))
                    if "valid_mass" in row:
                        self.assertEqual(Fraction(row["valid_mass"]), Fraction(3, 8))
                    self.assertNotIn("outside_and_original_marginals", row)
            original_sample = Rejection.sample

            def interrupted(sampler, rng, *, max_trials):
                if getattr(sampler, "used", False):
                    raise CompilationLimit("batch-only refusal")
                sampler.used = True
                return original_sample(sampler, rng, max_trials=max_trials)

            arguments.method = "rejection"
            with patch.object(Rejection, "sample", interrupted):
                row = worker(arguments, protocol)
            self.assertEqual(row["first_status"], "complete")
            self.assertEqual(row["status"], "resource_refusal")
            row["first_total"] = {"wall": 1, "cpu": 1}
            candidate = dict(
                row,
                first_total={"wall": 1, "cpu": 1},
                batch_total={"wall": 2, "cpu": 2},
                status="complete",
            )
            self.assertFalse(paired([candidate], [row], 1, "first_total", "first_status")["useful"])
            self.assertTrue(paired([candidate], [row], 1, "batch_total", "status")["useful"])
