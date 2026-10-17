"""Independent exact source-logit and population-score identities."""

from importlib import import_module

ScientificScoreTests = import_module(
    "attempts.61-scientific-semantic-score.work.test_reference"
).ScientificScoreTests
