"""Optional native SAT reference over a larger, explicitly inactive reservoir."""

from .native_sat import SatPrefix


class ReserveSat(SatPrefix):
    def __init__(self, plan, active_rows):
        self.active_rows = tuple(frozenset(row) for row in active_rows)
        if any(not r.issubset(plan.state.support.rows[p]) for p, r in enumerate(self.active_rows)):
            raise ValueError("active support outside reservoir")
        super().__init__(plan)
