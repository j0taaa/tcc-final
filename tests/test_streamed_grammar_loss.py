"""Exact derivative and full CPU autodiff oracles for isolated A58."""

import importlib

GrammarLossTests = importlib.import_module(
    "attempts.58-streamed-grammar-loss.work.test_reference"
).GrammarLossTests
