"""Exact maximum-weight parallel commitment research package."""

from mwpc_exact.support import (
    PerPositionSupport,
    SupportInputSource,
    SupportPolicy,
    build_per_position_support,
    canonical_support_rows_json,
    support_rows_sha256,
)
from mwpc_exact.token_lattice import (
    TokenChoice,
    TokenLattice,
    TokenLatticePath,
    build_token_lattice,
)
from mwpc_exact.tokenizer_bytes import (
    BYTE_LEVEL_ALPHABET,
    CompositionalByteLevelAdapter,
    UnsupportedTokenError,
    byte_level_piece_to_bytes,
)
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
    "BYTE_LEVEL_ALPHABET",
    "AggregatedProposal",
    "CompositionalByteLevelAdapter",
    "EOSWitnessValidator",
    "EpsilonEdge",
    "ExactCommitResult",
    "ExactnessScope",
    "GrammarRecognizer",
    "PerPositionSupport",
    "Proposal",
    "SolveStatus",
    "SupportInputSource",
    "SupportKind",
    "SupportPolicy",
    "TerminalEdge",
    "TokenArc",
    "TokenChoice",
    "TokenLattice",
    "TokenLatticePath",
    "TokenizerWitnessValidator",
    "UnsupportedTokenError",
    "ValidationCode",
    "ValidationIssue",
    "ValidationReport",
    "WeightedTerminalDAG",
    "aggregate_proposals",
    "build_per_position_support",
    "build_token_lattice",
    "byte_level_piece_to_bytes",
    "canonical_support_rows_json",
    "support_rows_sha256",
    "validate_exact_commit_certificate",
]
