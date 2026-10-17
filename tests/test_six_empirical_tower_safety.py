"""Independent rational six-pool laws and square certificate; no model imports."""

from importlib import import_module

SixTowerTests = import_module(
    "attempts.45-random-order-empirical-towers.work.test_six_safety"
).SixSafetyTests
