"""Original-ID and actual random-law oracles for exact envelope sampling."""

from importlib import import_module

ExactEnvelopeCorrectness = import_module(
    "attempts.25-exact-envelope-sampling.work.test_correctness"
).ExactEnvelopeCorrectness
