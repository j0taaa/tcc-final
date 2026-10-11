"""A30: fixed-K strata revealed lazily by complete history, not by canvas."""

from dataclasses import dataclass, field


@dataclass
class _Table:
    total: int
    remaining: int
    pool: dict[int, int] = field(default_factory=dict)
    tickets: dict[int, int] = field(default_factory=dict)


class HistoryLedger:
    """One ledger per fixed batch; caller supplies pure, full-history keys.

    RNG must expose independent uniform randrange(n) draws. Repeated (h,label)
    requests are idempotent. This reference is serial, not thread-safe; total
    cannot change at an existing node. It never looks at a verifier or output.
    """

    def __init__(self, size, rng):
        if type(size) is not int or size < 1:
            raise ValueError("batch size must be a positive integer")
        if not callable(getattr(rng, "randrange", None)):
            raise TypeError("explicit uniform integer RNG required")
        self.size, self.rng, self.tables = size, rng, {}

    def draw(self, history, label, total):
        if type(label) is not int or not 0 <= label < self.size:
            raise ValueError("label outside the fixed batch")
        if type(total) is not int or total < 1:
            raise ValueError("positive integer ticket count required")
        hash(history)
        table = self.tables.get(history)
        if table is None:
            table = _Table(total, self.size)
            self.tables[history] = table
        if total != table.total:
            raise ValueError("kernel ticket count changed at an existing history")
        if label not in table.tickets:
            # Deferred decisions of a uniform permutation: allocate a stratum
            # only when its label arrives, without materializing K items.
            j = self.rng.randrange(table.remaining)
            stratum = table.pool.get(j, j)
            table.remaining -= 1
            table.pool[j] = table.pool.get(table.remaining, table.remaining)
            table.pool.pop(table.remaining, None)
            table.tickets[label] = (stratum * total + self.rng.randrange(total)) // self.size
        return table.tickets[label]


def _double_ticket(ticket):
    if type(ticket) is not int or not 0 <= ticket < 2**53:
        raise ValueError("uniform-double ticket must have53 bits")


def cpu_double(ticket):
    """Audited PyTorch2.8 CPU float64 transformation, not a softmax law."""
    _double_ticket(ticket)
    return ticket * 2**-53


def cuda_double(ticket):
    """Audited curand double-hq rounding plus PyTorch2.8 reversed upper bound."""
    _double_ticket(ticket)
    value = ticket * 2**-53 + 2**-54
    return 0.0 if value == 1.0 else value
