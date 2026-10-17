"""Execute TWO unchanged original vLLM functions with finite packet stubs."""

import ast
import hashlib
import math
import threading
import time
from fractions import Fraction
from pathlib import Path

SOURCE = (
    Path(__file__).parent
    / "native_source_v1/examples/features/structured_diffusion/structured_server.py"
)
EXPECTED = "9d085496ccaeec833ddf4ffe4b89212512121a6790f5844891b389cbeb02d36e"


class NativeReplay:
    def __init__(self):
        data = SOURCE.read_bytes()
        if hashlib.sha256(data).hexdigest() != EXPECTED:
            raise ValueError("Native source changed")
        tree = ast.parse(data)
        selected = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in {"decide_group", "read_many"}
        ]
        if len(selected) != 2:
            raise ValueError("Missing original function")
        self.code = compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec")
        self.runs = self.packet_calls = 0

    def run(self, packets, cap, threshold=0.1, fail_seed=None):
        questions = len(packets[0])
        seeds = [17] + [18 + 7919 * k for k in range(cap - 1)]
        lookup = dict(zip(seeds, packets, strict=True))
        calls = []

        def one_read(schema, template, slots, system, state, seed, prefix, thinking):
            calls.append(seed)
            if seed == fail_seed:
                raise RuntimeError("Declared packet failure")
            result = []
            for yes in lookup[seed]:
                probs = [float(yes), float(1 - yes)]
                result.append(
                    {
                        "probs": probs,
                        "entropy": -sum(p * math.log(p) for p in probs if p > 0),
                        "label_mass": 1.0,
                        "argmax_is_label": True,
                    }
                )
            return result, {"prompt_tokens": 1}

        namespace = {
            "time": time,
            "threading": threading,
            "SCAFFOLD": [],
            "one_read": one_read,
            "template_for": lambda *args: ([0] * questions, [{"pos": j} for j in range(questions)]),
        }
        exec(self.code, namespace)
        schema = {
            "questions": [
                {
                    "id": str(j),
                    "type": "noul",
                    "labels": ["yes", "no"],
                    "choices": [("yes", None), ("no", None)],
                }
                for j in range(questions)
            ],
            "think": 0,
            "steps": 1,
            "policy": {"mode": "auto", "max": cap, "threshold": threshold},
        }
        self.runs += 1
        try:
            result, _ = namespace["decide_group"](schema, "", "", 17)
        finally:
            self.packet_calls += len(calls)
        output = tuple(
            Fraction(result["answers"][str(j)]["probabilities"][label])
            for j in range(questions)
            for label in ("yes", "no")
        )
        n = result["diagnostics"]["samples"]["n"]
        if sorted(calls) != sorted(seeds[:n]) or len(calls) != n:
            raise AssertionError("Native request/seed accounting changed")
        return output, n, tuple(sorted(calls))
