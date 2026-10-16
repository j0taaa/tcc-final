"""Regression for V8's foreign process during CPU preparation; no GPU query."""

import json
import tempfile
import unittest
from pathlib import Path

from .capture_occupancy_v10 import CaptureOccupancy
from .consumer_resource import ResourceRefusal


class CaptureOccupancyTests(unittest.TestCase):
    def test_foreign_cpu_preparation_observation_stays_invalid_after_clear(self):
        rows = iter(("", "2026/10/16 16:00:00.000, 23, fake-model, 2 MiB\n", ""))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "observations.jsonl"
            monitor = CaptureOccupancy(path, lambda: next(rows), pid=11)
            try:
                monitor.check()
                with self.assertRaises(ResourceRefusal):
                    monitor.check()
                with self.assertRaises(ResourceRefusal):
                    monitor.check()
                self.assertFalse(monitor.report()["whole_capture_isolation_satisfied"])
                # Each observation is visible BEFORE close, unlike buffered NVML -l/-f.
                observations = [json.loads(s) for s in path.read_text().splitlines()]
                self.assertEqual(len(observations), 3)
                self.assertEqual(observations[1]["foreign_pids"], [23])
            finally:
                monitor.close()

    def test_own_pid_allowed_query_error_refuses_and_is_preserved(self):
        def broken():
            raise TimeoutError("fake bounded NVML timeout")

        with tempfile.TemporaryDirectory() as folder:
            monitor = CaptureOccupancy(
                Path(folder) / "own.jsonl",
                lambda: "2026/10/16 16:00:00.000, 11, own-model, 5 MiB\n",
                pid=11,
            )
            try:
                monitor.check()
                self.assertTrue(monitor.report()["whole_capture_isolation_satisfied"])
                monitor.reader = broken
                with self.assertRaises(ResourceRefusal):
                    monitor.check()
                self.assertIn(
                    "TimeoutError", monitor.report()["occupancy_failures"][0]["query_error"]
                )
            finally:
                monitor.close()


if __name__ == "__main__":
    unittest.main()
