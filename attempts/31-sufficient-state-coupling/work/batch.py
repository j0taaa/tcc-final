"""A31 reference on explicit tiny kernels; not an EPIC replacement/parser."""

from dataclasses import dataclass

from .ledger import HistoryLedger


@dataclass(frozen=True)
class Kernel:
    # One row per uniform primary ticket; a uniform independent auxiliary
    # chooses among the row's actions. Actual model noise remains native.
    rows: tuple[tuple[object, ...], ...]

    def __post_init__(self):
        if not self.rows or any(not row for row in self.rows):
            raise ValueError("kernel rows and auxiliary supports must be nonempty")

    def step(self, ticket, rng):
        row = self.rows[ticket]
        return row[rng.randrange(len(row))]


def decode(kernel_for, initial, size, horizon, rng, *, mode="state", order=None, summary=None):
    """Return original state traces, using one fixed-K ledger per batch.

    kernel_for(t,s) must be pure and s sufficient. summary is an optional
    candidate state map; its sufficiency is the CALLER'S proof obligation.
    Modes compare identical operations. Complete states/traces stay in output.
    """
    if mode not in ("state", "history", "iid", "root"):
        raise ValueError("unknown coupling mode")
    if type(horizon) is not int or horizon < 0:
        raise ValueError("finite nonnegative horizon required")
    book = HistoryLedger(size, rng)
    traces = [(initial,)] * size
    if order is None:
        order = [(label, t) for t in range(horizon) for label in range(size)]
    for label, t in order:
        if (
            type(label) is not int
            or not 0 <= label < size
            or type(t) is not int
            or not 0 <= t < horizon
            or len(traces[label]) != t + 1
        ):
            raise ValueError("service order is not a valid per-label trajectory")
        state = traces[label][-1]
        kernel = kernel_for(t, state)
        if not isinstance(kernel, Kernel):
            raise TypeError("explicit finite kernel required")
        if mode == "iid" or (mode == "root" and t > 0):
            ticket = rng.randrange(len(kernel.rows))
        else:
            key = traces[label] if mode == "history" else state
            if summary is not None:
                key = summary(t, state, traces[label])
            ticket = book.draw((t, key), label, len(kernel.rows))
        traces[label] = (*traces[label], kernel.step(ticket, rng))
    if any(len(h) != horizon + 1 for h in traces):
        raise ValueError("service order did not finish every trajectory")
    return tuple(traces)
