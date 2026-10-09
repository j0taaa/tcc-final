"""Independent JSON recognition + competent original-token bitset control."""

import itertools
import json
from collections import defaultdict
from math import prod

from monotone import Monotone


class Enumeration:
    transition = Monotone.transition

    def __init__(self, state, *, max_products=1_000_000):
        if prod(map(len, state.support.rows)) > max_products:
            raise OverflowError("enumeration_product_budget")
        self.canvas = list(state.canvas)
        self.index = [dict((t, i) for i, t in enumerate(row)) for row in state.support.rows]
        self.bits = defaultdict(int)
        accepted = 0
        for path in itertools.product(*state.support.rows):
            words = [state.tokenizer_adapter.emissions[t] for t in path]
            if any(w is None for w in words):
                continue
            try:
                json.loads(b"".join(words), parse_constant=self.reject_constant)
            except (ValueError, UnicodeDecodeError):
                continue
            bit = 1 << accepted
            accepted += 1
            for p, token in enumerate(path):
                self.bits[p, token] |= bit
        if not accepted:
            raise ValueError("infeasible_on_support")
        self.domain = (1 << accepted) - 1
        self.valid_paths = accepted

    @staticmethod
    def reject_constant(value):
        raise ValueError(value)

    def feasible(self, position, token):
        return bool(self.domain & self.bits[position, token])

    def commit(self, position, token):
        if not self.feasible(position, token):
            raise ValueError("incompatible commitment")
        self.domain &= self.bits[position, token]
        self.canvas[position] = token
