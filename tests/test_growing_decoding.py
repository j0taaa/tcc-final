"""Only the new finite-product adaptive-domain oracles; no model/SAT needed."""

from importlib import import_module

GrowingCorrectness = import_module(
    "attempts.19-growing-support-decoding.work.test_correctness"
).GrowingCorrectness
