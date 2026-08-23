"""Exact maximum-weight parallel commitment research package."""

from mwpc_exact.types import (
    AggregatedProposal,
    ExactCommitResult,
    ExactCommitStatus,
    ExactnessScope,
    Proposal,
    SolveStatus,
    SupportKind,
    TerminalEdge,
    TokenArc,
    WeightedTerminalDAG,
    aggregate_proposals,
)

__all__ = [
    "AggregatedProposal",
    "ExactCommitResult",
    "ExactCommitStatus",
    "ExactnessScope",
    "Proposal",
    "SolveStatus",
    "SupportKind",
    "TerminalEdge",
    "TokenArc",
    "WeightedTerminalDAG",
    "aggregate_proposals",
]
