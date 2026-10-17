"""Focused independent arithmetic proof audit for the isolated A56 reference."""

import importlib

StaticRoundingTests = importlib.import_module(
    "attempts.56-static-rounding-sampler.work.test_reference"
).StaticRoundingTests
