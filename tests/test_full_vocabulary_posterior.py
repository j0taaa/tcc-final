"""Offline exact-law and independent original-token enumeration oracles."""

from importlib import import_module

FullVocabularyCorrectness = import_module(
    "attempts.22-full-vocabulary-posterior.work.test_correctness"
).FullVocabularyCorrectness
