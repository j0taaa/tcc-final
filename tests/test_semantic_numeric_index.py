"""Independent semantic numerical CDF/quantile oracles, finite rational source."""

from importlib import import_module

SemanticIndexTests = import_module(
    "attempts.60-semantic-numeric-index.work.test_semantic_index"
).SemanticIndexTests
