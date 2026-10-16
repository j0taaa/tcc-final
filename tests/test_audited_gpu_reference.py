"""Offline law oracles; no optional CUDA dependency in the maintained suite."""

from importlib import import_module

ExecutedProposalTests = import_module(
    "attempts.51-audited-gpu-posterior.work.test_reference"
).ExecutedProposalTests

RetainedIntervalTests = import_module(
    "attempts.51-audited-gpu-posterior.work.test_reference"
).RetainedIntervalTests
