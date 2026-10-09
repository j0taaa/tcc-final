"""Offline original-token oracles for contextual overlapping groups."""

from importlib import import_module

LexicalCorrectness = import_module(
    "attempts.21-contextual-token-groups.work.test_correctness"
).LexicalCorrectness
