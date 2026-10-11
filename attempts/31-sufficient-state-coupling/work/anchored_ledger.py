"""Conditional fixed-K strata retaining the first visitor's original ticket."""

from .ledger import HistoryLedger, _Table, cpu_double, cuda_double


class AnchoredLedger(HistoryLedger):
    def anchor(self, history, label, total, ticket):
        if type(label) is not int or not 0 <= label < self.size:
            raise ValueError("label outside fixed batch")
        if type(total) is not int or total < 1:
            raise ValueError("positive ticket count required")
        if type(ticket) is not int or not 0 <= ticket < total:
            raise ValueError("original ticket outside support")
        hash(history)
        if history in self.tables:
            raise ValueError("anchor requires a fresh node")
        stratum = (ticket * self.size + self.rng.randrange(self.size)) // total
        remaining = self.size - 1
        pool = {stratum: remaining} if stratum < remaining else {}
        self.tables[history] = _Table(total, remaining, pool, {label: ticket})
        return ticket


def observed_ticket(value, profile, rng):
    """Exact conditional latent-ticket law for audited Torch2.8 f64 profiles."""
    if type(value) is not float or not 0 <= value < 1:
        raise ValueError("unsupported observed uniform-double")
    total = 2**53
    if profile == "cpu":
        tickets = (int(value * total),)
        convert = cpu_double
    elif profile == "cuda":
        if value == 0:
            tickets = (total - 1,)
        elif value <= 0.5:
            tickets = (int(value * total),)
        else:
            upper = int(value * total)
            tickets = (upper - 1, upper)
        convert = cuda_double
    else:
        raise ValueError("unsupported uniform profile")
    if any(not 0 <= i < total or convert(i) != value for i in tickets):
        raise ValueError("observed value is outside audited grid")
    return tickets[0] if len(tickets) == 1 else tickets[rng.randrange(len(tickets))]
