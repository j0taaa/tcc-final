"""Gate regressions: missing controls and one unfavorable repeat receive no win."""

import unittest

from .resource_analysis_v7 import analyze, cell


def rows(method, wall, peak, n=16):
    return [
        {
            "kind": "warm",
            "N": n,
            "method": method,
            "rep": rep,
            "status": "COMPLETE",
            "wall_ns": v,
            "workspace_bytes": peak,
        }
        for rep, v in enumerate(wall)
    ]


class ResourceGateTests(unittest.TestCase):
    def test_missing_control_never_awards_positive_and_cannot_hide_known_loss(self):
        data = rows("candidate", [79, 79, 79], 100) + rows("observed", [100, 100, 100], 100)
        self.assertFalse(cell(data, 16, "candidate", ["observed", "missing"])["win"])
        self.assertTrue(cell(data, 16, "candidate", ["observed", "missing"])["possible"])
        losing = rows("candidate", [200, 200, 200], 100) + rows("observed", [100, 100, 100], 100)
        self.assertFalse(cell(losing, 16, "candidate", ["observed", "missing"])["possible"])

    def test_paired_sign_and_memory_alternative(self):
        data = rows("candidate", [60, 79, 101], 100) + rows("control", [100, 100, 100], 100)
        self.assertFalse(cell(data, 16, "candidate", ["control"])["win"])
        data = rows("candidate", [105, 105, 105], 50) + rows("control", [100, 100, 100], 100)
        self.assertTrue(cell(data, 16, "candidate", ["control"])["memory"])
        self.assertFalse(cell(data, 16, "candidate", ["control"])["speed"])

    def test_negative_shortcut_counts_unknown_states_optimistically(self):
        data = []
        for n in range(6):
            data += rows("candidate", [200, 200, 200], 100, n) + rows(
                "control", [100, 100, 100], 100, n
            )
        report = analyze(data, list(range(8)), ["candidate"], ["control", "unmeasured"])
        self.assertEqual(report["possible"]["candidate"], 2)
        self.assertTrue(report["negative_shortcut"])
        self.assertFalse(report["gate"])


if __name__ == "__main__":
    unittest.main()
