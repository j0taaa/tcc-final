"""Independent original-ID/tied-parameter oracles for the A58 controls."""

import importlib

StrongHeadTests = importlib.import_module(
    "attempts.58-streamed-grammar-loss.work.test_strong_head"
).StrongHeadTests
