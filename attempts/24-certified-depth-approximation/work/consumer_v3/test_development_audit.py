"""Independent necessary-condition examples for the first-stage decision."""

import unittest
from copy import deepcopy

from .development_audit import FIRST_METHODS, audit


class DevelopmentAuditTests(unittest.TestCase):
    def fixture(self, rejected_cases):
        cases = [str(i) for i in range(15)]
        protocol = dict(repetitions=3, candidate_family=list(FIRST_METHODS[:2]))
        rows = []
        for i, case in enumerate(cases):
            for repetition in range(3):
                for method in FIRST_METHODS:
                    # Candidates are half as costly in favorable cases; an
                    # independently faster exact control rejects the others.
                    value = (3 if i < rejected_cases else 1) if method in FIRST_METHODS[:2] else 2
                    result = dict(
                        status="complete",
                        correctness_gate=True,
                        projected=dict(wall=value, cpu=value),
                    )
                    rows.append(
                        dict(
                            case=case,
                            repetition=repetition,
                            method=method,
                            cold=deepcopy(result),
                            warm=deepcopy(result),
                        )
                    )
        return cases, protocol, rows

    def test_two_possible_states_prove_negative_but_three_require_full_stage(self):
        cases, protocol, rows = self.fixture(13)
        result = audit(rows, cases, protocol)
        self.assertTrue(result["negative_gate_proved"])
        self.assertEqual(
            {k: len(v) for k, v in result["possible_states"].items()},
            {"handoff_cpu": 2, "closed_cpu": 2},
        )
        cases, protocol, rows = self.fixture(12)
        result = audit(rows, cases, protocol)
        self.assertFalse(result["negative_gate_proved"])
        self.assertTrue(result["remaining_methods_required"])
        self.assertFalse(result["positive_gate_claim"])

    def test_missing_or_invalid_controls_cannot_be_used_as_negative_witnesses(self):
        cases, protocol, rows = self.fixture(15)
        for row in rows:
            if row["method"] in FIRST_METHODS[2:]:
                row["warm"].update(status="resource_refusal", correctness_gate=False)
        result = audit(rows, cases, protocol)
        self.assertFalse(result["negative_gate_proved"])
        with self.assertRaisesRegex(ValueError, "partial FIRST"):
            audit(rows[:-1], cases, protocol)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit([*rows, rows[0]], cases, protocol)
