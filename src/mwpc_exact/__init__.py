"""Shared finite-token data contracts. Algorithms live in their explicit modules."""

from mwpc_exact.backend import ExactBackend
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import PerPositionSupport, SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactCommitResult, ExactnessScope, Proposal, SolveStatus, SupportKind

__all__ = [
    "CompositionalByteLevelAdapter",
    "EOSMode",
    "EOSPolicy",
    "ExactBackend",
    "ExactCommitResult",
    "ExactnessScope",
    "PerPositionSupport",
    "Proposal",
    "SelectionInput",
    "SolveStatus",
    "SupportKind",
    "SupportPolicy",
    "build_per_position_support",
]
