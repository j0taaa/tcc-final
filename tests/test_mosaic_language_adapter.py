"""Offline original-byte language check; no Mosaic/Torch dependency in CI."""

from importlib import import_module

GraphLanguageTests = import_module(
    "attempts.24-certified-depth-approximation.work.consumer_v3.test_graph"
).GraphLanguageTests

TerminationTests = import_module(
    "attempts.24-certified-depth-approximation.work.consumer_v3.test_termination"
).TerminationTests

CompactTerminationTests = import_module(
    "attempts.24-certified-depth-approximation.work.consumer_v3.test_compact_termination"
).CompactTerminationTests
