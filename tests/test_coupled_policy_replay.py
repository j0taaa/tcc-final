"""Small rational coupling/work oracles, no pretrained model dependencies."""

from importlib import import_module

CoupledPolicyTests = import_module(
    "attempts.54-coupled-policy-replay.work.test_coupling"
).CoupledPolicyTests

LengthReadoutTests = import_module(
    "attempts.54-coupled-policy-replay.work.test_length_readout"
).LengthReadoutTests
