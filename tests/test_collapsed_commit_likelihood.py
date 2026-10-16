"""Independent rational laws; no optional neural/GPU package imported."""

from importlib import import_module

CollapsedActionTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_reference"
).CollapsedActionTests

SmoothActionTests = import_module(
    "attempts.52-collapsed-commit-likelihood.work.test_smooth"
).SmoothActionTests
