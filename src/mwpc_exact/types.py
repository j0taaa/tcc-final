"""Scientific data contracts shared by reference and production solvers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any, Literal


class ExactCommitStatus(StrEnum):
    """Mutually exclusive solver outcomes."""

    OPTIMAL = "optimal"
    INFEASIBLE_ON_SUPPORT = "infeasible_on_support"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ExactnessScope:
    """Finite domain over which an optimality claim is valid."""

    kind: Literal["full_vocabulary", "finite_support"]
    description: str
    top_k: int | None = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("exactness scope requires a non-empty description")
        if self.kind == "full_vocabulary" and self.top_k is not None:
            raise ValueError("full-vocabulary scope cannot define top_k")
        if self.top_k is not None and self.top_k <= 0:
            raise ValueError("top_k must be positive")


@dataclass(frozen=True, slots=True)
class Proposal:
    """One weighted model proposal for one physical token slot."""

    proposal_id: str
    position: int
    token_id: int
    weight: float
    model_confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            raise ValueError("proposal_id must be non-empty")
        if self.position < 0:
            raise ValueError("position must be non-negative")
        if self.token_id < 0:
            raise ValueError("token_id must be non-negative")
        if not isfinite(self.weight) or self.weight < 0:
            raise ValueError("weight must be finite and non-negative")
        if self.model_confidence is not None and not isfinite(self.model_confidence):
            raise ValueError("model_confidence must be finite when provided")


@dataclass(frozen=True, slots=True)
class ExactCommitResult:
    """Solver result plus the certificate needed for independent validation."""

    status: ExactCommitStatus
    exactness_scope: ExactnessScope
    objective_value: float | None = None
    selected_proposal_ids: tuple[str, ...] = ()
    witness_token_ids: tuple[int, ...] = ()
    witness_terminal_labels: tuple[str, ...] = ()
    witness_graph_edge_ids: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.objective_value is not None:
            if not isfinite(self.objective_value) or self.objective_value < 0:
                raise ValueError("objective_value must be finite and non-negative")

        if self.status is ExactCommitStatus.OPTIMAL:
            if self.objective_value is None:
                raise ValueError("OPTIMAL requires objective_value")
            if not self.witness_token_ids:
                raise ValueError("OPTIMAL requires a non-empty witness token sequence")
            if not self.witness_graph_edge_ids:
                raise ValueError("OPTIMAL requires a reconstructible witness path")
        elif self.selected_proposal_ids:
            raise ValueError("non-OPTIMAL results cannot claim selected proposals")
