"""Maintained independent exact numeral compiler oracles; no neural capture."""

from importlib import import_module

NumericIntervalTests = import_module(
    "attempts.59-numeric-interval-infilling.work.test_interval"
).NumericIntervalTests
