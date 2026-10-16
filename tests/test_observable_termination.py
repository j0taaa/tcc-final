"""Small research oracle; no pretrained heads or real-path measurements."""

import importlib

FlatLanguageTests = importlib.import_module(
    "attempts.53-observable-termination.work.test_flat_language"
).FlatLanguageTests

TerminalCompilerTests = importlib.import_module(
    "attempts.53-observable-termination.work.test_terminal_compiler"
).TerminalCompilerTests
