"""Model-independent budget result, importable without the optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from mwpc_exact.budget_graph import CompiledBudgetGraph
from mwpc_exact.reference.budget_types import BudgetPathResult, ResourceDAG, nonnegative_integer
from mwpc_exact.types import ExactnessScope, SolveStatus


@dataclass(frozen=True)
class BudgetedCommitResult:
    status: SolveStatus
    budget: int
    objective_value: Fraction | None
    committed_positions: tuple[int, ...]
    committed_proposal_ids: tuple[int, ...]
    matched_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...] | None
    witness_terminal_labels: tuple[int | str, ...] | None
    exactness_scope: ExactnessScope
    path_result: BudgetPathResult
    proof_graph: ResourceDAG
    input_fingerprint: str
    compiled_graph: CompiledBudgetGraph

    def __post_init__(self) -> None:
        # Python's True == 1 must not let malformed certificate IDs masquerade
        # as the independently recomputed identifiers.
        if not isinstance(self.status, SolveStatus):
            raise ValueError("status must be a SolveStatus")
        nonnegative_integer(self.budget, "budget")
        if self.objective_value is not None and (
            not isinstance(self.objective_value, Fraction) or self.objective_value < 0
        ):
            raise ValueError("objective must be a non-negative exact Fraction")
        for field in (
            "committed_positions",
            "committed_proposal_ids",
            "matched_proposal_ids",
            "witness_token_ids",
        ):
            values = getattr(self, field)
            if values is None and field == "witness_token_ids":
                continue
            if isinstance(values, (str, bytes)) or values is None:
                raise ValueError(f"{field} must contain integer identifiers")
            values = tuple(values)
            for value in values:
                nonnegative_integer(value, field)
            object.__setattr__(self, field, values)
        if self.witness_terminal_labels is not None:
            labels = tuple(self.witness_terminal_labels)
            for label in labels:
                if (
                    isinstance(label, bool)
                    or not isinstance(label, (int, str))
                    or (isinstance(label, int) and not 0 <= label <= 255)
                    or label == ""
                ):
                    raise ValueError("terminal label must be a byte or nonempty string")
            object.__setattr__(self, "witness_terminal_labels", labels)
