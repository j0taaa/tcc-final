"""Flushed NVML observations with irreversible foreign-PID/error refusal latch."""

import csv
import io
import json
import os
import subprocess
import threading
import time

from .consumer_resource import ResourceRefusal


def nvml_rows():
    return subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=timestamp,pid,process_name,used_memory",
            "--format=csv,noheader",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout


class CaptureOccupancy:
    def __init__(self, path, reader=nvml_rows, pid=None):
        self.reader, self.pid = reader, os.getpid() if pid is None else pid
        self.stream = path.open("x", buffering=1)
        self.lock, self.poll_lock = threading.Lock(), threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.failures = []
        self.observations = 0

    def poll(self):
        with self.poll_lock:
            observation = {"utc_seconds": time.time(), "own_pid": self.pid}
            try:
                raw = self.reader()
                rows = list(csv.reader(io.StringIO(raw), skipinitialspace=True))
                pids = [int(row[1]) for row in rows if row]
                observation.update({"raw": raw, "pids": pids})
                foreign = sorted(set(pids) - {self.pid})
                if foreign:
                    observation["foreign_pids"] = foreign
            except Exception as error:
                observation["query_error"] = repr(error)
            with self.lock:
                if "foreign_pids" in observation or "query_error" in observation:
                    self.failures.append(observation)
                self.observations += 1
                self.stream.write(json.dumps(observation) + "\n")

    def check(self):
        self.poll()
        with self.lock:
            if self.failures:
                raise ResourceRefusal(f"whole-capture GPU isolation invalid: {self.failures[0]}")

    def start(self):
        self.check()

        def watch():
            while not self.stop.wait(1):
                self.poll()

        self.thread = threading.Thread(target=watch, daemon=True)
        self.thread.start()

    def report(self):
        with self.lock:
            return {
                "whole_capture_isolation_satisfied": not self.failures,
                "occupancy_observations": self.observations,
                "occupancy_failures": list(self.failures),
                "capture_pid": self.pid,
                "polling_scope": "one-second sampled observations, not continuous exclusion",
            }

    def close(self):
        self.stop.set()
        if self.thread is not None:
            self.thread.join(6)
            if self.thread.is_alive():
                raise ResourceRefusal("NVML observer did not stop within its bounded query time")
        self.stream.close()
