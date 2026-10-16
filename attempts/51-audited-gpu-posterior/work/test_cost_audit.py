"""Complete/error/favorable cases of the negative-only cost gate."""

import unittest

from .cost_audit import audit


class CostAuditTests(unittest.TestCase):
    def test_unknown_errors_and_partial_rows_do_not_prove_negative(self):
        protocol = dict(
            repetitions=3, primary_gate=dict(minimum_states=3, wall_ratio=0.8, cpu_ratio=0.8)
        )
        cases = ["a", "b", "c"]
        rows = [
            dict(
                case=c,
                rep=r,
                method=m,
                warm=dict(status="complete", correctness=True, projected=dict(wall=v, cpu=v)),
            )
            for c in cases
            for r in range(3)
            for m, v in (("ticket_scalar", 2), ("interval_exact", 1))
        ]
        self.assertTrue(audit(rows, cases, protocol)["negative_gate_proved"])
        with self.assertRaises(ValueError):
            audit(rows[:-1], cases, protocol)
        for row in rows:
            if row["method"] == "interval_exact":
                row["warm"]["status"] = "error"
        self.assertFalse(audit(rows, cases, protocol)["negative_gate_proved"])

    def test_first_stage_cannot_declare_positive_even_with_favorable_pairs(self):
        protocol = dict(
            repetitions=3, primary_gate=dict(minimum_states=3, wall_ratio=0.8, cpu_ratio=0.8)
        )
        cases = ["a", "b", "c"]
        rows = [
            dict(
                case=c,
                rep=r,
                method=m,
                warm=dict(status="complete", correctness=True, projected=dict(wall=v, cpu=v)),
            )
            for c in cases
            for r in range(3)
            for m, v in (("ticket_scalar", 1), ("interval_exact", 2))
        ]
        decision = audit(rows, cases, protocol)
        self.assertFalse(decision["negative_gate_proved"])
        self.assertTrue(decision["remaining_methods_required"])
        self.assertFalse(decision["positive_result_permitted"])
