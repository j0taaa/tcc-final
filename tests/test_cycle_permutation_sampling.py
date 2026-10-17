"""Rational assignment/soup oracles; no pretrained model or Monte Carlo claims."""

from importlib import import_module

CycleTests = import_module("attempts.55-cycle-permutation-sampling.work.oracles").CycleOracles
