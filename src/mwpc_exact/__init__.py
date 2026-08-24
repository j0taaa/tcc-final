"""Exact maximum-weight parallel commitment research package."""

from mwpc_exact.types import (
    AggregatedProposal,
    EpsilonEdge,
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    SupportKind,
    TerminalEdge,
    TokenArc,
    WeightedTerminalDAG,
    aggregate_proposals,
)
from mwpc_exact.validator import (
    EOSWitnessValidator,
    GrammarRecognizer,
    TokenizerWitnessValidator,
    ValidationCode,
    ValidationIssue,
    ValidationReport,
    validate_exact_commit_certificate,
)

__all__ = [
    "AggregatedProposal",
    "EOSWitnessValidator",
    "EpsilonEdge",
    "ExactCommitResult",
    "ExactnessScope",
    "GrammarRecognizer",
    "Proposal",
    "SolveStatus",
    "SupportKind",
    "TerminalEdge",
    "TokenArc",
    "TokenizerWitnessValidator",
    "ValidationCode",
    "ValidationIssue",
    "ValidationReport",
    "WeightedTerminalDAG",
    "aggregate_proposals",
    "validate_exact_commit_certificate",
]
