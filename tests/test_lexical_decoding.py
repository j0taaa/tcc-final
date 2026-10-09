"""Offline original-token correctness for the isolated lexical prototype."""

from importlib import import_module

LexicalCorrectness = import_module(
    "attempts.20-lexical-support-quotient.work.test_correctness"
).LexicalCorrectness
