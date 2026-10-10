"""Independent original-token oracles for the canonical epsilon compiler."""

from importlib import import_module

EpsilonCorrectness = import_module(
    "attempts.23-canonical-epsilon-posterior.work.test_correctness"
).FullVocabularyCorrectness
