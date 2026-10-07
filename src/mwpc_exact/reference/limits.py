"""Cooperative deadline and pre-allocation work limits for CFG compilation."""

from dataclasses import dataclass, field
from math import isfinite
from time import monotonic


class CompilationLimit(TimeoutError):
    """Unresolved work/deadline limit, never evidence of zero valid mass."""


@dataclass
class WorkBudget:
    """Share across preprocessing stages; deadline also covers forest building.

    Work counts symbol visits/copies and intermediate alternatives, rather than
    wall time or exact bytes. Check projected expansion before allocating it.
    This is cooperative cancellation, not an OS memory limit or hard preemption.
    """

    max_work: int | None = None
    deadline: float | None = None
    used: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_work is not None and (type(self.max_work) is not int or self.max_work < 0):
            raise ValueError("preprocessing work limit must be a non-negative integer")
        if self.deadline is not None and (
            isinstance(self.deadline, bool)
            or not isinstance(self.deadline, (int, float))
            or not isfinite(self.deadline)
        ):
            raise ValueError("deadline must be finite")

    def check(self) -> None:
        if self.deadline is not None and monotonic() >= self.deadline:
            raise CompilationLimit("compilation deadline; feasibility remains unresolved")

    def consume(self, amount: int = 1) -> None:
        self.check()
        if self.max_work is not None and amount > self.max_work - self.used:
            raise CompilationLimit("preprocessing work budget; feasibility remains unresolved")
        self.used += amount
